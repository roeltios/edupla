"""add project manual resources table

Revision ID: c4e2f9b0a1d7
Revises: b7f4c8d21a9e
Create Date: 2026-05-05 15:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4e2f9b0a1d7'
down_revision = 'b7f4c8d21a9e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project_manual_resource',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manual_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['manual_id'], ['project_manual.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_project_manual_resource_manual_position', 'project_manual_resource', ['manual_id', 'position'], unique=False)


def downgrade():
    op.drop_index('ix_project_manual_resource_manual_position', table_name='project_manual_resource')
    op.drop_table('project_manual_resource')
