"""Human review of G2 dish-name candidates, then merge the accepted ones into the dish seeds.

    uv run python -m happygut_pipelines.aliases export   # G2 output → data/review/g2-aliases.csv
    (a native Bangla speaker fills `decision` with yes / no and `reviewer` with their initials)
    uv run python -m happygut_pipelines.aliases apply    # accepted spellings → aliases in data/seeds/dishes

The CSV is UTF-8 with a byte-order mark so Excel on Windows shows Bangla correctly. Exporting again
keeps decisions already made. The committed CSV is the review record for every alias added.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

from .gpu_jobs import JOBS_DIR, REPO
from .seeds import DEFAULT_SEEDS, _read

REVIEW_CSV = REPO / "data" / "review" / "g2-aliases.csv"
FIELDS = ["dish_id", "name_en", "name_bn", "script", "candidate", "votes", "auto_check", "decision", "reviewer", "note"]
YES, NO = {"yes", "y", "accept"}, {"no", "n", "reject"}
_ALIASES_LINE = re.compile(r"^aliases: \[.*\]$", re.M)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).strip().lower())


def auto_checks(dish: dict, candidate: str, names_of: dict[str, set[str]], suggested_for: dict[str, set[str]]) -> str:
    """Objective warnings for the reviewer; the decision stays with the person."""
    c = _norm(candidate)
    notes = []
    if "\u200c" in candidate or "\u200d" in candidate:
        notes.append("contains an invisible joiner character")
    if others := sorted(names_of.get(c, set()) - {dish["id"]}):
        notes.append(f"already a name of {', '.join(others)}: would make search ambiguous")
    if others := sorted(suggested_for.get(c, set()) - {dish["id"]}):
        notes.append(f"also suggested for {', '.join(others)}")
    words = c.split()
    if len(words) == 1 and any(len(_norm(n).split()) > 1 and words[0] in _norm(n).split()
                               for n in (dish["name_en"], dish["name_bn"], *dish.get("aliases", []))):
        notes.append("one word from the dish name: may match other dishes")
    return "; ".join(notes)


def read_review(path: Path = REVIEW_CSV) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def export(jobs_dir: Path = JOBS_DIR, seeds: Path = DEFAULT_SEEDS, path: Path = REVIEW_CSV) -> dict:
    """Write one row per G2 candidate. Earlier decisions are kept; candidates already in the seeds are skipped."""
    output = jobs_dir / "g2" / "output.jsonl"
    if not output.exists():
        raise FileNotFoundError(f"{output} not found: run G2 on Ubuntu and pull its output first")
    decided = {(r["dish_id"], _norm(r["candidate"])): r for r in read_review(path)}
    dishes = {d["id"]: d for d in (_read(p) for p in sorted((seeds / "dishes").glob("*.yaml")))}
    names_of: dict[str, set[str]] = {}
    for d in dishes.values():
        for n in (d["name_en"], d["name_bn"], *d.get("aliases", [])):
            names_of.setdefault(_norm(n), set()).add(d["id"])
    g2_rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    suggested_for: dict[str, set[str]] = {}
    for g2 in g2_rows:
        for script in ("bangla", "banglish"):
            for candidate in g2["candidates"][script]:
                suggested_for.setdefault(_norm(candidate), set()).add(g2["id"])
    rows = []
    for g2 in g2_rows:
        dish = dishes.get(g2["id"])
        if dish is None:
            continue
        known = {_norm(n) for n in (dish["name_en"], dish["name_bn"], *dish.get("aliases", []))}
        for script in ("bangla", "banglish"):
            for candidate in g2["candidates"][script]:
                key = (dish["id"], _norm(candidate))
                if key[1] in known and key not in decided:
                    continue
                previous = decided.get(key, {})
                rows.append({
                    "dish_id": dish["id"], "name_en": dish["name_en"], "name_bn": dish["name_bn"],
                    "script": script, "candidate": candidate,
                    "votes": f"{g2.get('votes', {}).get(script, {}).get(candidate, '')}/{len(g2.get('raw', [])) or ''}",
                    "auto_check": auto_checks(dish, candidate, names_of, suggested_for),
                    "decision": previous.get("decision", ""), "reviewer": previous.get("reviewer", ""),
                    "note": previous.get("note", ""),
                })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return {"rows": len(rows), "undecided": sum(not r["decision"].strip() for r in rows)}


def apply(path: Path = REVIEW_CSV, seeds: Path = DEFAULT_SEEDS) -> dict:
    """Add every accepted candidate to its dish's aliases. Rows need a reviewer to count."""
    accepted: dict[str, list[str]] = {}
    counts = {"accepted": 0, "rejected": 0, "undecided": 0, "added": 0}
    for row in read_review(path):
        decision = row["decision"].strip().lower()
        if decision in YES and row["reviewer"].strip():
            counts["accepted"] += 1
            accepted.setdefault(row["dish_id"], []).append(_norm(row["candidate"]))
        elif decision in NO:
            counts["rejected"] += 1
        else:
            counts["undecided"] += 1  # blank, unclear, or accepted without a reviewer
    for dish_id, candidates in accepted.items():
        file = seeds / "dishes" / f"{dish_id.removeprefix('dish.')}.yaml"
        dish = _read(file)
        aliases = list(dish.get("aliases", []))
        known = {_norm(n) for n in (dish["name_en"], dish["name_bn"], *aliases)}
        new = [c for c in dict.fromkeys(candidates) if c not in known]
        if not new:
            continue
        text = file.read_text(encoding="utf-8")
        line = "aliases: " + json.dumps(aliases + new, ensure_ascii=False)
        text, n = _ALIASES_LINE.subn(lambda _: line, text, count=1)
        if n != 1:
            raise ValueError(f"{file}: expected one 'aliases: [...]' line")
        file.write_text(text, encoding="utf-8")
        counts["added"] += len(new)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review G2 dish-name candidates")
    parser.add_argument("command", choices=["export", "apply"])
    args = parser.parse_args(argv)
    if args.command == "export":
        result = export()
        print(f"{REVIEW_CSV.relative_to(REPO)}: {result['rows']} candidates, {result['undecided']} waiting for a decision.")
        print("Fill `decision` (yes/no) and `reviewer`, save as CSV, then run: python -m happygut_pipelines.aliases apply")
    else:
        result = apply()
        print(f"accepted {result['accepted']}, rejected {result['rejected']}, undecided {result['undecided']}; "
              f"{result['added']} new aliases written to data/seeds/dishes")
        if result["added"]:
            print("Next: run the seed validator and tests, commit, and rerun G3 so the new spellings get embeddings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
