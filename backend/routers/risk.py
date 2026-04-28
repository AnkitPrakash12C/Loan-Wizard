"""
backend/routers/risk.py
Runs policy + ML risk evaluation for an application.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.session import LoanApplication, VideoSession, AuditLog
from backend.services.risk_service import RiskService
from backend.services.llm_service import LLMService

router = APIRouter()
risk_svc = RiskService()
llm_svc = LLMService()


@router.post("/evaluate/{session_id}")
async def evaluate_risk(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Orchestrates:
    1. LLM classification (risk band, persona)
    2. Policy + ML risk evaluation
    3. Persists results to LoanApplication
    """
    # Load application
    res = await db.execute(
        select(LoanApplication).where(LoanApplication.session_id == session_id)
    )
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found for this session")

    profile = {
        "full_name": app.full_name,
        "employment_type": app.employment_type,
        "monthly_income": app.monthly_income,
        "loan_purpose": app.loan_purpose,
        "requested_amount": app.requested_amount,
        "declared_age": app.declared_age,
        "verbal_consent": app.verbal_consent,
        "estimated_age": app.estimated_age,
        "age_match_ok": app.age_match_ok,
    }

    # LLM classification
    classification = await llm_svc.classify_customer(profile)
    app.llm_risk_band = classification.get("risk_band")
    app.llm_persona = classification.get("persona")
    app.llm_confidence = classification.get("confidence")
    app.llm_summary = classification.get("summary")

    # Risk evaluation
    risk_input = {**profile, "llm_risk_band": app.llm_risk_band}
    risk_result = risk_svc.evaluate(risk_input)

    app.risk_score = risk_result["risk_score"]
    app.propensity_score = risk_result["propensity_score"]
    app.is_eligible = risk_result["is_eligible"]
    app.rejection_reason = "; ".join(risk_result["rejection_reasons"])

    # Load session for audit
    res2 = await db.execute(select(VideoSession).where(VideoSession.id == session_id))
    session = res2.scalar_one_or_none()

    log = AuditLog(
        session=session,
        event="risk_evaluated",
        detail={
            "classification": classification,
            "risk_result": risk_result,
        },
    )
    db.add(log)
    await db.commit()

    return {
        "is_eligible": app.is_eligible,
        "risk_score": app.risk_score,
        "propensity_score": app.propensity_score,
        "classification": classification,
        "rejection_reasons": risk_result["rejection_reasons"],
    }
