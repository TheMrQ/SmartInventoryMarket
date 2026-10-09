"""Persistence queries for P15 sales and forecast workflows."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import ForecastRun, Product, SalesDaily


class SalesForecastRepository:
    @staticmethod
    def product_by_sku(session: Session, sku: str) -> Product | None:
        return session.scalar(select(Product).where(Product.sku == sku))

    @staticmethod
    def sales_daily(session: Session, product_id: int, sale_date: date, lock: bool = False) -> SalesDaily | None:
        statement = select(SalesDaily).where(SalesDaily.product_id == product_id, SalesDaily.sale_date == sale_date)
        if lock:
            statement = statement.with_for_update()
        return session.scalar(statement)

    @staticmethod
    def sales_history(session: Session, product_id: int | None, start_date: date | None, end_date: date | None, limit: int, offset: int) -> list[SalesDaily]:
        statement = select(SalesDaily).order_by(SalesDaily.sale_date.desc(), SalesDaily.id.desc())
        if product_id is not None:
            statement = statement.where(SalesDaily.product_id == product_id)
        if start_date is not None:
            statement = statement.where(SalesDaily.sale_date >= start_date)
        if end_date is not None:
            statement = statement.where(SalesDaily.sale_date <= end_date)
        return list(session.scalars(statement.limit(limit).offset(offset)))

    @staticmethod
    def product_history_between(session: Session, product_id: int, start_date: date, end_date: date) -> list[SalesDaily]:
        return list(session.scalars(select(SalesDaily).where(SalesDaily.product_id == product_id, SalesDaily.sale_date >= start_date, SalesDaily.sale_date <= end_date).order_by(SalesDaily.sale_date)))

    @staticmethod
    def forecast_run(session: Session, run_id: int) -> ForecastRun | None:
        return session.scalar(select(ForecastRun).options(selectinload(ForecastRun.values)).where(ForecastRun.id == run_id))

    @staticmethod
    def forecast_runs(session: Session, limit: int, offset: int) -> list[ForecastRun]:
        ids = list(session.scalars(select(ForecastRun.id).order_by(ForecastRun.generated_at.desc(), ForecastRun.id.desc()).limit(limit).offset(offset)))
        return [run for run_id in ids if (run := SalesForecastRepository.forecast_run(session, run_id)) is not None]

    @staticmethod
    def latest_run_for_product(session: Session, product_id: int) -> ForecastRun | None:
        statement = select(ForecastRun).join(ForecastRun.values).where(ForecastRun.values.any(product_id=product_id)).order_by(ForecastRun.generated_at.desc(), ForecastRun.id.desc()).options(selectinload(ForecastRun.values))
        return session.scalar(statement)
