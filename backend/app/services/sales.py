"""P15 historical ingestion and operational-sale business rules."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models import SalesDaily, StockTransaction, StockTransactionType, utc_now
from backend.app.repositories.business import BusinessRepository
from backend.app.repositories.sales_forecasts import SalesForecastRepository
from backend.app.schemas.business import OperationalSaleCreate
from backend.app.services.errors import ConflictError, NotFoundError


REQUIRED_IMPORT_COLUMNS = {"sku", "sale_date", "quantity_sold"}


class SalesService:
    """Keeps historical backfills separate from inventory-changing operational sales."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = SalesForecastRepository()
        self.business_repo = BusinessRepository()

    def history(self, product_id: int | None, start_date: date | None, end_date: date | None, limit: int, offset: int) -> list[SalesDaily]:
        if start_date and end_date and start_date > end_date:
            raise ConflictError("start_date must not be later than end_date")
        if product_id is not None and self.business_repo.product(self.session, product_id) is None:
            raise NotFoundError("product not found")
        return self.repo.sales_history(self.session, product_id, start_date, end_date, limit, offset)

    @staticmethod
    def _parse_csv(content: str) -> list[dict]:
        try:
            reader = csv.DictReader(StringIO(content))
            if reader.fieldnames is None:
                raise ConflictError("CSV must include a header row")
            headers = {header.strip() for header in reader.fieldnames if header}
            missing = REQUIRED_IMPORT_COLUMNS.difference(headers)
            if missing:
                raise ConflictError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
            rows = []
            seen: set[tuple[str, date]] = set()
            for number, raw in enumerate(reader, start=2):
                sku = (raw.get("sku") or "").strip()
                if not sku:
                    raise ConflictError(f"row {number}: sku is required")
                try:
                    sale_date = date.fromisoformat((raw.get("sale_date") or "").strip())
                except ValueError as exc:
                    raise ConflictError(f"row {number}: sale_date must use YYYY-MM-DD") from exc
                try:
                    quantity = int((raw.get("quantity_sold") or "").strip())
                except ValueError as exc:
                    raise ConflictError(f"row {number}: quantity_sold must be an integer") from exc
                if quantity < 0:
                    raise ConflictError(f"row {number}: quantity_sold must be nonnegative")
                price_text = (raw.get("sell_price") or "").strip()
                try:
                    sell_price = None if not price_text else Decimal(price_text)
                except InvalidOperation as exc:
                    raise ConflictError(f"row {number}: sell_price must be a decimal or blank") from exc
                if sell_price is not None and sell_price < 0:
                    raise ConflictError(f"row {number}: sell_price must be nonnegative")
                key = (sku, sale_date)
                if key in seen:
                    raise ConflictError(f"row {number}: duplicate sku/sale_date within CSV")
                seen.add(key)
                rows.append({"sku": sku, "sale_date": sale_date, "quantity_sold": quantity, "sell_price": sell_price, "source": (raw.get("source") or "").strip() or None})
            return rows
        except UnicodeDecodeError as exc:
            raise ConflictError("CSV must be UTF-8 text") from exc

    def import_csv(self, content: str) -> dict[str, int]:
        rows = self._parse_csv(content)
        resolved: list[tuple[dict, int]] = []
        for row in rows:
            product = self.repo.product_by_sku(self.session, row["sku"])
            if product is None:
                raise NotFoundError(f"unknown SKU in CSV: {row['sku']}")
            resolved.append((row, product.id))
        inserted = updated = 0
        try:
            for row, product_id in resolved:
                existing = self.repo.sales_daily(self.session, product_id, row["sale_date"], lock=True)
                if existing is None:
                    self.session.add(SalesDaily(product_id=product_id, sale_date=row["sale_date"], quantity_sold=row["quantity_sold"], sell_price=row["sell_price"], source=row["source"]))
                    inserted += 1
                else:
                    existing.quantity_sold = row["quantity_sold"]
                    existing.sell_price = row["sell_price"]
                    existing.source = row["source"]
                    updated += 1
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("sales import conflicts with an existing record or constraint") from exc
        return {"rows_received": len(rows), "rows_inserted": inserted, "rows_updated": updated, "rows_rejected": 0}

    def record_sale(self, data: OperationalSaleCreate) -> SalesDaily:
        product = self.business_repo.product(self.session, data.product_id)
        if product is None:
            raise NotFoundError("product not found")
        if not product.is_active:
            raise ConflictError("inactive products cannot be sold")
        if data.created_by_user_id is not None and not self.business_repo.user_exists(self.session, data.created_by_user_id):
            raise NotFoundError("user not found")
        inventory = self.business_repo.lock_inventory(self.session, data.product_id)
        if inventory is None:
            raise ConflictError("product has no inventory row")
        if data.quantity > inventory.on_hand:
            raise ConflictError("sale quantity exceeds on-hand inventory")
        daily = self.repo.sales_daily(self.session, data.product_id, data.sale_date, lock=True)
        if daily is None:
            daily = SalesDaily(product_id=data.product_id, sale_date=data.sale_date, quantity_sold=data.quantity, sell_price=data.sell_price, source=data.source)
            self.session.add(daily)
            self.session.flush()
        else:
            daily.quantity_sold += data.quantity
            # A supplied price is the latest observed price for that daily aggregate;
            # an omitted price preserves the existing observed value.
            if data.sell_price is not None:
                daily.sell_price = data.sell_price
            if data.source:
                daily.source = data.source
        inventory.on_hand -= data.quantity
        self.session.add(StockTransaction(product_id=data.product_id, transaction_type=StockTransactionType.SALE, quantity=data.quantity, sales_daily_id=daily.id, created_by_user_id=data.created_by_user_id, reason="operational sale", occurred_at=utc_now()))
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("sale conflicts with an existing record or constraint") from exc
        self.session.refresh(daily)
        return daily
