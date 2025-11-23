import asyncio
import contextlib
import os
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Ensure repo root on path so backend can import sibling packages (data/, agent/)
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db.base import engine
from db.models import SQLModel
from state import SREState
from graph import build_graph
from routes.config import router as config_router
from routes.dashboard import router as dashboard_router
from routes.signals import router as signals_router
from services.poller import run_polling_loop

# Load environment variables
load_dotenv()
ENABLE_AUTO_POLL = os.getenv("SRE_ENABLE_AUTO_POLL", "true").lower() not in {"0", "false", "no"}
ENABLE_AGENT_WORKER = os.getenv("SRE_ENABLE_AGENT_WORKER", "true").lower() not in {"0", "false", "no"}

# Build the graph
graph = build_graph()

# Create FastAPI app
app = FastAPI(title="AI SRE Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten once frontend origin is known
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers for APIs the frontend will call
app.include_router(config_router)
app.include_router(signals_router)
app.include_router(dashboard_router)


@app.on_event("startup")
async def init_db() -> None:
    """Ensure all SQLModel tables exist before handling traffic."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    if ENABLE_AUTO_POLL:
        app.state.poller_task = asyncio.create_task(run_polling_loop())
    if ENABLE_AGENT_WORKER:
        from worker import run_forever as worker_loop  # defer import to avoid circulars

        app.state.worker_task = asyncio.create_task(worker_loop())


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "AI SRE Agent is running"}


@app.get("/api/health")
async def api_health():
    """API specific health check used by the frontend."""
    return {"ok": True, "graph_ready": True}


@app.on_event("shutdown")
async def shutdown_background_tasks() -> None:
    for attr in ("poller_task", "worker_task"):
        task = getattr(app.state, attr, None)
        if not task:
            continue
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        setattr(app.state, attr, None)


@app.websocket("/stream")
async def stream(ws: WebSocket):
    """
    WebSocket endpoint for streaming graph execution events.
    Frontend can connect to ws://localhost:8000/stream
    """
    await ws.accept()

    try:
        initial_state = SREState()

        async for event in graph.astream(initial_state):
            await ws.send_json(event)

        await ws.close()
    except Exception as e:
        print(f"WebSocket error: {e}")
        await ws.close(code=1011, reason=str(e))


def run_cli():
    """
    CLI runner for direct execution without WebSocket.
    Run with: python -c "from app import run_cli; run_cli()"
    """
    print("Running AI SRE Agent in CLI mode...")
    result = graph.invoke(SREState())
    print("\n=== Final Result ===")
    print(result)


if __name__ == "__main__":
    # Ensure database tables exist before serving
    import asyncio

    async def _init_db():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.run(_init_db())
    uvicorn.run(app, host="0.0.0.0", port=8000)
