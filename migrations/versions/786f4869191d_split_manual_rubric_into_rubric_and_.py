"""split manual rubric into rubric and criteria

Revision ID: 786f4869191d
Revises: 42b8948b2da4
Create Date: 2026-04-30 10:24:06.122104

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '786f4869191d'
down_revision = '42b8948b2da4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project_rubric',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manual_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manual_id'], ['project_manual.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'project_rubric_criterion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rubric_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['rubric_id'], ['project_rubric.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    bind = op.get_bind()
    old_rubric = sa.table(
        'manual_rubric',
        sa.column('id', sa.Integer),
        sa.column('manual_id', sa.Integer),
        sa.column('bank_item_id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('dimension', sa.String),
        sa.column('description', sa.Text),
        sa.column('weight', sa.Integer),
        sa.column('level_4', sa.Text),
        sa.column('level_3', sa.Text),
        sa.column('level_2', sa.Text),
        sa.column('level_1', sa.Text),
    )
    new_rubric = sa.table(
        'project_rubric',
        sa.column('id', sa.Integer),
        sa.column('manual_id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('created_at', sa.DateTime),
    )
    new_criterion = sa.table(
        'project_rubric_criterion',
        sa.column('rubric_id', sa.Integer),
        sa.column('bank_item_id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('dimension', sa.String),
        sa.column('description', sa.Text),
        sa.column('weight', sa.Integer),
        sa.column('level_4', sa.Text),
        sa.column('level_3', sa.Text),
        sa.column('level_2', sa.Text),
        sa.column('level_1', sa.Text),
    )

    manual_ids = [
        row[0] for row in bind.execute(
            sa.select(old_rubric.c.manual_id).distinct()
        ).fetchall()
    ]

    for manual_id in manual_ids:
        bind.execute(
            new_rubric.insert().values(
                manual_id=manual_id,
                name='Rubrica general',
                description='Migrada automaticamente desde criterios existentes.',
                created_at=datetime.utcnow(),
            )
        )
        rubric_id = bind.execute(
            sa.select(new_rubric.c.id)
            .where(new_rubric.c.manual_id == manual_id)
            .order_by(new_rubric.c.id.desc())
            .limit(1)
        ).scalar_one()

        old_rows = bind.execute(
            sa.select(
                old_rubric.c.bank_item_id,
                old_rubric.c.name,
                old_rubric.c.dimension,
                old_rubric.c.description,
                old_rubric.c.weight,
                old_rubric.c.level_4,
                old_rubric.c.level_3,
                old_rubric.c.level_2,
                old_rubric.c.level_1,
            ).where(old_rubric.c.manual_id == manual_id)
        ).fetchall()

        for row in old_rows:
            bind.execute(
                new_criterion.insert().values(
                    rubric_id=rubric_id,
                    bank_item_id=row.bank_item_id,
                    name=row.name,
                    dimension=row.dimension,
                    description=row.description,
                    weight=row.weight,
                    level_4=row.level_4,
                    level_3=row.level_3,
                    level_2=row.level_2,
                    level_1=row.level_1,
                )
            )

    op.drop_table('manual_rubric')


def downgrade():
    op.create_table(
        'manual_rubric',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('manual_id', sa.INTEGER(), nullable=False),
        sa.Column('bank_item_id', sa.INTEGER(), nullable=True),
        sa.Column('name', sa.VARCHAR(length=120), nullable=False),
        sa.Column('dimension', sa.VARCHAR(length=80), nullable=True),
        sa.Column('description', sa.TEXT(), nullable=True),
        sa.Column('weight', sa.INTEGER(), nullable=True),
        sa.Column('level_4', sa.TEXT(), nullable=True),
        sa.Column('level_3', sa.TEXT(), nullable=True),
        sa.Column('level_2', sa.TEXT(), nullable=True),
        sa.Column('level_1', sa.TEXT(), nullable=True),
        sa.ForeignKeyConstraint(['bank_item_id'], ['rubric_bank_item.id']),
        sa.ForeignKeyConstraint(['manual_id'], ['project_manual.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    bind = op.get_bind()
    old_rubric = sa.table(
        'manual_rubric',
        sa.column('manual_id', sa.Integer),
        sa.column('bank_item_id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('dimension', sa.String),
        sa.column('description', sa.Text),
        sa.column('weight', sa.Integer),
        sa.column('level_4', sa.Text),
        sa.column('level_3', sa.Text),
        sa.column('level_2', sa.Text),
        sa.column('level_1', sa.Text),
    )
    project_rubric = sa.table(
        'project_rubric',
        sa.column('id', sa.Integer),
        sa.column('manual_id', sa.Integer),
    )
    criteria = sa.table(
        'project_rubric_criterion',
        sa.column('rubric_id', sa.Integer),
        sa.column('bank_item_id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('dimension', sa.String),
        sa.column('description', sa.Text),
        sa.column('weight', sa.Integer),
        sa.column('level_4', sa.Text),
        sa.column('level_3', sa.Text),
        sa.column('level_2', sa.Text),
        sa.column('level_1', sa.Text),
    )

    rows = bind.execute(
        sa.select(
            project_rubric.c.manual_id,
            criteria.c.bank_item_id,
            criteria.c.name,
            criteria.c.dimension,
            criteria.c.description,
            criteria.c.weight,
            criteria.c.level_4,
            criteria.c.level_3,
            criteria.c.level_2,
            criteria.c.level_1,
        ).select_from(
            criteria.join(project_rubric, criteria.c.rubric_id == project_rubric.c.id)
        )
    ).fetchall()

    for row in rows:
        bind.execute(
            old_rubric.insert().values(
                manual_id=row.manual_id,
                bank_item_id=row.bank_item_id,
                name=row.name,
                dimension=row.dimension,
                description=row.description,
                weight=row.weight,
                level_4=row.level_4,
                level_3=row.level_3,
                level_2=row.level_2,
                level_1=row.level_1,
            )
        )

    op.drop_table('project_rubric_criterion')
    op.drop_table('project_rubric')
