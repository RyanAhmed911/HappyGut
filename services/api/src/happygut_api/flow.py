"""The meal-check flow as a LangGraph graph (docs/02-architecture.md §2).

sentinel ─┬─ red flag ──► escalate ──► END
          └─ scrub ──► perceive ─┬─ not food ──► END
                                 └─ resolve ──► decide ──► explain ──► store ──► END

Each node returns a state update; ``MealCheckFlow.stream`` turns those updates into the
staged events the client renders: dishes → verdict → explanation → done.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
import re
from typing import Any, AsyncIterator, Awaitable, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from happygut_engine import DEFAULT_CONFIG, DishEvidence, MealVerdict, Verdict, assess_meal, check_red_flags

from . import guard, i18n
from .agents import Explainer, Explanation, PerceivedItem, Perceiver, Perception, describe_error
from .evidence import DishContext, build_evidence, packet
from .images import CleanImage
from .knowledge import Knowledge
from .pii import Scrubber
from .store import MealCheckRecord, Patient, Store

log = logging.getLogger("happygut.flow")


class State(TypedDict, total=False):
    patient: Patient
    lang: str
    text: str | None
    image: CleanImage | None
    red_flags: list[str]
    scrubbed: str | None
    pii_found: dict[str, int]
    perception: Perception | None
    perception_model: str
    perception_prompt: str
    perception_error: str | None
    pending: list  # list[_Pending], after resolve
    contexts: list[DishContext]  # after decide
    meal: MealVerdict
    clarifying_question: str | None
    explanation: Explanation
    explanation_source: str  # model | template
    explanation_model: str
    explanation_prompt: str
    guard_problems: list[str]
    meal_check_id: str


# Separators between dishes in typed text, in English and Bangla.
_SPLIT = re.compile(r"[,;+&\n।]|\band\b|\bwith\b|(?<=\s)(?:ও|আর|এবং|সাথে|সঙ্গে)(?=\s)", re.I)


@dataclass(frozen=True)
class Event:
    name: str
    data: dict[str, Any]


class MealCheckFlow:
    def __init__(self, knowledge: Knowledge, perceiver: Perceiver, explainer: Explainer, scrubber: Scrubber, store: Store,
                 personal: Callable[[Patient], Awaitable[dict]] | None = None):
        self.knowledge, self.perceiver, self.explainer, self.scrubber, self.store = (
            knowledge, perceiver, explainer, scrubber, store)
        self.personal = personal  # the patient's learned food evidence (spec 003); default: the store's
        self.graph = self._build()

    # ------------------------------------------------------------ graph

    def _build(self):
        g = StateGraph(State)
        g.add_node("sentinel", self.sentinel)
        g.add_node("escalate", self.escalate)
        g.add_node("scrub", self.scrub)
        g.add_node("perceive", self.perceive)
        g.add_node("resolve", self.resolve)
        g.add_node("decide", self.decide)
        g.add_node("explain", self.explain)
        g.add_node("store", self.save)
        g.add_edge(START, "sentinel")
        g.add_conditional_edges("sentinel", lambda s: "escalate" if s["red_flags"] else "scrub", ["escalate", "scrub"])
        g.add_edge("escalate", END)
        g.add_edge("scrub", "perceive")
        g.add_conditional_edges("perceive", self._after_perceive, ["resolve", END])
        g.add_edge("resolve", "decide")
        g.add_edge("decide", "explain")
        g.add_edge("explain", "store")
        g.add_edge("store", END)
        return g.compile()

    @staticmethod
    def _after_perceive(s: State) -> str:
        p = s.get("perception")
        if s.get("perception_error") or (p is not None and not p.is_food):
            return END
        return "resolve"

    # ------------------------------------------------------------ nodes

    async def sentinel(self, s: State) -> State:
        # Runs on the raw text, before anything else and before any model call (Constitution II).
        result = check_red_flags(s.get("text") or "")
        return {"red_flags": list(result.categories)}

    async def escalate(self, s: State) -> State:
        await self.store.save_red_flag(s["patient"].id, s["red_flags"])
        return {}

    async def scrub(self, s: State) -> State:
        text = s.get("text")
        if not text:
            return {"scrubbed": None, "pii_found": {}}
        result = self.scrubber.scrub(text)
        return {"scrubbed": result.text, "pii_found": result.found}

    async def perceive(self, s: State) -> State:
        try:
            run = await self.perceiver.perceive(text=s.get("scrubbed"), image=s.get("image"), lang=s["lang"])
        except Exception as exc:  # every model in the fallback chain failed
            log.warning("perception failed: %s", describe_error(exc))
            if s.get("image") is None and s.get("scrubbed"):
                # Text still works without a model: split the sentence and resolve each part against the dish names.
                parts = [p.strip() for p in _SPLIT.split(s["scrubbed"]) if p.strip()][:12] or [s["scrubbed"]]
                items = [PerceivedItem.model_construct(name_en=p, name_bn=None, confidence=0.8, preparation=None,
                                                       portion=None) for p in parts]
                return {"perception": Perception(is_food=True, items=items), "perception_model": "none",
                        "perception_prompt": "none"}
            return {"perception": None, "perception_error": "perception_unavailable",
                    "perception_model": "none", "perception_prompt": "none"}
        return {"perception": run.output, "perception_model": run.model, "perception_prompt": run.prompt}

    async def resolve(self, s: State) -> State:
        lang = s["lang"]
        contexts = []
        for i, item in enumerate(s["perception"].items):
            res = self.knowledge.resolve(item.name_en, item.name_bn or "")
            if res is None:
                evidence = DishEvidence(dish_id=f"unresolved:{i}", components={}, perception_confidence=item.confidence,
                                        resolution_confidence=0.0)
                name = item.name_bn if lang == "bn" and item.name_bn else item.name_en
                contexts.append(_Pending(item.name_en, name, evidence, resolved=False))
            else:
                evidence = self.knowledge.evidence(res.dish_id, item.confidence, res.score)
                name = res.name_bn if lang == "bn" else res.name_en
                contexts.append(_Pending(item.name_en, name, evidence, resolved=True))
        return {"pending": contexts}

    async def decide(self, s: State) -> State:
        lang, patient = s["lang"], s["patient"]
        pending: list[_Pending] = s["pending"]
        personal = await (self.personal(patient) if self.personal else self.store.personal_evidence(patient.id))
        meal = assess_meal(
            [p.evidence for p in pending], patient.profile, self.knowledge.rules(), personal,
            self.knowledge.alternatives_pool(), DEFAULT_CONFIG,
        )
        contexts = []
        for p, dv in zip(pending, meal.dishes):
            alt_name = None
            if dv.alternative_id:
                en, bn = self.knowledge.names(dv.alternative_id)
                alt_name = bn if lang == "bn" else en
            ctx = DishContext(perceived_name=p.perceived_name, verdict=dv, resolved=p.resolved, name=p.name,
                              alternative_name=alt_name)
            ctx.evidence = build_evidence(ctx, self.knowledge, lang)
            contexts.append(ctx)

        question = s["perception"].clarifying_question if s.get("perception") else None
        if question and guard.check_text(question, lang):
            question = None  # the model's question failed the wording/language check
        if meal.verdict == Verdict.NOT_SURE and not question:
            question = i18n.t(lang, "clarify.default" if contexts else "no_items")
        return {"contexts": contexts, "meal": meal, "clarifying_question": question}

    async def explain(self, s: State) -> State:
        lang, contexts = s["lang"], s["contexts"]
        explained = [c for c in contexts if c.explainable]
        if not explained:
            return {"explanation": guard.template(contexts, lang), "explanation_source": "template",
                    "explanation_model": "none", "explanation_prompt": "none", "guard_problems": []}
        problems: list[str] = []
        data = packet(contexts)
        for _attempt in range(2):  # one regeneration, then the template (plan decision MC5)
            try:
                run = await self.explainer.explain(packet=data, lang=lang, diagnosis=s["patient"].diagnosis.value)
            except Exception as exc:
                log.warning("explanation failed: %s", describe_error(exc))
                problems.append(f"model_error:{type(exc).__name__}")
                break
            result = guard.check(run.output, contexts, lang)
            if result.ok:
                return {"explanation": guard.complete(run.output, contexts, lang), "explanation_source": "model",
                        "explanation_model": run.model, "explanation_prompt": run.prompt, "guard_problems": problems}
            problems += list(result.problems)
        return {"explanation": guard.template(contexts, lang), "explanation_source": "template",
                "explanation_model": "none", "explanation_prompt": "none", "guard_problems": problems}

    async def save(self, s: State) -> State:
        meal: MealVerdict = s["meal"]
        record = MealCheckRecord(
            patient_id=s["patient"].id,
            input_type="photo" if s.get("image") is not None else "text",
            input_text=s.get("scrubbed"),
            dishes=dishes_payload(s["contexts"], s["lang"]),
            verdict=meal.verdict.value,
            risk=meal.risk,
            confidence=meal.confidence,
            evidence_ids=sorted({e for c in s["contexts"] for e in c.verdict.evidence_ids}),
            explanation={**explanation_payload(s), "clarifying_question": s.get("clarifying_question")},
            engine_version=meal.config_version,
            model_versions={"perception": s.get("perception_model", "none"), "explanation": s.get("explanation_model", "none")},
            prompt_versions={"perception": s.get("perception_prompt", "none"), "explanation": s.get("explanation_prompt", "none")},
            is_synthetic=s["patient"].is_synthetic,
        )
        await self.store.save_meal_check(record)
        return {"meal_check_id": record.id}

    # ------------------------------------------------------------ streaming

    async def stream(self, patient: Patient, lang: str, text: str | None, image: CleanImage | None) -> AsyncIterator[Event]:
        state: State = {"patient": patient, "lang": lang, "text": text, "image": image}
        current: dict = dict(state)
        async for update in self.graph.astream(state, stream_mode="updates"):
            for node, delta in update.items():
                current.update(delta or {})
                for event in self._events(node, current):
                    yield event

    def _events(self, node: str, s: dict) -> list[Event]:
        lang = s["lang"]
        if node == "escalate":
            cats = s["red_flags"]
            return [Event("red_flag", {
                "categories": cats,
                "title": i18n.t(lang, "red_flag.title"),
                "message": i18n.t(lang, "red_flag.body"),
                "reasons": [i18n.t(lang, f"red_flag.category.{c}") for c in cats],
            })]
        if node == "perceive":
            if s.get("perception_error"):
                return [Event("error", {"code": s["perception_error"]})]
            if s.get("perception") is not None and not s["perception"].is_food:
                return [Event("not_food", {"message": i18n.t(lang, "not_food")})]
        if node == "resolve":
            return [Event("dishes", {"dishes": [
                {"dish_id": p.evidence.dish_id if p.resolved else None, "name": p.name, "perceived_name": p.perceived_name,
                 "resolved": p.resolved, "perception_confidence": p.evidence.perception_confidence,
                 "resolution_confidence": p.evidence.resolution_confidence}
                for p in s["pending"]
            ]})]
        if node == "decide":
            meal: MealVerdict = s["meal"]
            data = {
                "verdict": meal.verdict.value, "emoji": meal.verdict.emoji, "label": i18n.t(lang, f"verdict.{meal.verdict.value}"),
                "risk": meal.risk, "confidence": meal.confidence, "engine_version": meal.config_version,
                "dishes": dishes_payload(s["contexts"], lang), "clarifying_question": s.get("clarifying_question"),
            }
            if not self.knowledge.reviewed_only:
                data["note"] = i18n.t(lang, "unreviewed_knowledge")
            return [Event("verdict", data)]
        if node == "explain":
            return [Event("explanation", explanation_payload(s))]
        if node == "store":
            return [Event("done", {"meal_check_id": s["meal_check_id"]})]
        return []


@dataclass
class _Pending:
    perceived_name: str
    name: str
    evidence: DishEvidence
    resolved: bool


def dishes_payload(contexts: list[DishContext], lang: str) -> list[dict]:
    out = []
    for c in contexts:
        v = c.verdict
        out.append({
            "dish_id": v.dish_id if c.resolved else None,
            "name": c.name,
            "perceived_name": c.perceived_name,
            "verdict": v.verdict.value,
            "emoji": v.verdict.emoji,
            "label": i18n.t(lang, f"verdict.{v.verdict.value}"),
            "risk": v.risk,
            "confidence": v.confidence,
            "reason": v.reason,
            "contributions": {"guideline": v.guideline_contribution, "personal": v.personal_contribution},
            "components": [
                {"component": a.component.value, "level": a.level.name.lower() if a.level is not None else "unknown",
                 "risk": a.risk, "guideline": a.guideline_score, "personal": a.personal_score,
                 "rule_ids": list(a.rule_ids), "tolerated": a.tolerated}
                for a in v.components if a.risk > 0 or a.rule_ids
            ],
            "evidence_ids": list(v.evidence_ids),
            "alternative": {"dish_id": v.alternative_id, "name": c.alternative_name} if v.alternative_id else None,
        })
    return out


def explanation_payload(s: dict) -> dict:
    exp: Explanation = s["explanation"]
    by_id = {c.dish_id: c for c in s["contexts"]}
    dishes = []
    for e in exp.dishes:
        ctx = by_id.get(e.dish_id)
        citations = [ev for ev in (ctx.evidence if ctx else []) if ev["id"] in e.cited_ids]
        dishes.append({"dish_id": e.dish_id if ctx is None or ctx.resolved else None, "text": e.text,
                       "cited_ids": e.cited_ids, "citations": citations})
    return {"dishes": dishes, "summary": exp.summary, "source": s.get("explanation_source", "template")}
