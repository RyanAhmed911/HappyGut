"""End-to-end meal check through the HTTP API with fake model agents."""

from __future__ import annotations

import io

from PIL import Image

from conftest import FakeExplainer, FakePerceiver, auth, events, perception
from happygut_api.agents import DishExplanation, Explanation


def names(evts):
    return [e for e, _ in evts]


def test_health(make_client):
    with make_client() as c:
        r = c.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["knowledge"] == {"dishes": 4, "rule_cards": 2, "reviewed_only": True}


def test_auth_required(make_client, issuer):
    with make_client() as c:
        assert c.post("/v1/meal-checks", data={"text": "kacchi"}).status_code == 401
        bad = {"Authorization": "Bearer " + issuer.token("user-flare", aud="anon")}
        assert c.post("/v1/meal-checks", data={"text": "kacchi"}, headers=bad).status_code == 401
        assert c.post("/v1/meal-checks", data={"text": "kacchi"}, headers=auth(issuer, "nobody")).status_code == 404


def test_text_meal_check_streams_stages_in_order(make_client, issuer, store):
    with make_client() as c:
        r = c.post("/v1/meal-checks", data={"text": "I had kacchi for lunch"}, headers=auth(issuer))
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    evts = events(r.text)
    assert names(evts) == ["dishes", "verdict", "explanation", "done"]
    dishes, verdict, explanation, done = (d for _, d in evts)
    assert dishes["dishes"][0]["dish_id"] == "dish.kacchi_biryani"
    # Flare + high fat → the guideline rule applies; the engine decides, not the model.
    assert verdict["verdict"] in {"caution", "likely_trigger"}
    assert "RC-TEST-FAT-FLARE" in verdict["dishes"][0]["evidence_ids"]
    assert verdict["dishes"][0]["alternative"]["dish_id"] in {"dish.murgir_patla_jhol", "dish.plain_rice"}
    assert explanation["source"] == "model"
    assert explanation["dishes"][0]["citations"]
    record = store.meal_checks[done["meal_check_id"]]
    assert record.verdict == verdict["verdict"]
    assert record.model_versions == {"perception": "fake-vision", "explanation": "fake-writer"}
    assert record.prompt_versions == {"perception": "meal-perception@v1", "explanation": "meal-explanation@v1"}
    assert record.engine_version and record.is_synthetic


def test_same_dish_differs_by_profile(make_client, issuer):
    with make_client() as c:
        calm = events(c.post("/v1/meal-checks", data={"text": "kacchi"}, headers=auth(issuer, "user-calm")).text)
        flare = events(c.post("/v1/meal-checks", data={"text": "kacchi"}, headers=auth(issuer, "user-flare")).text)
    calm_v = dict(calm)["verdict"]["verdict"]
    flare_v = dict(flare)["verdict"]["verdict"]
    assert calm_v == "likely_ok" and flare_v != "likely_ok"


def test_stricturing_hard_rule_in_bangla(make_client, issuer):
    with make_client(FakePerceiver(perception(("shak bhaji", 0.9)))) as c:
        evts = dict(events(c.post("/v1/meal-checks", data={"text": "শাক ভাজি"}, headers=auth(issuer, "user-strict")).text))
    v = evts["verdict"]
    assert v["verdict"] == "likely_trigger" and v["dishes"][0]["reason"] == "hard_rule"
    assert v["label"] == "আপনার জন্য সম্ভবত সমস্যা করবে"
    assert v["dishes"][0]["name"] == "শাক ভাজি"


def test_red_flag_stops_everything(make_client, issuer, store):
    perceiver, explainer = FakePerceiver(perception(("kacchi", 0.9))), FakeExplainer()
    with make_client(perceiver, explainer) as c:
        r = c.post("/v1/meal-checks", data={"text": "ate kacchi, now heavy blood in stool"}, headers=auth(issuer))
    evts = events(r.text)
    assert names(evts) == ["red_flag"]
    assert "heavy_bleeding" in evts[0][1]["categories"]
    assert perceiver.calls == [] and explainer.packets == []  # no model saw the text
    assert store.red_flags == [("p-flare", ["heavy_bleeding"])]
    assert store.meal_checks == {}


def test_pii_is_scrubbed_before_the_model(make_client, issuer, store):
    perceiver = FakePerceiver(perception(("kacchi", 0.9)))
    with make_client(perceiver) as c:
        c.post("/v1/meal-checks", data={"text": "my name is Rahim Uddin, call 01712345678. I had kacchi"}, headers=auth(issuer))
    sent = perceiver.calls[0]["text"]
    assert "Rahim" not in sent and "01712345678" not in sent and "<PHONE>" in sent and "kacchi" in sent
    assert "Rahim" not in next(iter(store.meal_checks.values())).input_text


def test_photo_without_food(make_client, issuer, store):
    img = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(img, format="PNG")
    with make_client(FakePerceiver(perception(is_food=False))) as c:
        r = c.post("/v1/meal-checks", files={"image": ("x.png", img.getvalue(), "image/png")}, headers=auth(issuer))
    assert names(events(r.text)) == ["not_food"]
    assert store.meal_checks == {}


def test_bad_upload_rejected(make_client, issuer):
    with make_client() as c:
        r = c.post("/v1/meal-checks", files={"image": ("x.jpg", b"not an image", "image/jpeg")}, headers=auth(issuer))
        assert r.status_code == 422 and r.json()["detail"] == "not_an_image"
        assert c.post("/v1/meal-checks", data={}, headers=auth(issuer)).status_code == 422


def test_unknown_dish_is_not_sure_with_question(make_client, issuer):
    with make_client(FakePerceiver(perception(("mystery stew", 0.8)))) as c:
        evts = dict(events(c.post("/v1/meal-checks", data={"text": "mystery stew"}, headers=auth(issuer)).text))
    assert evts["dishes"]["dishes"][0]["resolved"] is False
    assert evts["verdict"]["verdict"] == "not_sure"
    assert evts["verdict"]["clarifying_question"]
    assert evts["explanation"]["source"] == "template"
    assert "mystery stew" in evts["explanation"]["dishes"][0]["text"]


def test_low_confidence_photo_is_not_sure(make_client, issuer):
    with make_client(FakePerceiver(perception(("kacchi biryani", 0.3), question="Is this beef or mutton?"))) as c:
        evts = dict(events(c.post("/v1/meal-checks", data={"text": "kacchi"}, headers=auth(issuer)).text))
    assert evts["verdict"]["verdict"] == "not_sure"
    assert evts["verdict"]["clarifying_question"] == "Is this beef or mutton?"


def test_guard_rejects_twice_then_template(make_client, issuer):
    bad = Explanation(dishes=[DishExplanation(dish_id="dish.kacchi_biryani", text="This is safe for you.",
                                              cited_ids=["dish:dish.kacchi_biryani"])], summary="ok")
    explainer = FakeExplainer([bad, bad])
    with make_client(explainer=explainer) as c:
        evts = dict(events(c.post("/v1/meal-checks", data={"text": "kacchi"}, headers=auth(issuer)).text))
    assert len(explainer.packets) == 2
    exp = evts["explanation"]
    assert exp["source"] == "template" and "safe" not in exp["dishes"][0]["text"].lower()
    assert "RC-TEST-FAT-FLARE" in exp["dishes"][0]["cited_ids"]


def test_model_outage_still_completes(make_client, issuer):
    with make_client(FakePerceiver(error=RuntimeError("quota")), FakeExplainer(error=RuntimeError("quota"))) as c:
        evts = events(c.post("/v1/meal-checks", data={"text": "kacchi khabo"}, headers=auth(issuer)).text)
    assert names(evts) == ["dishes", "verdict", "explanation", "done"]
    assert dict(evts)["dishes"]["dishes"][0]["dish_id"] == "dish.kacchi_biryani"
    assert dict(evts)["explanation"]["source"] == "template"


def test_photo_outage_reports_error(make_client, issuer):
    img = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(img, format="JPEG")
    with make_client(FakePerceiver(error=RuntimeError("quota"))) as c:
        r = c.post("/v1/meal-checks", files={"image": ("x.jpg", img.getvalue(), "image/jpeg")}, headers=auth(issuer))
    assert events(r.text) == [("error", {"code": "perception_unavailable"})]


def test_get_and_feedback(make_client, issuer):
    with make_client() as c:
        done = dict(events(c.post("/v1/meal-checks", data={"text": "kacchi"}, headers=auth(issuer)).text))["done"]
        mid = done["meal_check_id"]
        got = c.get(f"/v1/meal-checks/{mid}", headers=auth(issuer))
        assert got.status_code == 200 and got.json()["id"] == mid
        assert c.get(f"/v1/meal-checks/{mid}", headers=auth(issuer, "user-calm")).status_code == 404  # other patient
        assert c.post(f"/v1/meal-checks/{mid}/feedback", json={"answer": "right"}, headers=auth(issuer)).status_code == 201
        assert c.post(f"/v1/meal-checks/{mid}/feedback", json={"answer": "maybe"}, headers=auth(issuer)).status_code == 422
