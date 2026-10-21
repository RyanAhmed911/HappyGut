"""Load and validate the knowledge seeds in data/seeds.

Only ``status: approved`` items are used in the product. Drafts can be loaded
for development with ``include_drafts=True``.

Usage:  uv run python -m happygut_pipelines.seeds [path/to/data/seeds]
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from happygut_engine import Component, DiseaseState, Diagnosis, DishEvidence, Level, RuleCard

DEFAULT_SEEDS = Path(__file__).resolve().parents[3] / "data" / "seeds"
STATUSES = {"draft", "approved"}
EVIDENCE_LEVELS = {"guideline", "trial", "clinical_practice", "patient_reported"}


@dataclass(frozen=True)
class DishSeed:
    id: str
    name_en: str
    name_bn: str
    aliases: tuple[str, ...]
    components: dict[Component, Level | None]
    gentler_alternatives: tuple[str, ...]
    status: str
    raw: dict

    def to_evidence(self, perception_confidence: float = 1.0, resolution_confidence: float = 1.0) -> DishEvidence:
        return DishEvidence(
            dish_id=self.id,
            components=dict(self.components),
            perception_confidence=perception_confidence,
            resolution_confidence=resolution_confidence,
            alternatives=self.gentler_alternatives,
        )


@dataclass(frozen=True)
class RuleSeed:
    rule: RuleCard
    status: str
    evidence_level: str
    raw: dict


def _read(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _dish(raw: dict) -> DishSeed:
    comps = raw.get("components") or {}
    return DishSeed(
        id=raw["id"],
        name_en=raw["name_en"],
        name_bn=raw["name_bn"],
        aliases=tuple(raw.get("aliases") or ()),
        components={Component(k): Level.parse(v) for k, v in comps.items()},
        gentler_alternatives=tuple(raw.get("gentler_alternatives") or ()),
        status=raw.get("status", "draft"),
        raw=raw,
    )


def _rule(raw: dict) -> RuleSeed:
    applies = raw["applies_to"]
    phenotypes = [p for p in applies.get("phenotype", []) if p != "any"]
    rule = RuleCard(
        id=raw["id"],
        component=Component(raw["component"]),
        min_level=Level.parse(raw["min_level"]),
        severity=int(raw["severity"]),
        diagnoses=frozenset(Diagnosis(d) for d in applies["diagnosis"]),
        phenotypes=frozenset(phenotypes),
        states=frozenset(DiseaseState(s) for s in applies["state"]),
        hard=bool(raw.get("hard", False)),
    )
    return RuleSeed(rule=rule, status=raw.get("status", "draft"), evidence_level=raw.get("evidence_level", ""), raw=raw)


def load_dishes(seeds: Path = DEFAULT_SEEDS, include_drafts: bool = False) -> dict[str, DishSeed]:
    dishes = {}
    for path in sorted((seeds / "dishes").glob("*.yaml")):
        d = _dish(_read(path))
        if include_drafts or d.status == "approved":
            dishes[d.id] = d
    return dishes


def load_rules(seeds: Path = DEFAULT_SEEDS, include_drafts: bool = False) -> list[RuleCard]:
    rules = []
    for path in sorted((seeds / "rule_cards").glob("*.yaml")):
        r = _rule(_read(path))
        if include_drafts or r.status == "approved":
            rules.append(r.rule)
    return rules


def validate(seeds: Path = DEFAULT_SEEDS) -> list[str]:
    """Return a list of problems; empty means the seeds are consistent."""
    errors: list[str] = []
    vocab = {c.value for c in Component}

    dish_raws = {p: _read(p) for p in sorted((seeds / "dishes").glob("*.yaml"))}
    ids = [r.get("id") for r in dish_raws.values()]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"duplicate dish id {dup}")
    alias_owner: dict[str, str] = {}
    for path, raw in dish_raws.items():
        did = raw.get("id", path.stem)
        if not str(did).startswith("dish.") or did != f"dish.{path.stem}":
            errors.append(f"{path.name}: id must be dish.<file name>")
        for field in ("name_en", "name_bn"):
            if not raw.get(field):
                errors.append(f"{did}: missing {field}")
        if not raw.get("aliases"):
            errors.append(f"{did}: needs at least one alias")
        comps = raw.get("components") or {}
        if set(comps) != vocab:
            errors.append(f"{did}: components must list every vocabulary key exactly once "
                          f"(missing {sorted(vocab - set(comps))}, unknown {sorted(set(comps) - vocab)})")
        for k, v in comps.items():
            if v not in {"none", "low", "medium", "high", "unknown"}:
                errors.append(f"{did}: {k} has invalid level {v!r}")
        for alt in raw.get("gentler_alternatives") or []:
            if alt not in ids:
                errors.append(f"{did}: alternative {alt} does not exist")
            if alt == did:
                errors.append(f"{did}: lists itself as an alternative")
        for name in [raw.get("name_en", ""), raw.get("name_bn", "")] + list(raw.get("aliases") or []):
            key = str(name).strip().lower()
            if key in alias_owner and alias_owner[key] != did:
                errors.append(f"name/alias {name!r} used by both {alias_owner[key]} and {did}")
            alias_owner[key] = did
        status = raw.get("status")
        if status not in STATUSES:
            errors.append(f"{did}: status must be draft or approved")
        if status == "approved":
            if not raw.get("reviewed_by"):
                errors.append(f"{did}: approved dish needs reviewed_by")
            if not raw.get("sources"):
                errors.append(f"{did}: approved dish needs at least one source")

    rule_raws = {p: _read(p) for p in sorted((seeds / "rule_cards").glob("*.yaml"))}
    rids = [r.get("id") for r in rule_raws.values()]
    for dup in {i for i in rids if rids.count(i) > 1}:
        errors.append(f"duplicate rule id {dup}")
    for path, raw in rule_raws.items():
        rid = raw.get("id", path.stem)
        if rid != path.stem:
            errors.append(f"{path.name}: id must equal the file name")
        try:
            seed = _rule(raw)
        except (KeyError, ValueError) as exc:
            errors.append(f"{rid}: invalid rule ({exc})")
            continue
        if seed.evidence_level not in EVIDENCE_LEVELS:
            errors.append(f"{rid}: evidence_level must be one of {sorted(EVIDENCE_LEVELS)}")
        for field in ("recommendation_en", "recommendation_bn", "title_en", "title_bn"):
            if not raw.get(field):
                errors.append(f"{rid}: missing {field}")
        text = f"{raw.get('recommendation_en', '')} {raw.get('title_en', '')}".lower()
        if " safe" in f" {text}" or "medication" in text or "medicine" in text:
            errors.append(f"{rid}: wording must not say 'safe' or mention medication")
        if seed.rule.hard and seed.rule.phenotypes != frozenset({"stricturing"}):
            errors.append(f"{rid}: hard rules are reserved for stricturing Crohn's safety rules")
        if not raw.get("sources"):
            errors.append(f"{rid}: needs at least one source")
        if raw.get("status") not in STATUSES:
            errors.append(f"{rid}: status must be draft or approved")
        if raw.get("status") == "approved":
            if not raw.get("reviewed_by"):
                errors.append(f"{rid}: approved rule needs reviewed_by")
            supported = [s for s in raw.get("sources") or [] if s.get("quote") and s.get("licence")]
            if not supported:
                errors.append(f"{rid}: approved rule needs a source with an exact quote and a licence")
    return errors


def review_status(seeds: Path = DEFAULT_SEEDS) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for kind in ("dishes", "rule_cards"):
        counts = {"draft": 0, "approved": 0}
        for path in (seeds / kind).glob("*.yaml"):
            counts[_read(path).get("status", "draft")] += 1
        out[kind] = counts
    return out


def main(argv: list[str]) -> int:
    seeds = Path(argv[1]) if len(argv) > 1 else DEFAULT_SEEDS
    errors = validate(seeds)
    for kind, counts in review_status(seeds).items():
        print(f"{kind}: {counts['approved']} approved, {counts['draft']} draft")
    for e in errors:
        print(f"ERROR {e}")
    print("OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
