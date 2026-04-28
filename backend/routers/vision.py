"""
backend/routers/vision.py
Computer vision endpoint: estimate age from a single video frame.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.session import LoanApplication, VideoSession, AuditLog
from backend.services.vision_service import VisionService

router = APIRouter()
vision = VisionService()


@router.post("/analyze-frame/{session_id}")
async def analyze_frame(
    session_id: str,
    frame: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a JPEG/PNG frame from the client-side video stream.
    Returns age estimate and any fraud signals.
    """
    # Verify session
    res = await db.execute(select(VideoSession).where(VideoSession.id == session_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    frame_bytes = await frame.read()
    vision_result = await vision.estimate_age(frame_bytes)

    # Fetch application to cross-check declared age
    res2 = await db.execute(
        select(LoanApplication).where(LoanApplication.session_id == session_id)
    )
    app = res2.scalar_one_or_none()

    age_validation = {"ok": True, "reason": "no_application_yet"}

    if app:
        app.estimated_age = vision_result.get("estimated_age")
        if app.declared_age and vision_result.get("estimated_age"):
            age_validation = vision.validate_age(
                vision_result["estimated_age"], app.declared_age
            )
            app.age_match_ok = age_validation["ok"]

        log = AuditLog(
            session=session,
            event="vision_analyzed",
            detail={**vision_result, "age_validation": age_validation},
        )
        db.add(log)
        await db.commit()

    return {
        "vision": vision_result,
        "age_validation": age_validation,
    }
