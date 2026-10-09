"""P14 transactional business rules for the single-store MVP."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models import (
    Category,
    Inventory,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    StockTransaction,
    StockTransactionType,
    Supplier,
    SupplierProduct,
    utc_now,
)
from backend.app.repositories.business import BusinessRepository
from backend.app.schemas.business import (
    AdjustmentCreate,
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductUpdate,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderItemUpdate,
    PurchaseOrderTransition,
    ReceiptCreate,
    SupplierCreate,
    SupplierProductCreate,
    SupplierProductUpdate,
    SupplierUpdate,
)
from backend.app.services.errors import ConflictError, NotFoundError


INCOMING_STATUSES = {PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.IN_TRANSIT}
TRANSITIONS = {
    PurchaseOrderStatus.DRAFT: {PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.APPROVED: {PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.ORDERED: {PurchaseOrderStatus.IN_TRANSIT, PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.IN_TRANSIT: {PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.RECEIVED: set(),
    PurchaseOrderStatus.CANCELLED: set(),
}


class BusinessService:
    """Coordinates validation and atomic writes; routes do not contain business rules."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = BusinessRepository()

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("operation conflicts with an existing record or constraint") from exc

    def _flush(self) -> None:
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("operation conflicts with an existing record or constraint") from exc

    @staticmethod
    def _not_found(resource: str) -> NotFoundError:
        return NotFoundError(f"{resource} not found")

    def _require_user(self, user_id: int | None) -> None:
        if not self.repo.user_exists(self.session, user_id):
            raise self._not_found("user")

    def _category(self, category_id: int) -> Category:
        category = self.repo.category(self.session, category_id)
        if category is None:
            raise self._not_found("category")
        return category

    def _product(self, product_id: int) -> Product:
        product = self.repo.product(self.session, product_id)
        if product is None:
            raise self._not_found("product")
        return product

    def _supplier(self, supplier_id: int) -> Supplier:
        supplier = self.repo.supplier(self.session, supplier_id)
        if supplier is None:
            raise self._not_found("supplier")
        return supplier

    def category_create(self, data: CategoryCreate) -> Category:
        item = Category(**data.model_dump())
        self.session.add(item)
        self._commit()
        self.session.refresh(item)
        return item

    def category(self, category_id: int) -> Category:
        return self._category(category_id)

    def categories(self, limit: int, offset: int) -> list[Category]:
        return list(self.session.scalars(select(Category).order_by(Category.code).limit(limit).offset(offset)))

    def category_update(self, category_id: int, data: CategoryUpdate) -> Category:
        item = self._category(category_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self._commit()
        self.session.refresh(item)
        return item

    def product_create(self, data: ProductCreate) -> Product:
        self._category(data.category_id)
        product = Product(**data.model_dump())
        self.session.add(product)
        self._flush()
        self.session.add(Inventory(product_id=product.id, on_hand=0))
        self._commit()
        self.session.refresh(product)
        return product

    def product(self, product_id: int) -> Product:
        return self._product(product_id)

    def products(
        self, search: str | None, category_id: int | None, is_active: bool | None, limit: int, offset: int
    ) -> list[Product]:
        statement = select(Product).order_by(Product.sku)
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(or_(Product.sku.ilike(pattern), Product.name.ilike(pattern)))
        if category_id is not None:
            statement = statement.where(Product.category_id == category_id)
        if is_active is not None:
            statement = statement.where(Product.is_active == is_active)
        return list(self.session.scalars(statement.limit(limit).offset(offset)))

    def product_update(self, product_id: int, data: ProductUpdate) -> Product:
        product = self._product(product_id)
        fields = data.model_dump(exclude_unset=True)
        if "category_id" in fields:
            self._category(fields["category_id"])
        for field, value in fields.items():
            setattr(product, field, value)
        self._commit()
        self.session.refresh(product)
        return product

    def supplier_create(self, data: SupplierCreate) -> Supplier:
        item = Supplier(**data.model_dump())
        self.session.add(item)
        self._commit()
        self.session.refresh(item)
        return item

    def supplier(self, supplier_id: int) -> Supplier:
        return self._supplier(supplier_id)

    def suppliers(self, is_active: bool | None, limit: int, offset: int) -> list[Supplier]:
        statement = select(Supplier).order_by(Supplier.code)
        if is_active is not None:
            statement = statement.where(Supplier.is_active == is_active)
        return list(self.session.scalars(statement.limit(limit).offset(offset)))

    def supplier_update(self, supplier_id: int, data: SupplierUpdate) -> Supplier:
        item = self._supplier(supplier_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self._commit()
        self.session.refresh(item)
        return item

    def supplier_product_create(self, data: SupplierProductCreate) -> SupplierProduct:
        supplier = self._supplier(data.supplier_id)
        product = self._product(data.product_id)
        if not supplier.is_active or not product.is_active:
            raise ConflictError("inactive suppliers or products cannot receive new mappings")
        if self.repo.supplier_product(self.session, data.supplier_id, data.product_id) is not None:
            raise ConflictError("supplier-product relationship already exists")
        if data.is_preferred:
            self._clear_preferred_supplier(data.product_id)
        item = SupplierProduct(**data.model_dump())
        self.session.add(item)
        self._commit()
        self.session.refresh(item)
        return item

    def _clear_preferred_supplier(self, product_id: int, exclude_id: int | None = None) -> None:
        statement = select(SupplierProduct).where(
            SupplierProduct.product_id == product_id, SupplierProduct.is_preferred.is_(True)
        )
        for mapping in self.session.scalars(statement):
            if mapping.id != exclude_id:
                mapping.is_preferred = False

    def supplier_product_update(self, mapping_id: int, data: SupplierProductUpdate) -> SupplierProduct:
        item = self.session.get(SupplierProduct, mapping_id)
        if item is None:
            raise self._not_found("supplier-product relationship")
        fields = data.model_dump(exclude_unset=True)
        if fields.get("is_preferred") is True:
            self._clear_preferred_supplier(item.product_id, exclude_id=item.id)
        for field, value in fields.items():
            setattr(item, field, value)
        self._commit()
        self.session.refresh(item)
        return item

    def supplier_products(
        self, supplier_id: int | None, product_id: int | None, limit: int, offset: int
    ) -> list[SupplierProduct]:
        statement = select(SupplierProduct).order_by(SupplierProduct.id)
        if supplier_id is not None:
            statement = statement.where(SupplierProduct.supplier_id == supplier_id)
        if product_id is not None:
            statement = statement.where(SupplierProduct.product_id == product_id)
        return list(self.session.scalars(statement.limit(limit).offset(offset)))

    def inventory_views(self, product_id: int | None, limit: int, offset: int) -> list[dict]:
        incoming = self.repo.incoming_quantity_subquery()
        statement = (
            select(
                Inventory.product_id,
                Product.sku,
                Product.name.label("product_name"),
                Inventory.on_hand,
                func.coalesce(incoming.c.incoming_quantity, 0).label("incoming_quantity"),
                Inventory.updated_at,
            )
            .select_from(Inventory)
            .join(Product, Product.id == Inventory.product_id)
            .outerjoin(incoming, incoming.c.product_id == Inventory.product_id)
            .order_by(Product.sku)
        )
        if product_id is not None:
            statement = statement.where(Inventory.product_id == product_id)
        rows = self.session.execute(statement.limit(limit).offset(offset)).mappings()
        return [
            {
                **dict(row),
                "inventory_position": row["on_hand"] + row["incoming_quantity"],
            }
            for row in rows
        ]

    def stock_transactions(
        self,
        product_id: int | None,
        transaction_type: StockTransactionType | None,
        start_at,
        end_at,
        limit: int,
        offset: int,
    ) -> list[StockTransaction]:
        statement = select(StockTransaction).order_by(StockTransaction.occurred_at.desc(), StockTransaction.id.desc())
        if product_id is not None:
            statement = statement.where(StockTransaction.product_id == product_id)
        if transaction_type is not None:
            statement = statement.where(StockTransaction.transaction_type == transaction_type)
        if start_at is not None:
            statement = statement.where(StockTransaction.occurred_at >= start_at)
        if end_at is not None:
            statement = statement.where(StockTransaction.occurred_at <= end_at)
        return list(self.session.scalars(statement.limit(limit).offset(offset)))

    def adjustment(self, product_id: int, data: AdjustmentCreate) -> StockTransaction:
        self._product(product_id)
        self._require_user(data.created_by_user_id)
        inventory = self.repo.lock_inventory(self.session, product_id)
        if inventory is None:
            raise ConflictError("product has no inventory row")
        if data.transaction_type == StockTransactionType.ADJUSTMENT_OUT and data.quantity > inventory.on_hand:
            raise ConflictError("adjustment would make on-hand inventory negative")
        if data.transaction_type == StockTransactionType.ADJUSTMENT_IN:
            inventory.on_hand += data.quantity
        else:
            inventory.on_hand -= data.quantity
        transaction = StockTransaction(
            product_id=product_id,
            transaction_type=data.transaction_type,
            quantity=data.quantity,
            created_by_user_id=data.created_by_user_id,
            reason=data.reason.strip(),
            occurred_at=utc_now(),
        )
        self.session.add(transaction)
        self._commit()
        self.session.refresh(transaction)
        return transaction

    def purchase_order_create(self, data: PurchaseOrderCreate) -> PurchaseOrder:
        supplier = self._supplier(data.supplier_id)
        if not supplier.is_active:
            raise ConflictError("inactive suppliers cannot receive new purchase orders")
        self._require_user(data.created_by_user_id)
        product_ids = [line.product_id for line in data.items]
        if len(product_ids) != len(set(product_ids)):
            raise ConflictError("a purchase order cannot contain duplicate product lines")
        lines: list[PurchaseOrderItem] = []
        for line in data.items:
            product = self._product(line.product_id)
            if not product.is_active:
                raise ConflictError("inactive products cannot be ordered")
            mapping = self.repo.supplier_product(self.session, data.supplier_id, line.product_id)
            if mapping is None:
                raise ConflictError("supplier does not supply one of the requested products")
            unit_cost = line.unit_cost if line.unit_cost is not None else mapping.unit_cost
            lines.append(
                PurchaseOrderItem(
                    product_id=line.product_id,
                    ordered_quantity=line.ordered_quantity,
                    unit_cost=unit_cost,
                )
            )
        order = PurchaseOrder(
            po_number=data.po_number,
            supplier_id=data.supplier_id,
            expected_arrival_date=data.expected_arrival_date,
            created_by_user_id=data.created_by_user_id,
            notes=data.notes,
            status=PurchaseOrderStatus.DRAFT,
            items=lines,
        )
        self.session.add(order)
        self._commit()
        return self.purchase_order(order.id)

    def purchase_order(self, purchase_order_id: int) -> PurchaseOrder:
        order = self.repo.purchase_order(self.session, purchase_order_id)
        if order is None:
            raise self._not_found("purchase order")
        return order

    def purchase_orders(
        self, status: PurchaseOrderStatus | None, limit: int, offset: int
    ) -> list[PurchaseOrder]:
        statement = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
        if status is not None:
            statement = statement.where(PurchaseOrder.status == status)
        ids = list(self.session.scalars(statement.with_only_columns(PurchaseOrder.id).limit(limit).offset(offset)))
        return [self.purchase_order(order_id) for order_id in ids]

    def _draft_order(self, purchase_order_id: int) -> PurchaseOrder:
        order = self.purchase_order(purchase_order_id)
        if order.status != PurchaseOrderStatus.DRAFT:
            raise ConflictError("purchase-order lines can only be edited while the order is DRAFT")
        return order

    def purchase_order_item_add(self, purchase_order_id: int, data: PurchaseOrderItemCreate) -> PurchaseOrder:
        order = self._draft_order(purchase_order_id)
        product = self._product(data.product_id)
        if not product.is_active:
            raise ConflictError("inactive products cannot be ordered")
        if any(item.product_id == data.product_id for item in order.items):
            raise ConflictError("a purchase order cannot contain duplicate product lines")
        mapping = self.repo.supplier_product(self.session, order.supplier_id, data.product_id)
        if mapping is None:
            raise ConflictError("supplier does not supply the requested product")
        order.items.append(
            PurchaseOrderItem(
                product_id=data.product_id,
                ordered_quantity=data.ordered_quantity,
                unit_cost=data.unit_cost if data.unit_cost is not None else mapping.unit_cost,
            )
        )
        self._commit()
        return self.purchase_order(purchase_order_id)

    def purchase_order_item_update(self, purchase_order_id: int, item_id: int, data: PurchaseOrderItemUpdate) -> PurchaseOrder:
        order = self._draft_order(purchase_order_id)
        item = next((item for item in order.items if item.id == item_id), None)
        if item is None:
            raise self._not_found("purchase-order item")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self._commit()
        return self.purchase_order(purchase_order_id)

    def purchase_order_item_delete(self, purchase_order_id: int, item_id: int) -> None:
        order = self._draft_order(purchase_order_id)
        item = next((item for item in order.items if item.id == item_id), None)
        if item is None:
            raise self._not_found("purchase-order item")
        self.session.delete(item)
        self._commit()

    def purchase_order_transition(self, purchase_order_id: int, data: PurchaseOrderTransition) -> PurchaseOrder:
        order = self.purchase_order(purchase_order_id)
        target = data.target_status
        if target == PurchaseOrderStatus.RECEIVED:
            raise ConflictError("purchase orders become RECEIVED only through goods receipt")
        if target not in TRANSITIONS[order.status]:
            raise ConflictError(f"cannot transition from {order.status.value} to {target.value}")
        if target == PurchaseOrderStatus.APPROVED:
            if not order.items:
                raise ConflictError("an empty purchase order cannot be approved")
            self._require_user(data.approved_by_user_id)
            order.approved_by_user_id = data.approved_by_user_id
        if target == PurchaseOrderStatus.ORDERED and order.order_date is None:
            order.order_date = utc_now().date()
        order.status = target
        self._commit()
        return self.purchase_order(purchase_order_id)

    def receive_purchase_order(self, purchase_order_id: int, data: ReceiptCreate) -> PurchaseOrder:
        self._require_user(data.created_by_user_id)
        if len({line.purchase_order_item_id for line in data.items}) != len(data.items):
            raise ConflictError("a receipt cannot contain duplicate purchase-order items")
        order = self.repo.lock_purchase_order(self.session, purchase_order_id)
        if order is None:
            raise self._not_found("purchase order")
        if order.status != PurchaseOrderStatus.IN_TRANSIT:
            raise ConflictError("only IN_TRANSIT purchase orders may receive goods")
        items = {item.id: item for item in self.repo.purchase_order_items(self.session, purchase_order_id, lock=True)}
        receipt_lines: list[tuple[PurchaseOrderItem, int, Inventory]] = []
        for line in data.items:
            item = items.get(line.purchase_order_item_id)
            if item is None:
                raise ConflictError("receipt item does not belong to this purchase order")
            if item.received_quantity + line.quantity > item.ordered_quantity:
                raise ConflictError("receipt quantity exceeds the remaining ordered quantity")
            inventory = self.repo.lock_inventory(self.session, item.product_id)
            if inventory is None:
                raise ConflictError("product has no inventory row")
            receipt_lines.append((item, line.quantity, inventory))
        for item, quantity, inventory in receipt_lines:
            item.received_quantity += quantity
            inventory.on_hand += quantity
            self.session.add(
                StockTransaction(
                    product_id=item.product_id,
                    transaction_type=StockTransactionType.RECEIPT,
                    quantity=quantity,
                    purchase_order_item_id=item.id,
                    created_by_user_id=data.created_by_user_id,
                    reason="Purchase-order receipt",
                    occurred_at=utc_now(),
                )
            )
        if all(item.received_quantity == item.ordered_quantity for item in items.values()):
            order.status = PurchaseOrderStatus.RECEIVED
            order.received_at = utc_now()
        self._commit()
        return self.purchase_order(purchase_order_id)
