"""add M5 demo scenario provenance

Revision ID: f6b8c4d92a10
Revises: d4e9a6c21f35
"""

from alembic import op
import sqlalchemy as sa


revision = "f6b8c4d92a10"
down_revision = "d4e9a6c21f35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "demo_scenarios",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("scenario_key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("m5_store_id", sa.String(length=32), nullable=False),
        sa.Column("source_sales_file", sa.String(length=255), nullable=False),
        sa.Column("source_calendar_file", sa.String(length=255), nullable=False),
        sa.Column("source_prices_file", sa.String(length=255), nullable=False),
        sa.Column("history_start_d", sa.String(length=16), nullable=False),
        sa.Column("history_end_d", sa.String(length=16), nullable=False),
        sa.Column("selection_size", sa.Integer(), nullable=False),
        sa.Column("selection_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "demo_product_sources",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("scenario_id", sa.BigInteger(), sa.ForeignKey("demo_scenarios.id"), nullable=False),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("m5_item_id", sa.String(length=100), nullable=False),
        sa.Column("m5_dept_id", sa.String(length=64), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.UniqueConstraint("scenario_id", "product_id", name="demo_scenario_product"),
        sa.UniqueConstraint("scenario_id", "m5_item_id", name="demo_scenario_m5_item"),
    )
    op.create_table(
        "demo_scenario_forecasts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("scenario_id", sa.BigInteger(), sa.ForeignKey("demo_scenarios.id"), nullable=False),
        sa.Column("forecast_run_id", sa.BigInteger(), sa.ForeignKey("forecast_runs.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("scenario_id", "forecast_run_id", name="demo_scenario_forecast"),
    )


def downgrade() -> None:
    op.drop_table("demo_scenario_forecasts")
    op.drop_table("demo_product_sources")
    op.drop_table("demo_scenarios")
