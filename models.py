import re
from datetime import datetime

import bleach
import markdown
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


learning_experience_iste = db.Table(
    'learning_experience_iste',
    db.Column('learning_experience_id', db.Integer, db.ForeignKey('learning_experience.id'), primary_key=True),
    db.Column('iste_id', db.Integer, db.ForeignKey('iste_standard.id'), primary_key=True),
)


course_teacher = db.Table(
    'course_teacher',
    db.Column('course_id', db.Integer, db.ForeignKey('training_course.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
)


def render_safe_markdown(content):
    raw_html = markdown.markdown(content or '', extensions=['extra'])
    raw_html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', raw_html, flags=re.IGNORECASE | re.DOTALL)
    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union(
        {'p', 'pre', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br'}
    )
    allowed_attributes = {
        'a': ['href', 'title', 'rel'],
        'abbr': ['title'],
        'acronym': ['title'],
        'code': ['class'],
    }
    return bleach.clean(raw_html, tags=allowed_tags, attributes=allowed_attributes, strip=True)


class ISTEStandard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.Text)


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='pzs')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='teacher')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courses = db.relationship('Course', secondary=course_teacher, back_populates='teachers')
    scheduled_sessions = db.relationship('ProjectManualSchedule', backref='teacher')

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == 'admin'


class Course(db.Model):
    __tablename__ = 'training_course'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    target_profile = db.Column(db.String(160))
    duration = db.Column(db.String(60), default='4 semanas')
    viewer_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    modules = db.relationship('CourseModule', backref='course', cascade='all, delete-orphan')
    resources = db.relationship('Resource', backref='course')
    teachers = db.relationship('User', secondary=course_teacher, back_populates='courses')


class CourseModule(db.Model):
    __tablename__ = 'course_module'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('training_course.id'), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    sequence = db.Column(db.Integer, default=1)

    learning_experiences = db.relationship('LearningExperience', backref='module')
    resources = db.relationship('Resource', backref='module')


class Resource(db.Model):
    __tablename__ = 'resource'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    resource_type = db.Column(db.String(30), default='document')
    description = db.Column(db.Text)
    url = db.Column(db.String(500), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('training_course.id'))
    module_id = db.Column(db.Integer, db.ForeignKey('course_module.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LearningExperience(db.Model):
    __tablename__ = 'learning_experience'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    level = db.Column(db.String(50))
    module_id = db.Column(db.Integer, db.ForeignKey('course_module.id'))
    teacher_profile = db.Column(db.String(120), default='Docente frente a grupo')
    course_focus = db.Column(db.String(120), default='Tecnologia educativa')
    learning_objective = db.Column(db.Text)
    classroom_application = db.Column(db.Text)
    minimal_technology = db.Column(db.String(120), default='Computadora con editor de codigo')
    estimated_duration = db.Column(db.String(50), default='60 minutos')
    workflow_status = db.Column(db.String(20), default='draft')
    board_stage = db.Column(db.String(30), default='por_planear')
    week_slot = db.Column(db.Integer, default=1)
    is_template = db.Column(db.Boolean, default=False)
    planning_markdown = db.Column(db.Text)
    image_file = db.Column(db.String(100), default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    iste_standards = db.relationship('ISTEStandard', secondary=learning_experience_iste, backref='learning_experiences')
    requirements = db.relationship('LearningExperienceRequirement', backref='learning_experience', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='learning_experience', cascade='all, delete-orphan')
    rubrics = db.relationship('LearningExperienceRubric', backref='learning_experience', cascade='all, delete-orphan')
    evaluations = db.relationship('LearningExperienceEvaluation', backref='learning_experience', cascade='all, delete-orphan')

    @property
    def html_content(self):
        return render_safe_markdown(self.planning_markdown)


class LearningExperienceRequirement(db.Model):
    __tablename__ = 'learning_experience_requirement'

    id = db.Column(db.Integer, primary_key=True)
    learning_experience_id = db.Column(db.Integer, db.ForeignKey('learning_experience.id'))
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    quantity_needed = db.Column(db.Integer, nullable=False)
    material = db.relationship('Material')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), default='Docente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    learning_experience_id = db.Column(db.Integer, db.ForeignKey('learning_experience.id'))


class RubricBankItem(db.Model):
    __tablename__ = 'rubric_bank_item'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    dimension = db.Column(db.String(80), default='Pedagogia')
    description = db.Column(db.Text)
    default_weight = db.Column(db.Integer, default=20)
    level_4 = db.Column(db.Text, default='Demuestra dominio sobresaliente y transferencia a otros contextos.')
    level_3 = db.Column(db.Text, default='Cumple de forma consistente con los criterios esperados.')
    level_2 = db.Column(db.Text, default='Evidencia avance parcial; requiere apoyo puntual.')
    level_1 = db.Column(db.Text, default='Presenta dificultades para cumplir el criterio y requiere acompanamiento continuo.')
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LearningExperienceRubric(db.Model):
    __tablename__ = 'learning_experience_rubric'

    id = db.Column(db.Integer, primary_key=True)
    learning_experience_id = db.Column(db.Integer, db.ForeignKey('learning_experience.id'), nullable=False)
    bank_item_id = db.Column(db.Integer, db.ForeignKey('rubric_bank_item.id'))
    name = db.Column(db.String(120), nullable=False)
    dimension = db.Column(db.String(80), default='Pedagogia')
    description = db.Column(db.Text)
    weight = db.Column(db.Integer, default=20)
    level_4 = db.Column(db.Text, default='Demuestra dominio sobresaliente y transferencia a otros contextos.')
    level_3 = db.Column(db.Text, default='Cumple de forma consistente con los criterios esperados.')
    level_2 = db.Column(db.Text, default='Evidencia avance parcial; requiere apoyo puntual.')
    level_1 = db.Column(db.Text, default='Presenta dificultades para cumplir el criterio y requiere acompanamiento continuo.')

    bank_item = db.relationship('RubricBankItem')
    scores = db.relationship('LearningExperienceEvaluationScore', backref='rubric', cascade='all, delete-orphan')


class LearningExperienceEvaluation(db.Model):
    __tablename__ = 'learning_experience_evaluation'

    id = db.Column(db.Integer, primary_key=True)
    learning_experience_id = db.Column(db.Integer, db.ForeignKey('learning_experience.id'), nullable=False)
    evaluator_name = db.Column(db.String(100), default='Docente evaluador')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scores = db.relationship('LearningExperienceEvaluationScore', backref='evaluation', cascade='all, delete-orphan')

    @property
    def weighted_score(self):
        total_weight = sum(score.weight for score in self.scores)
        if total_weight <= 0:
            return 0
        weighted_sum = sum(score.level * score.weight for score in self.scores)
        return round(weighted_sum / total_weight, 2)


class LearningExperienceEvaluationScore(db.Model):
    __tablename__ = 'learning_experience_evaluation_score'

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('learning_experience_evaluation.id'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('learning_experience_rubric.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, default=20)


# ---------------------------------------------------------------------------
# Nuevos modelos simplificados
# ---------------------------------------------------------------------------

GRADE_LEVELS = [
    '1ro Primaria', '2do Primaria', '3ro Primaria',
    '4to Primaria', '5to Primaria', '6to Primaria',
    '1ro Secundaria', '2do Secundaria', '3ro Secundaria',
]

MANUAL_TOPICS = [
    'Programacion',
    'Ciudadania Digital',
    'Robotica',
]


class ProjectManual(db.Model):
    __tablename__ = 'project_manual'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    grade_level = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text)
    iframe_url = db.Column(db.String(500))
    content_markdown = db.Column(db.Text)
    estimated_sessions = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rubrics = db.relationship(
        'ProjectRubric',
        backref='manual',
        cascade='all, delete-orphan',
        order_by='ProjectRubric.created_at.asc()'
    )
    weekly_plans = db.relationship('WeeklyPlan', backref='manual', cascade='all, delete-orphan')
    session_plans = db.relationship(
        'ManualSessionPlan',
        backref='manual',
        cascade='all, delete-orphan',
        order_by='ManualSessionPlan.session_number.asc()'
    )
    themes = db.relationship(
        'ProjectManualTheme',
        backref='manual',
        cascade='all, delete-orphan',
        order_by='ProjectManualTheme.theme.asc()'
    )
    scheduled_sessions = db.relationship(
        'ProjectManualSchedule',
        backref='manual',
        cascade='all, delete-orphan',
        order_by='ProjectManualSchedule.start_at.asc()'
    )
    resources = db.relationship(
        'ProjectManualResource',
        backref='manual',
        cascade='all, delete-orphan',
        order_by='ProjectManualResource.position.asc()'
    )

    @property
    def html_content(self):
        return render_safe_markdown(self.content_markdown)

    @property
    def criteria_count(self):
        return sum(len(r.criteria) for r in self.rubrics)

    @property
    def theme_names(self):
        return [t.theme for t in self.themes]


class ProjectManualTheme(db.Model):
    __tablename__ = 'project_manual_theme'

    id = db.Column(db.Integer, primary_key=True)
    manual_id = db.Column(db.Integer, db.ForeignKey('project_manual.id'), nullable=False)
    theme = db.Column(db.String(60), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('manual_id', 'theme', name='uq_project_manual_theme_manual_theme'),
    )


class ProjectManualResource(db.Model):
    __tablename__ = 'project_manual_resource'

    id = db.Column(db.Integer, primary_key=True)
    manual_id = db.Column(db.Integer, db.ForeignKey('project_manual.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500))
    description = db.Column(db.Text)
    position = db.Column(db.Integer, default=1)


class ProjectRubric(db.Model):
    __tablename__ = 'project_rubric'

    id = db.Column(db.Integer, primary_key=True)
    manual_id = db.Column(db.Integer, db.ForeignKey('project_manual.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    criteria = db.relationship(
        'ProjectRubricCriterion',
        backref='rubric',
        cascade='all, delete-orphan',
        order_by='ProjectRubricCriterion.id.asc()'
    )


class ProjectRubricCriterion(db.Model):
    __tablename__ = 'project_rubric_criterion'

    id = db.Column(db.Integer, primary_key=True)
    rubric_id = db.Column(db.Integer, db.ForeignKey('project_rubric.id'), nullable=False)
    bank_item_id = db.Column(db.Integer, db.ForeignKey('rubric_bank_item.id'))
    name = db.Column(db.String(120), nullable=False)
    dimension = db.Column(db.String(80), default='Competencia')
    description = db.Column(db.Text)
    weight = db.Column(db.Integer, default=25)
    level_4 = db.Column(db.Text, default='Demuestra dominio sobresaliente y transferencia a otros contextos.')
    level_3 = db.Column(db.Text, default='Cumple de forma consistente con los criterios esperados.')
    level_2 = db.Column(db.Text, default='Evidencia avance parcial; requiere apoyo puntual.')
    level_1 = db.Column(db.Text, default='Presenta dificultades para cumplir el criterio y requiere acompanamiento continuo.')

    bank_item = db.relationship('RubricBankItem')


class WeeklyPlan(db.Model):
    __tablename__ = 'weekly_plan'

    id = db.Column(db.Integer, primary_key=True)
    manual_id = db.Column(db.Integer, db.ForeignKey('project_manual.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sessions_per_week = db.Column(db.Integer, default=1)
    start_week = db.Column(db.Integer, default=1)  # semana del ciclo escolar
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    @property
    def weeks_needed(self):
        import math
        if self.sessions_per_week <= 0:
            return 0
        return math.ceil(self.manual.estimated_sessions / self.sessions_per_week)

    @property
    def end_week(self):
        return self.start_week + self.weeks_needed - 1


class ManualSessionPlan(db.Model):
    __tablename__ = 'manual_session_plan'

    id = db.Column(db.Integer, primary_key=True)
    manual_id = db.Column(db.Integer, db.ForeignKey('project_manual.id'), nullable=False)
    level = db.Column(db.String(30), default='1')
    session_number = db.Column(db.Integer, nullable=False)
    objective = db.Column(db.Text, nullable=False)
    steam_area_focus = db.Column(db.String(200))
    transversality = db.Column(db.String(200))
    topic = db.Column(db.String(200))
    activity_detail = db.Column(db.Text)
    resources = db.Column(db.String(200))


class ProjectManualSchedule(db.Model):
    __tablename__ = 'project_manual_schedule'

    id = db.Column(db.Integer, primary_key=True)
    manual_id = db.Column(db.Integer, db.ForeignKey('project_manual.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='planned')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)