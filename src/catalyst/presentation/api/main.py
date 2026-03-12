from fastapi import FastAPI
from pydantic import BaseModel
from catalyst.domain.engine import WorkflowEngine
from typing import Any

app = FastAPI(
    title="Catalyst Workflow API",
    description="High-performance DAG execution engine interface",
    version="0.1.0",
)


class StatusResponse(BaseModel):
    status: str
    message: str


@app.get("/", response_model=StatusResponse)
async def health_check() -> StatusResponse:
    """Check API health and status."""
    return StatusResponse(status="ok", message="Catalyst is primed and ready.")


# A mock endpoint for running an engine demonstration
@app.post("/execute")
async def execute_workflow() -> dict[str, Any]:
    """Execute a demonstration workflow DAG."""
    engine = WorkflowEngine()
    engine.add_task("ingest", lambda: "Data Ingested")
    engine.add_task("transform", lambda: "Data Transformed", ["ingest"])
    engine.add_task("load", lambda: "Data Loaded", ["transform"])

    results = await engine.execute()
    return {"status": "success", "results": results}
