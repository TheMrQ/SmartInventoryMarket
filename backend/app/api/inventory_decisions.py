"""P16 HTTP adapters for explainable inventory decisions and review."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.db.models import RecommendationStatus
from backend.app.schemas.business import (
    InventoryDecisionRead,
    RecommendationGenerate,
    RecommendationGenerateResult,
    RecommendationReview,
    ReorderRecommendationRead,
)
from backend.app.services.inventory_decisions import InventoryDecisionService


router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_db_session)]
PageSize = Annotated[int, Query(ge=1, le=100)]
PageOffset = Annotated[int, Query(ge=0)]


@router.get("/inventory-decisions", response_model=list[InventoryDecisionRead], tags=["Inventory Decisions"])
def inventory_decisions(session: SessionDep, risk_status: str | None = None, search: str | None = None, limit: PageSize = 50, offset: PageOffset = 0):
    return [decision.as_dict() for decision in InventoryDecisionService(session).decisions(risk_status, search, limit, offset)]


@router.post("/reorder-recommendations/generate", response_model=RecommendationGenerateResult, status_code=status.HTTP_201_CREATED, tags=["Reorder Recommendations"])
def generate_recommendation(data: RecommendationGenerate, session: SessionDep):
    return InventoryDecisionService(session).generate(data.product_id)


@router.get("/reorder-recommendations", response_model=list[ReorderRecommendationRead], tags=["Reorder Recommendations"])
def list_recommendations(session: SessionDep, product_id: int | None = Query(default=None, gt=0), status_filter: RecommendationStatus | None = Query(default=None, alias="status"), limit: PageSize = 50, offset: PageOffset = 0):
    return InventoryDecisionService(session).recommendations(product_id, status_filter, limit, offset)


@router.get("/reorder-recommendations/{recommendation_id}", response_model=ReorderRecommendationRead, tags=["Reorder Recommendations"])
def get_recommendation(recommendation_id: int, session: SessionDep):
    return InventoryDecisionService(session).recommendation(recommendation_id)


@router.post("/reorder-recommendations/{recommendation_id}/review", response_model=ReorderRecommendationRead, tags=["Reorder Recommendations"])
def review_recommendation(recommendation_id: int, data: RecommendationReview, session: SessionDep):
    return InventoryDecisionService(session).review(recommendation_id, data)
