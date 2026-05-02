"""Add workflow/template/board fields to learning experience

Revision ID: e1b0f4d22a1d
Revises: c92f1c14a6be
Create Date: 2026-04-25 14:05:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1b0f4d22a1d'
down_revision = 'c92f1c14a6be'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('learning_experience', sa.Column('workflow_status', sa.String(length=20), nullable=True))
    op.add_column('learning_experience', sa.Column('board_stage', sa.String(length=30), nullable=True))
    op.add_column('learning_experience', sa.Column('week_slot', sa.Integer(), nullable=True))
    op.add_column('learning_experience', sa.Column('is_template', sa.Boolean(), nullable=True))

    op.execute("UPDATE learning_experience SET workflow_status = 'draft' WHERE workflow_status IS NULL")
    op.execute("UPDATE learning_experience SET board_stage = 'por_planear' WHERE board_stage IS NULL")
    op.execute("UPDATE learning_experience SET week_slot = 1 WHERE week_slot IS NULL")
    op.execute("UPDATE learning_experience SET is_template = FALSE WHERE is_template IS NULL")


def downgrade():
    op.drop_column('learning_experience', 'is_template')
    op.drop_column('learning_experience', 'week_slot')
    op.drop_column('learning_experience', 'board_stage')
    op.drop_column('learning_experience', 'workflow_status')
