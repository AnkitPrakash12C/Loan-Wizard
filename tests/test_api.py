"""
tests/test_api.py
Basic integration tests using httpx AsyncClient.
Run with:  pytest tests/ -v
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app

@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client():
    # Import here so DB is configured before first request
    from backend.main import app
    from backend.database import create_tables
    await create_tables()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ─── Session tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_session(client):
    resp = await client.post("/api/session/create", json={
        "customer_phone": "9876543210",
        "customer_email": "test@example.com",
        "campaign_id": "CAMP_001",
        "geo_lat": 19.076,
        "geo_lng": 72.877,
        "geo_city": "Mumbai",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["status"] == "initiated"
    return data["id"]


@pytest.mark.asyncio
async def test_full_flow(client):
    """Create session → risk evaluate (no audio, inject data manually)."""
    # 1. Create session
    resp = await client.post("/api/session/create", json={
        "customer_phone": "9999999999",
    })
    assert resp.status_code == 200
    session_id = resp.json()["id"]

    # 2. Get session
    resp2 = await client.get(f"/api/session/{session_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == session_id

    # 3. End session
    resp3 = await client.post(f"/api/session/{session_id}/end")
    assert resp3.status_code == 200
    assert resp3.json()["ok"] is True

    # 4. Check audit trail
    resp4 = await client.get(f"/api/audit/{session_id}")
    assert resp4.status_code == 200
    events = [e["event"] for e in resp4.json()]
    assert "session_created" in events
    assert "session_ended" in events


@pytest.mark.asyncio
async def test_session_not_found(client):
    resp = await client.get("/api/session/nonexistent-id")
    assert resp.status_code == 404
