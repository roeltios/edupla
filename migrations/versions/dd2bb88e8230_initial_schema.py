"""Initial schema

Revision ID: dd2bb88e8230
Revises: 
Create Date: 2026-04-25 08:19:22.093980

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd2bb88e8230'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'iste_standard',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    op.create_table(
        'material',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('level', sa.String(length=50), nullable=True),
        sa.Column('planning_markdown', sa.Text(), nullable=True),
        sa.Column('image_file', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'project_iste',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('iste_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['iste_id'], ['iste_standard.id']),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('project_id', 'iste_id'),
    )

    op.create_table(
        'project_requirement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('material_id', sa.Integer(), nullable=True),
        sa.Column('quantity_needed', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['material_id'], ['material.id']),
        sa.ForeignKeyConstraint(['project_id'], ['project.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('project_requirement')
    op.drop_table('project_iste')
    op.drop_table('comment')
    op.drop_table('project')
    op.drop_table('material')
    op.drop_table('iste_standard')
