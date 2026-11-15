"""Spec 003 through the HTTP API in demo mode: diary, stressful periods, insights, report."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from conftest import FIXTURE_SEEDS, events
from happygut_api.agents import Unavailable
from happygut_api.demo import DemoVerifier
from happygut_api.flow import MealCheckFlow
from happygut_api.knowledge import MemoryKnowledge
from happygut_api.main import Services, create_app
from happygut_api.pii import Scrubber
from happygut_api.settings import Settings
from happygut_api.store import MemoryStore, PostgresStore


@pytest.fixture(scope="module")
def demo():
    """One seeded demo app for the module (seeding runs the simulator and the Pattern Finder)."""
    knowledge = MemoryKnowledge.from_seeds(FIXTURE_SEEDS)
    store = MemoryStore()
    verifier = DemoVerifier()
    flow = MealCheckFlow(knowledge, Unavailable(), Unavailable(), Scrubber(), store)
    services = Services(Settings(seeds_dir=FIXTURE_SEEDS, demo_mode=True), knowledge, store, verifier, flow, demo=verifier,
                        models={"perception": False, "explanation": False})
    with TestClient(create_app(services)) as client:
        token = client.post("/v1/demo/login").json()["token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client, services


def today_of(client) -> date:
    return date.fromisoformat(client.get("/v1/diary/days?limit=1").json()["today"])


def test_demo_login_and_profile(demo):
    client, _ = demo
    me = client.get("/v1/me").json()
    assert me["is_synthetic"] is True and me["display_name"] == "Nusrat" and me["diagnosis"] == "CD"
    assert client.get("/v1/health").json()["demo_mode"] is True
    assert client.patch("/v1/me", json={"language": "en", "reminder_time": "21:45"}).json()["reminder_time"] == "21:45"
    assert client.patch("/v1/me", json={"reminder_time": "25:00"}).status_code == 422


def test_demo_login_is_off_outside_demo_mode(make_client):
    with make_client() as c:
        assert c.post("/v1/demo/login").status_code == 404


def test_persona_history_periods_and_patterns(demo):
    client, _ = demo
    days = client.get("/v1/diary/days").json()
    assert days["is_synthetic"] and len(days["days"]) >= 100
    assert date.fromisoformat(days["days"][-1]["date"]) == today_of(client) - timedelta(days=1)

    periods = client.get("/v1/insights/periods").json()
    flares = [p for p in periods["periods"] if p["kind"] == "flare"]
    assert len(flares) == 2 and all(p["status"] == "confirmed" for p in flares)
    assert periods["current_state"] == "remission" and periods["pending"] == []
    assert periods["summaries"]["flare"]["avg_index"] > periods["summaries"]["remission"]["avg_index"] + 3
    assert len(periods["before_flares"]) == 2

    patterns = client.get("/v1/insights/patterns").json()
    by = {r["factor"]: r for r in patterns["results"]}
    assert patterns["enough_data"] and by["food:fat"]["label"] == "likely_contributor"  # injected truth
    assert by["sleep:late_night"]["label"] in {"likely_contributor", "possible"}
    assert by["period:exam"]["avg_index_exposed"] > by["period:exam"]["avg_index_unexposed"]
    assert by["food:capsaicin_spice"]["label"] != "likely_contributor"  # no injected effect
    assert client.get("/v1/insights/patterns?scope=flare").json()["scope"] == "flare"
    assert client.get("/v1/insights/patterns?scope=nope").status_code == 422


def test_flare_risk_names_drivers_and_the_upcoming_exam(demo):
    client, _ = demo
    risk = client.get("/v1/insights/flare-risk").json()
    assert risk["enough_data"] and risk["level"] in {"raised", "high"}
    assert risk["score"] == min(100, sum(d["points"] for d in risk["drivers"]))
    assert risk["upcoming_periods"][0]["type"] == "exam" and risk["upcoming_periods"][0]["days_until"] == 3


def test_meal_check_uses_learned_evidence_without_any_model(demo):
    client, _ = demo
    r = client.post("/v1/meal-checks", data={"text": "kacchi and plain rice", "lang": "en"})
    evts = dict(events(r.text))
    dishes = {d["dish_id"]: d for d in evts["verdict"]["dishes"]}
    assert set(dishes) == {"dish.kacchi_biryani", "dish.plain_rice"}  # the sentence was split without a model
    assert dishes["dish.kacchi_biryani"]["verdict"] == "likely_trigger" and dishes["dish.kacchi_biryani"]["reason"] == "personal"
    assert dishes["dish.plain_rice"]["verdict"] == "likely_ok"
    assert evts["explanation"]["source"] == "template"
    assert "personal:fat" in evts["explanation"]["dishes"][0]["cited_ids"]


def test_diary_prefill_save_and_index(demo):
    client, _ = demo
    day = today_of(client).isoformat()
    before = client.get(f"/v1/diary/{day}").json()
    assert before["entry"] is None and before["editable"] and before["usual"]["bedtime"]
    prefill = before["prefill"]
    assert {f["dish_id"] for f in prefill} >= {"dish.kacchi_biryani", "dish.plain_rice"}  # from the meal check above

    foods = [dict(f, reactions=["stomach_ache"]) if f["dish_id"] == "dish.kacchi_biryani" else f for f in prefill]
    body = {"foods": foods, "stool": {"count": 4, "bristol": 6, "urgency": "hurry"}, "pain": 2, "wellbeing": 2,
            "medication": "taken", "notes": "Wedding dinner. My name is Rahim Uddin, 01712345678",
            "sleep": {"bedtime": "02:40", "wake_time": "08:10", "quality": "poor"}, "stress": 3}
    saved = client.put(f"/v1/diary/{day}?lang=en", json=body).json()
    entry = saved["entry"]
    assert entry["index"] == {"name": "HBI", "score": 8, "parts": {"wellbeing": 2, "abdominal_pain": 2, "liquid_stools": 4,
                                                                 "abdominal_mass": 0, "complications": 0}}
    assert entry["sleep_hours"] == 5.5 and entry["late_night"] is True and entry["completed_late"] is False
    assert "Rahim" not in entry["notes"] and "<PHONE>" in entry["notes"]
    assert saved["red_flag"] is None and saved["comparison"]["delta"] == 8 - saved["comparison"]["usual"]

    after = client.get(f"/v1/diary/{day}").json()
    assert after["entry"]["index"]["score"] == 8 and after["prefill"] == []  # not offered twice
    assert client.get("/v1/diary/days?limit=1").json()["days"][0]["food_reaction"] is True


def test_diary_date_rules(demo):
    client, _ = demo
    today = today_of(client)
    assert client.put(f"/v1/diary/{today + timedelta(days=1)}", json={}).status_code == 422
    assert client.put(f"/v1/diary/{today - timedelta(days=3)}", json={}).status_code == 422
    late = client.put(f"/v1/diary/{today - timedelta(days=2)}", json={"pain": 1}).json()
    assert late["entry"]["completed_late"] is True
    assert client.get(f"/v1/diary/{today - timedelta(days=30)}").json()["editable"] is False
    assert client.put(f"/v1/diary/{today}", json={"stool": {"count": 1, "bristol": 9}}).status_code == 422


@pytest.mark.parametrize("body,category", [
    ({"stool": {"count": 5, "blood": "a_lot"}}, "heavy_bleeding"),
    ({"pain": 2, "signs": {"fever": True}}, "fever_with_abdominal_pain"),
    ({"pain": 1, "signs": {"vomiting": True, "no_stool_or_gas": True}}, "possible_obstruction"),
    ({"signs": {"dizzy_or_little_urine": True}}, "severe_dehydration"),
    ({"notes": "পায়খানার সাথে অনেক রক্ত যাচ্ছে"}, "heavy_bleeding"),
])
def test_diary_red_flags_stop_feedback_and_are_stored(demo, body, category):
    client, services = demo
    day = (today_of(client) - timedelta(days=1)).isoformat()
    before = len(services.store.red_flags)
    out = client.put(f"/v1/diary/{day}?lang=bn", json=body).json()
    assert category in out["red_flag"]["categories"] and out["comparison"] is None
    assert out["red_flag"]["title"] == "এখনই চিকিৎসকের সাহায্য নিন"
    assert out["entry"]["red_flags"] and len(services.store.red_flags) == before + 1  # what was entered is still saved


def test_stress_periods_tag_diary_days(demo):
    client, _ = demo
    today = today_of(client)
    created = client.post("/v1/stress-periods", json={"type": "work", "name": "Deadline", "start": str(today - timedelta(days=1)),
                                                      "end": str(today + timedelta(days=2))})
    assert created.status_code == 201
    pid = created.json()["id"]
    assert any(t["id"] == pid for t in client.get(f"/v1/diary/{today}").json()["tags"])
    assert "work" in client.get("/v1/diary/days?limit=2").json()["days"][0]["tags"]
    bad = {"type": "work", "name": "x", "start": str(today), "end": str(today - timedelta(days=1))}
    assert client.post("/v1/stress-periods", json=bad).status_code == 422
    assert client.delete(f"/v1/stress-periods/{pid}").status_code == 204
    assert client.delete(f"/v1/stress-periods/{pid}").status_code == 404


def test_user_decisions_on_periods_win(demo):
    client, _ = demo
    periods = client.get("/v1/insights/periods").json()
    first_flare = next(p for p in periods["periods"] if p["kind"] == "flare")
    after = client.post("/v1/insights/periods/decision", json={"start": first_flare["start"], "decision": "reject"}).json()
    assert all(p["start"] != first_flare["start"] or p["kind"] != "flare" for p in after["periods"])
    assert client.post("/v1/insights/periods/decision", json={"start": "2020-01-01", "decision": "confirm"}).status_code == 404
    manual = client.post("/v1/insights/periods/manual", json={"start": first_flare["start"], "end": first_flare["end"]}).json()
    restored = next(p for p in manual["periods"] if p["start"] == first_flare["start"])
    assert restored["kind"] == "flare" and restored["source"] == "user" and restored["status"] == "confirmed"


def test_previsit_report(demo):
    client, _ = demo
    report = client.get("/v1/reports/previsit?days=60").json()
    assert report["is_synthetic"] and report["patient"]["diagnosis"] == "CD" and report["index_name"] == "HBI"
    assert report["adherence"]["logged"] >= report["adherence"]["missed"] >= 1
    assert report["contributors"] and len(report["series"]) == report["days_logged"]
    assert sum(report["meal_verdicts"].values()) >= 1


def test_history_and_food_search(demo):
    client, _ = demo
    items = client.get("/v1/meal-checks?limit=50").json()["items"]
    assert len(items) >= 5 and items[0]["created_at"] >= items[-1]["created_at"]
    results = client.get("/v1/foods/search", params={"q": "kachchi"}).json()["results"]
    assert results[0]["dish_id"] == "dish.kacchi_biryani" and results[0]["name_bn"] == "কাচ্চি বিরিয়ানি"


def test_storage_without_spec_003_tables_answers_501(issuer, store):
    from conftest import SUPABASE_URL, auth
    from happygut_api.auth import SupabaseVerifier

    class WithoutDiaryTables(PostgresStore):
        def __init__(self, inner):
            self.inner = inner

        async def patient_for_user(self, user_id):
            return await self.inner.patient_for_user(user_id)

    partial = WithoutDiaryTables(store)
    knowledge = MemoryKnowledge.from_seeds(FIXTURE_SEEDS)
    flow = MealCheckFlow(knowledge, Unavailable(), Unavailable(), Scrubber(), partial)
    services = Services(Settings(supabase_url=SUPABASE_URL, seeds_dir=FIXTURE_SEEDS), knowledge, partial,
                        SupabaseVerifier(SUPABASE_URL, jwks_client=issuer.jwks_client()), flow)
    with TestClient(create_app(services)) as c:
        r = c.get("/v1/insights/patterns", headers=auth(issuer))
        assert r.status_code == 501 and r.json()["detail"].startswith("not_available_on_this_storage")
        assert c.get("/v1/me", headers=auth(issuer)).json()["state"] == "flare"  # falls back to the stored profile


def test_food_guide_and_plan_follow_the_profile(demo):
    client, _ = demo
    client.patch("/v1/me", json={"phenotypes": []})
    guide = {d["dish_id"]: d for d in client.get("/v1/foods/guide").json()["items"]}
    assert guide["dish.kacchi_biryani"]["verdict"] == "likely_trigger"  # her learned fat trigger
    assert guide["dish.kacchi_biryani"]["components"][0] == {"component": "fat", "level": "high", "source": "personal"}
    assert guide["dish.plain_rice"]["verdict"] == "likely_ok" and guide["dish.shak_bhaji"]["verdict"] == "likely_ok"

    plan = client.get("/v1/foods/plan").json()
    assert plan["enough"] and len(plan["days"]) == 7
    ok = {d for d, v in guide.items() if v["verdict"] == "likely_ok"}
    used = {i["dish_id"] for day in plan["days"] for meal in day["meals"].values() for i in meal}
    assert used and used <= ok  # every idea is rated "likely OK" by the engine
    assert plan == client.get("/v1/foods/plan").json()  # stable within the week

    # A stricture changes the same dishes for the same person (the hard safety rule).
    me = client.patch("/v1/me", json={"phenotypes": ["stricturing"]}).json()
    assert me["phenotypes"] == ["stricturing"]
    strict = {d["dish_id"]: d for d in client.get("/v1/foods/guide").json()["items"]}
    assert strict["dish.shak_bhaji"]["verdict"] == "likely_trigger" and strict["dish.shak_bhaji"]["reason"] == "hard_rule"
    used = {i["dish_id"] for day in client.get("/v1/foods/plan").json()["days"] for meal in day["meals"].values() for i in meal}
    assert "dish.shak_bhaji" not in used
    assert client.patch("/v1/me", json={"phenotypes": ["made_up"]}).status_code == 422
    client.patch("/v1/me", json={"phenotypes": []})


def test_changing_the_diagnosis_rescores_the_diary(demo):
    client, _ = demo
    assert client.get("/v1/insights/periods").json()["index_name"] == "HBI"
    assert client.patch("/v1/me", json={"diagnosis": "UC"}).json()["diagnosis"] == "UC"
    periods = client.get("/v1/insights/periods").json()
    assert periods["index_name"] == "SCCAI"
    day = client.get(f"/v1/diary/{periods['periods'][0]['start']}").json()["entry"]
    assert day["index"]["name"] == "SCCAI"
    client.patch("/v1/me", json={"diagnosis": "CD"})
    assert client.get("/v1/insights/periods").json()["index_name"] == "HBI"
