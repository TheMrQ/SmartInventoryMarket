"""Public request/response contracts for the P14 operational API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.db.models import PurchaseOrderStatus, RecommendationStatus, StockTransactionType


NonBlank = Annotated[str, Field(min_length=1)]


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(ApiModel):
    code: NonBlank = Field(max_length=64)
    name: NonBlank = Field(max_length=255)
    description: str | None = None

    @field_validator("code", "name")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class CategoryUpdate(ApiModel):
    code: NonBlank | None = Field(default=None, max_length=64)
    name: NonBlank | None = Field(default=None, max_length=255)
    description: str | None = None

    @field_validator("code", "name")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class CategoryRead(CategoryCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class ProductCreate(ApiModel):
    sku: NonBlank = Field(max_length=100)
    name: NonBlank = Field(max_length=255)
    category_id: int = Field(gt=0)
    unit: NonBlank = Field(default="unit", max_length=32)
    is_active: bool = True

    @field_validator("sku", "name", "unit")
    @classmethod
    def trim_product_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class ProductUpdate(ApiModel):
    sku: NonBlank | None = Field(default=None, max_length=100)
    name: NonBlank | None = Field(default=None, max_length=255)
    category_id: int | None = Field(default=None, gt=0)
    unit: NonBlank | None = Field(default=None, max_length=32)
    is_active: bool | None = None

    @field_validator("sku", "name", "unit")
    @classmethod
    def trim_optional_product_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class ProductRead(ProductCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class SupplierCreate(ApiModel):
    code: NonBlank = Field(max_length=64)
    name: NonBlank = Field(max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    address: str | None = None
    is_active: bool = True

    @field_validator("code", "name")
    @classmethod
    def trim_supplier_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class SupplierUpdate(ApiModel):
    code: NonBlank | None = Field(default=None, max_length=64)
    name: NonBlank | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    address: str | None = None
    is_active: bool | None = None


class SupplierRead(SupplierCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class SupplierProductCreate(ApiModel):
    supplier_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    supplier_sku: str | None = Field(default=None, max_length=100)
    unit_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    lead_time_days: int = Field(gt=0)
    is_preferred: bool = False


class SupplierProductUpdate(ApiModel):
    supplier_sku: str | None = Field(default=None, max_length=100)
    unit_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    lead_time_days: int | None = Field(default=None, gt=0)
    is_preferred: bool | None = None


class SupplierProductRead(SupplierProductCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class InventoryRead(ApiModel):
    product_id: int
    sku: str
    product_name: str
    on_hand: int
    incoming_quantity: int
    inventory_position: int
    updated_at: datetime


class AdjustmentCreate(ApiModel):
    transaction_type: StockTransactionType
    quantity: int = Field(gt=0)
    reason: NonBlank = Field(max_length=2000)
    created_by_user_id: int | None = Field(default=None, gt=0)

    @field_validator("transaction_type")
    @classmethod
    def adjustment_type_only(cls, value: StockTransactionType) -> StockTransactionType:
        if value not in {StockTransactionType.ADJUSTMENT_IN, StockTransactionType.ADJUSTMENT_OUT}:
            raise ValueError("manual adjustments must use ADJUSTMENT_IN or ADJUSTMENT_OUT")
        return value


class StockTransactionRead(ApiModel):
    id: int
    product_id: int
    transaction_type: StockTransactionType
    quantity: int
    occurred_at: datetime
    purchase_order_item_id: int | None
    sales_daily_id: int | None
    created_by_user_id: int | None
    reason: str | None
    created_at: datetime


class SalesDailyRead(ApiModel):
    id: int
    product_id: int
    sale_date: date
    quantity_sold: int
    sell_price: Decimal | None
    source: str | None
    created_at: datetime
    updated_at: datetime


class SalesImportResult(ApiModel):
    rows_received: int
    rows_inserted: int
    rows_updated: int
    rows_rejected: int


class OperationalSaleCreate(ApiModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    sale_date: date
    sell_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    source: str | None = Field(default="MANUAL", max_length=100)
    created_by_user_id: int | None = Field(default=None, gt=0)


class ForecastCreate(ApiModel):
    product_ids: list[int] = Field(min_length=1, max_length=100)
    horizon_days: int

    @field_validator("product_ids")
    @classmethod
    def unique_product_ids(cls, values: list[int]) -> list[int]:
        if any(value <= 0 for value in values) or len(values) != len(set(values)):
            raise ValueError("product_ids must be unique positive identifiers")
        return values

    @field_validator("horizon_days")
    @classmethod
    def supported_horizon(cls, value: int) -> int:
        if value not in {7, 14, 28}:
            raise ValueError("horizon_days must be one of 7, 14, or 28")
        return value


class ForecastValueRead(ApiModel):
    id: int
    product_id: int
    forecast_date: date
    horizon_day: int
    predicted_demand: Decimal


class ForecastTotals(ApiModel):
    days_7: Decimal | None = None
    days_14: Decimal | None = None
    days_28: Decimal | None = None


class ForecastRunRead(ApiModel):
    id: int
    model_name: str
    feature_set: str
    model_version: str | None
    history_end_date: date
    forecast_start_date: date
    horizon_days: int
    generated_at: datetime
    values: list[ForecastValueRead] = []
    totals_by_product: dict[int, ForecastTotals] = {}


class InventoryDecisionRead(ApiModel):
    product_id: int
    sku: str
    product_name: str
    on_hand: int
    incoming_quantity: int
    inventory_position: int
    forecast_run_id: int
    lead_time_days: int
    expected_lead_time_demand: Decimal
    safety_stock: int
    reorder_point: int
    target_stock: int
    risk_status: Literal["STOCKOUT_RISK", "REORDER_NEEDED", "HEALTHY", "OVERSTOCK_RISK"]
    recommended_quantity: int
    supplier_id: int
    supplier_name: str


class RecommendationGenerate(ApiModel):
    product_id: int = Field(gt=0)


class RecommendationGenerateResult(ApiModel):
    decision: InventoryDecisionRead
    recommendation: "ReorderRecommendationRead | None" = None


class ReorderRecommendationRead(ApiModel):
    id: int
    product_id: int
    forecast_run_id: int | None
    status: "RecommendationStatus"
    current_on_hand: int
    incoming_quantity: int
    lead_time_days: int
    safety_stock: int
    reorder_point: int
    recommended_quantity: int
    approved_quantity: int | None
    created_at: datetime
    expires_at: datetime | None
    reviewed_at: datetime | None
    reviewed_by_user_id: int | None
    notes: str | None
    supplier_id: int | None = None
    supplier_name: str | None = None


class RecommendationReview(ApiModel):
    action: Literal["ACCEPT", "MODIFY", "REJECT"]
    approved_quantity: int | None = Field(default=None, ge=0)
    reviewed_by_user_id: int | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=2000)


class PurchaseOrderItemCreate(ApiModel):
    product_id: int = Field(gt=0)
    ordered_quantity: int = Field(gt=0)
    unit_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class PurchaseOrderItemUpdate(ApiModel):
    ordered_quantity: int | None = Field(default=None, gt=0)
    unit_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class PurchaseOrderItemRead(ApiModel):
    id: int
    product_id: int
    ordered_quantity: int
    received_quantity: int
    unit_cost: Decimal | None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderCreate(ApiModel):
    po_number: NonBlank = Field(max_length=64)
    supplier_id: int = Field(gt=0)
    expected_arrival_date: date | None = None
    created_by_user_id: int | None = Field(default=None, gt=0)
    notes: str | None = None
    items: list[PurchaseOrderItemCreate] = Field(min_length=1)

    @field_validator("po_number")
    @classmethod
    def trim_po_number(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class PurchaseOrderRead(ApiModel):
    id: int
    po_number: str
    supplier_id: int
    status: PurchaseOrderStatus
    order_date: date | None
    expected_arrival_date: date | None
    received_at: datetime | None
    created_by_user_id: int | None
    approved_by_user_id: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItemRead]


class PurchaseOrderTransition(ApiModel):
    target_status: PurchaseOrderStatus
    approved_by_user_id: int | None = Field(default=None, gt=0)


class ReceiptLine(ApiModel):
    purchase_order_item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class ReceiptCreate(ApiModel):
    items: list[ReceiptLine] = Field(min_length=1)
    created_by_user_id: int | None = Field(default=None, gt=0)
