"""add nullable daily retail sell price

Revision ID: 8ac7d44590e3
Revises: f86d36b27719
Create Date: 2026-10-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "8ac7d44590e3"
down_revision: str | Sequence[str] | None = "f86d36b27719"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sales_daily", sa.Column("sell_price", sa.Numeric(precision=12, scale=2), nullable=True))
    op.create_check_constraint("ck_sales_daily_sell_price_nonnegative", "sales_daily", "sell_price IS NULL OR sell_price >= 0")


def downgrade() -> None:
    op.drop_constraint("ck_sales_daily_sell_price_nonnegative", "sales_daily", type_="check")
    op.drop_column("sales_daily", "sell_price")
