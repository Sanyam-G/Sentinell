"""
Sentinell Backend - Observer Node API

Exposes WebSocket endpoints for real-time log/event streaming.
Phase 3: Agent integration with POST /analyze endpoint.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Set, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .observer import ContainerObserver
from .agent import SentinellAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
observer: ContainerObserver = None
agent: Optional[SentinellAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global observer, agent

    # Startup
    logger.info("🚀 Starting Sentinell Observer Node...")
    observer = ContainerObserver()
    await observer.start()

    # Initialize Agent (Phase 3)
    try:
        logger.info("🧠 Initializing Sentinell Agent...")
        agent = SentinellAgent()
        logger.info("✅ Agent ready")
    except Exception as e:
        logger.warning(f"⚠️ Agent initialization failed: {e}")
        logger.warning("Agent endpoints will not be available")
        agent = None

    yield

    # Shutdown
    logger.info("🛑 Shutting down Observer Node...")
    if observer:
        await observer.stop()


app = FastAPI(
    title="Sentinell Observer Node",
    description="Real-time container monitoring and event streaming",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track active WebSocket connections
active_connections: Set[WebSocket] = set()


@app.get("/")
async def root():
    """Health check and info."""
    return {
        "service": "sentinell-observer",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "monitored_containers": len(observer.monitored_containers) if observer else 0,
        "active_ws_connections": len(active_connections)
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/containers")
async def list_containers():
    """List all monitored containers."""
    if not observer:
        return {"error": "Observer not initialized"}

    containers = observer.get_victim_containers()
    return {
        "containers": [
            {
                "id": c.id[:12],
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown"
            }
            for c in containers
        ],
        "count": len(containers)
    }


@app.get("/stats")
async def get_stats():
    """Get current resource stats for all containers."""
    if not observer:
        return {"error": "Observer not initialized"}

    stats = await observer.get_all_stats()
    return {"stats": stats, "timestamp": datetime.now().isoformat()}


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for live log streaming.

    Streams all logs and events in real-time.
    """
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"🔌 WebSocket connected: {websocket.client.host}")

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Sentinell Observer"
        })

        # Stream events from the observer
        while True:
            if not observer:
                await asyncio.sleep(1)
                continue

            try:
                # Wait for next event (with timeout to allow connection checks)
                event = await asyncio.wait_for(
                    observer.event_queue.get(),
                    timeout=1.0
                )

                # Send to client
                await websocket.send_json(event)

            except asyncio.TimeoutError:
                # No event, send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {websocket.client.host}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)


@app.websocket("/ws/logs/{container_name}")
async def websocket_container_logs(websocket: WebSocket, container_name: str):
    """
    WebSocket endpoint for streaming logs from a specific container.
    """
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected for {container_name}: {websocket.client.host}")

    try:
        # Verify container exists
        if not observer or container_name not in observer.log_queues:
            await websocket.send_json({
                "type": "error",
                "message": f"Container {container_name} not found or not monitored"
            })
            await websocket.close()
            return

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "container": container_name,
            "message": f"Connected to {container_name} logs"
        })

        # Stream logs for this container
        queue = observer.log_queues[container_name]

        while True:
            try:
                log_entry = await asyncio.wait_for(queue.get(), timeout=5.0)
                await websocket.send_json(log_entry)

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "container": container_name
                })

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for {container_name}")
    except Exception as e:
        logger.error(f"WebSocket error for {container_name}: {e}")


@app.post("/events/anomaly")
async def report_anomaly(anomaly: dict):
    """
    Accept anomaly reports from external systems.

    This can be used by the Agent to report detected issues.
    """
    logger.warning(f"🚨 Anomaly reported: {anomaly}")

    # Broadcast to all connected clients
    anomaly_event = {
        "type": "anomaly",
        "timestamp": datetime.now().isoformat(),
        **anomaly
    }

    if observer:
        await observer.event_queue.put(anomaly_event)

    return {"status": "received", "anomaly": anomaly_event}


# ==================== PHASE 3: AGENT ENDPOINTS ====================

class AnalyzeRequest(BaseModel):
    """Request model for /analyze endpoint."""
    problem_description: str
    container_name: str


class ApprovalRequest(BaseModel):
    """Request model for /approve endpoint."""
    approved: bool
    feedback: str = ""
    state: dict  # The agent state from the previous analysis


@app.post("/analyze")
async def analyze_problem(request: AnalyzeRequest):
    """
    Analyze a problem using the Sentinell Agent.

    This endpoint:
    1. Detects the issue from logs
    2. Retrieves relevant documentation
    3. Creates a fix plan
    4. Returns the plan for human approval

    Returns the agent state at the human_approval node.
    """
    if not agent:
        raise HTTPException(
            status_code=503,
            detail="Agent not available. Check ANTHROPIC_API_KEY environment variable."
        )

    logger.info(f"🔍 Analysis requested for {request.container_name}: {request.problem_description}")

    try:
        # Run agent analysis (stops at human_approval)
        state = agent.analyze(
            problem_description=request.problem_description,
            container_name=request.container_name
        )

        # Return state for human review
        return {
            "status": "awaiting_approval",
            "container": request.container_name,
            "problem": request.problem_description,
            "detected_issue": state.get("detected_issue", ""),
            "diagnosis": state.get("diagnosis", ""),
            "proposed_fix": state.get("proposed_fix", ""),
            "fix_steps": state.get("fix_steps", []),
            "current_step": state.get("current_step", ""),
            "error": state.get("error", ""),
            "state": state  # Include full state for continuation
        }

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approve")
async def approve_fix(request: ApprovalRequest):
    """
    Approve or reject the agent's proposed fix.

    If approved:
    1. Agent applies the fix
    2. Agent verifies the fix worked
    3. Returns final result

    If rejected:
    1. Returns without executing
    """
    if not agent:
        raise HTTPException(
            status_code=503,
            detail="Agent not available"
        )

    logger.info(f"👤 Human decision: {'APPROVED' if request.approved else 'REJECTED'}")

    try:
        # Continue agent execution with approval decision
        final_state = agent.approve_and_execute(
            state=request.state,
            approved=request.approved,
            feedback=request.feedback
        )

        if not request.approved:
            return {
                "status": "rejected",
                "message": "Fix rejected by human",
                "feedback": request.feedback
            }

        # Return execution results
        return {
            "status": "completed",
            "fix_applied": final_state.get("fix_applied", False),
            "execution_log": final_state.get("execution_log", []),
            "verification": final_state.get("verification_result", ""),
            "issue_resolved": final_state.get("issue_resolved", False),
            "error": final_state.get("error", "")
        }

    except Exception as e:
        logger.error(f"❌ Approval processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
