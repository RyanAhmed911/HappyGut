"""Rule-based red-flag sentinel (Constitution II).

Runs before any other processing. It is deliberately tuned for recall: a false
alarm sends someone to their doctor, a miss could hurt them. An LLM second check
may add detections in the API layer, but can never remove one found here.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    return re.sub(r"\s+", " ", text).strip()


def _terms(*terms: str) -> tuple[str, ...]:
    return tuple(normalise(t) for t in terms)


# English and Banglish use regex with word boundaries; Bangla uses substrings
# (word boundaries don't work across Bangla combining marks).
_EN = {
    "blood": r"\bblood(y)?\b|\bbleed(ing|s)?\b|\bclots?\b",
    "stool": r"\bstools?\b|\bpoo(p)?\b|\bmotions?\b|\btoilet\b|\bbowel\b|\bdiarrh?o?ea\b|\brectal\b|\bbottom\b",
    "heavy": r"\bheavy\b|\ba lot\b|\blots? of\b|\bnon.?stop\b|\bwon'?t stop\b|\bkeeps? (bleeding|coming)\b|\bsoaked\b",
    "vomit_blood": r"\bvomit(ing|ed)? blood\b|\bthrowing up blood\b",
    "fever": r"\bfever\b|\bhigh temp(erature)?\b|\bfeverish\b",
    "pain": r"\b(abdominal|stomach|belly|tummy|abdomen) (pain|ache|cramps?)\b|\bpain in (my )?(stomach|belly|tummy|abdomen)\b|\bstomach ?ache\b|\bsevere cramps?\b",
    "vomit": r"\bvomit(ing|ed|s)?\b|\bthrowing up\b|\bthrew up\b|\bpuking\b",
    "no_pass": r"\b(can'?t|cannot|unable to|haven'?t|not) (pass(ed)?|poo(p)?|passed) (any )?(gas|wind|stool|motion)?|\bno (stool|bowel movement|gas|wind|poo(p)?)\b|\bhaven'?t pooped\b|\bnot pooped\b",
    "dehydration": r"\bsevere(ly)? dehydrat(ed|ion)\b|\bvery dehydrated\b|\bcan'?t keep (any )?(water|fluids?|anything) down\b|\bno urine\b|\bhaven'?t (peed|urinated)\b|\bfaint(ed|ing)?\b|\bpass(ed|ing) out\b",
}
_BN = {
    "blood": _terms("রক্ত"),
    "stool": _terms("পায়খানা", "মল", "টয়লেট", "পাতলা পায়খানা", "ডায়রিয়া"),
    "heavy": _terms("অনেক", "প্রচুর", "খুব বেশি", "থামছে না"),
    "vomit_blood": _terms("রক্ত বমি", "বমিতে রক্ত"),
    "fever": _terms("জ্বর"),
    "pain": _terms("পেট ব্যথা", "পেটে ব্যথা", "পেট ব্যাথা", "পেটে ব্যাথা", "পেট কামড়"),
    "vomit": _terms("বমি"),
    "no_pass": _terms(
        "পায়খানা হচ্ছে না", "পায়খানা হয়নি", "পায়খানা হয় নি", "বায়ু বের হচ্ছে না",
        "গ্যাস বের হচ্ছে না", "পায়খানা বন্ধ",
    ),
    "dehydration": _terms("পানিশূন্য", "প্রস্রাব হচ্ছে না", "প্রস্রাব হয়নি", "অজ্ঞান", "মাথা ঘুরে পড়ে"),
}
_BANGLISH = {
    "blood": r"\b(rokto|rakto|roktho|rokt)\b",
    "stool": r"\b(paikhana|pykhana|paykhana|paikana|paekhana|toilet|patla)\b",
    "heavy": r"\b(onek|prochur|beshi|thamche na)\b",
    "vomit_blood": r"\b(rokto bomi|bomite rokto)\b",
    "fever": r"\b(jor|jwor|jwar|jhor)\b",
    "pain": r"\bpet(e)? (betha|batha|bytha|byatha|beta|kamrache|kamray)\b",
    "vomit": r"\b(bomi|bomee)\b",
    "no_pass": r"\b(paikhana|pykhana|paykhana) (hocche na|hoy ?ni|bondho)\b|\b(gas|batash|bayu) ber hocche na\b",
    "dehydration": r"\b(pani ?shunno(ta)?|prosrab (hocche na|hoy ?ni)|ogyan|ogga?n|matha ghure)\b",
}


@dataclass(frozen=True)
class RedFlagResult:
    triggered: bool
    categories: tuple[str, ...]


def _found(concept: str, text: str) -> bool:
    if re.search(_EN[concept], text) or re.search(_BANGLISH[concept], text):
        return True
    return any(term in text for term in _BN[concept])


def check_red_flags(text: str) -> RedFlagResult:
    """Return which red-flag categories the text matches.

    Categories:
    - ``heavy_bleeding``: blood with stool or a "heavy" word, or vomiting blood
    - ``fever_with_abdominal_pain``
    - ``possible_obstruction``: vomiting or abdominal pain with no stool / gas
    - ``severe_dehydration``
    """
    t = normalise(text)
    has = {concept: _found(concept, t) for concept in _EN}
    categories = []
    if has["vomit_blood"] or (has["blood"] and (has["stool"] or has["heavy"])):
        categories.append("heavy_bleeding")
    if has["fever"] and has["pain"]:
        categories.append("fever_with_abdominal_pain")
    if has["no_pass"] and (has["vomit"] or has["pain"]):
        categories.append("possible_obstruction")
    if has["dehydration"]:
        categories.append("severe_dehydration")
    return RedFlagResult(triggered=bool(categories), categories=tuple(categories))
