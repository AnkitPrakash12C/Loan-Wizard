"""
backend/main.py
FastAPI application – entry point
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from loguru import logger
from pathlib import Path

from backend.database import create_tables
from backend.routers import session, stt, vision, risk, offer, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Loan Wizard …")
    await create_tables()
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Poonawalla Fincorp – Loan Wizard",
    description="Agentic AI Video Call–Based Onboarding System",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────────────────────
app.include_router(session.router, prefix="/api/session", tags=["Session"])
app.include_router(stt.router,     prefix="/api/stt",     tags=["STT"])
app.include_router(vision.router,  prefix="/api/vision",  tags=["Vision"])
app.include_router(risk.router,    prefix="/api/risk",    tags=["Risk"])
app.include_router(offer.router,   prefix="/api/offer",   tags=["Offer"])
app.include_router(audit.router,   prefix="/api/audit",   tags=["Audit"])

# ── Serve frontend ────────────────────────────────────────────────
FRONTEND = Path(__file__).parent.parent / "frontend"
if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(str(FRONTEND / "index.html"))

    @app.get("/call", include_in_schema=False)
    async def call_page():
        return FileResponse(str(FRONTEND / "video_call.html"))

    @app.get("/offer-result", include_in_schema=False)
    async def offer_page():
        return FileResponse(str(FRONTEND / "offer.html"))
