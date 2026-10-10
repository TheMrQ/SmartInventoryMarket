from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.api.business import router as business_router
from backend.app.api.auth import router as auth_router
from backend.app.api.health import router as health_router
from backend.app.api.inventory_decisions import router as inventory_decision_router
from backend.app.api.sales_forecasts import router as sales_forecasts_router
from backend.app.services.errors import DomainError

app = FastAPI(
    title="Smart Inventory Market",
    version="0.1.0",
    description="Single-store inventory decision-support thesis application.",
)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    """Return expected business failures without leaking SQL/database detail."""
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/")
def project_status() -> dict[str, str]:
    """Return the minimal project-status response for the operational API core."""
    return {"project": "Smart Inventory Market", "status": "inventory-operations"}


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(business_router)
app.include_router(sales_forecasts_router)
app.include_router(inventory_decision_router)
