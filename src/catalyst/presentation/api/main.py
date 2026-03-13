import os
from typing import Any
from fastapi import FastAPI, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from catalyst.domain.engine import WorkflowEngine

app = FastAPI(
    title="Catalyst Workflow API",
    description="High-performance DAG execution engine interface",
    version="0.1.0",
)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
CATALYST_API_KEY = os.getenv("CATALYST_API_KEY", "catalyst-dev-token-2024")


async def get_api_key(
    api_key_header: str | None = Security(api_key_header),
) -> str:
    """Validate the API key from the header."""
    if api_key_header == CATALYST_API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing API Key",
    )


class StatusResponse(BaseModel):
    status: str
    message: str


@app.get("/", response_model=StatusResponse)
async def health_check() -> StatusResponse:
    """Check API health and status."""
    return StatusResponse(status="ok", message="Catalyst is primed and ready.")


# A mock endpoint for running an engine demonstration
@app.post("/execute", dependencies=[Depends(get_api_key)])
async def execute_workflow() -> dict[str, Any]:
    """Execute a demonstration workflow DAG."""
    engine = WorkflowEngine()
    engine.add_task("ingest", lambda: "Data Ingested")
    engine.add_task("transform", lambda: "Data Transformed", ["ingest"])
    engine.add_task("load", lambda: "Data Loaded", ["transform"])

    results = await engine.execute()
    return {"status": "success", "results": results}
