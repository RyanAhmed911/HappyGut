"""Tracing: one meal check is one trace, model calls nest under it, and photos and names never leave."""

from __future__ import annotations

import anyio
import pytest
from conftest import FIXTURE_SEEDS
from happygut_engine import Diagnosis, DiseaseState
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic_ai.models.test import TestModel

from happygut_api import tracing
from happygut_api.agents import PydanticExplainer, PydanticPerceiver
from happygut_api.flow import MealCheckFlow
from happygut_api.knowledge import MemoryKnowledge
from happygut_api.pii import Scrubber
from happygut_api.prompts import load_prompt
from happygut_api.settings import Settings
from happygut_api.store import MemoryStore, Patient

PROMPTS = Settings().prompts_dir


@pytest.fixture
def exporter():
    exp = InMemorySpanExporter()
    assert tracing.setup("", "", "", environment="test", version="t", exporter=exp)
    yield exp
    tracing.shutdown()


def run_check(text: str) -> list:
    knowledge = MemoryKnowledge.from_seeds(FIXTURE_SEEDS)
    flow = MealCheckFlow(
        knowledge,
        PydanticPerceiver(TestModel(custom_output_args={"is_food": True, "items": [{"name_en": "kacchi biryani", "confidence": 0.9}]}),
                          load_prompt(PROMPTS, "meal-perception")),
        PydanticExplainer(TestModel(), load_prompt(PROMPTS, "meal-explanation")),
        Scrubber(), MemoryStore())
    patient = Patient("patient-trace", Diagnosis.CD, DiseaseState.REMISSION, frozenset(), "en", is_synthetic=True)

    async def go():
        return [e async for e in flow.stream(patient, "en", text, None)]
    return anyio.run(go)


def test_off_without_keys():
    assert tracing.setup("", "", "https://cloud.langfuse.com", environment="test", version="t") is False
    assert not tracing.enabled()


def test_langfuse_endpoint_and_basic_auth():
    assert tracing.endpoint("https://cloud.langfuse.com/") == "https://cloud.langfuse.com/api/public/otel/v1/traces"
    assert tracing.auth_header("pk-lf-1", "sk-lf-2") == "Basic cGstbGYtMTpzay1sZi0y"


def test_a_meal_check_is_one_trace_with_model_calls_inside(exporter):
    events = run_check("My name is Rahim Uddin, I ate kacchi biryani")
    assert events[-1].name == "done"
    spans = exporter.get_finished_spans()
    root = next(s for s in spans if s.name == "meal_check")
    assert root.parent is None
    a = root.attributes
    assert a["happygut.input_type"] == "text" and a["happygut.verdict"] and a["happygut.engine_version"].startswith("engine-")
    assert a["happygut.meal_check_id"] == events[-1].data["meal_check_id"] and a["happygut.total_ms"] >= 0
    assert a["langfuse.user.id"] == tracing.pseudonym("patient-trace") and "patient-trace" not in str(dict(a))
    assert {e.name for e in root.events} >= {"step:scrub", "step:perceive", "step:decide", "step:store"}
    children = [s for s in spans if s is not root and s.context.trace_id == root.context.trace_id]
    assert children, "model calls nest under the meal check"
    # The name was scrubbed before the model call, so it can't appear anywhere in the trace.
    everything = " ".join(str(dict(s.attributes or {})) for s in spans)
    assert "Rahim" not in everything


def test_tracing_off_changes_nothing():
    tracing.shutdown()
    assert run_check("kacchi biryani")[-1].name == "done"
