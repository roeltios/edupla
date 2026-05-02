import os
import re
import textwrap
import calendar
from datetime import date, datetime, time, timedelta
from functools import wraps
from io import BytesIO
from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, send_file, session, url_for
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import inspect
from werkzeug.utils import secure_filename

from extensions import db
from models import (
    Comment,
    Course,
    CourseModule,
    GRADE_LEVELS,
    MANUAL_TOPICS,
    ISTEStandard,
    LearningExperience,
    LearningExperienceEvaluation,
    LearningExperienceEvaluationScore,
    LearningExperienceRequirement,
    LearningExperienceRubric,
    ProjectRubric,
    ProjectRubricCriterion,
    ProjectManualSchedule,
    ProjectManualTheme,
    ManualSessionPlan,
    Material,
    ProjectManual,
    RubricBankItem,
    Resource,
    User,
    WeeklyPlan,
    course_teacher,
)


main_bp = Blueprint('main', __name__)

WORKFLOW_STATUSES = {'draft', 'review', 'published'}
BOARD_STAGES = {'por_planear', 'lista', 'en_clase', 'ajustar', 'archivada'}
USER_ROLES = {'admin', 'teacher'}
SCHEDULE_STATUSES = {'planned', 'done', 'canceled'}

BASE_RUBRIC_BANK_TEMPLATES = [
    {
        'name': 'Dominio conceptual',
        'dimension': 'Aprendizaje',
        'description': 'Comprende y explica los conceptos clave trabajados en la experiencia.',
        'default_weight': 25,
    },
    {
        'name': 'Analisis y argumentacion disciplinar',
        'dimension': 'Aprendizaje',
        'description': 'Analiza informacion relevante y sustenta ideas con evidencia.',
        'default_weight': 40,
    },
    {
        'name': 'Transferencia de aprendizajes',
        'dimension': 'Aprendizaje',
        'description': 'Aplica conceptos en situaciones nuevas y contextualizadas.',
        'default_weight': 35,
    },
    {
        'name': 'Aplicacion practica',
        'dimension': 'Desempeno',
        'description': 'Aplica lo aprendido para resolver una tarea o reto concreto.',
        'default_weight': 30,
    },
    {
        'name': 'Calidad del producto o evidencia',
        'dimension': 'Desempeno',
        'description': 'Produce evidencias claras, completas y alineadas al objetivo.',
        'default_weight': 35,
    },
    {
        'name': 'Autonomia en la ejecucion',
        'dimension': 'Desempeno',
        'description': 'Gestiona tiempos y recursos para completar tareas con autonomia.',
        'default_weight': 35,
    },
    {
        'name': 'Colaboracion y comunicacion',
        'dimension': 'Socioemocional',
        'description': 'Colabora de forma activa y comunica ideas con claridad.',
        'default_weight': 20,
    },
    {
        'name': 'Escucha activa y respeto',
        'dimension': 'Socioemocional',
        'description': 'Escucha y valora aportes de otros con actitud respetuosa.',
        'default_weight': 40,
    },
    {
        'name': 'Gestion emocional y perseverancia',
        'dimension': 'Socioemocional',
        'description': 'Maneja frustracion y sostiene el esfuerzo ante desafios.',
        'default_weight': 40,
    },
    {
        'name': 'Uso responsable de tecnologia',
        'dimension': 'Ciudadania digital',
        'description': 'Utiliza herramientas digitales con seguridad y etica.',
        'default_weight': 15,
    },
    {
        'name': 'Seguridad y proteccion de datos',
        'dimension': 'Ciudadania digital',
        'description': 'Cuida credenciales, privacidad y gestion responsable de datos.',
        'default_weight': 45,
    },
    {
        'name': 'Huella digital y convivencia en linea',
        'dimension': 'Ciudadania digital',
        'description': 'Interactua con respeto y conciencia del impacto de sus acciones en linea.',
        'default_weight': 40,
    },
    {
        'name': 'Creatividad e innovacion',
        'dimension': 'Pensamiento creativo',
        'description': 'Propone soluciones originales y mejora iterativamente su producto.',
        'default_weight': 10,
    },
    {
        'name': 'Originalidad de propuestas',
        'dimension': 'Pensamiento creativo',
        'description': 'Genera ideas novedosas y pertinentes para el reto planteado.',
        'default_weight': 45,
    },
    {
        'name': 'Iteracion y mejora de ideas',
        'dimension': 'Pensamiento creativo',
        'description': 'Refina propuestas con base en retroalimentacion y pruebas.',
        'default_weight': 45,
    },
]


def _ensure_default_admin():
    if not inspect(db.engine).has_table('user'):
        return

    if User.query.first() is not None:
        return

    admin = User(
        full_name='Administrador Inicial',
        email='admin@edupla.local',
        role='admin',
    )
    admin.set_password('admin1234')
    db.session.add(admin)
    db.session.commit()


def _current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.session.get(User, user_id)


def _is_admin():
    return bool(g.current_user and g.current_user.role == 'admin')


def _is_teacher():
    return bool(g.current_user and g.current_user.role == 'teacher')


def _accessible_course_ids():
    if _is_admin():
        return None
    if not g.current_user:
        return set()
    return {course.id for course in g.current_user.courses}


def _assert_course_access(course):
    if _is_admin():
        return
    if not g.current_user:
        abort(401)
    if course.id not in _accessible_course_ids():
        abort(403)


def _assert_module_access(module):
    _assert_course_access(module.course)


def _assert_experience_access(experience):
    if experience.module is None:
        if _is_admin():
            return
        abort(403)
    _assert_module_access(experience.module)


def _normalize_week_start(reference_date):
    return reference_date - timedelta(days=reference_date.weekday())


def _parse_date_arg(value, fallback):
    try:
        return datetime.strptime((value or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return fallback


def _parse_local_datetime_arg(value):
    try:
        return datetime.strptime((value or '').strip(), '%Y-%m-%dT%H:%M')
    except ValueError:
        return None


def _schedule_query_for_current_user():
    query = ProjectManualSchedule.query
    if _is_teacher():
        query = query.filter(ProjectManualSchedule.user_id == g.current_user.id)
    return query


def _assert_schedule_access(schedule_item):
    if _is_admin() or schedule_item.user_id == g.current_user.id:
        return
    abort(403, description='No tienes permisos para gestionar esta sesion calendarizada.')


def _validate_schedule_conflict(start_at, end_at, current_schedule_id=None):
    conflict_query = _schedule_query_for_current_user().filter(
        ProjectManualSchedule.start_at < end_at,
        ProjectManualSchedule.end_at > start_at,
    )
    if current_schedule_id is not None:
        conflict_query = conflict_query.filter(ProjectManualSchedule.id != current_schedule_id)
    return conflict_query.first()


def _dashboard_redirect_for_date(target_date, manual_id=None):
    return_view = (request.form.get('return_view') or 'week').strip().lower()
    if return_view == 'month':
        return redirect(url_for('main.dashboard', view='month', date=target_date.isoformat(), manual_id=manual_id))
    return redirect(url_for('main.dashboard', view='week', week_start=_normalize_week_start(target_date).isoformat(), manual_id=manual_id))


def login_required(view_func):
    @wraps(view_func)
    def _wrapped(*args, **kwargs):
        if not g.current_user:
            return redirect(url_for('main.login', next=request.path))
        return view_func(*args, **kwargs)

    return _wrapped


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(*args, **kwargs):
        if not _is_admin():
            abort(403)
        return view_func(*args, **kwargs)

    return _wrapped


@main_bp.before_app_request
def _load_user_context():
    # Keep the first-run experience simple while introducing role-based auth.
    _ensure_default_admin()
    g.current_user = _current_user()


@main_bp.app_context_processor
def inject_user_context():
    return {
        'current_user': g.current_user,
        'is_admin': _is_admin(),
        'is_teacher': _is_teacher(),
    }


def _copy_template_fields(template, target):
    target.title = f'{template.title} (copia)'
    target.level = template.level
    target.module_id = template.module_id
    target.teacher_profile = template.teacher_profile
    target.course_focus = template.course_focus
    target.learning_objective = template.learning_objective
    target.classroom_application = template.classroom_application
    target.minimal_technology = template.minimal_technology
    target.estimated_duration = template.estimated_duration
    target.planning_markdown = template.planning_markdown
    target.image_file = template.image_file
    target.workflow_status = 'draft'
    target.board_stage = 'por_planear'
    target.week_slot = 1
    target.is_template = False
    target.iste_standards = list(template.iste_standards)

    target.requirements.clear()
    for requirement in template.requirements:
        target.requirements.append(
            LearningExperienceRequirement(
                material_id=requirement.material_id,
                quantity_needed=requirement.quantity_needed,
            )
        )


def seed_iste_standards():
    if ISTEStandard.query.first():
        return

    codes = [
        ('1.1', 'Aprendiz Empoderado'),
        ('1.2', 'Ciudadano Digital'),
        ('1.3', 'Constructor de Conocimiento'),
        ('1.4', 'Diseñador Innovador'),
        ('1.5', 'Pensador Computacional'),
        ('1.6', 'Comunicador Creativo'),
        ('1.7', 'Colaborador Global'),
    ]
    for code, description in codes:
        db.session.add(ISTEStandard(code=code, description=description))
    db.session.commit()


def seed_rubric_bank_items():
    has_changes = False
    for item in BASE_RUBRIC_BANK_TEMPLATES:
        existing = RubricBankItem.query.filter(RubricBankItem.name.ilike(item['name'])).first()
        if existing is None:
            db.session.add(
                RubricBankItem(
                    name=item['name'],
                    dimension=item['dimension'],
                    description=item['description'],
                    default_weight=item['default_weight'],
                    is_system=True,
                )
            )
            has_changes = True
            continue

        if existing.is_system and existing.dimension == item['dimension']:
            if existing.default_weight != item['default_weight']:
                existing.default_weight = item['default_weight']
                has_changes = True

    if has_changes:
        db.session.commit()


def _extract_total_minutes(duration_text):
    text = (duration_text or '').lower()
    sessions_match = re.search(r'(\d+)\s*sesion', text)
    minutes_match = re.search(r'(\d+)\s*min', text)
    hours_match = re.search(r'(\d+)\s*hora', text)

    if sessions_match and minutes_match:
        return int(sessions_match.group(1)) * int(minutes_match.group(1))
    if minutes_match:
        return int(minutes_match.group(1))
    if hours_match:
        return int(hours_match.group(1)) * 60
    return 120


def _build_weekly_plan(learning_experience):
    total_minutes = _extract_total_minutes(learning_experience.estimated_duration)
    suggested_weeks = max(1, min(6, (total_minutes + 99) // 100))
    requirements = learning_experience.requirements[:3]
    materials_text = ', '.join(req.material.name for req in requirements) if requirements else 'Materiales basicos del aula'
    level = (learning_experience.level or 'General').strip()

    week_prompts = [
        ('Diagnostico y contexto', 'Activar saberes previos, identificar necesidades y presentar el reto.'),
        ('Construccion guiada', 'Desarrollar la actividad central con modelado y acompanamiento docente.'),
        ('Practica autonoma', 'Resolver un reto con menor intervencion y registrar evidencias.'),
        ('Iteracion y mejora', 'Corregir, optimizar y justificar cambios a partir de retroalimentacion.'),
        ('Transferencia', 'Aplicar lo aprendido en un contexto nuevo del aula o comunidad.'),
        ('Socializacion y cierre', 'Presentar resultados, reflexionar sobre logros y definir siguientes pasos.'),
    ]

    plan = []
    for week in range(1, suggested_weeks + 1):
        title, objective = week_prompts[week - 1]
        plan.append(
            {
                'week': week,
                'title': title,
                'objective': objective,
                'activities': [
                    f'Sesion de {level}: mini-reto alineado al objetivo semanal.',
                    f'Trabajo practico con enfoque en {learning_experience.course_focus or "tecnologia educativa"}.',
                    f'Registro de evidencias en bitacora usando {materials_text}.',
                ],
                'assessment_focus': 'Observacion de desempeno + lista de cotejo por criterio de rubrica.',
                'expected_product': 'Evidencia parcial documentada y retroalimentada por el docente.',
            }
        )

    return plan


def _draw_wrapped_text(pdf_canvas, text, x, y, max_chars=110, line_height=13, font_name='Helvetica', font_size=10):
    pdf_canvas.setFont(font_name, font_size)
    lines = textwrap.wrap(text or '', width=max_chars) or ['']
    for line in lines:
        if y < 40:
            pdf_canvas.showPage()
            y = A4[1] - 40
            pdf_canvas.setFont(font_name, font_size)
        pdf_canvas.drawString(x, y, line)
        y -= line_height
    return y


def _build_experience_pdf(learning_experience):
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    y = A4[1] - 40

    y = _draw_wrapped_text(
        pdf_canvas,
        f'Experiencia: {learning_experience.title}',
        36,
        y,
        max_chars=85,
        line_height=16,
        font_name='Helvetica-Bold',
        font_size=14,
    )
    y -= 6
    y = _draw_wrapped_text(pdf_canvas, f'Nivel: {learning_experience.level or "General"}', 36, y)
    y = _draw_wrapped_text(pdf_canvas, f'Duracion estimada: {learning_experience.estimated_duration or "No definida"}', 36, y)
    y = _draw_wrapped_text(pdf_canvas, f'Perfil docente: {learning_experience.teacher_profile or "No definido"}', 36, y)
    y = _draw_wrapped_text(pdf_canvas, f'Enfoque: {learning_experience.course_focus or "No definido"}', 36, y)
    y -= 4

    y = _draw_wrapped_text(pdf_canvas, 'Objetivo de aprendizaje:', 36, y, font_name='Helvetica-Bold')
    y = _draw_wrapped_text(pdf_canvas, learning_experience.learning_objective or 'Sin objetivo registrado.', 36, y)
    y -= 4

    y = _draw_wrapped_text(pdf_canvas, 'Aplicacion en aula:', 36, y, font_name='Helvetica-Bold')
    y = _draw_wrapped_text(pdf_canvas, learning_experience.classroom_application or 'Sin aplicacion registrada.', 36, y)
    y -= 4

    y = _draw_wrapped_text(pdf_canvas, 'Materiales requeridos:', 36, y, font_name='Helvetica-Bold')
    if learning_experience.requirements:
        for req in learning_experience.requirements:
            y = _draw_wrapped_text(pdf_canvas, f'- {req.material.name}: {req.quantity_needed}', 46, y)
    else:
        y = _draw_wrapped_text(pdf_canvas, '- Sin materiales registrados.', 46, y)
    y -= 4

    y = _draw_wrapped_text(pdf_canvas, 'Rubrica de evaluacion:', 36, y, font_name='Helvetica-Bold')
    rubrics = (
        LearningExperienceRubric.query.filter_by(learning_experience_id=learning_experience.id)
        .order_by(LearningExperienceRubric.dimension.asc(), LearningExperienceRubric.id.asc())
        .all()
    )
    if rubrics:
        for rubric in rubrics:
            y = _draw_wrapped_text(
                pdf_canvas,
                f'- {rubric.name} ({rubric.dimension}) | Peso {rubric.weight}%: {rubric.description or "Sin descripcion."}',
                46,
                y,
            )
    else:
        y = _draw_wrapped_text(pdf_canvas, '- Sin criterios configurados.', 46, y)
    y -= 4

    y = _draw_wrapped_text(pdf_canvas, 'Planeacion semanal sugerida:', 36, y, font_name='Helvetica-Bold')
    for week in _build_weekly_plan(learning_experience):
        y = _draw_wrapped_text(pdf_canvas, f'Semana {week["week"]}: {week["title"]}', 46, y, font_name='Helvetica-Bold')
        y = _draw_wrapped_text(pdf_canvas, f'Objetivo: {week["objective"]}', 46, y)
        for activity in week['activities']:
            y = _draw_wrapped_text(pdf_canvas, f'  - {activity}', 56, y)
        y = _draw_wrapped_text(pdf_canvas, f'Producto esperado: {week["expected_product"]}', 46, y)
        y -= 2

    pdf_canvas.showPage()
    pdf_canvas.save()
    buffer.seek(0)
    return buffer


def _is_allowed_image(image):
    filename = secure_filename(image.filename or '')
    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return (
        extension in current_app.config['ALLOWED_IMAGE_EXTENSIONS']
        and image.mimetype in current_app.config['ALLOWED_IMAGE_MIME_TYPES']
    )


def _save_image(image):
    if not _is_allowed_image(image):
        abort(400, description='Formato de imagen no permitido.')

    original_name = secure_filename(image.filename)
    extension = original_name.rsplit('.', 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    image.save(upload_path)
    return filename


def _delete_uploaded_image(filename):
    if not filename or filename == 'default.jpg':
        return

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)


def _apply_learning_experience_form(learning_experience):
    learning_experience.title = (request.form.get('title') or '').strip()
    if not learning_experience.title:
        abort(400, description='El titulo de la experiencia es obligatorio.')

    learning_experience.level = (request.form.get('level') or '').strip()
    learning_experience.module_id = int(request.form['module_id']) if request.form.get('module_id') else None
    learning_experience.teacher_profile = (request.form.get('teacher_profile') or 'Docente frente a grupo').strip()
    learning_experience.course_focus = (request.form.get('course_focus') or 'Tecnologia educativa').strip()
    learning_experience.learning_objective = (request.form.get('learning_objective') or '').strip()
    learning_experience.classroom_application = (request.form.get('classroom_application') or '').strip()
    learning_experience.minimal_technology = (request.form.get('minimal_technology') or 'Computadora con editor de codigo').strip()
    learning_experience.estimated_duration = (request.form.get('estimated_duration') or '60 minutos').strip()
    workflow_status = (request.form.get('workflow_status') or 'draft').strip().lower()
    learning_experience.workflow_status = workflow_status if workflow_status in WORKFLOW_STATUSES else 'draft'
    board_stage = (request.form.get('board_stage') or 'por_planear').strip().lower()
    learning_experience.board_stage = board_stage if board_stage in BOARD_STAGES else 'por_planear'
    week_slot = request.form.get('week_slot', type=int) or 1
    learning_experience.week_slot = max(1, min(16, week_slot))
    learning_experience.is_template = bool(request.form.get('is_template'))
    learning_experience.planning_markdown = request.form['planning']

    image = request.files.get('image')
    if image and image.filename:
        new_filename = _save_image(image)
        _delete_uploaded_image(learning_experience.image_file)
        learning_experience.image_file = new_filename

    selected_standards = []
    for iste_id in request.form.getlist('iste_ids'):
        if not iste_id.isdigit():
            continue
        standard = db.session.get(ISTEStandard, int(iste_id))
        if standard is not None:
            selected_standards.append(standard)
    learning_experience.iste_standards = selected_standards

    learning_experience.requirements.clear()
    material_names = request.form.getlist('material_names[]')
    quantities = request.form.getlist('quantities[]')
    for name, quantity in zip(material_names, quantities):
        clean_name = name.strip()
        clean_quantity = quantity.strip()
        if not clean_name or not clean_quantity:
            continue

        quantity_needed = int(clean_quantity)
        if quantity_needed <= 0:
            continue

        material = Material.query.filter(Material.name.ilike(clean_name)).first()
        if material is None:
            material = Material(name=clean_name, stock=0)
            db.session.add(material)
            db.session.flush()

        learning_experience.requirements.append(
            LearningExperienceRequirement(material_id=material.id, quantity_needed=quantity_needed)
        )


@main_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if g.current_user:
        return redirect(url_for('main.index'))

    next_url = request.args.get('next') or request.form.get('next') or url_for('main.index')
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        user = User.query.filter(db.func.lower(User.email) == email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Sesion iniciada.', 'success')
            return redirect(next_url)

        flash('Credenciales invalidas.', 'error')

    return render_template('login.html', next_url=next_url)


@main_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    flash('Sesion cerrada.', 'success')
    return redirect(url_for('main.login'))


@main_bp.route('/users', methods=['GET', 'POST'])
@admin_required
def users_admin():
    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        role = (request.form.get('role') or 'teacher').strip().lower()

        if not full_name or not email or not password:
            abort(400, description='Nombre, email y contrasena son obligatorios.')
        if role not in USER_ROLES:
            abort(400, description='Rol no permitido.')
        if User.query.filter(db.func.lower(User.email) == email).first():
            flash('Ya existe un usuario con ese email.', 'error')
            return redirect(url_for('main.users_admin'))

        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Usuario creado correctamente.', 'success')
        return redirect(url_for('main.users_admin'))

    users = User.query.order_by(User.role.asc(), User.full_name.asc()).all()
    return render_template('users.html', users=users)


@main_bp.route('/')
@login_required
def index():
    return redirect(url_for('main.manuals'))


@main_bp.route('/templates/library')
@login_required
def templates_library():
    templates = (
        LearningExperience.query.filter_by(is_template=True)
        .order_by(LearningExperience.created_at.desc())
        .all()
    )
    return render_template('templates_library.html', templates=templates)


@main_bp.route('/templates/<int:template_id>/use', methods=['POST'])
@admin_required
def use_template(template_id):
    template = LearningExperience.query.filter_by(id=template_id, is_template=True).first_or_404()
    new_learning_experience = LearningExperience(image_file=template.image_file or 'default.jpg')
    db.session.add(new_learning_experience)
    db.session.flush()
    _copy_template_fields(template, new_learning_experience)
    db.session.commit()
    flash('Plantilla aplicada. Ya puedes personalizar la nueva experiencia.', 'success')
    return redirect(url_for('main.edit_learning_experience', experience_id=new_learning_experience.id))


@main_bp.route('/board')
@login_required
def board():
    week = request.args.get('week', default=1, type=int)
    week = max(1, min(16, week))

    experiences_query = LearningExperience.query.filter_by(is_template=False, week_slot=week)
    if _is_teacher():
        accessible_ids = _accessible_course_ids()
        if not accessible_ids:
            experiences = []
        else:
            experiences = (
                experiences_query.join(CourseModule, LearningExperience.module_id == CourseModule.id)
                .filter(CourseModule.course_id.in_(accessible_ids))
                .order_by(LearningExperience.created_at.desc())
                .all()
            )
    else:
        experiences = experiences_query.order_by(LearningExperience.created_at.desc()).all()

    grouped = {
        'por_planear': [],
        'lista': [],
        'en_clase': [],
        'ajustar': [],
        'archivada': [],
    }
    for experience in experiences:
        grouped.setdefault(experience.board_stage or 'por_planear', []).append(experience)

    return render_template('board.html', week=week, grouped=grouped)


@main_bp.route('/board/move', methods=['POST'])
@admin_required
def move_board_card():
    experience_id = request.form.get('experience_id', type=int)
    experience = LearningExperience.query.filter_by(id=experience_id, is_template=False).first_or_404()

    board_stage = (request.form.get('board_stage') or 'por_planear').strip().lower()
    week_slot = request.form.get('week_slot', type=int) or experience.week_slot or 1
    if board_stage not in BOARD_STAGES:
        board_stage = 'por_planear'

    experience.board_stage = board_stage
    experience.week_slot = max(1, min(16, week_slot))
    db.session.commit()

    flash('Tarjeta movida en el tablero.', 'success')
    return redirect(url_for('main.board', week=experience.week_slot))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    view_mode = (request.args.get('view') or 'week').strip().lower()
    if view_mode not in {'week', 'month'}:
        view_mode = 'week'

    selected_date = _parse_date_arg(request.args.get('date'), today)
    week_start = _normalize_week_start(_parse_date_arg(request.args.get('week_start'), selected_date))
    week_days = [week_start + timedelta(days=offset) for offset in range(7)]
    month_start = selected_date.replace(day=1)
    month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)

    if view_mode == 'month':
        range_start = datetime.combine(month_start, time.min)
        range_end = datetime.combine(month_end, time.min)
    else:
        range_start = datetime.combine(week_start, time.min)
        range_end = range_start + timedelta(days=7)

    calendar_sessions = (
        _schedule_query_for_current_user()
        .join(ProjectManual)
        .filter(ProjectManualSchedule.start_at >= range_start, ProjectManualSchedule.start_at < range_end)
        .order_by(ProjectManualSchedule.start_at.asc())
        .all()
    )

    sessions_by_day = {}
    for schedule_item in calendar_sessions:
        schedule_day = schedule_item.start_at.date()
        sessions_by_day.setdefault(schedule_day, []).append(schedule_item)

    month_calendar = []
    if view_mode == 'month':
        month_weeks = calendar.monthcalendar(month_start.year, month_start.month)
        for week in month_weeks:
            week_row = []
            for day_num in week:
                week_row.append(month_start.replace(day=day_num) if day_num else None)
            month_calendar.append(week_row)

    selected_manual_id = request.args.get('manual_id', type=int)
    selected_manual = db.session.get(ProjectManual, selected_manual_id) if selected_manual_id else None
    manuals = ProjectManual.query.order_by(ProjectManual.grade_level.asc(), ProjectManual.title.asc()).all()

    prev_month = (month_start - timedelta(days=1)).replace(day=1)
    next_month = month_end

    return render_template(
        'dashboard.html',
        view_mode=view_mode,
        week_start=week_start,
        week_days=week_days,
        prev_week_start=(week_start - timedelta(days=7)).isoformat(),
        next_week_start=(week_start + timedelta(days=7)).isoformat(),
        month_start=month_start,
        month_name=month_start.strftime('%B %Y'),
        prev_month_start=prev_month.isoformat(),
        next_month_start=next_month.isoformat(),
        month_calendar=month_calendar,
        selected_date=selected_date,
        selected_manual=selected_manual,
        manuals=manuals,
        sessions_by_day=sessions_by_day,
        schedule_statuses=sorted(SCHEDULE_STATUSES),
    )


@main_bp.route('/dashboard/sessions/create', methods=['POST'])
@login_required
def create_dashboard_session():
    manual_id = request.form.get('manual_id', type=int)
    manual = db.session.get(ProjectManual, manual_id)
    if manual is None:
        abort(400, description='Selecciona un manual valido para calendarizar.')

    start_at = _parse_local_datetime_arg(request.form.get('start_at'))
    if start_at is None:
        abort(400, description='Selecciona una fecha y hora validas para la sesion.')

    duration_minutes = request.form.get('duration_minutes', type=int) or 120
    duration_minutes = max(30, min(360, duration_minutes))
    end_at = start_at + timedelta(minutes=duration_minutes)

    conflict = _validate_schedule_conflict(start_at, end_at)
    if conflict:
        flash('Ya tienes otra sesion en ese rango horario. Ajusta fecha u hora.', 'error')
        return _dashboard_redirect_for_date(start_at.date(), manual_id=manual.id)

    status = (request.form.get('status') or 'planned').strip().lower()
    if status not in SCHEDULE_STATUSES:
        status = 'planned'

    schedule_item = ProjectManualSchedule(
        manual_id=manual.id,
        user_id=g.current_user.id,
        title=(request.form.get('title') or '').strip() or manual.title,
        start_at=start_at,
        end_at=end_at,
        notes=(request.form.get('notes') or '').strip(),
        status=status,
    )
    db.session.add(schedule_item)
    db.session.commit()
    flash('Sesion calendarizada correctamente.', 'success')
    return _dashboard_redirect_for_date(start_at.date(), manual_id=manual.id)


@main_bp.route('/dashboard/sessions/<int:schedule_id>/update', methods=['POST'])
@login_required
def update_dashboard_session(schedule_id):
    schedule_item = db.session.get(ProjectManualSchedule, schedule_id)
    if schedule_item is None:
        abort(404)
    _assert_schedule_access(schedule_item)

    manual_id = request.form.get('manual_id', type=int)
    manual = db.session.get(ProjectManual, manual_id)
    if manual is None:
        abort(400, description='Selecciona un manual valido para la sesion.')

    start_at = _parse_local_datetime_arg(request.form.get('start_at'))
    if start_at is None:
        abort(400, description='Selecciona una fecha y hora validas para la sesion.')

    current_duration = int((schedule_item.end_at - schedule_item.start_at).total_seconds() // 60)
    duration_minutes = request.form.get('duration_minutes', type=int) or current_duration
    duration_minutes = max(30, min(360, duration_minutes))
    end_at = start_at + timedelta(minutes=duration_minutes)

    conflict = _validate_schedule_conflict(start_at, end_at, current_schedule_id=schedule_item.id)
    if conflict:
        flash('Esa actualizacion genera traslape con otra sesion tuya.', 'error')
        return _dashboard_redirect_for_date(start_at.date(), manual_id=manual.id)

    status = (request.form.get('status') or schedule_item.status or 'planned').strip().lower()
    if status not in SCHEDULE_STATUSES:
        status = 'planned'

    schedule_item.manual_id = manual.id
    schedule_item.title = (request.form.get('title') or '').strip() or manual.title
    schedule_item.start_at = start_at
    schedule_item.end_at = end_at
    schedule_item.notes = (request.form.get('notes') or '').strip()
    schedule_item.status = status
    db.session.commit()
    flash('Sesion actualizada.', 'success')
    return _dashboard_redirect_for_date(start_at.date(), manual_id=manual.id)


@main_bp.route('/dashboard/sessions/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_dashboard_session(schedule_id):
    schedule_item = db.session.get(ProjectManualSchedule, schedule_id)
    if schedule_item is None:
        abort(404)
    _assert_schedule_access(schedule_item)

    schedule_date = schedule_item.start_at.date()
    manual_id = schedule_item.manual_id
    db.session.delete(schedule_item)
    db.session.commit()
    flash('Sesion eliminada del calendario.', 'success')
    return _dashboard_redirect_for_date(schedule_date, manual_id=manual_id)


@main_bp.route('/courses')
@login_required
def courses():
    page = request.args.get('page', default=1, type=int)
    courses_query = Course.query
    if _is_teacher():
        courses_query = courses_query.join(course_teacher).filter(course_teacher.c.user_id == g.current_user.id)
    courses_page = courses_query.order_by(Course.created_at.desc()).paginate(page=page, per_page=6, error_out=False)
    return render_template('courses.html', courses=courses_page.items, courses_page=courses_page)


@main_bp.route('/courses/new', methods=['GET', 'POST'])
@admin_required
def create_course():
    teachers = User.query.filter_by(role='teacher').order_by(User.full_name.asc()).all()
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        if not title:
            abort(400, description='El titulo del curso es obligatorio.')

        course = Course(
            title=title,
            description=(request.form.get('description') or '').strip(),
            target_profile=(request.form.get('target_profile') or '').strip(),
            duration=(request.form.get('duration') or '4 semanas').strip(),
            viewer_url=(request.form.get('viewer_url') or '').strip() or None,
        )
        db.session.add(course)
        db.session.flush()

        selected_teacher_ids = {
            int(user_id)
            for user_id in request.form.getlist('teacher_ids[]')
            if user_id.isdigit()
        }
        if selected_teacher_ids:
            selected_teachers = User.query.filter(User.id.in_(selected_teacher_ids), User.role == 'teacher').all()
            course.teachers = selected_teachers

        module_titles = request.form.getlist('module_titles[]')
        for index, module_title in enumerate(module_titles, start=1):
            clean_title = module_title.strip()
            if clean_title:
                db.session.add(CourseModule(course_id=course.id, title=clean_title, sequence=index))

        db.session.commit()
        flash('Curso creado correctamente.', 'success')
        return redirect(url_for('main.course_detail', course_id=course.id))

    return render_template('create_course.html', teachers=teachers)


@main_bp.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    _assert_course_access(course)
    resources = Resource.query.filter_by(course_id=course.id).order_by(Resource.created_at.desc()).all()
    return render_template('course_detail.html', course=course, resources=resources)


@main_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    blocked_modules = []
    for module in course.modules:
        if module.learning_experiences or module.resources:
            blocked_modules.append(module.title)

    direct_resources_count = Resource.query.filter_by(course_id=course.id, module_id=None).count()

    if blocked_modules or direct_resources_count:
        details = []
        if blocked_modules:
            details.append('modulos con dependencias: ' + ', '.join(blocked_modules))
        if direct_resources_count:
            details.append(f'recursos del curso sin modulo: {direct_resources_count}')

        flash(
            'No se puede eliminar el curso porque tiene dependencias (' + '; '.join(details) + ').',
            'error',
        )
        return redirect(url_for('main.course_detail', course_id=course.id))

    db.session.delete(course)
    db.session.commit()
    flash('Curso eliminado correctamente.', 'success')
    return redirect(url_for('main.courses'))


@main_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    teachers = User.query.filter_by(role='teacher').order_by(User.full_name.asc()).all()

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        if not title:
            abort(400, description='El titulo del curso es obligatorio.')

        course.title = title
        course.description = (request.form.get('description') or '').strip()
        course.target_profile = (request.form.get('target_profile') or '').strip()
        course.duration = (request.form.get('duration') or '4 semanas').strip()
        course.viewer_url = (request.form.get('viewer_url') or '').strip() or None

        selected_teacher_ids = {
            int(user_id)
            for user_id in request.form.getlist('teacher_ids[]')
            if user_id.isdigit()
        }
        course.teachers = User.query.filter(User.id.in_(selected_teacher_ids), User.role == 'teacher').all()

        existing_ids = request.form.getlist('existing_module_ids[]')
        existing_titles = request.form.getlist('existing_module_titles[]')
        delete_ids = {module_id for module_id in request.form.getlist('delete_module_ids[]') if module_id.isdigit()}

        sequence = 1
        retained_modules = []

        for module_id_raw, module_title_raw in zip(existing_ids, existing_titles):
            if not module_id_raw.isdigit():
                continue

            module = CourseModule.query.filter_by(id=int(module_id_raw), course_id=course.id).first()
            if module is None:
                continue

            if module_id_raw in delete_ids:
                if module.learning_experiences or module.resources:
                    flash(
                        (
                            f'No se puede eliminar el modulo "{module.title}" porque tiene '
                            'experiencias o recursos vinculados.'
                        ),
                        'error',
                    )
                    return redirect(url_for('main.edit_course', course_id=course.id))

                db.session.delete(module)
                continue

            clean_title = module_title_raw.strip()
            retained_modules.append((module, clean_title))

        for module, clean_title in retained_modules:
            if clean_title:
                module.title = clean_title
            module.sequence = sequence
            sequence += 1

        # Append any newly added modules.
        for module_title in request.form.getlist('module_titles[]'):
            clean_title = module_title.strip()
            if not clean_title:
                continue

            db.session.add(CourseModule(course_id=course.id, title=clean_title, sequence=sequence))
            sequence += 1

        db.session.commit()
        flash('Curso actualizado correctamente.', 'success')
        return redirect(url_for('main.course_detail', course_id=course.id))

    modules = sorted(course.modules, key=lambda item: item.sequence)
    return render_template('edit_course.html', course=course, modules=modules, teachers=teachers)


@main_bp.route('/courses/<int:course_id>/studio', methods=['GET', 'POST'])
@admin_required
def course_studio(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        action = (request.form.get('action') or '').strip()

        if action == 'create_experience':
            title = (request.form.get('title') or '').strip()
            if not title:
                abort(400, description='El titulo de la experiencia es obligatorio.')

            module_id = request.form.get('module_id', type=int)
            module = CourseModule.query.filter_by(id=module_id, course_id=course.id).first() if module_id else None

            experience = LearningExperience(
                title=title,
                level=(request.form.get('level') or 'Secundaria').strip(),
                module_id=module.id if module else None,
                planning_markdown=(request.form.get('planning_markdown') or '').strip(),
                estimated_duration=(request.form.get('estimated_duration') or '60 minutos').strip(),
                workflow_status='draft',
                board_stage='por_planear',
                image_file='default.jpg',
            )
            db.session.add(experience)
            db.session.commit()
            flash('Experiencia creada desde el editor del curso.', 'success')
            return redirect(url_for('main.course_studio', course_id=course.id))

        if action == 'create_resource':
            title = (request.form.get('title') or '').strip()
            url = (request.form.get('url') or '').strip()
            if not title or not url:
                abort(400, description='Titulo y URL del recurso son obligatorios.')
            if not re.match(r'^https?://', url, re.IGNORECASE):
                abort(400, description='La URL del recurso debe iniciar con http:// o https://.')

            module_id = request.form.get('module_id', type=int)
            module = CourseModule.query.filter_by(id=module_id, course_id=course.id).first() if module_id else None

            resource = Resource(
                title=title,
                resource_type=(request.form.get('resource_type') or 'document').strip(),
                description=(request.form.get('description') or '').strip(),
                url=url,
                course_id=course.id,
                module_id=module.id if module else None,
            )
            db.session.add(resource)
            db.session.commit()
            flash('Recurso agregado al curso.', 'success')
            return redirect(url_for('main.course_studio', course_id=course.id))

        if action == 'create_rubric':
            experience_id = request.form.get('experience_id', type=int)
            experience = LearningExperience.query.join(CourseModule).filter(
                LearningExperience.id == experience_id,
                CourseModule.course_id == course.id,
            ).first_or_404()

            rubric_name = (request.form.get('rubric_name') or '').strip()
            if not rubric_name:
                abort(400, description='El nombre del criterio de rubrica es obligatorio.')

            db.session.add(
                LearningExperienceRubric(
                    learning_experience_id=experience.id,
                    name=rubric_name,
                    dimension=(request.form.get('rubric_dimension') or 'Pedagogia').strip(),
                    description=(request.form.get('rubric_description') or '').strip(),
                    weight=max(1, min(100, request.form.get('rubric_weight', type=int) or 20)),
                    level_4=(request.form.get('level_4') or '').strip() or 'Desempeno sobresaliente.',
                    level_3=(request.form.get('level_3') or '').strip() or 'Desempeno esperado.',
                    level_2=(request.form.get('level_2') or '').strip() or 'Desempeno basico con apoyo.',
                    level_1=(request.form.get('level_1') or '').strip() or 'Desempeno inicial.',
                )
            )
            db.session.commit()
            flash('Rubrica agregada a la experiencia.', 'success')
            return redirect(url_for('main.course_studio', course_id=course.id))

    modules = CourseModule.query.filter_by(course_id=course.id).order_by(CourseModule.sequence.asc()).all()
    experiences = (
        LearningExperience.query.join(CourseModule)
        .filter(CourseModule.course_id == course.id)
        .order_by(CourseModule.sequence.asc(), LearningExperience.created_at.desc())
        .all()
    )
    resources = (
        Resource.query.filter_by(course_id=course.id)
        .order_by(Resource.created_at.desc())
        .all()
    )
    rubric_counts = {
        row.learning_experience_id: row.total
        for row in db.session.query(
            LearningExperienceRubric.learning_experience_id,
            db.func.count(LearningExperienceRubric.id).label('total'),
        )
        .join(LearningExperience, LearningExperienceRubric.learning_experience_id == LearningExperience.id)
        .join(CourseModule, LearningExperience.module_id == CourseModule.id)
        .filter(CourseModule.course_id == course.id)
        .group_by(LearningExperienceRubric.learning_experience_id)
        .all()
    }

    return render_template(
        'course_studio.html',
        course=course,
        modules=modules,
        experiences=experiences,
        resources=resources,
        rubric_counts=rubric_counts,
    )


@main_bp.route('/resources')
@login_required
def resources():
    selected_type = (request.args.get('type') or '').strip().lower()
    selected_course = (request.args.get('course') or '').strip()
    selected_module = (request.args.get('module') or '').strip()
    query = (request.args.get('q') or '').strip()

    resources_query = Resource.query

    if _is_teacher():
        accessible_ids = _accessible_course_ids()
        if not accessible_ids:
            resources_query = resources_query.filter(db.text('1=0'))
        else:
            resources_query = resources_query.outerjoin(CourseModule, Resource.module_id == CourseModule.id).filter(
                db.or_(
                    Resource.course_id.in_(accessible_ids),
                    CourseModule.course_id.in_(accessible_ids),
                )
            )

    if selected_type:
        resources_query = resources_query.filter(Resource.resource_type == selected_type)
    if selected_course.isdigit():
        resources_query = resources_query.filter(Resource.course_id == int(selected_course))
    if selected_module.isdigit():
        resources_query = resources_query.filter(Resource.module_id == int(selected_module))
    if query:
        resources_query = resources_query.filter(
            db.or_(
                Resource.title.ilike(f'%{query}%'),
                Resource.description.ilike(f'%{query}%'),
            )
        )

    page = request.args.get('page', default=1, type=int)
    resources_page = resources_query.order_by(Resource.created_at.desc()).paginate(page=page, per_page=8, error_out=False)

    courses_list = Course.query.order_by(Course.title.asc())
    modules_list = CourseModule.query.order_by(CourseModule.sequence.asc())
    if _is_teacher():
        accessible_ids = _accessible_course_ids()
        courses_list = courses_list.filter(Course.id.in_(accessible_ids))
        modules_list = modules_list.filter(CourseModule.course_id.in_(accessible_ids))
    courses_list = courses_list.all()
    modules_list = modules_list.all()
    resource_types = ['document', 'video', 'infographic', 'guide']

    return render_template(
        'resources.html',
        resources=resources_page.items,
        resources_page=resources_page,
        courses=courses_list,
        modules=modules_list,
        resource_types=resource_types,
        selected_type=selected_type,
        selected_course=selected_course,
        selected_module=selected_module,
        query=query,
    )


@main_bp.route('/resources/new', methods=['GET', 'POST'])
@admin_required
def create_resource():
    courses_list = Course.query.order_by(Course.title.asc()).all()
    modules = CourseModule.query.order_by(CourseModule.sequence.asc()).all()

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        url = (request.form.get('url') or '').strip()
        if not title or not url:
            abort(400, description='Titulo y enlace del recurso son obligatorios.')

        resource = Resource(
            title=title,
            resource_type=(request.form.get('resource_type') or 'document').strip(),
            description=(request.form.get('description') or '').strip(),
            url=url,
            course_id=int(request.form['course_id']) if request.form.get('course_id') else None,
            module_id=int(request.form['module_id']) if request.form.get('module_id') else None,
        )
        db.session.add(resource)
        db.session.commit()
        flash('Recurso creado correctamente.', 'success')
        return redirect(url_for('main.resources'))

    return render_template('create_resource.html', courses=courses_list, modules=modules)


@main_bp.route('/resources/<int:resource_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    courses_list = Course.query.order_by(Course.title.asc()).all()
    modules = CourseModule.query.order_by(CourseModule.sequence.asc()).all()

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        url = (request.form.get('url') or '').strip()
        if not title or not url:
            abort(400, description='Titulo y enlace del recurso son obligatorios.')

        resource.title = title
        resource.resource_type = (request.form.get('resource_type') or 'document').strip()
        resource.description = (request.form.get('description') or '').strip()
        resource.url = url
        resource.course_id = int(request.form['course_id']) if request.form.get('course_id') else None
        resource.module_id = int(request.form['module_id']) if request.form.get('module_id') else None

        db.session.commit()
        flash('Recurso actualizado correctamente.', 'success')
        return redirect(url_for('main.resources'))

    return render_template('edit_resource.html', resource=resource, courses=courses_list, modules=modules)


@main_bp.route('/resources/<int:resource_id>/delete', methods=['POST'])
@admin_required
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    db.session.delete(resource)
    db.session.commit()
    flash('Recurso eliminado correctamente.', 'success')
    return redirect(url_for('main.resources'))


@main_bp.route('/experiences/<int:experience_id>', methods=['GET', 'POST'])
@login_required
def learning_experience_detail(experience_id):
    if not RubricBankItem.query.first():
        seed_rubric_bank_items()

    learning_experience = LearningExperience.query.get_or_404(experience_id)
    _assert_experience_access(learning_experience)
    if request.method == 'POST':
        if not _is_admin():
            abort(403)
        action = (request.form.get('action') or '').strip()

        if action == 'add_bank_rubrics':
            selected_bank_ids = request.form.getlist('bank_rubric_ids[]')
            added = 0
            for bank_id in selected_bank_ids:
                if not bank_id.isdigit():
                    continue
                bank_item = db.session.get(RubricBankItem, int(bank_id))
                if bank_item is None:
                    continue

                exists = LearningExperienceRubric.query.filter_by(
                    learning_experience_id=learning_experience.id,
                    bank_item_id=bank_item.id,
                ).first()
                if exists:
                    continue

                db.session.add(
                    LearningExperienceRubric(
                        learning_experience_id=learning_experience.id,
                        bank_item_id=bank_item.id,
                        name=bank_item.name,
                        dimension=bank_item.dimension,
                        description=bank_item.description,
                        weight=bank_item.default_weight,
                        level_4=bank_item.level_4,
                        level_3=bank_item.level_3,
                        level_2=bank_item.level_2,
                        level_1=bank_item.level_1,
                    )
                )
                added += 1

            db.session.commit()
            flash(f'Se agregaron {added} criterios desde el banco.', 'success')
            return redirect(url_for('main.learning_experience_detail', experience_id=learning_experience.id))

        if action == 'add_custom_rubric':
            name = (request.form.get('rubric_name') or '').strip()
            if not name:
                abort(400, description='El nombre del criterio de rubrica es obligatorio.')

            weight = request.form.get('rubric_weight', type=int) or 20
            weight = max(1, min(100, weight))
            db.session.add(
                LearningExperienceRubric(
                    learning_experience_id=learning_experience.id,
                    name=name,
                    dimension=(request.form.get('rubric_dimension') or 'Pedagogia').strip(),
                    description=(request.form.get('rubric_description') or '').strip(),
                    weight=weight,
                    level_4=(request.form.get('level_4') or '').strip() or 'Desempeno sobresaliente.',
                    level_3=(request.form.get('level_3') or '').strip() or 'Desempeno esperado.',
                    level_2=(request.form.get('level_2') or '').strip() or 'Desempeno basico con apoyo.',
                    level_1=(request.form.get('level_1') or '').strip() or 'Desempeno inicial.',
                )
            )
            db.session.commit()
            flash('Criterio de rubrica agregado.', 'success')
            return redirect(url_for('main.learning_experience_detail', experience_id=learning_experience.id))

        if action == 'save_evaluation':
            rubrics = (
                LearningExperienceRubric.query.filter_by(learning_experience_id=learning_experience.id)
                .order_by(LearningExperienceRubric.id.asc())
                .all()
            )
            if not rubrics:
                flash('Agrega al menos un criterio de rubrica antes de evaluar.', 'error')
                return redirect(url_for('main.learning_experience_detail', experience_id=learning_experience.id))

            evaluation = LearningExperienceEvaluation(
                learning_experience_id=learning_experience.id,
                evaluator_name=(request.form.get('evaluator_name') or 'Docente evaluador').strip(),
                notes=(request.form.get('evaluation_notes') or '').strip(),
            )
            db.session.add(evaluation)
            db.session.flush()

            for rubric in rubrics:
                level = request.form.get(f'rubric_level_{rubric.id}', type=int) or 1
                level = max(1, min(4, level))
                db.session.add(
                    LearningExperienceEvaluationScore(
                        evaluation_id=evaluation.id,
                        rubric_id=rubric.id,
                        level=level,
                        weight=rubric.weight,
                    )
                )

            db.session.commit()
            flash('Evaluacion guardada correctamente.', 'success')
            return redirect(url_for('main.learning_experience_detail', experience_id=learning_experience.id))

        content = (request.form.get('content') or '').strip()
        if content:
            db.session.add(Comment(content=content, learning_experience_id=learning_experience.id))
            db.session.commit()
            return redirect(url_for('main.learning_experience_detail', experience_id=learning_experience.id))

    comments = Comment.query.filter_by(learning_experience_id=experience_id).order_by(Comment.created_at.desc()).all()
    rubrics = (
        LearningExperienceRubric.query.filter_by(learning_experience_id=learning_experience.id)
        .order_by(LearningExperienceRubric.dimension.asc(), LearningExperienceRubric.id.asc())
        .all()
    )
    rubric_bank_items = RubricBankItem.query.order_by(RubricBankItem.dimension.asc(), RubricBankItem.name.asc()).all()
    evaluations = (
        LearningExperienceEvaluation.query.filter_by(learning_experience_id=learning_experience.id)
        .order_by(LearningExperienceEvaluation.created_at.desc())
        .limit(5)
        .all()
    )
    weekly_plan = _build_weekly_plan(learning_experience)

    return render_template(
        'learning_experience_detail.html',
        learning_experience=learning_experience,
        comments=comments,
        rubrics=rubrics,
        rubric_bank_items=rubric_bank_items,
        evaluations=evaluations,
        weekly_plan=weekly_plan,
    )


@main_bp.route('/experiences/<int:experience_id>/rubrics/<int:rubric_id>/delete', methods=['POST'])
@admin_required
def delete_experience_rubric(experience_id, rubric_id):
    rubric = LearningExperienceRubric.query.filter_by(
        id=rubric_id,
        learning_experience_id=experience_id,
    ).first_or_404()
    db.session.delete(rubric)
    db.session.commit()
    flash('Criterio de rubrica eliminado.', 'success')
    return redirect(url_for('main.learning_experience_detail', experience_id=experience_id))


@main_bp.route('/experiences/<int:experience_id>/rubrics/<int:rubric_id>/edit', methods=['POST'])
@admin_required
def edit_experience_rubric(experience_id, rubric_id):
    rubric = LearningExperienceRubric.query.filter_by(
        id=rubric_id,
        learning_experience_id=experience_id,
    ).first_or_404()

    name = (request.form.get('name') or '').strip()
    if not name:
        abort(400, description='El nombre del criterio de rubrica es obligatorio.')

    rubric.name = name
    rubric.dimension = (request.form.get('dimension') or 'Pedagogia').strip()
    rubric.description = (request.form.get('description') or '').strip()
    rubric.weight = max(1, min(100, request.form.get('weight', type=int) or 20))
    rubric.level_4 = (request.form.get('level_4') or '').strip() or rubric.level_4
    rubric.level_3 = (request.form.get('level_3') or '').strip() or rubric.level_3
    rubric.level_2 = (request.form.get('level_2') or '').strip() or rubric.level_2
    rubric.level_1 = (request.form.get('level_1') or '').strip() or rubric.level_1

    db.session.commit()
    flash('Criterio de rubrica actualizado.', 'success')
    return redirect(url_for('main.learning_experience_detail', experience_id=experience_id))


@main_bp.route('/experiences/<int:experience_id>/export/pdf')
@login_required
def export_learning_experience_pdf(experience_id):
    learning_experience = LearningExperience.query.get_or_404(experience_id)
    _assert_experience_access(learning_experience)
    filename = secure_filename(f'{learning_experience.title.lower()}-planeacion.pdf') or f'experiencia-{learning_experience.id}.pdf'
    pdf_buffer = _build_experience_pdf(learning_experience)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )


@main_bp.route('/rubrics/bank', methods=['GET'])
@admin_required
def rubric_bank():
    seed_rubric_bank_items()

    items = RubricBankItem.query.order_by(RubricBankItem.dimension.asc(), RubricBankItem.name.asc()).all()
    rubric_groups = {}
    for item in items:
        rubric_name = (item.dimension or 'Sin categoria').strip() or 'Sin categoria'
        rubric_groups.setdefault(rubric_name, []).append(item)

    return render_template('rubric_bank.html', rubric_groups=rubric_groups)


@main_bp.route('/rubrics/bank/new', methods=['GET', 'POST'])
@admin_required
def create_rubric_bank_item():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if not name:
            abort(400, description='El nombre del criterio es obligatorio.')

        exists = RubricBankItem.query.filter(RubricBankItem.name.ilike(name)).first()
        if exists:
            flash('Ya existe un criterio con ese nombre en el banco.', 'error')
            return redirect(url_for('main.create_rubric_bank_item'))

        db.session.add(
            RubricBankItem(
                name=name,
                dimension=(request.form.get('dimension') or 'Pedagogia').strip(),
                description=(request.form.get('description') or '').strip(),
                default_weight=max(1, min(100, request.form.get('default_weight', type=int) or 20)),
                level_4=(request.form.get('level_4') or '').strip() or 'Desempeno sobresaliente.',
                level_3=(request.form.get('level_3') or '').strip() or 'Desempeno esperado.',
                level_2=(request.form.get('level_2') or '').strip() or 'Desempeno basico con apoyo.',
                level_1=(request.form.get('level_1') or '').strip() or 'Desempeno inicial.',
            )
        )
        db.session.commit()
        flash('Criterio agregado al banco.', 'success')
        return redirect(url_for('main.rubric_bank'))

    return render_template('rubric_bank_new.html')


@main_bp.route('/rubrics/bank/<int:item_id>/delete', methods=['POST'])
@admin_required
def delete_rubric_bank_item(item_id):
    item = RubricBankItem.query.get_or_404(item_id)
    if item.is_system:
        flash('No puedes eliminar un criterio base del sistema.', 'error')
        return redirect(url_for('main.rubric_bank'))

    db.session.delete(item)
    db.session.commit()
    flash('Criterio eliminado del banco.', 'success')
    return redirect(url_for('main.rubric_bank'))


@main_bp.route('/rubrics/bank/<int:item_id>/edit', methods=['POST'])
@admin_required
def edit_rubric_bank_item(item_id):
    item = RubricBankItem.query.get_or_404(item_id)

    name = (request.form.get('name') or '').strip()
    if not name:
        abort(400, description='El nombre del criterio es obligatorio.')

    duplicate = RubricBankItem.query.filter(RubricBankItem.name.ilike(name), RubricBankItem.id != item.id).first()
    if duplicate:
        flash('Ya existe otro criterio con ese nombre en el banco.', 'error')
        return redirect(url_for('main.rubric_bank'))

    item.name = name
    item.dimension = (request.form.get('dimension') or 'Pedagogia').strip()
    item.description = (request.form.get('description') or '').strip()
    item.default_weight = max(1, min(100, request.form.get('default_weight', type=int) or 20))
    item.level_4 = (request.form.get('level_4') or '').strip() or item.level_4
    item.level_3 = (request.form.get('level_3') or '').strip() or item.level_3
    item.level_2 = (request.form.get('level_2') or '').strip() or item.level_2
    item.level_1 = (request.form.get('level_1') or '').strip() or item.level_1

    db.session.commit()
    flash('Criterio del banco actualizado.', 'success')
    return redirect(url_for('main.rubric_bank'))


@main_bp.route('/experiences/new', methods=['GET', 'POST'])
@admin_required
def create_learning_experience():
    iste_list = ISTEStandard.query.order_by(ISTEStandard.code.asc()).all()
    modules = CourseModule.query.order_by(CourseModule.sequence.asc()).all()

    if request.method == 'POST':
        new_learning_experience = LearningExperience(image_file='default.jpg')
        db.session.add(new_learning_experience)
        _apply_learning_experience_form(new_learning_experience)

        db.session.commit()
        flash('Experiencia creada correctamente.', 'success')
        return redirect(url_for('main.index'))

    from_template_id = request.args.get('from_template_id', type=int)
    selected_template = None
    if from_template_id:
        selected_template = LearningExperience.query.filter_by(id=from_template_id, is_template=True).first()

    initial_experience = None
    material_requirements = [{'name': '', 'quantity': ''}]
    selected_iste_ids = set()
    if selected_template:
        initial_experience = selected_template
        material_requirements = [
            {'name': requirement.material.name, 'quantity': requirement.quantity_needed}
            for requirement in selected_template.requirements
        ] or material_requirements
        selected_iste_ids = {standard.id for standard in selected_template.iste_standards}

    return render_template(
        'create.html',
        iste_list=iste_list,
        modules=modules,
        learning_experience=initial_experience,
        selected_iste_ids=selected_iste_ids,
        material_requirements=material_requirements,
        workflow_status_value='draft',
        board_stage_value='por_planear',
        week_slot_value=1,
        is_template_value=False,
        form_title='Nueva Experiencia Formativa',
        form_description='Construye una secuencia para capacitar docentes en tecnologia educativa con una implementacion realista para escuela.',
        submit_label='GUARDAR EXPERIENCIA',
        cancel_url=url_for('main.index'),
    )


@main_bp.route('/experiences/<int:experience_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_learning_experience(experience_id):
    learning_experience = LearningExperience.query.get_or_404(experience_id)
    iste_list = ISTEStandard.query.order_by(ISTEStandard.code.asc()).all()
    modules = CourseModule.query.order_by(CourseModule.sequence.asc()).all()

    if request.method == 'POST':
        _apply_learning_experience_form(learning_experience)
        db.session.commit()
        flash('Experiencia actualizada correctamente.', 'success')
        return redirect(url_for('main.learning_experience_detail', experience_id=learning_experience.id))

    return render_template(
        'create.html',
        iste_list=iste_list,
        modules=modules,
        learning_experience=learning_experience,
        selected_iste_ids={standard.id for standard in learning_experience.iste_standards},
        material_requirements=[
            {'name': requirement.material.name, 'quantity': requirement.quantity_needed}
            for requirement in learning_experience.requirements
        ]
        or [{'name': '', 'quantity': ''}],
        workflow_status_value=learning_experience.workflow_status or 'draft',
        board_stage_value=learning_experience.board_stage or 'por_planear',
        week_slot_value=learning_experience.week_slot or 1,
        is_template_value=learning_experience.is_template,
        form_title='Editar Experiencia Formativa',
        form_description='Actualiza la secuencia, el contexto docente y los recursos minimos necesarios.',
        submit_label='GUARDAR CAMBIOS',
        cancel_url=url_for('main.learning_experience_detail', experience_id=learning_experience.id),
    )


@main_bp.route('/experiences/<int:experience_id>/delete', methods=['POST'])
@admin_required
def delete_learning_experience(experience_id):
    learning_experience = LearningExperience.query.get_or_404(experience_id)
    _delete_uploaded_image(learning_experience.image_file)
    db.session.delete(learning_experience)
    db.session.commit()
    flash('Experiencia eliminada correctamente.', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/inventory', methods=['GET', 'POST'])
@admin_required
def inventory():
    if request.method == 'POST':
        name = request.form['name'].strip()
        stock = int(request.form['stock'])
        if not name:
            abort(400, description='El nombre del material es obligatorio.')
        if stock < 0:
            abort(400, description='La cantidad no puede ser negativa.')

        material = Material.query.filter(Material.name.ilike(name)).first()
        if material:
            material.stock += stock
        else:
            db.session.add(Material(name=name, stock=stock))
        db.session.commit()
        return redirect(url_for('main.inventory'))

    materials = Material.query.order_by(Material.name.asc()).all()
    return render_template('inventory.html', materials=materials)


# ---------------------------------------------------------------------------
# Manuales de Proyectos
# ---------------------------------------------------------------------------

@main_bp.route('/manuals')
@login_required
def manuals():
    selected_grade = request.args.get('grade', 'all').strip()
    query_text = request.args.get('q', '').strip()
    selected_theme = request.args.get('theme', 'all').strip()

    base_query = ProjectManual.query
    if selected_grade != 'all':
        if selected_grade not in GRADE_LEVELS:
            abort(400, description='El grado seleccionado no es valido.')
        base_query = base_query.filter_by(grade_level=selected_grade)
    if selected_theme != 'all':
        if selected_theme not in MANUAL_TOPICS:
            abort(400, description='El tema seleccionado no es valido.')
        base_query = base_query.join(ProjectManualTheme).filter(ProjectManualTheme.theme == selected_theme)
    if query_text:
        like = f'%{query_text}%'
        base_query = base_query.filter(
            db.or_(
                ProjectManual.title.ilike(like),
                ProjectManual.description.ilike(like),
                ProjectManual.content_markdown.ilike(like),
            )
        )

    manuals_list = base_query.distinct().order_by(ProjectManual.grade_level.asc(), ProjectManual.title.asc()).all()
    return render_template(
        'manuals.html',
        manuals_list=manuals_list,
        grade_levels=GRADE_LEVELS,
        manual_topics=MANUAL_TOPICS,
        selected_grade=selected_grade,
        selected_theme=selected_theme,
        query_text=query_text,
    )


@main_bp.route('/manuals/new', methods=['GET', 'POST'])
@admin_required
def create_manual():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        grade_level = request.form.get('grade_level', '').strip()
        selected_topics = [t for t in request.form.getlist('themes') if t in MANUAL_TOPICS]
        if not title or grade_level not in GRADE_LEVELS:
            abort(400, description='Título y grado son obligatorios.')
        if not selected_topics:
            abort(400, description='Selecciona al menos un tema para el manual.')
        manual = ProjectManual(
            title=title,
            grade_level=grade_level,
            description=request.form.get('description', '').strip(),
            iframe_url=request.form.get('iframe_url', '').strip() or None,
            content_markdown=request.form.get('content_markdown', '').strip() or None,
            estimated_sessions=int(request.form.get('estimated_sessions') or 4),
        )
        manual.themes = [ProjectManualTheme(theme=topic) for topic in dict.fromkeys(selected_topics)]
        db.session.add(manual)
        db.session.commit()
        return redirect(url_for('main.manual_detail', manual_id=manual.id))
    return render_template('manual_form.html', manual=None, grade_levels=GRADE_LEVELS, manual_topics=MANUAL_TOPICS)


@main_bp.route('/manuals/<int:manual_id>')
@login_required
def manual_detail(manual_id):
    manual = ProjectManual.query.get_or_404(manual_id)
    current = g.current_user
    my_plan = WeeklyPlan.query.filter_by(manual_id=manual_id, user_id=current.id).first()
    rubric_bank_items = RubricBankItem.query.order_by(RubricBankItem.name).all()
    session_rows = ManualSessionPlan.query.filter_by(manual_id=manual_id).order_by(ManualSessionPlan.session_number.asc()).all()
    scheduled_query = ProjectManualSchedule.query.filter_by(manual_id=manual_id)
    if _is_teacher():
        scheduled_query = scheduled_query.filter(ProjectManualSchedule.user_id == current.id)
    upcoming_scheduled_sessions = (
        scheduled_query
        .filter(ProjectManualSchedule.start_at >= datetime.utcnow())
        .order_by(ProjectManualSchedule.start_at.asc())
        .limit(8)
        .all()
    )
    return render_template(
        'manual_detail.html',
        manual=manual,
        my_plan=my_plan,
        rubric_bank_items=rubric_bank_items,
        session_rows=session_rows,
        upcoming_scheduled_sessions=upcoming_scheduled_sessions,
    )


@main_bp.route('/manuals/<int:manual_id>/calendarize')
@login_required
def calendarize_manual(manual_id):
    manual = ProjectManual.query.get_or_404(manual_id)
    selected_date = _parse_date_arg(request.args.get('date'), date.today())
    return redirect(url_for('main.dashboard', manual_id=manual.id, date=selected_date.isoformat()))


@main_bp.route('/manuals/<int:manual_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_manual(manual_id):
    manual = ProjectManual.query.get_or_404(manual_id)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        grade_level = request.form.get('grade_level', '').strip()
        selected_topics = [t for t in request.form.getlist('themes') if t in MANUAL_TOPICS]
        if not title or grade_level not in GRADE_LEVELS:
            abort(400, description='Título y grado son obligatorios.')
        if not selected_topics:
            abort(400, description='Selecciona al menos un tema para el manual.')
        manual.title = title
        manual.grade_level = grade_level
        manual.description = request.form.get('description', '').strip()
        manual.iframe_url = request.form.get('iframe_url', '').strip() or None
        manual.content_markdown = request.form.get('content_markdown', '').strip() or None
        manual.estimated_sessions = int(request.form.get('estimated_sessions') or 4)
        manual.themes = [ProjectManualTheme(theme=topic) for topic in dict.fromkeys(selected_topics)]
        db.session.commit()
        return redirect(url_for('main.manual_detail', manual_id=manual.id))
    return render_template('manual_form.html', manual=manual, grade_levels=GRADE_LEVELS, manual_topics=MANUAL_TOPICS)


@main_bp.route('/manuals/<int:manual_id>/delete', methods=['POST'])
@admin_required
def delete_manual(manual_id):
    manual = ProjectManual.query.get_or_404(manual_id)
    db.session.delete(manual)
    db.session.commit()
    return redirect(url_for('main.manuals'))


# Rúbricas del manual
@main_bp.route('/manuals/<int:manual_id>/rubrics/create', methods=['POST'])
@admin_required
def create_manual_rubric(manual_id):
    manual = ProjectManual.query.get_or_404(manual_id)
    name = request.form.get('name', '').strip()
    if not name:
        abort(400, description='El nombre de la rubrica es obligatorio.')
    rubric = ProjectRubric(
        manual_id=manual.id,
        name=name,
        description=request.form.get('description', '').strip(),
    )
    db.session.add(rubric)
    db.session.commit()
    return redirect(url_for('main.manual_detail', manual_id=manual_id))


@main_bp.route('/manuals/<int:manual_id>/rubrics/<int:rubric_id>/delete', methods=['POST'])
@admin_required
def delete_manual_rubric(manual_id, rubric_id):
    rubric = ProjectRubric.query.filter_by(id=rubric_id, manual_id=manual_id).first_or_404()
    db.session.delete(rubric)
    db.session.commit()
    return redirect(url_for('main.manual_detail', manual_id=manual_id))


@main_bp.route('/manuals/<int:manual_id>/rubrics/<int:rubric_id>/criteria/add', methods=['POST'])
@admin_required
def add_manual_rubric_criterion(manual_id, rubric_id):
    rubric = ProjectRubric.query.filter_by(id=rubric_id, manual_id=manual_id).first_or_404()

    bank_item_id = request.form.get('bank_item_id')
    if bank_item_id:
        item = RubricBankItem.query.get_or_404(int(bank_item_id))
        criterion = ProjectRubricCriterion(
            rubric_id=rubric.id,
            bank_item_id=item.id,
            name=item.name,
            dimension=item.dimension,
            description=item.description,
            weight=item.default_weight,
            level_4=item.level_4,
            level_3=item.level_3,
            level_2=item.level_2,
            level_1=item.level_1,
        )
    else:
        name = request.form.get('name', '').strip()
        if not name:
            abort(400, description='El nombre del criterio es obligatorio.')
        criterion = ProjectRubricCriterion(
            rubric_id=rubric.id,
            name=name,
            dimension=request.form.get('dimension', 'Competencia').strip(),
            description=request.form.get('description', '').strip(),
            weight=int(request.form.get('weight') or 25),
            level_4=request.form.get('level_4', '').strip(),
            level_3=request.form.get('level_3', '').strip(),
            level_2=request.form.get('level_2', '').strip(),
            level_1=request.form.get('level_1', '').strip(),
        )

    db.session.add(criterion)
    db.session.commit()
    return redirect(url_for('main.manual_detail', manual_id=manual_id))


@main_bp.route('/manuals/<int:manual_id>/rubrics/<int:rubric_id>/criteria/<int:criterion_id>/delete', methods=['POST'])
@admin_required
def delete_manual_rubric_criterion(manual_id, rubric_id, criterion_id):
    criterion = ProjectRubricCriterion.query.join(ProjectRubric).filter(
        ProjectRubricCriterion.id == criterion_id,
        ProjectRubric.id == rubric_id,
        ProjectRubric.manual_id == manual_id,
    ).first_or_404()
    db.session.delete(criterion)
    db.session.commit()
    return redirect(url_for('main.manual_detail', manual_id=manual_id))


# Planeación semanal
@main_bp.route('/manuals/<int:manual_id>/plan', methods=['POST'])
@login_required
def save_weekly_plan(manual_id):
    ProjectManual.query.get_or_404(manual_id)
    current = g.current_user
    plan = WeeklyPlan.query.filter_by(manual_id=manual_id, user_id=current.id).first()
    sessions_per_week = int(request.form.get('sessions_per_week') or 1)
    start_week = int(request.form.get('start_week') or 1)
    notes = request.form.get('notes', '').strip()
    if plan:
        plan.sessions_per_week = sessions_per_week
        plan.start_week = start_week
        plan.notes = notes
    else:
        plan = WeeklyPlan(
            manual_id=manual_id,
            user_id=current.id,
            sessions_per_week=sessions_per_week,
            start_week=start_week,
            notes=notes,
        )
        db.session.add(plan)
    db.session.commit()
    return redirect(url_for('main.manual_detail', manual_id=manual_id))


@main_bp.route('/manuals/<int:manual_id>/session-plan/add', methods=['POST'])
@admin_required
def add_manual_session_plan_row(manual_id):
    manual = ProjectManual.query.get_or_404(manual_id)
    objective = request.form.get('objective', '').strip()
    if not objective:
        abort(400, description='El objetivo de la sesion es obligatorio.')

    session_number = int(request.form.get('session_number') or 1)
    if session_number <= 0:
        abort(400, description='La sesion debe ser mayor a cero.')

    row = ManualSessionPlan(
        manual_id=manual.id,
        level=request.form.get('level', '').strip() or manual.grade_level,
        session_number=session_number,
        objective=objective,
        steam_area_focus=request.form.get('steam_area_focus', '').strip(),
        transversality=request.form.get('transversality', '').strip(),
        topic=request.form.get('topic', '').strip(),
        activity_detail=request.form.get('activity_detail', '').strip(),
        resources=request.form.get('resources', '').strip(),
    )
    db.session.add(row)
    db.session.commit()
    return redirect(url_for('main.manual_detail', manual_id=manual_id))


@main_bp.route('/manuals/<int:manual_id>/session-plan/<int:row_id>/delete', methods=['POST'])
@admin_required
def delete_manual_session_plan_row(manual_id, row_id):
    row = ManualSessionPlan.query.filter_by(id=row_id, manual_id=manual_id).first_or_404()
    db.session.delete(row)
    db.session.commit()
    return redirect(url_for('main.manual_detail', manual_id=manual_id))