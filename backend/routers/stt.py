"""
backend/routers/stt.py
STT endpoints: upload audio → transcript → structured fields
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.session import LoanApplication, VideoSession, AuditLog
from backend.services.stt_service import STTService

router = APIRouter()
stt = STTService()


@router.post("/transcribe/{session_id}")
async def transcribe_audio(
    session_id: str,
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept audio file from the video call client.
    1. Transcribe with Whisper / Deepgram
    2. Extract structured fields with LLM
    3. Upsert LoanApplication
    """
    # Verify session
    res = await db.execute(select(VideoSession).where(VideoSession.id == session_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    audio_bytes = await audio.read()
    mime = audio.content_type or "audio/webm"

    # STT
    transcript = await stt.transcribe(audio_bytes, mime)

    # LLM field extraction
    fields = await stt.extract_fields(transcript)

    # Upsert LoanApplication
    res2 = await db.execute(
        select(LoanApplication).where(LoanApplication.session_id == session_id)
    )
    app = res2.scalar_one_or_none()

    if app is None:
        app = LoanApplication(session_id=session_id)
        db.add(app)

    app.transcript = transcript
    app.full_name = fields.get("full_name")
    app.employment_type = fields.get("employment_type")
    app.monthly_income = fields.get("monthly_income")
    app.loan_purpose = fields.get("loan_purpose")
    app.requested_amount = fields.get("requested_amount")
    app.declared_age = fields.get("declared_age")
    app.verbal_consent = bool(fields.get("verbal_consent", False))

    log = AuditLog(
        session=session,
        event="stt_completed",
        detail={"transcript_length": len(transcript), "fields": fields},
    )
    db.add(log)
    await db.commit()

    return {"transcript": transcript, "fields": fields, "application_id": app.id}
