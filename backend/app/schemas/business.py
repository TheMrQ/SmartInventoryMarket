"""Public request/response contracts for the P14 operational API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.db.models import PurchaseOrderStatus, StockTransactionType


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
