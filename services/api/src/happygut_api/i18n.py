"""Backend-generated user-facing strings, from locales/<lang>.json (Constitution VI)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LANGS = ("bn", "en")
_DIR = Path(__file__).parent / "locales"


@lru_cache
def _table(lang: str) -> dict[str, str]:
    if lang not in LANGS:
        raise ValueError(f"unsupported language: {lang}")
    data = json.loads((_DIR / f"{lang}.json").read_text(encoding="utf-8"))
    data.pop("_meta", None)
    return data


def t(lang: str, key: str, **values: str) -> str:
    text = _table(lang)[key]
    return text.format(**values) if values else text


def join(lang: str, items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + t(lang, "list.and") + items[-1]


def keys(lang: str) -> set[str]:
    return set(_table(lang))
