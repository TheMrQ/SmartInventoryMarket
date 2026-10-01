from fastapi import FastAPI

from backend.app.api.health import router as health_router

app = FastAPI(
    title="Smart Inventory Market",
    version="0.1.0",
    description="Single-store inventory decision-support thesis application.",
)


@app.get("/")
def project_status() -> dict[str, str]:
    """Return the minimal project-status response for the application core."""
    return {"project": "Smart Inventory Market", "status": "database-core"}


app.include_router(health_router)
