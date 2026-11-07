"""Output guard for explanations, and the deterministic template used when the guard fails.

Checks (spec 002 FR-007, Constitution II-IV):
- one explanation per explained dish, and no others
- every cited ID is in that dish's evidence, and at least one is cited
- no verdict label or paraphrase (the app shows the engine's verdict; MC4)
- no "safe" claims, no medication words, no causal claims
- the text is in the patient's language
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from happygut_engine import Verdict

from . import i18n
from .agents import DishExplanation, Explanation
from .evidence import DishContext

_BANNED = {
    "en": [
        r"\bsafe(ly|ty)?\b", r"\bharmless\b", r"\bwon'?t (cause|hurt|trigger)\b", r"\bwill not (cause|hurt|trigger)\b",
        r"\bguarantee", r"\bcaused\b", r"\bcure[sd]?\b",
        r"\b(medicines?|medications?|doses?|dosage|drugs?|tablets?|pills?|steroids?|prednisolone|mesalazine|mesalamine|"
        r"azathioprine|infliximab|adalimumab|biologics?)\b",
        r"\b(likely ok|likely okay|likely trigger|fine for you|ok(ay)? for you|good for you|no problem)\b",
    ],
    "bn": [
        r"নিরাপদ", r"ঝুঁকিমুক্ত", r"নিশ্চিতভাবে", r"ওষুধ", r"ডোজ", r"ট্যাবলেট", r"স্টেরয়েড", r"সমস্যা নেই", r"কোনো সমস্যা হবে না",
    ],
}


def _verdict_phrases() -> list[str]:
    return [i18n.t(lang, f"verdict.{v.value}").lower() for lang in i18n.LANGS for v in Verdict if v != Verdict.NOT_SURE]


def _bangla_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if "ঀ" <= c <= "৿") / len(letters)


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    problems: tuple[str, ...]


def check_text(text: str, lang: str) -> list[str]:
    problems = []
    low = text.lower()
    for pattern in _BANNED["en"] + _BANNED["bn"]:
        if re.search(pattern, low):
            problems.append(f"banned:{pattern}")
    for phrase in _verdict_phrases():
        if phrase in low:
            problems.append(f"verdict_label:{phrase}")
    ratio = _bangla_ratio(text)
    if lang == "bn" and ratio < 0.6:
        problems.append("language:not_bangla")
    if lang == "en" and ratio > 0.2:
        problems.append("language:not_english")
    return problems


def check(explanation: Explanation, dishes: list[DishContext], lang: str) -> GuardResult:
    expected = {d.dish_id: d for d in dishes if d.explainable}
    problems: list[str] = []
    got = {e.dish_id for e in explanation.dishes}
    for missing in expected.keys() - got:
        problems.append(f"missing:{missing}")
    for e in explanation.dishes:
        ctx = expected.get(e.dish_id)
        if ctx is None:
            problems.append(f"unexpected_dish:{e.dish_id}")
            continue
        if not e.cited_ids:
            problems.append(f"no_citation:{e.dish_id}")
        for cid in e.cited_ids:
            if cid not in ctx.evidence_ids:
                problems.append(f"uncited_evidence:{e.dish_id}:{cid}")
        problems += [f"{p}:{e.dish_id}" for p in check_text(e.text, lang)]
    problems += [f"{p}:summary" for p in check_text(explanation.summary, lang)]
    return GuardResult(not problems, tuple(problems))


# ---------------------------------------------------------------- template fallback

def _components(ctx: DishContext, lang: str, which: str) -> list[str]:
    v = ctx.verdict
    if which == "hard":
        comps = [a for a in v.components if a.hard_rule_ids]
    elif which == "personal":
        comps = [a for a in v.components if a.personal is not None and a.personal_score > 0 and not a.tolerated]
    else:
        comps = [a for a in v.components if a.guideline_score > 0]
    comps.sort(key=lambda a: -a.risk)
    return [i18n.t(lang, f"component.{a.component.value}") for a in comps[:3]]


def template_for(ctx: DishContext, lang: str) -> DishExplanation:
    v = ctx.verdict
    if not ctx.resolved:
        return DishExplanation(dish_id=ctx.dish_id, text=i18n.t(lang, "template.unresolved", name=ctx.perceived_name), cited_ids=[])
    cites = [f"dish:{v.dish_id}"]
    reason = v.reason
    if reason == "hard_rule":
        text = i18n.t(lang, "template.hard_rule", components=i18n.join(lang, _components(ctx, lang, "hard")))
        cites += list(v.hard_rule_ids)
    elif reason == "personal":
        text = i18n.t(lang, "template.personal", components=i18n.join(lang, _components(ctx, lang, "personal")))
        cites += [e["id"] for e in ctx.evidence if e["type"] == "personal"]
    elif reason == "guideline":
        text = i18n.t(lang, "template.guideline", name=ctx.name, components=i18n.join(lang, _components(ctx, lang, "guideline")))
        top = next((e for e in ctx.evidence if e["type"] == "guideline"), None)
        if top is not None:
            text += " " + top["recommendation"]
            cites.append(top["id"])
    elif reason == "low_confidence":
        text = i18n.t(lang, "template.low_confidence", name=ctx.name)
    else:
        text = i18n.t(lang, "template.no_risk", name=ctx.name)
    if ctx.alternative_name:
        text += " " + i18n.t(lang, "template.alternative", alternative=ctx.alternative_name)
    return DishExplanation(dish_id=ctx.dish_id, text=text, cited_ids=list(dict.fromkeys(cites)))


def template(dishes: list[DishContext], lang: str) -> Explanation:
    return Explanation(dishes=[template_for(d, lang) for d in dishes], summary=i18n.t(lang, "template.summary"))


def complete(explanation: Explanation, dishes: list[DishContext], lang: str) -> Explanation:
    """Add template text for dishes the model doesn't explain (unresolved, not sure), in plate order."""
    by_id = {e.dish_id: e for e in explanation.dishes}
    out = [by_id.get(d.dish_id) or template_for(d, lang) for d in dishes]
    return Explanation(dishes=out, summary=explanation.summary)
