from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel
from catalyst.domain.engine import TaskError, WorkflowEngine

app = FastAPI(
    title="Catalyst Workflow API",
    description="High-performance DAG execution engine interface",
    version="0.1.8",
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

    def failing_task() -> str:
        raise ValueError("Simulated failure")

    engine.add_task("fail", failing_task, ["ingest"])
    engine.add_task("skipped", lambda: "Skipped Data", ["fail"])

    results = await engine.execute()

    # Convert any TaskError objects to serializable dicts
    serializable_results = {}
    for task_name, result in results.items():
        if isinstance(result, TaskError):
            serializable_results[task_name] = {
                "error": str(result.exception),
                "task_name": result.task_name,
            }
        else:
            serializable_results[task_name] = result

    return {"status": "success", "results": serializable_results}
