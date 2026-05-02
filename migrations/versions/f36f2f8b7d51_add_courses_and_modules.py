"""Add courses and modules

Revision ID: f36f2f8b7d51
Revises: b0d7d9a4c6ef
Create Date: 2026-04-25 09:28:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f36f2f8b7d51'
down_revision = 'b0d7d9a4c6ef'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'training_course',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_profile', sa.String(length=160), nullable=True),
        sa.Column('duration', sa.String(length=60), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'course_module',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['training_course.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('learning_experience', schema=None) as batch_op:
        batch_op.add_column(sa.Column('module_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_learning_experience_module_id', 'course_module', ['module_id'], ['id'])


def downgrade():
    with op.batch_alter_table('learning_experience', schema=None) as batch_op:
        batch_op.drop_constraint('fk_learning_experience_module_id', type_='foreignkey')
        batch_op.drop_column('module_id')

    op.drop_table('course_module')
    op.drop_table('training_course')