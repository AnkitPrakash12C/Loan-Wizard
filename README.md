# Poonawalla Fincorp Loan Wizard
## Agentic AI Video Call–Based Onboarding System

---

## Project Structure

```
loan-wizard/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── routers/
│   │   ├── session.py           # Video session management
│   │   ├── stt.py               # Speech-to-Text endpoints
│   │   ├── vision.py            # Computer Vision (age estimation)
│   │   ├── risk.py              # Risk & Policy evaluation
│   │   ├── offer.py             # Loan offer generation
│   │   └── audit.py             # Logging & audit trail
│   ├── services/
│   │   ├── stt_service.py       # STT logic (Whisper / Deepgram)
│   │   ├── vision_service.py    # Age estimation (DeepFace / OpenCV)
│   │   ├── llm_service.py       # LLM intelligence layer (Claude)
│   │   ├── risk_service.py      # Risk scoring logic
│   │   └── offer_service.py     # Offer computation
│   ├── models/
│   │   ├── session.py           # Session DB model
│   │   ├── application.py       # Loan application model
│   │   └── offer.py             # Offer model
│   ├── database.py              # SQLAlchemy setup
│   └── config.py                # Settings
├── frontend/
│   ├── index.html               # Entry page
│   ├── video_call.html          # Video call UI
│   └── offer.html               # Offer display
├── ml/
│   ├── risk_model.py            # ML risk model
│   └── propensity_model.py      # Propensity scoring
├── config/
│   └── policy.json              # Loan policy rules
├── scripts/
│   └── seed_db.py               # DB seeding script
├── tests/
│   └── test_api.py              # Basic test suite
├── requirements.txt
├── .env.example
└── docker-compose.yml
```

## Setup Instructions

### 1. Clone & navigate
```bash
cd loan-wizard
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 5. Initialize database
```bash
python scripts/seed_db.py
```

### 6. Run the server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 7. Open browser
```
http://localhost:8000
```
