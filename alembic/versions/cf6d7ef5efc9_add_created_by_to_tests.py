"""add_created_by_to_tests

Revision ID: cf6d7ef5efc9
Revises: add_teacher_student
Create Date: 2026-04-12 14:41:36.970303

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf6d7ef5efc9'
down_revision = 'add_teacher_student'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_by column to tests table
    op.add_column('tests', sa.Column('created_by', sa.String(), nullable=True))
    op.create_foreign_key('tests_created_by_fkey', 'tests', 'users', ['created_by'], ['id'], ondelete='CASCADE')
    op.create_index('ix_tests_created_by', 'tests', ['created_by'])


def downgrade() -> None:
    # Remove created_by column from tests table
    op.drop_index('ix_tests_created_by', 'tests')
    op.drop_constraint('tests_created_by_fkey', 'tests', type_='foreignkey')
    op.drop_column('tests', 'created_by')
