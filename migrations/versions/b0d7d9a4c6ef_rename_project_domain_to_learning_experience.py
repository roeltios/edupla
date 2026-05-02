"""Rename project domain to learning experience

Revision ID: b0d7d9a4c6ef
Revises: 4d4af9d1e2b1
Create Date: 2026-04-25 09:05:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'b0d7d9a4c6ef'
down_revision = '4d4af9d1e2b1'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('project', 'learning_experience')
    op.rename_table('project_requirement', 'learning_experience_requirement')
    op.rename_table('project_iste', 'learning_experience_iste')

    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.alter_column('project_id', new_column_name='learning_experience_id')

    with op.batch_alter_table('learning_experience_requirement', schema=None) as batch_op:
        batch_op.alter_column('project_id', new_column_name='learning_experience_id')

    with op.batch_alter_table('learning_experience_iste', schema=None) as batch_op:
        batch_op.alter_column('project_id', new_column_name='learning_experience_id')


def downgrade():
    with op.batch_alter_table('learning_experience_iste', schema=None) as batch_op:
        batch_op.alter_column('learning_experience_id', new_column_name='project_id')

    with op.batch_alter_table('learning_experience_requirement', schema=None) as batch_op:
        batch_op.alter_column('learning_experience_id', new_column_name='project_id')

    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.alter_column('learning_experience_id', new_column_name='project_id')

    op.rename_table('learning_experience_iste', 'project_iste')
    op.rename_table('learning_experience_requirement', 'project_requirement')
    op.rename_table('learning_experience', 'project')