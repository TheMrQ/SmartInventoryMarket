"""Persistence queries for the P16 decision-support service."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import (
    ForecastRun,
    ForecastValue,
    Inventory,
    Product,
    RecommendationStatus,
    ReorderRecommendation,
    SalesDaily,
    Supplier,
    SupplierProduct,
)


class InventoryDecisionRepository:
    @staticmethod
    def product(session: Session, product_id: int) -> Product | None:
        return session.get(Product, product_id)

    @staticmethod
    def products(session: Session, search: str | None, limit: int, offset: int) -> list[Product]:
        statement = select(Product).where(Product.is_active.is_(True)).order_by(Product.sku)
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(Product.sku.ilike(pattern) | Product.name.ilike(pattern))
        return list(session.scalars(statement.limit(limit).offset(offset)))

    @staticmethod
    def inventory(session: Session, product_id: int) -> Inventory | None:
        return session.get(Inventory, product_id)

    @staticmethod
    def incoming_quantity(session: Session, product_id: int) -> int:
        from backend.app.repositories.business import BusinessRepository

        incoming = BusinessRepository.incoming_quantity_subquery()
        return int(session.scalar(select(func.coalesce(incoming.c.incoming_quantity, 0)).where(incoming.c.product_id == product_id)) or 0)

    @staticmethod
    def supplier_mappings(session: Session, product_id: int) -> list[SupplierProduct]:
        statement = select(SupplierProduct).join(Supplier).where(SupplierProduct.product_id == product_id, Supplier.is_active.is_(True)).options(selectinload(SupplierProduct.supplier))
        return list(session.scalars(statement))

    @staticmethod
    def latest_forecast(session: Session, product_id: int) -> ForecastRun | None:
        statement = select(ForecastRun).join(ForecastValue).where(ForecastValue.product_id == product_id).order_by(ForecastRun.generated_at.desc(), ForecastRun.id.desc()).options(selectinload(ForecastRun.values))
        return session.scalar(statement)

    @staticmethod
    def sales_history(session: Session, product_id: int, start: date, end: date) -> list[SalesDaily]:
        return list(session.scalars(select(SalesDaily).where(SalesDaily.product_id == product_id, SalesDaily.sale_date >= start, SalesDaily.sale_date <= end).order_by(SalesDaily.sale_date)))

    @staticmethod
    def recommendation(session: Session, recommendation_id: int, lock: bool = False) -> ReorderRecommendation | None:
        statement = select(ReorderRecommendation).where(ReorderRecommendation.id == recommendation_id)
        if lock:
            statement = statement.with_for_update()
        return session.scalar(statement)

    @staticmethod
    def recommendations(session: Session, product_id: int | None, status: RecommendationStatus | None, limit: int, offset: int) -> list[ReorderRecommendation]:
        statement = select(ReorderRecommendation).order_by(ReorderRecommendation.created_at.desc(), ReorderRecommendation.id.desc())
        if product_id is not None:
            statement = statement.where(ReorderRecommendation.product_id == product_id)
        if status is not None:
            statement = statement.where(ReorderRecommendation.status == status)
        return list(session.scalars(statement.limit(limit).offset(offset)))

    @staticmethod
    def active_new_recommendations(session: Session, product_id: int) -> list[ReorderRecommendation]:
        return list(session.scalars(select(ReorderRecommendation).where(ReorderRecommendation.product_id == product_id, ReorderRecommendation.status == RecommendationStatus.NEW).with_for_update()))
