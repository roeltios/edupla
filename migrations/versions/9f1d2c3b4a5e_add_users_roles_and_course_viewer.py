"""Add users, roles, teacher-course assignments and course viewer URL

Revision ID: 9f1d2c3b4a5e
Revises: e1b0f4d22a1d
Create Date: 2026-04-25 18:50:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f1d2c3b4a5e'
down_revision = 'e1b0f4d22a1d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=160), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='teacher'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    op.create_table(
        'course_teacher',
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['training_course.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('course_id', 'user_id'),
    )

    op.add_column('training_course', sa.Column('viewer_url', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('training_course', 'viewer_url')
    op.drop_table('course_teacher')
    op.drop_table('user')
