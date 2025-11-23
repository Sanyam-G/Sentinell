"""Background worker that continually processes queued incidents via the LangGraph."""
from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Ensure repo root is importable so we can load data/ modules for Pinecone access.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Load environment variables from root .env
load_dotenv(ROOT_DIR / ".env")

from db.base import SessionLocal
from graph import build_graph
from services.context import (
    fetch_next_incident,
    hydrate_state_from_incident,
    mark_incident_resolved,
)
from services.pr_service import pr_service
from state import SREState

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")

graph = build_graph()


async def process_once() -> bool:
    async with SessionLocal() as session:
        incident = await fetch_next_incident(session)
        if not incident:
            return False

        state = await hydrate_state_from_incident(session, SREState(), incident)
        success = False
        try:
            raw_result = await asyncio.to_thread(graph.invoke, state)
            final_state = SREState(**raw_result) if isinstance(raw_result, dict) else raw_result
            success = bool(final_state.resolved)

            if final_state.plan and final_state.repo:
                await asyncio.to_thread(
                    pr_service.create_pr,
                    final_state.repo,
                    final_state.plan,
                    incident=incident,
                )
        except Exception:
            logger.exception("Graph execution failed for incident %s", incident.id)
            success = False
        finally:
            await mark_incident_resolved(session, incident.id, success=success)

        return True


async def run_forever(poll_interval: float = 2.0) -> None:
    while True:
        try:
            processed = await process_once()
        except Exception as exc:  # pragma: no cover - defensive loop guard
            logger.exception("Worker iteration crashed: %s", exc)
            processed = True

        await asyncio.sleep(0.1 if processed else poll_interval)


if __name__ == "__main__":
    print(f"[{datetime.utcnow().isoformat()}] Worker starting...")
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        print("Worker stopped")
