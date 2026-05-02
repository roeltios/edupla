"""Add teacher focus fields to project

Revision ID: 4d4af9d1e2b1
Revises: dd2bb88e8230
Create Date: 2026-04-25 08:32:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d4af9d1e2b1'
down_revision = 'dd2bb88e8230'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('teacher_profile', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('course_focus', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('learning_objective', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('classroom_application', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('minimal_technology', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('estimated_duration', sa.String(length=50), nullable=True))

    op.execute(
        """
        UPDATE project
        SET teacher_profile = COALESCE(teacher_profile, 'Docente frente a grupo'),
            course_focus = COALESCE(course_focus, 'Tecnologia educativa'),
            minimal_technology = COALESCE(minimal_technology, 'Computadora con editor de codigo'),
            estimated_duration = COALESCE(estimated_duration, '60 minutos')
        """
    )

    op.execute(
        """
        UPDATE project
        SET teacher_profile = 'Docente normalista con nociones basicas de computacion',
            course_focus = 'Pensamiento computacional aplicado a proyectos guiados',
            learning_objective = 'Ayudar al docente a traducir secuencias, ciclos y precision en una experiencia tangible y explicable para adolescentes.',
            classroom_application = 'Puede implementarse como demostracion guiada o como reto por equipos en una clase de tecnologia o ciencias.',
            minimal_technology = 'Una computadora por equipo y un Arduino Uno compartido',
            estimated_duration = '90 minutos'
        WHERE title = 'Brazo Robótico Programable'
        """
    )

    op.execute(
        """
        UPDATE project
        SET teacher_profile = 'Docente de ciencias o tecnologia con interes en proyectos interdisciplinarios',
            course_focus = 'Integracion de programacion, datos y sostenibilidad',
            learning_objective = 'Mostrar al docente como conectar programacion basica y analisis de datos con problemas reales del entorno escolar.',
            classroom_application = 'Funciona como proyecto de cierre para materias STEAM o para clubes escolares con enfoque ambiental.',
            minimal_technology = 'Una computadora con Wi-Fi y un ESP32 por equipo',
            estimated_duration = '2 sesiones de 50 minutos'
        WHERE title = 'Sistema de Riego Automático IoT'
        """
    )


def downgrade():
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('estimated_duration')
        batch_op.drop_column('minimal_technology')
        batch_op.drop_column('classroom_application')
        batch_op.drop_column('learning_objective')
        batch_op.drop_column('course_focus')
        batch_op.drop_column('teacher_profile')