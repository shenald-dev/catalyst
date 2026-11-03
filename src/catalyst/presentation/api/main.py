import asyncio
import collections
import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator, Callable
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

try:
    __version__ = version("catalyst")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "1.0.0"

from catalyst import RetryPolicy, TaskError, WorkflowEngine, WorkflowEvent

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Catalyst Workflow Engine & Real-Time Intelligence Platform",
    description="High-performance parallel DAG execution engine, declarative workflow API, and real-time dashboard",
    version=__version__,
)


class StatusResponse(BaseModel):
    status: str
    message: str


class TaskDefinition(BaseModel):
    name: str = Field(..., description="Unique task name in the DAG")
    operation: str = Field(
        "echo", description="Operation: echo, transform, sleep, fail, compute"
    )
    payload: Any = Field(None, description="Static payload, value, or configuration")
    dependencies: list[str] = Field(
        default_factory=list, description="List of dependency task names"
    )
    timeout: float | None = Field(None, description="Timeout in seconds")
    retries: int = Field(0, ge=0, le=10, description="Max retries on failure")


class WorkflowDefinition(BaseModel):
    name: str = Field("custom_dag", description="Workflow name")
    tasks: list[TaskDefinition] = Field(
        ..., min_length=1, description="List of tasks in workflow"
    )
    max_concurrency: int | None = Field(None, ge=1, description="Max parallel tasks")


class SystemHealthResponse(BaseModel):
    status: str
    version: str
    total_runs_recorded: int
    uptime_seconds: float
    active_listeners: int


# --- In-Memory Run Registry & Event Bus ---


class RunRegistry:
    def __init__(self, maxlen: int = 100) -> None:
        self.runs: collections.deque[dict[str, Any]] = collections.deque(maxlen=maxlen)
        self._runs_by_id: dict[str, dict[str, Any]] = {}
        self.start_time: float = time.time()

    def record_run(self, run_data: dict[str, Any]) -> None:
        self.runs.appendleft(run_data)
        self._runs_by_id[run_data["run_id"]] = run_data

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self._runs_by_id.get(run_id)

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return list(self.runs)[:limit]


class GlobalEventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(q)

    def publish(self, event_data: dict[str, Any]) -> None:
        dead_queues = []
        for q in self._subscribers:
            try:
                q.put_nowait(event_data)
            except asyncio.QueueFull:
                dead_queues.append(q)
        for dq in dead_queues:
            self._subscribers.discard(dq)


registry = RunRegistry()
event_bus = GlobalEventBus()


# --- Core Compatibility Endpoints ---


@app.get("/", response_model=StatusResponse)
async def health_check() -> StatusResponse:
    """Check API health and status."""
    return StatusResponse(status="ok", message="Catalyst is primed and ready.")


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

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    record = {
        "run_id": run_id,
        "name": "demo_pipeline",
        "status": results.status,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "duration_ms": round(results.total_duration_ms, 2),
        "results": serializable_results,
        "task_metrics": results.to_dict()["task_metrics"],
    }
    registry.record_run(record)

    return {"status": "success", "run_id": run_id, "results": serializable_results}


# --- Next-Gen Declarative Workflow API ---


def _build_task_callable(operation: str, payload: Any) -> Callable[..., Any]:
    async def callable_impl(*args: Any, **kwargs: Any) -> Any:
        if operation == "echo":
            return payload if payload is not None else (args or kwargs or "ok")
        elif operation == "sleep":
            duration = float(payload or 0.05)
            await asyncio.sleep(duration)
            return f"Slept {duration}s"
        elif operation == "fail":
            raise ValueError(payload or "Forced execution failure")
        elif operation == "compute":
            nums: list[float] = []
            for item in list(args) + list(kwargs.values()):
                if isinstance(item, (int, float)):
                    nums.append(float(item))
                elif isinstance(item, (list, tuple, set)):
                    nums.extend(float(x) for x in item if isinstance(x, (int, float)))
            return sum(nums) if nums else (payload or 0)
        elif operation == "transform":
            inputs = args or list(kwargs.values())
            return f"Transformed: {inputs}"
        return payload or "ok"

    return callable_impl


@app.post("/api/v1/workflows/run")
async def run_declarative_workflow(definition: WorkflowDefinition) -> dict[str, Any]:
    """Execute a dynamically specified workflow DAG and broadcast real-time events."""
    engine = WorkflowEngine(max_concurrency=definition.max_concurrency)
    run_id = f"run_{uuid.uuid4().hex[:8]}"

    def sse_event_relay(evt: WorkflowEvent) -> None:
        event_bus.publish(
            {
                "run_id": run_id,
                "event_type": evt.event_type,
                "task_name": evt.task_name,
                "data": evt.data,
                "timestamp": evt.timestamp,
            }
        )

    engine.add_listener(sse_event_relay)

    for t in definition.tasks:
        retry_policy = RetryPolicy(max_retries=t.retries) if t.retries > 0 else None
        engine.add_task(
            name=t.name,
            func=_build_task_callable(t.operation, t.payload),
            dependencies=t.dependencies,
            timeout=t.timeout,
            retry_policy=retry_policy,
        )

    results = await engine.execute()
    serialized = results.to_dict()

    record = {
        "run_id": run_id,
        "name": definition.name,
        "status": results.status,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "duration_ms": serialized["total_duration_ms"],
        "results": serialized["results"],
        "task_metrics": serialized["task_metrics"],
    }
    registry.record_run(record)

    return {
        "run_id": run_id,
        "status": results.status,
        "duration_ms": serialized["total_duration_ms"],
        "results": serialized["results"],
        "task_metrics": serialized["task_metrics"],
    }


@app.get("/api/v1/workflows/runs")
async def list_workflow_runs(limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
    """Retrieve history of recently executed workflow runs."""
    runs = registry.list_runs(limit=limit)
    return {"total": len(runs), "runs": runs}


@app.get("/api/v1/workflows/runs/{run_id}")
async def get_workflow_run(run_id: str) -> dict[str, Any]:
    """Get detailed telemetry and result metrics for a specific workflow run."""
    run = registry.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")
    return run


@app.get("/api/v1/health", response_model=SystemHealthResponse)
async def system_health() -> SystemHealthResponse:
    """Detailed platform health check and runtime metrics."""
    return SystemHealthResponse(
        status="operational",
        version=__version__,
        total_runs_recorded=len(registry.runs),
        uptime_seconds=round(time.time() - registry.start_time, 2),
        active_listeners=len(event_bus._subscribers),
    )


# --- Real-Time Server-Sent Events (SSE) Stream ---


@app.get("/api/v1/stream")
async def global_event_stream() -> StreamingResponse:
    """Server-Sent Events (SSE) stream delivering real-time task and DAG execution updates."""
    queue = event_bus.subscribe()

    async def sse_generator() -> AsyncGenerator[str, None]:
        try:
            yield f"event: connected\ndata: {json.dumps({'time': time.time(), 'status': 'connected'})}\n\n"
            while True:
                msg = await queue.get()
                evt_type = msg.get("event_type", "message")
                yield f"event: {evt_type}\ndata: {json.dumps(msg)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- Glassmorphic Interactive Dashboard UI ---

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Catalyst Engine | Real-Time Workflow Command Center</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#ECFDF5', 400: '#34D399', 500: '#10B981', 600: '#059669', 900: '#064E3B' },
            dark: { 900: '#0B0F19', 800: '#111827', 700: '#1F2937', 600: '#374151' }
          }
        }
      }
    }
  </script>
  <style>
    .glass { background: rgba(17, 24, 39, 0.75); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .glass-card { background: rgba(31, 41, 55, 0.45); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.06); }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
  </style>
</head>
<body class="bg-dark-900 text-gray-100 min-h-screen flex flex-col font-sans selection:bg-brand-500 selection:text-white">

  <!-- Top Navigation Header -->
  <header class="glass sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between border-b border-gray-800">
    <div class="flex items-center space-x-3">
      <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
        <i class="fa-solid fa-bolt text-white text-base"></i>
      </div>
      <div>
        <h1 class="font-bold text-lg leading-tight tracking-tight text-white flex items-center gap-2">
          Catalyst Engine <span class="text-xs px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 font-semibold border border-brand-500/20">v1.0</span>
        </h1>
        <p class="text-xs text-gray-400">High-Performance Parallel DAG Orchestrator</p>
      </div>
    </div>

    <!-- Live Stream Badge & Controls -->
    <div class="flex items-center space-x-4">
      <div id="sse-badge" class="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-full bg-gray-800/80 border border-gray-700">
        <span id="sse-dot" class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
        <span id="sse-status" class="text-gray-300 font-medium">Connecting...</span>
      </div>

      <button onclick="triggerDemoRun()" class="px-3.5 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-semibold shadow-md shadow-brand-500/20 flex items-center gap-2 transition active:scale-95">
        <i class="fa-solid fa-play"></i> Trigger Demo DAG
      </button>

      <a href="/docs" target="_blank" class="text-gray-400 hover:text-white text-xs flex items-center gap-1.5 transition">
        <i class="fa-solid fa-book-open"></i> Docs
      </a>
    </div>
  </header>

  <!-- Main Dashboard Content -->
  <main class="flex-1 p-6 space-y-6 max-w-7xl mx-auto w-full">

    <!-- KPI Statistics Grid -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="glass-card p-4 rounded-xl">
        <div class="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Total Executions</div>
        <div id="stat-total" class="text-2xl font-extrabold text-white">0</div>
        <div class="text-[11px] text-gray-500 mt-1 flex items-center gap-1"><i class="fa-solid fa-clock-rotate-left"></i> In-Memory Registry</div>
      </div>
      <div class="glass-card p-4 rounded-xl">
        <div class="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Success Rate</div>
        <div id="stat-success-rate" class="text-2xl font-extrabold text-emerald-400">100%</div>
        <div class="text-[11px] text-gray-500 mt-1 flex items-center gap-1"><i class="fa-solid fa-shield-halved"></i> Fault-Tolerant Engine</div>
      </div>
      <div class="glass-card p-4 rounded-xl">
        <div class="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Avg Execution Time</div>
        <div id="stat-avg-duration" class="text-2xl font-extrabold text-cyan-400">0.00 ms</div>
        <div class="text-[11px] text-gray-500 mt-1 flex items-center gap-1"><i class="fa-solid fa-gauge-high"></i> Microsecond Overhead</div>
      </div>
      <div class="glass-card p-4 rounded-xl">
        <div class="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Engine Engine Status</div>
        <div class="text-2xl font-extrabold text-brand-400 flex items-center gap-2">
          Active <span class="w-2.5 h-2.5 rounded-full bg-brand-500"></span>
        </div>
        <div class="text-[11px] text-gray-500 mt-1 flex items-center gap-1"><i class="fa-solid fa-microchip"></i> Pure Python AsyncIO</div>
      </div>
    </div>

    <!-- Active DAG Visualizer & Waterfall -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- Left 2 Cols: DAG Interactive Topology & Waterfall -->
      <div class="lg:col-span-2 space-y-6">
        
        <!-- DAG Graph Canvas Card -->
        <div class="glass rounded-2xl p-5 border border-gray-800">
          <div class="flex items-center justify-between mb-4">
            <h2 class="font-bold text-sm text-gray-200 flex items-center gap-2">
              <i class="fa-solid fa-network-wired text-brand-400"></i> Interactive DAG Topology
            </h2>
            <div id="current-run-label" class="text-xs font-mono text-gray-400">No active run selected</div>
          </div>

          <!-- Dynamic SVG Topology Container -->
          <div id="dag-container" class="w-full h-64 bg-dark-800/60 rounded-xl border border-gray-800 flex items-center justify-center overflow-auto p-4 relative">
            <p class="text-xs text-gray-500 italic">Trigger a workflow to render the live topological DAG execution graph.</p>
          </div>
        </div>

        <!-- Execution Waterfall Timeline -->
        <div class="glass rounded-2xl p-5 border border-gray-800">
          <h2 class="font-bold text-sm text-gray-200 mb-4 flex items-center gap-2">
            <i class="fa-solid fa-chart-gantt text-cyan-400"></i> Task Execution Waterfall
          </h2>
          <div id="waterfall-container" class="space-y-2">
            <p class="text-xs text-gray-500 italic py-4 text-center">Waterfall timeline appears after executing a DAG.</p>
          </div>
        </div>

      </div>

      <!-- Right 1 Col: Live Event Stream & Recent Runs -->
      <div class="space-y-6">
        
        <!-- Live SSE Event Stream -->
        <div class="glass rounded-2xl p-5 border border-gray-800 flex flex-col h-80">
          <div class="flex items-center justify-between mb-3">
            <h2 class="font-bold text-sm text-gray-200 flex items-center gap-2">
              <i class="fa-solid fa-satellite-dish text-emerald-400"></i> Live Telemetry Stream
            </h2>
            <button onclick="clearLogs()" class="text-[11px] text-gray-400 hover:text-white transition">Clear</button>
          </div>
          <div id="event-log-container" class="flex-1 overflow-y-auto space-y-2 font-mono text-[11px] pr-1">
            <div class="text-gray-500 italic text-center py-8">Listening for real-time engine events...</div>
          </div>
        </div>

        <!-- Recent Runs Table -->
        <div class="glass rounded-2xl p-5 border border-gray-800 flex flex-col h-80">
          <h2 class="font-bold text-sm text-gray-200 mb-3 flex items-center gap-2">
            <i class="fa-solid fa-list-check text-indigo-400"></i> Execution History
          </h2>
          <div id="recent-runs-container" class="flex-1 overflow-y-auto space-y-2 pr-1">
            <div class="text-gray-500 italic text-center py-8">No executions recorded yet.</div>
          </div>
        </div>

      </div>

    </div>

  </main>

  <!-- Interactive JavaScript Engine Client -->
  <script>
    let recentRuns = [];

    async function loadStats() {
      try {
        const res = await fetch('/api/v1/workflows/runs');
        const data = await res.json();
        recentRuns = data.runs || [];

        document.getElementById('stat-total').innerText = recentRuns.length;
        if (recentRuns.length > 0) {
          const successCount = recentRuns.filter(r => r.status === 'success').length;
          const rate = ((successCount / recentRuns.length) * 100).toFixed(0);
          document.getElementById('stat-success-rate').innerText = rate + '%';

          const totalMs = recentRuns.reduce((acc, r) => acc + (r.duration_ms || 0), 0);
          document.getElementById('stat-avg-duration').innerText = (totalMs / recentRuns.length).toFixed(2) + ' ms';
        }

        renderRecentRuns();
        if (recentRuns.length > 0) {
          renderRunDetails(recentRuns[0]);
        }
      } catch (e) {
        console.error('Failed to load stats:', e);
      }
    }

    function renderRecentRuns() {
      const container = document.getElementById('recent-runs-container');
      if (!recentRuns.length) {
        container.innerHTML = '<div class="text-gray-500 italic text-center py-8">No executions recorded yet.</div>';
        return;
      }

      container.innerHTML = recentRuns.map(r => `
        <div onclick='renderRunDetailsById("${r.run_id}")' class="p-2.5 rounded-xl bg-gray-800/40 hover:bg-gray-800 border border-gray-700/50 cursor-pointer transition flex items-center justify-between">
          <div>
            <div class="font-semibold text-xs text-white">${r.name || 'custom_dag'}</div>
            <div class="text-[10px] text-gray-400 font-mono">${r.run_id} • ${r.created_at}</div>
          </div>
          <div class="text-right">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.status === 'success' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}">${r.status.toUpperCase()}</span>
            <div class="text-[10px] text-gray-400 mt-0.5">${r.duration_ms ? r.duration_ms.toFixed(1) + 'ms' : ''}</div>
          </div>
        </div>
      `).join('');
    }

    function renderRunDetailsById(runId) {
      const r = recentRuns.find(item => item.run_id === runId);
      if (r) renderRunDetails(r);
    }

    function renderRunDetails(run) {
      document.getElementById('current-run-label').innerText = `${run.name} (${run.run_id}) — ${run.status.toUpperCase()}`;
      
      const metrics = run.task_metrics || {};
      const taskNames = Object.keys(metrics);

      // Render Topological DAG Graph
      const dagContainer = document.getElementById('dag-container');
      if (taskNames.length === 0) {
        dagContainer.innerHTML = '<p class="text-xs text-gray-500 italic">No tasks in this execution.</p>';
        return;
      }

      let nodesHtml = taskNames.map((name, idx) => {
        const m = metrics[name];
        const status = m ? m.status : 'success';
        let badgeColor = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
        if (status === 'failed') badgeColor = 'bg-rose-500/20 text-rose-400 border-rose-500/30';
        if (status === 'skipped') badgeColor = 'bg-amber-500/20 text-amber-400 border-amber-500/30';

        return `
          <div class="flex flex-col items-center min-w-[120px] p-3 rounded-xl bg-gray-800/80 border border-gray-700 shadow-md">
            <div class="font-bold text-xs text-white">${name}</div>
            <span class="mt-1.5 px-2 py-0.5 rounded text-[9px] font-semibold uppercase border ${badgeColor}">${status}</span>
            <div class="text-[10px] text-gray-400 mt-1">${m && m.duration_ms ? m.duration_ms.toFixed(1) + 'ms' : ''}</div>
          </div>
        `;
      }).join('<div class="text-gray-600 font-bold text-lg"><i class="fa-solid fa-arrow-right"></i></div>');

      dagContainer.innerHTML = `<div class="flex items-center space-x-3 overflow-x-auto w-full py-4 px-2 justify-center">${nodesHtml}</div>`;

      // Render Waterfall Bars
      const waterfallContainer = document.getElementById('waterfall-container');
      const maxDuration = Math.max(...taskNames.map(n => (metrics[n] ? metrics[n].duration_ms : 0)), 1);

      waterfallContainer.innerHTML = taskNames.map(name => {
        const m = metrics[name];
        const d = m ? m.duration_ms : 0;
        const widthPct = Math.max((d / maxDuration) * 100, 6);
        const barColor = m && m.status === 'failed' ? 'bg-rose-500' : (m && m.status === 'skipped' ? 'bg-amber-500' : 'bg-brand-500');

        return `
          <div class="flex items-center text-xs space-x-3">
            <div class="w-28 font-mono text-gray-300 truncate">${name}</div>
            <div class="flex-1 bg-gray-800 rounded-full h-4 overflow-hidden p-0.5">
              <div class="${barColor} h-full rounded-full transition-all duration-500 flex items-center justify-end pr-1 text-[9px] font-bold text-black" style="width: ${widthPct}%">
                ${d.toFixed(1)}ms
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    async function triggerDemoRun() {
      try {
        const res = await fetch('/execute', { method: 'POST' });
        const data = await res.json();
        await loadStats();
      } catch (e) {
        alert('Execution failed: ' + e.message);
      }
    }

    function clearLogs() {
      document.getElementById('event-log-container').innerHTML = '';
    }

    // Connect to Server-Sent Events (SSE) Stream
    function initSSE() {
      const evtSource = new EventSource('/api/v1/stream');
      const dot = document.getElementById('sse-dot');
      const statusText = document.getElementById('sse-status');

      evtSource.addEventListener('connected', () => {
        dot.className = 'w-2 h-2 rounded-full bg-emerald-400';
        statusText.innerText = 'Live Feed Connected';
      });

      function logEvent(evtName, data) {
        const container = document.getElementById('event-log-container');
        const row = document.createElement('div');
        row.className = 'p-1.5 rounded bg-gray-800/40 border border-gray-700/30 flex items-center justify-between text-gray-300';
        row.innerHTML = `
          <span><span class="text-brand-400 font-semibold">[${evtName}]</span> ${data.task_name ? data.task_name : ''}</span>
          <span class="text-gray-500 text-[10px]">${new Date().toLocaleTimeString()}</span>
        `;
        container.prepend(row);
      }

      ['task_started', 'task_completed', 'task_failed', 'task_skipped', 'workflow_started', 'workflow_completed'].forEach(evtName => {
        evtSource.addEventListener(evtName, (e) => {
          try {
            const data = JSON.parse(e.data);
            logEvent(evtName, data);
            if (evtName === 'workflow_completed') {
              loadStats();
            }
          } catch (err) {
            console.error(err);
          }
        });
      });

      evtSource.onerror = () => {
        dot.className = 'w-2 h-2 rounded-full bg-rose-500';
        statusText.innerText = 'Reconnecting...';
      };
    }

    window.onload = () => {
      loadStats();
      initSSE();
    };
  </script>
</body>
</html>
"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_ui() -> HTMLResponse:
    """Interactive real-time Glassmorphic Visual Dashboard for Catalyst Engine."""
    return HTMLResponse(content=DASHBOARD_HTML)
