"""Frozen P13 ORM schema for the single-store Smart Inventory Market MVP."""

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BIGINT,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


# MySQL keeps BIGINT identifiers; SQLite test databases require INTEGER primary
# keys to provide equivalent auto-increment behavior.
ID_TYPE = BIGINT().with_variant(Integer, "sqlite")


def utc_now() -> datetime:
    """Return a timezone-naive datetime whose value is explicitly UTC for MySQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    INVENTORY_STAFF = "INVENTORY_STAFF"


class PurchaseOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class StockTransactionType(str, Enum):
    RECEIPT = "RECEIPT"
    SALE = "SALE"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"


class RecommendationStatus(str, Enum):
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    MODIFIED = "MODIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimestampMixin:
    """Creation/update timestamps written by the application in UTC."""

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), default=utc_now, onupdate=utc_now, nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, native_enum=False, create_constraint=True, name="user_role"),
        nullable=False,
        default=UserRole.INVENTORY_STAFF,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        back_populates="created_by_user", foreign_keys="PurchaseOrder.created_by_user_id"
    )
    approved_purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        back_populates="approved_by_user", foreign_keys="PurchaseOrder.approved_by_user_id"
    )
    stock_transactions: Mapped[list["StockTransaction"]] = relationship(back_populates="created_by_user")
    reviewed_recommendations: Mapped[list["ReorderRecommendation"]] = relationship(
        back_populates="reviewed_by_user"
    )
    sessions: Mapped[list["AuthSession"]] = relationship(back_populates="user")


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (Index("ix_auth_sessions_token_hash", "token_hash", unique=True),)

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)
    user: Mapped[User] = relationship(back_populates="sessions")


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="unit", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped[Category] = relationship(back_populates="products")
    supplier_products: Mapped[list["SupplierProduct"]] = relationship(back_populates="product")
    inventory: Mapped["Inventory | None"] = relationship(back_populates="product", uselist=False)
    sales: Mapped[list["SalesDaily"]] = relationship(back_populates="product")
    purchase_order_items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="product")
    stock_transactions: Mapped[list["StockTransaction"]] = relationship(back_populates="product")
    forecast_values: Mapped[list["ForecastValue"]] = relationship(back_populates="product")
    reorder_recommendations: Mapped[list["ReorderRecommendation"]] = relationship(back_populates="product")


class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    supplier_products: Mapped[list["SupplierProduct"]] = relationship(back_populates="supplier")
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="supplier")


class SupplierProduct(TimestampMixin, Base):
    __tablename__ = "supplier_products"
    __table_args__ = (
        UniqueConstraint("supplier_id", "product_id", name="supplier_product_pair"),
        CheckConstraint("lead_time_days > 0", name="lead_time_positive"),
        CheckConstraint("unit_cost IS NULL OR unit_cost >= 0", name="unit_cost_nonnegative"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    supplier_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    supplier: Mapped[Supplier] = relationship(back_populates="supplier_products")
    product: Mapped[Product] = relationship(back_populates="supplier_products")


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (CheckConstraint("on_hand >= 0", name="on_hand_nonnegative"),)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, onupdate=utc_now, nullable=False)

    product: Mapped[Product] = relationship(back_populates="inventory")


class SalesDaily(TimestampMixin, Base):
    __tablename__ = "sales_daily"
    __table_args__ = (
        UniqueConstraint("product_id", "sale_date", name="product_sale_date"),
        CheckConstraint("quantity_sold >= 0", name="quantity_sold_nonnegative"),
        CheckConstraint("sell_price IS NULL OR sell_price >= 0", name="sell_price_nonnegative"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    sell_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)

    product: Mapped[Product] = relationship(back_populates="sales")
    stock_transactions: Mapped[list["StockTransaction"]] = relationship(back_populates="sales_daily")


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (Index("ix_purchase_orders_status", "status"),)

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        SqlEnum(PurchaseOrderStatus, native_enum=False, create_constraint=True, name="purchase_order_status"),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
    )
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_arrival_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier: Mapped[Supplier] = relationship(back_populates="purchase_orders")
    created_by_user: Mapped[User | None] = relationship(
        back_populates="created_purchase_orders", foreign_keys=[created_by_user_id]
    )
    approved_by_user: Mapped[User | None] = relationship(
        back_populates="approved_purchase_orders", foreign_keys=[approved_by_user_id]
    )
    items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="purchase_order")


class PurchaseOrderItem(TimestampMixin, Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        UniqueConstraint("purchase_order_id", "product_id", name="purchase_order_product"),
        CheckConstraint("ordered_quantity > 0", name="ordered_quantity_positive"),
        CheckConstraint("received_quantity >= 0", name="received_quantity_nonnegative"),
        CheckConstraint("received_quantity <= ordered_quantity", name="received_not_over_ordered"),
        CheckConstraint("unit_cost IS NULL OR unit_cost >= 0", name="unit_cost_nonnegative"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    ordered_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="purchase_order_items")
    stock_transactions: Mapped[list["StockTransaction"]] = relationship(back_populates="purchase_order_item")


class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_stock_transactions_product_occurred", "product_id", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    transaction_type: Mapped[StockTransactionType] = mapped_column(
        SqlEnum(StockTransactionType, native_enum=False, create_constraint=True, name="stock_transaction_type"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)
    purchase_order_item_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_order_items.id"), nullable=True)
    sales_daily_id: Mapped[int | None] = mapped_column(ForeignKey("sales_daily.id"), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)

    product: Mapped[Product] = relationship(back_populates="stock_transactions")
    purchase_order_item: Mapped[PurchaseOrderItem | None] = relationship(back_populates="stock_transactions")
    sales_daily: Mapped[SalesDaily | None] = relationship(back_populates="stock_transactions")
    created_by_user: Mapped[User | None] = relationship(back_populates="stock_transactions")


class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    __table_args__ = (CheckConstraint("horizon_days > 0", name="horizon_positive"),)

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_set: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    history_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    forecast_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)

    values: Mapped[list["ForecastValue"]] = relationship(back_populates="forecast_run")
    reorder_recommendations: Mapped[list["ReorderRecommendation"]] = relationship(back_populates="forecast_run")


class ForecastValue(Base):
    __tablename__ = "forecast_values"
    __table_args__ = (
        UniqueConstraint("forecast_run_id", "product_id", "forecast_date", name="forecast_run_product_date"),
        CheckConstraint("predicted_demand >= 0", name="predicted_demand_nonnegative"),
        CheckConstraint("horizon_day > 0", name="horizon_day_positive"),
        Index("ix_forecast_values_product_date", "product_id", "forecast_date"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    forecast_run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_day: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_demand: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)

    forecast_run: Mapped[ForecastRun] = relationship(back_populates="values")
    product: Mapped[Product] = relationship(back_populates="forecast_values")


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_set: Mapped[str] = mapped_column(String(100), nullable=False)
    dataset_split: Mapped[str] = mapped_column(String(64), nullable=False)
    mae: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    rmse: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    wape: Mapped[Decimal | None] = mapped_column(Numeric(14, 6), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ReorderRecommendation(Base):
    __tablename__ = "reorder_recommendations"
    __table_args__ = (
        CheckConstraint("current_on_hand >= 0", name="current_on_hand_nonnegative"),
        CheckConstraint("incoming_quantity >= 0", name="incoming_quantity_nonnegative"),
        CheckConstraint("lead_time_days > 0", name="lead_time_positive"),
        CheckConstraint("safety_stock >= 0", name="safety_stock_nonnegative"),
        CheckConstraint("reorder_point >= 0", name="reorder_point_nonnegative"),
        CheckConstraint("recommended_quantity >= 0", name="recommended_quantity_nonnegative"),
        CheckConstraint("approved_quantity IS NULL OR approved_quantity >= 0", name="approved_quantity_nonnegative"),
        Index("ix_reorder_recommendations_product_created", "product_id", "created_at"),
        Index("ix_reorder_recommendations_status", "status"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    forecast_run_id: Mapped[int | None] = mapped_column(ForeignKey("forecast_runs.id"), nullable=True)
    status: Mapped[RecommendationStatus] = mapped_column(
        SqlEnum(RecommendationStatus, native_enum=False, create_constraint=True, name="recommendation_status"),
        default=RecommendationStatus.NEW,
        nullable=False,
    )
    current_on_hand: Mapped[int] = mapped_column(Integer, nullable=False)
    incoming_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False)
    recommended_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped[Product] = relationship(back_populates="reorder_recommendations")
    forecast_run: Mapped[ForecastRun | None] = relationship(back_populates="reorder_recommendations")
    reviewed_by_user: Mapped[User | None] = relationship(back_populates="reviewed_recommendations")
