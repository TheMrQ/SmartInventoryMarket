"""P14 HTTP routes: thin request/response adapters over the business service."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.api.auth import operational_user
from backend.app.db.models import PurchaseOrderStatus, StockTransactionType
from backend.app.schemas.business import (
    AdjustmentCreate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    InventoryRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderItemUpdate,
    PurchaseOrderRead,
    PurchaseOrderTransition,
    ReceiptCreate,
    StockTransactionRead,
    SupplierCreate,
    SupplierProductCreate,
    SupplierProductRead,
    SupplierProductUpdate,
    SupplierRead,
    SupplierUpdate,
)
from backend.app.services.business import BusinessService
from backend.app.services.errors import NotFoundError


router = APIRouter(prefix="/api", dependencies=[Depends(operational_user)])
SessionDep = Annotated[Session, Depends(get_db_session)]
PageSize = Annotated[int, Query(ge=1, le=100)]
PageOffset = Annotated[int, Query(ge=0)]


def service(session: SessionDep) -> BusinessService:
    return BusinessService(session)


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(data: CategoryCreate, session: SessionDep):
    return service(session).category_create(data)


@router.get("/categories", response_model=list[CategoryRead], tags=["Categories"])
def list_categories(session: SessionDep, limit: PageSize = 50, offset: PageOffset = 0):
    return service(session).categories(limit, offset)


@router.get("/categories/{category_id}", response_model=CategoryRead, tags=["Categories"])
def get_category(category_id: int, session: SessionDep):
    return service(session).category(category_id)


@router.patch("/categories/{category_id}", response_model=CategoryRead, tags=["Categories"])
def update_category(category_id: int, data: CategoryUpdate, session: SessionDep):
    return service(session).category_update(category_id, data)


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_product(data: ProductCreate, session: SessionDep):
    return service(session).product_create(data)


@router.get("/products", response_model=list[ProductRead], tags=["Products"])
def list_products(
    session: SessionDep,
    search: str | None = None,
    category_id: int | None = Query(default=None, gt=0),
    is_active: bool | None = None,
    limit: PageSize = 50,
    offset: PageOffset = 0,
):
    return service(session).products(search, category_id, is_active, limit, offset)


@router.get("/products/{product_id}", response_model=ProductRead, tags=["Products"])
def get_product(product_id: int, session: SessionDep):
    return service(session).product(product_id)


@router.patch("/products/{product_id}", response_model=ProductRead, tags=["Products"])
def update_product(product_id: int, data: ProductUpdate, session: SessionDep):
    return service(session).product_update(product_id, data)


@router.post("/suppliers", response_model=SupplierRead, status_code=status.HTTP_201_CREATED, tags=["Suppliers"])
def create_supplier(data: SupplierCreate, session: SessionDep):
    return service(session).supplier_create(data)


@router.get("/suppliers", response_model=list[SupplierRead], tags=["Suppliers"])
def list_suppliers(session: SessionDep, is_active: bool | None = None, limit: PageSize = 50, offset: PageOffset = 0):
    return service(session).suppliers(is_active, limit, offset)


@router.get("/suppliers/{supplier_id}", response_model=SupplierRead, tags=["Suppliers"])
def get_supplier(supplier_id: int, session: SessionDep):
    return service(session).supplier(supplier_id)


@router.patch("/suppliers/{supplier_id}", response_model=SupplierRead, tags=["Suppliers"])
def update_supplier(supplier_id: int, data: SupplierUpdate, session: SessionDep):
    return service(session).supplier_update(supplier_id, data)


@router.post(
    "/supplier-products", response_model=SupplierProductRead, status_code=status.HTTP_201_CREATED, tags=["Suppliers"]
)
def create_supplier_product(data: SupplierProductCreate, session: SessionDep):
    return service(session).supplier_product_create(data)


@router.get("/supplier-products", response_model=list[SupplierProductRead], tags=["Suppliers"])
def list_supplier_products(
    session: SessionDep,
    supplier_id: int | None = Query(default=None, gt=0),
    product_id: int | None = Query(default=None, gt=0),
    limit: PageSize = 50,
    offset: PageOffset = 0,
):
    return service(session).supplier_products(supplier_id, product_id, limit, offset)


@router.patch("/supplier-products/{mapping_id}", response_model=SupplierProductRead, tags=["Suppliers"])
def update_supplier_product(mapping_id: int, data: SupplierProductUpdate, session: SessionDep):
    return service(session).supplier_product_update(mapping_id, data)


@router.get("/inventory", response_model=list[InventoryRead], tags=["Inventory"])
def list_inventory(session: SessionDep, limit: PageSize = 50, offset: PageOffset = 0):
    return service(session).inventory_views(None, limit, offset)


@router.get("/inventory/{product_id}", response_model=InventoryRead, tags=["Inventory"])
def get_inventory(product_id: int, session: SessionDep):
    records = service(session).inventory_views(product_id, 1, 0)
    if not records:
        raise NotFoundError("inventory not found")
    return records[0]


@router.post(
    "/inventory/{product_id}/adjustments",
    response_model=StockTransactionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Inventory"],
)
def create_adjustment(product_id: int, data: AdjustmentCreate, session: SessionDep):
    return service(session).adjustment(product_id, data)


@router.get("/stock-transactions", response_model=list[StockTransactionRead], tags=["Stock Transactions"])
def list_stock_transactions(
    session: SessionDep,
    product_id: int | None = Query(default=None, gt=0),
    transaction_type: StockTransactionType | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: PageSize = 50,
    offset: PageOffset = 0,
):
    return service(session).stock_transactions(product_id, transaction_type, start_at, end_at, limit, offset)


@router.post(
    "/purchase-orders", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED, tags=["Purchase Orders"]
)
def create_purchase_order(data: PurchaseOrderCreate, session: SessionDep):
    return service(session).purchase_order_create(data)


@router.get("/purchase-orders", response_model=list[PurchaseOrderRead], tags=["Purchase Orders"])
def list_purchase_orders(
    session: SessionDep,
    status_filter: PurchaseOrderStatus | None = Query(default=None, alias="status"),
    limit: PageSize = 50,
    offset: PageOffset = 0,
):
    return service(session).purchase_orders(status_filter, limit, offset)


@router.get("/purchase-orders/{purchase_order_id}", response_model=PurchaseOrderRead, tags=["Purchase Orders"])
def get_purchase_order(purchase_order_id: int, session: SessionDep):
    return service(session).purchase_order(purchase_order_id)


@router.post("/purchase-orders/{purchase_order_id}/items", response_model=PurchaseOrderRead, tags=["Purchase Orders"])
def add_purchase_order_item(purchase_order_id: int, data: PurchaseOrderItemCreate, session: SessionDep):
    return service(session).purchase_order_item_add(purchase_order_id, data)


@router.patch("/purchase-orders/{purchase_order_id}/items/{item_id}", response_model=PurchaseOrderRead, tags=["Purchase Orders"])
def update_purchase_order_item(purchase_order_id: int, item_id: int, data: PurchaseOrderItemUpdate, session: SessionDep):
    return service(session).purchase_order_item_update(purchase_order_id, item_id, data)


@router.delete("/purchase-orders/{purchase_order_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Purchase Orders"])
def delete_purchase_order_item(purchase_order_id: int, item_id: int, session: SessionDep) -> Response:
    service(session).purchase_order_item_delete(purchase_order_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/purchase-orders/{purchase_order_id}/transition", response_model=PurchaseOrderRead, tags=["Purchase Orders"])
def transition_purchase_order(purchase_order_id: int, data: PurchaseOrderTransition, session: SessionDep):
    return service(session).purchase_order_transition(purchase_order_id, data)


@router.post("/purchase-orders/{purchase_order_id}/receive", response_model=PurchaseOrderRead, tags=["Purchase Orders"])
def receive_purchase_order(purchase_order_id: int, data: ReceiptCreate, session: SessionDep):
    return service(session).receive_purchase_order(purchase_order_id, data)
