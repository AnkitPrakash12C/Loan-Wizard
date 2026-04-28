"""
backend/routers/offer.py
Generate and persist personalised loan offers.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.session import LoanApplication, LoanOffer, VideoSession, AuditLog
from backend.services.offer_service import OfferService
from backend.services.llm_service import LLMService

router = APIRouter()
offer_svc = OfferService()
llm_svc = LLMService()


@router.post("/generate/{session_id}")
async def generate_offers(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generate personalised loan offers for an eligible application.
    Returns list of offer objects + a human-friendly explanation.
    """
    res = await db.execute(
        select(LoanApplication).where(LoanApplication.session_id == session_id)
    )
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    classification = {
        "risk_band": app.llm_risk_band or "medium",
        "persona": app.llm_persona,
    }

    app_data = {
        "monthly_income": app.monthly_income,
        "requested_amount": app.requested_amount,
        "loan_purpose": app.loan_purpose,
    }

    # Generate offers
    offers = offer_svc.generate_offers(app_data, {"is_eligible": app.is_eligible}, classification)

    # Persist to DB
    db_offers = []
    for o in offers:
        db_offer = LoanOffer(application_id=app.id, **o)
        db.add(db_offer)
        db_offers.append(db_offer)

    # Human-friendly explanation
    if app.is_eligible:
        explanation = await llm_svc.generate_decision_explanation(
            decision="approved",
            reasons=["policy_passed", f"risk_band_{app.llm_risk_band}"],
            name=app.full_name,
        )
    else:
        reasons = (app.rejection_reason or "").split("; ")
        explanation = await llm_svc.generate_decision_explanation(
            decision="declined",
            reasons=reasons,
            name=app.full_name,
        )

    # Audit
    res2 = await db.execute(select(VideoSession).where(VideoSession.id == session_id))
    session = res2.scalar_one_or_none()
    log = AuditLog(
        session=session,
        event="offers_generated",
        detail={"count": len(offers), "eligible": app.is_eligible},
    )
    db.add(log)
    await db.commit()

    return {
        "eligible": app.is_eligible,
        "explanation": explanation,
        "offers": offers,
        "summary": app.llm_summary,
    }


@router.post("/accept/{session_id}/{offer_id}")
async def accept_offer(session_id: str, offer_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an offer as accepted by the customer."""
    res = await db.execute(select(LoanOffer).where(LoanOffer.id == offer_id))
    offer = res.scalar_one_or_none()
    if not offer:
        raise HTTPException(404, "Offer not found")

    offer.is_accepted = True

    res2 = await db.execute(select(VideoSession).where(VideoSession.id == session_id))
    session = res2.scalar_one_or_none()
    log = AuditLog(
        session=session,
        event="offer_accepted",
        detail={"offer_id": offer_id},
    )
    db.add(log)
    await db.commit()
    return {"ok": True, "offer_id": offer_id}
