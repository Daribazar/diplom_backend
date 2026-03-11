"""add_color_to_courses

Revision ID: 3f8a9b2c1d5e
Revises: 2604c9471c0c
Create Date: 2026-03-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f8a9b2c1d5e'
down_revision = '2604c9471c0c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add color column to courses table with default value
    op.add_column('courses', sa.Column('color', sa.String(length=20), nullable=False, server_default='indigo'))


def downgrade() -> None:
    # Remove color column from courses table
    op.drop_column('courses', 'color')
