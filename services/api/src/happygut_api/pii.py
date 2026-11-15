"""PII scrubbing inside our backend, before any cloud model call (Constitution V).

Three layers, applied in order:
1. Bangladesh rules (always on): phone numbers, NID / birth-registration numbers,
   emails, URLs, and names after self-introduction cues, in Bangla or English
   digits and script.
2. Presidio (optional, ``pii_presidio``): English names, locations and other entities.
3. A Bengali NER model (optional, ``pii_bengali_ner_model``): names and places in Bangla script.

Each detection is replaced by a typed placeholder such as ``<PHONE>``. Food words are
never touched by the rules, so dish names survive scrubbing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Protocol

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_D = r"[0-9০-৯]"
_SEP = r"[\s\-.]?"

_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")),
    ("URL", re.compile(r"\bhttps?://\S+|\bwww\.\S+", re.I)),
    # Bangladeshi mobile numbers: optional +880 / 880 / 0, then 1[3-9] and 8 more digits, with optional separators.
    ("PHONE", re.compile(
        rf"(?<![0-9০-৯])(?:(?:\+|00)?(?:88|৮৮)0?|[0০])?{_SEP}[1১][3-9৩-৯]{_D}{{2}}{_SEP}{_D}{{3}}{_SEP}{_D}{{3}}(?![0-9০-৯])"
    )),
    # NID (10, 13 or 17 digits) and birth registration (17 digits): long digit runs.
    ("ID_NUMBER", re.compile(rf"(?<![0-9০-৯])(?:{_D}[\s-]?){{9}}{_D}(?:(?:[\s-]?{_D}){{3}}(?:(?:[\s-]?{_D}){{4}})?)?(?![0-9০-৯])")),
]

# A name after an explicit self-introduction cue: "my name is Rahim Uddin", "আমার নাম রহিম".
# Only explicit cues: looser ones ("this is …", "আমি …") would also catch dish names.
_NAME_CUES_EN = re.compile(r"(?i:\b(my name is|call me|name:))\s+((?:[A-Z][a-z]+)(?:\s+[A-Z][a-z]+){0,2})")
_NAME_CUES_BN = re.compile(r"(আমার নাম|নাম:)\s*([\u0980-\u09FF]+(?:\s+[\u0980-\u09FF]+)?)")


class Detector(Protocol):
    def __call__(self, text: str) -> list[tuple[int, int, str]]: ...


@dataclass
class ScrubResult:
    text: str
    found: dict[str, int] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return bool(self.found)


def _rule_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    for label, pattern in _RULES:
        spans += [(m.start(), m.end(), label) for m in pattern.finditer(text)]
    for pattern in (_NAME_CUES_EN, _NAME_CUES_BN):
        for m in pattern.finditer(text):
            spans.append((m.start(2), m.end(2), "PERSON"))
    return spans


def _merge(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    merged: list[tuple[int, int, str]] = []
    for start, end, label in sorted(spans, key=lambda s: (s[0], -s[1])):
        if merged and start < merged[-1][1]:
            prev = merged[-1]
            merged[-1] = (prev[0], max(prev[1], end), prev[2])
        else:
            merged.append((start, end, label))
    return merged


def _words(text: str) -> list[str]:
    return re.findall(r"[\w\u0980-\u09FF]+", text.lower())


class Scrubber:
    """``food_words``: words from dish names and aliases. A model-detected name or place made only
    of food words (Presidio tags "murgir jhol" as a person) is kept; rule detections always apply."""

    def __init__(self, extra_detectors: list[Detector] | None = None, food_words: set[str] | None = None):
        self.extra: list[Detector] = list(extra_detectors or [])
        self.food_words = {w.lower() for w in (food_words or set())}

    def _is_food(self, span_text: str) -> bool:
        words = _words(span_text)
        return bool(words) and all(w in self.food_words for w in words)

    def scrub(self, text: str) -> ScrubResult:
        spans = _rule_spans(text)
        for detect in self.extra:
            spans += [sp for sp in detect(text) if not self._is_food(text[sp[0]:sp[1]])]
        out, found, cursor = [], {}, 0
        for start, end, label in _merge(spans):
            out.append(text[cursor:start])
            out.append(f"<{label}>")
            found[label] = found.get(label, 0) + 1
            cursor = end
        out.append(text[cursor:])
        return ScrubResult("".join(out), found)


def presidio_detector(
    entities: tuple[str, ...] = ("PERSON", "LOCATION", "EMAIL_ADDRESS", "PHONE_NUMBER"),
    spacy_model: str = "en_core_web_sm",
) -> Detector:
    """English entities via Presidio (requires the ``pii`` extra, which includes the spaCy model)."""
    from presidio_analyzer import AnalyzerEngine  # imported lazily: optional dependency
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    nlp = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": spacy_model}],
    }).create_engine()
    engine = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])

    def detect(text: str) -> list[tuple[int, int, str]]:
        results = engine.analyze(text=text, language="en", entities=list(entities))
        label = {"EMAIL_ADDRESS": "EMAIL", "PHONE_NUMBER": "PHONE"}
        return [(r.start, r.end, label.get(r.entity_type, r.entity_type)) for r in results if r.score >= 0.5]

    return detect


def bengali_ner_detector(model_id: str, pipeline_factory: Callable | None = None) -> Detector:
    """Bangla-script names and places via a token-classification model (requires the ``pii`` extra)."""
    if pipeline_factory is None:
        from transformers import pipeline as pipeline_factory  # optional dependency

    ner = pipeline_factory("token-classification", model=model_id, aggregation_strategy="simple")
    keep = {"PER": "PERSON", "PERSON": "PERSON", "LOC": "LOCATION", "GPE": "LOCATION"}

    def detect(text: str) -> list[tuple[int, int, str]]:
        if not re.search(r"[ঀ-৿]", text):
            return []
        return [(e["start"], e["end"], keep[e["entity_group"]]) for e in ner(text) if e["entity_group"] in keep]

    return detect


def build_scrubber(presidio: bool = False, bengali_ner_model: str = "", food_names: list[str] | None = None) -> Scrubber:
    extra: list[Detector] = []
    if presidio:
        extra.append(presidio_detector())
    if bengali_ner_model:
        extra.append(bengali_ner_detector(bengali_ner_model))
    words = {w for name in food_names or [] for w in _words(name)}
    return Scrubber(extra, food_words=words)


def normalise_digits(text: str) -> str:
    return text.translate(_BN_DIGITS)
