"""Add resource library

Revision ID: 7a13de6cb74f
Revises: f36f2f8b7d51
Create Date: 2026-04-25 09:42:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a13de6cb74f'
down_revision = 'f36f2f8b7d51'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resource',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('resource_type', sa.String(length=30), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('module_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['training_course.id']),
        sa.ForeignKeyConstraint(['module_id'], ['course_module.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('resource')