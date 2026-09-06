from fastapi import FastAPI

app = FastAPI(
    title="Smart Inventory Market",
    version="0.1.0",
    description="Initialization smoke application for the thesis project.",
)


@app.get("/")
def project_status() -> dict[str, str]:
    """Return the minimal project-status response used during initialization."""
    return {"project": "Smart Inventory Market", "status": "initializing"}


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight service-health response."""
    return {"status": "ok"}
