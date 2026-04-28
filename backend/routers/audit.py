"""
backend/routers/audit.py
Central audit/logging endpoints for compliance & traceability.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional

from backend.database import get_db
from backend.models.session import AuditLog, VideoSession, LoanApplication

router = APIRouter()


class AuditLogOut(BaseModel):
    id: str
    event: str
    detail: Optional[Any]
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/{session_id}", response_model=list[AuditLogOut])
async def get_audit_trail(session_id: str, db: AsyncSession = Depends(get_db)):
    """Return all audit events for a session (compliance view)."""
    res = await db.execute(select(VideoSession).where(VideoSession.id == session_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    res2 = await db.execute(
        select(AuditLog)
        .where(AuditLog.session_id == session_id)
        .order_by(AuditLog.timestamp)
    )
    logs = res2.scalars().all()
    return logs


@router.get("/application/{session_id}")
async def get_application_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    """Return the full application record for a session."""
    res = await db.execute(
        select(LoanApplication).where(LoanApplication.session_id == session_id)
    )
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    return {
        "id": app.id,
        "session_id": app.session_id,
        "full_name": app.full_name,
        "employment_type": app.employment_type,
        "monthly_income": app.monthly_income,
        "loan_purpose": app.loan_purpose,
        "requested_amount": app.requested_amount,
        "declared_age": app.declared_age,
        "estimated_age": app.estimated_age,
        "age_match_ok": app.age_match_ok,
        "verbal_consent": app.verbal_consent,
        "transcript": app.transcript,
        "llm_risk_band": app.llm_risk_band,
        "llm_persona": app.llm_persona,
        "llm_confidence": app.llm_confidence,
        "llm_summary": app.llm_summary,
        "risk_score": app.risk_score,
        "propensity_score": app.propensity_score,
        "is_eligible": app.is_eligible,
        "rejection_reason": app.rejection_reason,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
    }
