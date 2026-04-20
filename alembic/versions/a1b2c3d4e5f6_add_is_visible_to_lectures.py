"""add_is_visible_to_lectures

Revision ID: a1b2c3d4e5f6
Revises: cf6d7ef5efc9
Create Date: 2026-04-20 09:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "cf6d7ef5efc9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_visible column so teachers can hide lectures from students.
    op.add_column(
        "lectures",
        sa.Column(
            "is_visible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("lectures", "is_visible")
