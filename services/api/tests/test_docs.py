"""The live /docs page: public payload, the on / off switch and time window, and admin editing."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from happygut_api import docs
from happygut_api.agents import Unavailable
from happygut_api.demo import DemoVerifier
from happygut_api.flow import MealCheckFlow
from happygut_api.knowledge import MemoryKnowledge
from happygut_api.main import Services, create_app
from happygut_api.pii import Scrubber
from happygut_api.settings import Settings
from happygut_api.store import MemoryStore

from conftest import FIXTURE_SEEDS

PASSWORD = secrets.token_urlsafe(16)  # made up for each run


def make_client(**settings) -> TestClient:
    knowledge = MemoryKnowledge.from_seeds(FIXTURE_SEEDS)
    store = MemoryStore()
    flow = MealCheckFlow(knowledge, Unavailable(), Unavailable(), Scrubber(), store)
    services = Services(Settings(seeds_dir=FIXTURE_SEEDS, **settings), knowledge, store, DemoVerifier(), flow,
                        models={"perception": False, "explanation": True})
    return TestClient(create_app(services))


@pytest.fixture
def client():
    with make_client(docs_admin_password=PASSWORD) as c:
        yield c


def admin(client: TestClient) -> dict:
    r = client.post("/v1/docs/admin/login", json={"password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_public_payload_is_live(client):
    body = client.get("/v1/docs").json()
    assert body["available"] and body["reason"] == "open" and not body["preview"]
    live = body["live"]
    assert live["knowledge"]["dishes"] > 0 and live["engine_version"].startswith("engine-")
    paths = {(e["method"], e["path"]): e["access"] for e in live["endpoints"]}
    assert paths[("POST", "/v1/meal-checks")] == "patient" and paths[("GET", "/v1/docs")] == "public"
    assert paths[("PUT", "/v1/docs/admin/settings")] == "docs_admin" and paths[("POST", "/v1/jobs/nightly")] == "job_token"
    assert paths[("POST", "/v1/docs/admin/login")] == "public"
    status = {f["id"]: f["status"] for f in live["features"]}
    assert status["meal_check_photo"] == "off" and status["ai_explanation"] == "live"  # follows the running models
    assert status["neo4j_pgvector"] == "planned"
    assert live["usage"]["accounts"] == 0 and live["flare_model"]["v1"]["roc_auc"] > live["flare_model"]["v0"]["roc_auc"]
    members = body["team"]["members"]
    assert [m["name"] for m in members][0] == "Ryan Ahmed" and body["team"]["name"] == "Cinnamon Syrups"
    assert all(m["role"] and m["role_bn"] and m["email"] and m["photo_url"].startswith("/team/") for m in members)
    assert body["order"]["pitch"][0] == "problem" and body["sections"] == {}


def test_switch_and_window_close_the_page(client):
    headers = admin(client)
    now = datetime.now(UTC)
    off = client.put("/v1/docs/admin/settings", headers=headers, json={"visible": False})
    assert off.status_code == 200 and off.json()["reason"] == "off"
    assert client.get("/v1/docs").status_code == 403
    assert client.get("/v1/docs/status").json() == {"available": False, "reason": "off", "visible": False,
                                                    "starts_at": None, "ends_at": None, "admin": True}
    preview = client.get("/v1/docs", headers=headers).json()  # an admin still sees the page
    assert preview["preview"] and not preview["available"]

    later = {"visible": True, "starts_at": (now + timedelta(days=1)).isoformat(), "ends_at": (now + timedelta(days=2)).isoformat()}
    assert client.put("/v1/docs/admin/settings", headers=headers, json=later).json()["reason"] == "not_yet"
    assert client.get("/v1/docs").status_code == 403
    past = {"visible": True, "starts_at": (now - timedelta(days=2)).isoformat(), "ends_at": (now - timedelta(days=1)).isoformat()}
    assert client.put("/v1/docs/admin/settings", headers=headers, json=past).json()["reason"] == "ended"
    window = {"visible": True, "starts_at": (now - timedelta(hours=1)).isoformat(), "ends_at": (now + timedelta(hours=1)).isoformat()}
    assert client.put("/v1/docs/admin/settings", headers=headers, json=window).json()["reason"] == "open"
    assert client.get("/v1/docs").status_code == 200

    bad = [{"visible": True, "starts_at": now.isoformat(), "ends_at": (now - timedelta(hours=1)).isoformat()},
           {"visible": True, "starts_at": "2026-11-20T00:00:00"}]  # end before start; no time zone
    assert all(client.put("/v1/docs/admin/settings", headers=headers, json=b).status_code == 422 for b in bad)


def test_admin_edits_text_order_and_team(client):
    headers = admin(client)
    r = client.put("/v1/docs/admin/sections/vision", headers=headers, json={"en": "Our vision.", "bn": "আমাদের লক্ষ্য।"})
    assert r.status_code == 200 and r.json()["sections"]["vision"]["bn"] == "আমাদের লক্ষ্য।"
    assert client.get("/v1/docs").json()["sections"]["vision"]["en"] == "Our vision."
    assert client.put("/v1/docs/admin/sections/nope", headers=headers, json={"en": "x", "bn": "y"}).status_code == 404
    assert client.delete("/v1/docs/admin/sections/vision", headers=headers).json()["sections"] == {}

    pitch = list(reversed(docs.PITCH_SECTIONS))
    assert client.put("/v1/docs/admin/order", headers=headers, json={"pitch": pitch, "tech": list(docs.TECH_SECTIONS)}).status_code == 200
    assert client.get("/v1/docs").json()["order"]["pitch"][0] == "vision"
    missing = {"pitch": pitch[1:], "tech": list(docs.TECH_SECTIONS)}
    assert client.put("/v1/docs/admin/order", headers=headers, json=missing).status_code == 422

    team = {"team_name": "Cinnamon Syrups", "members": [{"name": "Ryan Ahmed", "role": "Team Leader", "email": "ryan@example.com"}]}
    body = client.put("/v1/docs/admin/team", headers=headers, json=team).json()
    assert body["team"]["members"] == [{"name": "Ryan Ahmed", "role": "Team Leader", "role_bn": "", "email": "ryan@example.com", "photo_url": ""}]
    for bad_photo in ("http://example.com/a.png", "/etc/passwd", "/team/../a.jpg", "javascript:alert(1)"):
        assert client.put("/v1/docs/admin/team", headers=headers, json={"members": [{"name": "A", "photo_url": bad_photo}]}).status_code == 422
    local = {"members": [{"name": "A", "photo_url": "/team/a-b.jpg"}]}
    assert client.put("/v1/docs/admin/team", headers=headers, json=local).status_code == 200
    history = client.get("/v1/docs/admin", headers=headers).json()["history"]
    assert [h["change"] for h in history][:3] == ["team updated (1 members)"] * 2 + ["section order changed"]


def test_admin_needs_the_password(client):
    assert client.get("/v1/docs/admin").status_code == 401
    assert client.put("/v1/docs/admin/settings", json={"visible": False}).status_code == 401
    assert client.get("/v1/docs/admin", headers={"Authorization": "Bearer forged"}).status_code == 401
    for _ in range(docs.DocsAdmin.MAX_FAILURES):
        assert client.post("/v1/docs/admin/login", json={"password": "wrong"}).status_code == 401
    assert client.post("/v1/docs/admin/login", json={"password": PASSWORD}).status_code == 429  # locked for a while


def test_admin_is_off_without_a_long_password():
    for password in ("", "short"):
        with make_client(docs_admin_password=password) as c:
            assert c.post("/v1/docs/admin/login", json={"password": password or "x"}).status_code == 404
            assert c.get("/v1/docs/status").json()["admin"] is False
            assert c.get("/v1/docs").status_code == 200  # the page itself stays public


def test_window_defaults_come_from_settings():
    start = datetime(2026, 11, 20, tzinfo=UTC)
    with make_client(docs_visible=True, docs_starts_at=start, docs_ends_at=start + timedelta(days=1)) as c:
        status = c.get("/v1/docs/status").json()
        assert status["starts_at"] == start.isoformat() and status["reason"] in ("not_yet", "open", "ended")
