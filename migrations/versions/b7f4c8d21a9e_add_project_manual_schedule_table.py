"""add project manual schedule table

Revision ID: b7f4c8d21a9e
Revises: a12d9f3c6e1b
Create Date: 2026-04-30 17:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f4c8d21a9e'
down_revision = 'a12d9f3c6e1b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project_manual_schedule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manual_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manual_id'], ['project_manual.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_project_manual_schedule_start_at', 'project_manual_schedule', ['start_at'], unique=False)
    op.create_index('ix_project_manual_schedule_user_start', 'project_manual_schedule', ['user_id', 'start_at'], unique=False)


def downgrade():
    op.drop_index('ix_project_manual_schedule_user_start', table_name='project_manual_schedule')
    op.drop_index('ix_project_manual_schedule_start_at', table_name='project_manual_schedule')
    op.drop_table('project_manual_schedule')
