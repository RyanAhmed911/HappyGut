import csv
import json
import shutil

import pytest

from happygut_pipelines import aliases as al
from happygut_pipelines.seeds import DEFAULT_SEEDS, _read, load_dishes


@pytest.fixture
def workspace(tmp_path):
    seeds = tmp_path / "seeds"
    (seeds / "dishes").mkdir(parents=True)
    for name in ("beef_bhuna", "beef_tehari"):
        shutil.copy(DEFAULT_SEEDS / "dishes" / f"{name}.yaml", seeds / "dishes")
    # Start from a dish that doesn't have the candidate spellings yet, whatever the real seed holds today.
    bhuna = seeds / "dishes" / "beef_bhuna.yaml"
    raw = _read(bhuna)
    kept = [a for a in raw["aliases"] if a not in {"গরুর ভুনা", "gorur bhuna", "gur mangsho bhuna"}]
    text = bhuna.read_text(encoding="utf-8")
    text, n = al._ALIASES_LINE.subn(lambda _: "aliases: " + json.dumps(kept, ensure_ascii=False), text, count=1)
    assert n == 1
    bhuna.write_text(text, encoding="utf-8")
    shutil.copytree(DEFAULT_SEEDS / "rule_cards", seeds / "rule_cards")
    g2 = tmp_path / "jobs" / "g2"
    g2.mkdir(parents=True)
    rows = [
        {"id": "dish.beef_bhuna", "candidates": {"bangla": ["গরুর ভুনা"], "banglish": ["gorur bhuna", "gur mangsho bhuna"]},
         "votes": {"bangla": {"গরুর ভুনা": 3}, "banglish": {"gorur bhuna": 3, "gur mangsho bhuna": 3}}, "raw": [{}, {}, {}]},
        {"id": "dish.beef_tehari", "candidates": {"bangla": [], "banglish": ["beef theory"]},
         "votes": {"bangla": {}, "banglish": {"beef theory": 2}}, "raw": [{}, {}, {}]},
    ]
    (g2 / "output.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return seeds, tmp_path / "jobs", tmp_path / "review.csv"


def decide(path, decisions):
    rows = al.read_review(path)
    for r in rows:
        r["decision"], r["reviewer"] = decisions.get(r["candidate"], ("", ""))
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=al.FIELDS)
        w.writeheader()
        w.writerows(rows)


def test_export_lists_candidates_with_votes(workspace):
    seeds, jobs, csv_path = workspace
    assert al.export(jobs, seeds, csv_path) == {"rows": 4, "undecided": 4}
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf"), "BOM so Excel reads Bangla"
    rows = {r["candidate"]: r for r in al.read_review(csv_path)}
    assert rows["gur mangsho bhuna"]["votes"] == "3/3" and rows["beef theory"]["votes"] == "2/3"


def test_auto_checks_flag_collisions_partial_names_and_invisible_characters():
    dish = {"id": "dish.a", "name_en": "Dim sheddho", "name_bn": "ডিম সেদ্ধ", "aliases": []}
    names_of = {"rui macher jhol": {"dish.b"}}
    suggested_for = {"rui er jhol": {"dish.a", "dish.c"}}
    assert "already a name of dish.b" in al.auto_checks(dish, "rui macher jhol", names_of, suggested_for)
    assert "also suggested for dish.c" in al.auto_checks(dish, "rui er jhol", names_of, suggested_for)
    assert "one word from the dish name" in al.auto_checks(dish, "dim", names_of, suggested_for)
    assert "invisible" in al.auto_checks(dish, "ফ\u200dুচকা", names_of, suggested_for)
    assert al.auto_checks(dish, "dim shiddho", names_of, suggested_for) == ""
    assert al.auto_checks(dish, "sheddho dim", names_of, suggested_for) == "", "short forms with 2+ words are fine"


def test_apply_adds_only_reviewed_acceptances_and_reexport_keeps_decisions(workspace):
    seeds, jobs, csv_path = workspace
    al.export(jobs, seeds, csv_path)
    decide(csv_path, {"গরুর ভুনা": ("yes", "RA"), "gorur bhuna": ("Y", "RA"), "gur mangsho bhuna": ("no", "RA"),
                      "beef theory": ("yes", "")})  # accepted without a reviewer → doesn't count
    assert al.apply(csv_path, seeds) == {"accepted": 2, "rejected": 1, "undecided": 1, "added": 2}
    bhuna = _read(seeds / "dishes" / "beef_bhuna.yaml")
    assert bhuna["aliases"][-2:] == ["গরুর ভুনা", "gorur bhuna"]
    assert "gur mangsho bhuna" not in bhuna["aliases"]
    assert "beef theory" not in _read(seeds / "dishes" / "beef_tehari.yaml")["aliases"]
    assert set(load_dishes(seeds, include_drafts=True)) == {"dish.beef_bhuna", "dish.beef_tehari"}
    assert al.apply(csv_path, seeds)["added"] == 0, "applying twice adds nothing"
    al.export(jobs, seeds, csv_path)
    rows = {r["candidate"]: r for r in al.read_review(csv_path)}
    assert rows["gur mangsho bhuna"]["decision"] == "no" and rows["gorur bhuna"]["decision"] == "Y"
