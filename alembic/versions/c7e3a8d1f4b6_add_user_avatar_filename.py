"""add nullable generated user avatar filename

Revision ID: c7e3a8d1f4b6
Revises: f6b8c4d92a10
"""

from alembic import op
import sqlalchemy as sa


revision = "c7e3a8d1f4b6"
down_revision = "f6b8c4d92a10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_filename", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_filename")
