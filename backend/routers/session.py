"""
backend/routers/session.py
Video session lifecycle: create, update, close
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.models.session import VideoSession, AuditLog

router = APIRouter()


# ─── Pydantic schemas ────────────────────────────────────────────

class SessionCreate(BaseModel):
    customer_phone: str
    customer_email: Optional[str] = None
    campaign_id: Optional[str] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lng: Optional[float] = None
    geo_city: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    status: str
    customer_phone: str
    started_at: datetime

    class Config:
        from_attributes = True


# ─── Endpoints ───────────────────────────────────────────────────

@router.post("/create", response_model=SessionResponse)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new video onboarding session (called when customer opens link)."""
    session = VideoSession(**body.model_dump())
    db.add(session)

    log = AuditLog(session=session, event="session_created", detail=body.model_dump())
    db.add(log)

    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VideoSession).where(VideoSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.post("/{session_id}/end")
async def end_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VideoSession).where(VideoSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    session.status = "completed"
    session.ended_at = datetime.utcnow()

    log = AuditLog(session=session, event="session_ended", detail={"session_id": session_id})
    db.add(log)
    await db.commit()
    return {"ok": True}
