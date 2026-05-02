"""Add rubric bank and evaluations

Revision ID: c92f1c14a6be
Revises: 7a13de6cb74f
Create Date: 2026-04-25 12:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c92f1c14a6be'
down_revision = '7a13de6cb74f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'rubric_bank_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('dimension', sa.String(length=80), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_weight', sa.Integer(), nullable=True),
        sa.Column('level_4', sa.Text(), nullable=True),
        sa.Column('level_3', sa.Text(), nullable=True),
        sa.Column('level_2', sa.Text(), nullable=True),
        sa.Column('level_1', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'learning_experience_rubric',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learning_experience_id', sa.Integer(), nullable=False),
        sa.Column('bank_item_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('dimension', sa.String(length=80), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Integer(), nullable=True),
        sa.Column('level_4', sa.Text(), nullable=True),
        sa.Column('level_3', sa.Text(), nullable=True),
        sa.Column('level_2', sa.Text(), nullable=True),
        sa.Column('level_1', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['bank_item_id'], ['rubric_bank_item.id']),
        sa.ForeignKeyConstraint(['learning_experience_id'], ['learning_experience.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'learning_experience_evaluation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learning_experience_id', sa.Integer(), nullable=False),
        sa.Column('evaluator_name', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['learning_experience_id'], ['learning_experience.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'learning_experience_evaluation_score',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('rubric_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['learning_experience_evaluation.id']),
        sa.ForeignKeyConstraint(['rubric_id'], ['learning_experience_rubric.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('learning_experience_evaluation_score')
    op.drop_table('learning_experience_evaluation')
    op.drop_table('learning_experience_rubric')
    op.drop_table('rubric_bank_item')
