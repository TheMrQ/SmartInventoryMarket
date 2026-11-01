"""add P21 audit attribution, sale idempotency, and recommendation PO link

Revision ID: d4e9a6c21f35
Revises: a91c2e6f4b20
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e9a6c21f35"
down_revision = "a91c2e6f4b20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operational_sales",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("sales_daily_id", sa.BigInteger(), sa.ForeignKey("sales_daily.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("sell_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="operational_sale_idempotency_key"),
    )
    with op.batch_alter_table("purchase_orders") as batch:
        batch.add_column(sa.Column("reorder_recommendation_id", sa.BigInteger(), nullable=True))
        batch.create_foreign_key(
            "fk_purchase_orders_reorder_recommendation",
            "reorder_recommendations",
            ["reorder_recommendation_id"],
            ["id"],
        )
        batch.create_unique_constraint("purchase_order_recommendation_unique", ["reorder_recommendation_id"])


def downgrade() -> None:
    with op.batch_alter_table("purchase_orders") as batch:
        batch.drop_constraint("purchase_order_recommendation_unique", type_="unique")
        batch.drop_constraint("fk_purchase_orders_reorder_recommendation", type_="foreignkey")
        batch.drop_column("reorder_recommendation_id")
    op.drop_table("operational_sales")
