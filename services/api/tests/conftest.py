"""Shared fixtures: fixture seeds, fake model agents, an in-memory store and a local ES256 JWT issuer."""

from __future__ import annotations

import json
import time
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from happygut_engine import Diagnosis, DiseaseState
from happygut_api.agents import AgentRun, DishExplanation, Explanation, PerceivedItem, Perception
from happygut_api.auth import SupabaseVerifier
from happygut_api.flow import MealCheckFlow
from happygut_api.knowledge import MemoryKnowledge
from happygut_api.main import Services, create_app
from happygut_api.pii import Scrubber
from happygut_api.settings import Settings
from happygut_api.store import MemoryStore, Patient

FIXTURE_SEEDS = Path(__file__).parent / "fixtures" / "seeds"
SUPABASE_URL = "https://test.supabase.co"


class FakePerceiver:
    def __init__(self, perception: Perception | None = None, error: Exception | None = None):
        self.perception = perception
        self.error = error
        self.calls: list[dict] = []

    async def perceive(self, *, text, image, lang):
        self.calls.append({"text": text, "image": image, "lang": lang})
        if self.error:
            raise self.error
        return AgentRun(self.perception, "fake-vision", "meal-perception@v1")


class FakeExplainer:
    """Returns queued explanations in order; ``None`` in the queue means "write a valid one from the packet"."""

    def __init__(self, queue: list | None = None, error: Exception | None = None):
        self.queue = list(queue or [None])
        self.error = error
        self.packets: list[dict] = []

    async def explain(self, *, packet, lang, diagnosis):
        self.packets.append(packet)
        if self.error:
            raise self.error
        item = self.queue.pop(0) if self.queue else None
        if item is None:
            text = {"en": "This dish is rich in ghee and meat.", "bn": "এই খাবারে ঘি ও মাংস বেশি।"}[lang]
            item = Explanation(
                dishes=[DishExplanation(dish_id=d["dish_id"], text=text, cited_ids=[d["evidence"][0]["id"]])
                        for d in packet["dishes"]],
                summary={"en": "Here is why.", "bn": "এর কারণ নিচে দেওয়া হলো।"}[lang],
            )
        return AgentRun(item, "fake-writer", "meal-explanation@v1")


def perception(*items: tuple[str, float], is_food: bool = True, question: str | None = None) -> Perception:
    return Perception(is_food=is_food, items=[PerceivedItem(name_en=n, confidence=c) for n, c in items],
                      clarifying_question=question)


class Issuer:
    def __init__(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.kid = "test-key"

    def token(self, sub: str, **overrides) -> str:
        claims = {"sub": sub, "aud": "authenticated", "iss": f"{SUPABASE_URL}/auth/v1", "exp": int(time.time()) + 600,
                  "role": "authenticated", **overrides}
        return jwt.encode(claims, self.key, algorithm="ES256", headers={"kid": self.kid})

    def jwks_client(self):
        public = jwt.PyJWK(json.loads(jwt.algorithms.ECAlgorithm.to_jwk(self.key.public_key())) | {"kid": self.kid, "alg": "ES256"})

        class Client:
            def get_signing_key_from_jwt(self_inner, token):
                header = jwt.get_unverified_header(token)
                if header.get("kid") != self.kid:
                    raise jwt.PyJWKClientError("unknown kid")
                return public

        return Client()


@pytest.fixture
def issuer() -> Issuer:
    return Issuer()


@pytest.fixture
def knowledge() -> MemoryKnowledge:
    return MemoryKnowledge.from_seeds(FIXTURE_SEEDS)


@pytest.fixture
def store() -> MemoryStore:
    s = MemoryStore()
    s.patients["user-flare"] = Patient("p-flare", Diagnosis.CD, DiseaseState.FLARE, frozenset(), "en", is_synthetic=True)
    s.patients["user-strict"] = Patient("p-strict", Diagnosis.CD, DiseaseState.REMISSION, frozenset({"stricturing"}), "bn",
                                        is_synthetic=True)
    s.patients["user-calm"] = Patient("p-calm", Diagnosis.UC, DiseaseState.REMISSION, frozenset(), "en", is_synthetic=True)
    return s


@pytest.fixture
def make_client(knowledge, store, issuer):
    def make(perceiver=None, explainer=None):
        perceiver = perceiver or FakePerceiver(perception(("kacchi biryani", 0.9)))
        explainer = explainer or FakeExplainer()
        flow = MealCheckFlow(knowledge, perceiver, explainer, Scrubber(), store)
        settings = Settings(supabase_url=SUPABASE_URL, seeds_dir=FIXTURE_SEEDS, cors_origins=["http://localhost:5173"])
        services = Services(settings, knowledge, store, SupabaseVerifier(SUPABASE_URL, jwks_client=issuer.jwks_client()), flow)
        return TestClient(create_app(services))

    return make


def auth(issuer: Issuer, user: str = "user-flare") -> dict:
    return {"Authorization": f"Bearer {issuer.token(user)}"}


def events(body: str) -> list[tuple[str, dict]]:
    out = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out
