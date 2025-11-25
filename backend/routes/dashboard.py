"""Dashboard-friendly APIs that aggregate context for the frontend."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import get_session
from schemas import IncidentContextResponse
from services.context import get_incident_context

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/incidents/{incident_id}/context", response_model=IncidentContextResponse)
async def fetch_incident_context(
    incident_id: str, session: AsyncSession = Depends(get_session)
) -> IncidentContextResponse:
    payload = await get_incident_context(session, incident_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Incident not found")
    return payload
