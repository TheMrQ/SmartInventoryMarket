"""Persistence queries isolated from P14 business rules."""

from datetime import date, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import (
    Category,
    Inventory,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Supplier,
    SupplierProduct,
    User,
)


class BusinessRepository:
    """Small focused repository helpers; services own all workflow decisions."""

    @staticmethod
    def category(session: Session, category_id: int) -> Category | None:
        return session.get(Category, category_id)

    @staticmethod
    def product(session: Session, product_id: int) -> Product | None:
        return session.get(Product, product_id)

    @staticmethod
    def supplier(session: Session, supplier_id: int) -> Supplier | None:
        return session.get(Supplier, supplier_id)

    @staticmethod
    def user_exists(session: Session, user_id: int | None) -> bool:
        return user_id is None or session.get(User, user_id) is not None

    @staticmethod
    def supplier_product(session: Session, supplier_id: int, product_id: int) -> SupplierProduct | None:
        return session.scalar(
            select(SupplierProduct).where(
                SupplierProduct.supplier_id == supplier_id,
                SupplierProduct.product_id == product_id,
            )
        )

    @staticmethod
    def lock_inventory(session: Session, product_id: int) -> Inventory | None:
        return session.scalar(select(Inventory).where(Inventory.product_id == product_id).with_for_update())

    @staticmethod
    def purchase_order(session: Session, purchase_order_id: int) -> PurchaseOrder | None:
        return session.scalar(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == purchase_order_id)
        )

    @staticmethod
    def lock_purchase_order(session: Session, purchase_order_id: int) -> PurchaseOrder | None:
        return session.scalar(select(PurchaseOrder).where(PurchaseOrder.id == purchase_order_id).with_for_update())

    @staticmethod
    def purchase_order_items(session: Session, purchase_order_id: int, lock: bool = False) -> list[PurchaseOrderItem]:
        statement: Select[tuple[PurchaseOrderItem]] = select(PurchaseOrderItem).where(
            PurchaseOrderItem.purchase_order_id == purchase_order_id
        )
        if lock:
            statement = statement.with_for_update()
        return list(session.scalars(statement))

    @staticmethod
    def list_statement(model: type, limit: int, offset: int):
        return select(model).limit(limit).offset(offset)

    @staticmethod
    def incoming_quantity_subquery():
        from backend.app.db.models import PurchaseOrderStatus

        return (
            select(
                PurchaseOrderItem.product_id.label("product_id"),
                func.coalesce(func.sum(PurchaseOrderItem.ordered_quantity - PurchaseOrderItem.received_quantity), 0).label(
                    "incoming_quantity"
                ),
            )
            .join(PurchaseOrder)
            .where(PurchaseOrder.status.in_([PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.IN_TRANSIT]))
            .group_by(PurchaseOrderItem.product_id)
            .subquery()
        )
