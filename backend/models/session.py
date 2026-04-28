"""
backend/models/session.py
SQLAlchemy ORM models
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class VideoSession(Base):
    __tablename__ = "video_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(120), nullable=True)
    campaign_id: Mapped[str] = mapped_column(String(64), nullable=True)

    # Session metadata
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True)
    device_info: Mapped[str] = mapped_column(Text, nullable=True)
    geo_lat: Mapped[float] = mapped_column(Float, nullable=True)
    geo_lng: Mapped[float] = mapped_column(Float, nullable=True)
    geo_city: Mapped[str] = mapped_column(String(64), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="initiated")
    # initiated | active | completed | failed

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        back_populates="session", uselist=False
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="session")


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("video_sessions.id"))

    # Captured from STT
    full_name: Mapped[str] = mapped_column(String(120), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(64), nullable=True)
    monthly_income: Mapped[float] = mapped_column(Float, nullable=True)
    loan_purpose: Mapped[str] = mapped_column(String(128), nullable=True)
    requested_amount: Mapped[float] = mapped_column(Float, nullable=True)
    verbal_consent: Mapped[bool] = mapped_column(Boolean, default=False)

    # STT raw transcript
    transcript: Mapped[str] = mapped_column(Text, nullable=True)

    # Vision outputs
    estimated_age: Mapped[int] = mapped_column(nullable=True)
    declared_age: Mapped[int] = mapped_column(nullable=True)
    age_match_ok: Mapped[bool] = mapped_column(Boolean, nullable=True)

    # LLM outputs
    llm_persona: Mapped[str] = mapped_column(String(64), nullable=True)
    llm_risk_band: Mapped[str] = mapped_column(String(32), nullable=True)
    llm_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    llm_summary: Mapped[str] = mapped_column(Text, nullable=True)

    # Risk scores
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    propensity_score: Mapped[float] = mapped_column(Float, nullable=True)
    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    session: Mapped["VideoSession"] = relationship(back_populates="application")
    offers: Mapped[list["LoanOffer"]] = relationship(back_populates="application")


class LoanOffer(Base):
    __tablename__ = "loan_offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("loan_applications.id"))

    loan_amount: Mapped[float] = mapped_column(Float)
    tenure_months: Mapped[int] = mapped_column()
    annual_interest_rate: Mapped[float] = mapped_column(Float)
    emi: Mapped[float] = mapped_column(Float)
    processing_fee: Mapped[float] = mapped_column(Float, default=0.0)
    offer_type: Mapped[str] = mapped_column(String(32), default="standard")

    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    application: Mapped["LoanApplication"] = relationship(back_populates="offers")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("video_sessions.id"))
    event: Mapped[str] = mapped_column(String(128))
    detail: Mapped[str] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["VideoSession"] = relationship(back_populates="audit_logs")
