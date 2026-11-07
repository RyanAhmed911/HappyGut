"""Unit tests: PII scrubber, image sanitiser, prompts, guard, locales, agents, auth."""

from __future__ import annotations

import asyncio
import io
import time

import pytest
from PIL import Image

from conftest import FIXTURE_SEEDS, SUPABASE_URL, Issuer
from happygut_api import guard, i18n
from happygut_api.agents import (DishExplanation, Explanation, Perception, PydanticPerceiver, build_model)
from happygut_api.auth import AuthError, SupabaseVerifier
from happygut_api.images import ImageRejected, sanitise
from happygut_api.pii import Scrubber, bengali_ner_detector
from happygut_api.prompts import load_prompt
from happygut_api.settings import REPO_ROOT

PROMPTS = REPO_ROOT / "prompts" / "runtime"


# ---------------------------------------------------------------- PII

@pytest.mark.parametrize("text,label", [
    ("call me on 01712345678 tonight", "PHONE"),
    ("নম্বর ০১৭১২৩৪৫৬৭৮", "PHONE"),
    ("+880 1712-345678", "PHONE"),
    ("NID 1234567890", "ID_NUMBER"),
    ("nid 19901234567890123", "ID_NUMBER"),
    ("mail rahim@example.com", "EMAIL"),
    ("My name is Rahim Uddin", "PERSON"),
    ("আমার নাম রহিম উদ্দিন", "PERSON"),
])
def test_pii_detected(text, label):
    result = Scrubber().scrub(text)
    assert result.found.get(label) == 1, result


@pytest.mark.parametrize("text", [
    "I ate kacchi biryani and 2 roti at 1pm",
    "আজ দুপুরে কাচ্চি খেয়েছি, ২ প্লেট",
    "this is shorshe ilish with plain rice",
    "500 ml borhani",
])
def test_food_text_untouched(text):
    assert Scrubber().scrub(text).text == text


def test_bengali_ner_adapter():
    def fake_pipeline(task, model, aggregation_strategy):
        return lambda text: [{"entity_group": "PER", "start": 0, "end": 4}, {"entity_group": "MISC", "start": 5, "end": 9}]

    detect = bengali_ner_detector("some/model", pipeline_factory=fake_pipeline)
    s = Scrubber([detect], food_words={"কাচ্চি"}).scrub("রহিম কাচ্চি খেয়েছে")
    assert s.text.startswith("<PERSON>") and "কাচ্চি" in s.text
    assert detect("english only") == []
    # A model-detected "name" made only of food words is kept.
    food = Scrubber([lambda t: [(0, 6, "PERSON")]], food_words={"kacchi"}).scrub("kacchi tonight")
    assert food.text == "kacchi tonight"


# ---------------------------------------------------------------- images

def _jpeg_with_gps(size=(3000, 2000)) -> bytes:
    img = Image.new("RGB", size, "orange")
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"
    exif[0x8825] = {2: (23.0, 48.0, 0.0)}  # GPS info
    out = io.BytesIO()
    img.save(out, format="JPEG", exif=exif)
    return out.getvalue()


def test_image_metadata_stripped_and_downscaled():
    raw = _jpeg_with_gps()
    assert Image.open(io.BytesIO(raw)).getexif()
    clean = sanitise(raw, 8_000_000, 1536)
    out = Image.open(io.BytesIO(clean.data))
    assert not out.getexif() and max(out.size) == 1536 and clean.media_type == "image/jpeg"


@pytest.mark.parametrize("raw,code", [(b"", "empty_image"), (b"x" * 20, "not_an_image")])
def test_image_rejected(raw, code):
    with pytest.raises(ImageRejected) as e:
        sanitise(raw, 1000, 100)
    assert e.value.code == code


def test_image_too_large():
    with pytest.raises(ImageRejected) as e:
        sanitise(_jpeg_with_gps(), 100, 100)
    assert e.value.code == "image_too_large"


# ---------------------------------------------------------------- prompts and locales

def test_runtime_prompts_load_and_render():
    p = load_prompt(PROMPTS, "meal-perception")
    assert p.ref == "meal-perception@v1" and "{language}" not in p.render(language="English")
    e = load_prompt(PROMPTS, "meal-explanation")
    text = e.render(packet='{"dishes": []}', language_name="Bangla", diagnosis_text="Crohn's disease")
    assert '{"dishes": []}' in text
    with pytest.raises(KeyError):
        e.render(packet="{}")


def test_locales_have_the_same_keys():
    assert i18n.keys("bn") == i18n.keys("en")


# ---------------------------------------------------------------- guard

def _ctx(knowledge, lang="en"):
    from happygut_engine import Diagnosis, DiseaseState, Profile, assess_meal
    from happygut_api.evidence import DishContext, build_evidence

    ev = knowledge.evidence("dish.kacchi_biryani", 0.9, 1.0)
    meal = assess_meal([ev], Profile(Diagnosis.CD, DiseaseState.FLARE), knowledge.rules(), {}, knowledge.alternatives_pool())
    ctx = DishContext("kacchi", meal.dishes[0], True, "Kacchi biryani", "Light chicken curry")
    ctx.evidence = build_evidence(ctx, knowledge, lang)
    return ctx


def _exp(text, cited=("RC-TEST-FAT-FLARE",), summary="Why it matters."):
    return Explanation(dishes=[DishExplanation(dish_id="dish.kacchi_biryani", text=text, cited_ids=list(cited))], summary=summary)


def test_guard_accepts_grounded_text(knowledge):
    assert guard.check(_exp("Ghee and fatty mutton make it heavy during a flare."), [_ctx(knowledge)], "en").ok


@pytest.mark.parametrize("text,problem", [
    ("It is safe to eat.", "banned"),
    ("Stop your mesalazine before eating.", "banned"),
    ("This is likely trigger for you.", "verdict_label"),
    ("এটি খুব ভারী খাবার।", "language:not_english"),
])
def test_guard_rejects(knowledge, text, problem):
    result = guard.check(_exp(text), [_ctx(knowledge)], "en")
    assert not result.ok and any(p.startswith(problem) for p in result.problems)


def test_guard_rejects_uncited_and_missing(knowledge):
    ctx = _ctx(knowledge)
    assert any(p.startswith("uncited_evidence") for p in guard.check(_exp("Heavy.", cited=["RC-MADE-UP"]), [ctx], "en").problems)
    empty = Explanation(dishes=[], summary="Why.")
    assert "missing:dish.kacchi_biryani" in guard.check(empty, [ctx], "en").problems


def test_template_cites_rule_and_alternative(knowledge):
    exp = guard.template([_ctx(knowledge, "bn")], "bn")
    d = exp.dishes[0]
    assert "RC-TEST-FAT-FLARE" in d.cited_ids and "Light chicken curry" in d.text
    assert guard.check_text(d.text.replace("Light chicken curry", "মুরগির পাতলা ঝোল"), "bn") == []


# ---------------------------------------------------------------- agents

def test_build_model_needs_a_key():
    with pytest.raises(RuntimeError):
        build_model(["gemini-flash-latest", "llama-3.3-70b-versatile"], "", "")
    from pydantic_ai.models.fallback import FallbackModel

    assert isinstance(build_model(["gemini-flash-latest", "llama-3.3-70b-versatile"], "k1", "k2"), FallbackModel)


def test_pydantic_perceiver_returns_typed_output():
    from pydantic_ai.models.test import TestModel

    model = TestModel(custom_output_args={"is_food": True, "items": [{"name_en": "kacchi biryani", "confidence": 0.9}]})
    agent = PydanticPerceiver(model, load_prompt(PROMPTS, "meal-perception"))
    run = asyncio.run(agent.perceive(text="kacchi", image=None, lang="en"))
    assert isinstance(run.output, Perception) and run.output.items[0].name_en == "kacchi biryani"
    assert run.prompt == "meal-perception@v1"


# ---------------------------------------------------------------- auth

def test_verifier():
    iss = Issuer()
    v = SupabaseVerifier(SUPABASE_URL, jwks_client=iss.jwks_client())
    assert v.user_id(iss.token("u1")) == "u1"
    for bad in (iss.token("u1", exp=int(time.time()) - 10), iss.token("u1", iss="https://evil/auth/v1"),
                iss.token("u1", aud="anon"), Issuer().token("u1")):
        with pytest.raises(AuthError):
            v.user_id(bad)


def test_presidio_layer_when_installed():
    pytest.importorskip("presidio_analyzer")
    from happygut_api.pii import presidio_detector

    from happygut_api.knowledge import MemoryKnowledge
    from happygut_api.pii import build_scrubber

    names = MemoryKnowledge.from_seeds(REPO_ROOT / "data" / "seeds", include_drafts=True).all_names()
    s = build_scrubber(presidio=True, food_names=names)
    out = s.scrub("I had kacchi biryani with Rahim Uddin in Mirpur")
    assert "Rahim" not in out.text and "kacchi biryani" in out.text
    assert s.scrub("plain rice, masoor dal and murgir jhol").found == {}
    assert s.scrub("Shorshe ilish, begun bhaja and Mishti doi").found == {}
