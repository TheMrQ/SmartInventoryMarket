"""Thin HTTP adapters for P15 sales ingestion and frozen forecasts."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.api.auth import operational_user
from backend.app.schemas.business import (
    ForecastCreate,
    ForecastRunRead,
    OperationalSaleCreate,
    SalesDailyRead,
    SalesImportResult,
)
from backend.app.services.forecasting import ForecastService
from backend.app.services.sales import SalesService


router = APIRouter(prefix="/api", dependencies=[Depends(operational_user)])
SessionDep = Annotated[Session, Depends(get_db_session)]
PageSize = Annotated[int, Query(ge=1, le=100)]
PageOffset = Annotated[int, Query(ge=0)]


@router.get("/sales", response_model=list[SalesDailyRead], tags=["Sales"])
def list_sales(session: SessionDep, product_id: int | None = Query(default=None, gt=0), start_date: date | None = None, end_date: date | None = None, limit: PageSize = 50, offset: PageOffset = 0):
    return SalesService(session).history(product_id, start_date, end_date, limit, offset)


@router.post("/sales/import", response_model=SalesImportResult, tags=["Sales"])
async def import_sales(session: SessionDep, file: UploadFile = File(...)):
    if file.content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel", None}:
        from backend.app.services.errors import ConflictError
        raise ConflictError("sales import must be a CSV file")
    try:
        content = (await file.read()).decode("utf-8-sig")
    except UnicodeDecodeError:
        from backend.app.services.errors import ConflictError
        raise ConflictError("CSV must be UTF-8 text")
    return SalesService(session).import_csv(content)


@router.post("/sales/record", response_model=SalesDailyRead, status_code=status.HTTP_201_CREATED, tags=["Sales"])
def record_sale(data: OperationalSaleCreate, session: SessionDep):
    return SalesService(session).record_sale(data)


@router.get("/sales/{product_id}", response_model=list[SalesDailyRead], tags=["Sales"])
def product_sales(product_id: int, session: SessionDep, start_date: date | None = None, end_date: date | None = None, limit: PageSize = 50, offset: PageOffset = 0):
    return SalesService(session).history(product_id, start_date, end_date, limit, offset)


@router.post("/forecasts", response_model=ForecastRunRead, status_code=status.HTTP_201_CREATED, tags=["Forecasts"])
def create_forecast(data: ForecastCreate, session: SessionDep):
    return ForecastService(session).create(data)


@router.get("/forecast-runs", response_model=list[ForecastRunRead], tags=["Forecasts"])
def list_forecast_runs(session: SessionDep, limit: PageSize = 50, offset: PageOffset = 0):
    return ForecastService(session).runs(limit, offset)


@router.get("/forecast-runs/{run_id}", response_model=ForecastRunRead, tags=["Forecasts"])
def get_forecast_run(run_id: int, session: SessionDep):
    return ForecastService(session).run(run_id)


@router.get("/forecasts/latest", response_model=ForecastRunRead, tags=["Forecasts"])
def latest_forecast(session: SessionDep, product_id: int = Query(gt=0)):
    return ForecastService(session).latest(product_id)
