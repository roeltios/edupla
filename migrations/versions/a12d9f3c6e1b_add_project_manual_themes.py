"""add project manual themes

Revision ID: a12d9f3c6e1b
Revises: 786f4869191d
Create Date: 2026-04-30 11:05:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a12d9f3c6e1b'
down_revision = '786f4869191d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project_manual_theme',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manual_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(length=60), nullable=False),
        sa.ForeignKeyConstraint(['manual_id'], ['project_manual.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('manual_id', 'theme', name='uq_project_manual_theme_manual_theme'),
    )

    bind = op.get_bind()
    manual = sa.table(
        'project_manual',
        sa.column('id', sa.Integer),
        sa.column('title', sa.String),
        sa.column('description', sa.Text),
        sa.column('content_markdown', sa.Text),
    )
    manual_theme = sa.table(
        'project_manual_theme',
        sa.column('manual_id', sa.Integer),
        sa.column('theme', sa.String),
    )

    rows = bind.execute(
        sa.select(
            manual.c.id,
            manual.c.title,
            manual.c.description,
            manual.c.content_markdown,
        )
    ).fetchall()

    for row in rows:
        text = ' '.join([
            row.title or '',
            row.description or '',
            row.content_markdown or '',
        ]).lower()

        themes = set()
        if any(word in text for word in ['robot', 'sensor', 'motor', 'arduino']):
            themes.add('Robotica')
        if any(word in text for word in ['ciudadania', 'digital', 'internet', 'ciber', 'privacidad', 'seguridad']):
            themes.add('Ciudadania Digital')
        if any(word in text for word in ['program', 'codigo', 'algorit', 'scratch', 'computacion']):
            themes.add('Programacion')
        if not themes:
            themes.add('Programacion')

        for theme in sorted(themes):
            bind.execute(
                manual_theme.insert().values(
                    manual_id=row.id,
                    theme=theme,
                )
            )


def downgrade():
    op.drop_table('project_manual_theme')
