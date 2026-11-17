"""Evaluation run: numbers the team may quote, each reproducible with one command.

    uv run python -m happygut_api.evaluate            # full run (200 simulated patients)
    uv run python -m happygut_api.evaluate --patients 40

Writes ``evals/summary.json`` and ``evals/RESULTS.md``. Nothing here calls a language model:
it measures the deterministic parts (Pattern Finder, red-flag sentinel, verdict engine, dish
names). Every patient in the cohort is simulated, and the report says so.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

from happygut_engine import (
    Component, DayRecord, Diagnosis, DiseaseState, Level, Profile, Verdict, assess_meal, check_red_flags,
    detect_periods, find_patterns, hbi, is_late_night, kind_by_day, sleep_hours,
)
from happygut_engine.patterns import HIGH_STRESS, LATE_NIGHT, LIKELY, MISSED_DOSE, POOR_SLEEP, SHORT_SLEEP
from happygut_engine.simulate import Effect, MenuItem, SimConfig, SimDay, StressPeriod, simulate

from . import __version__
from .demo import build_menu
from .knowledge import MemoryKnowledge

ROOT = Path(__file__).resolve().parents[4]
SEEDS = ROOT / "data" / "seeds"
SETS = ROOT / "evals" / "sets"
HORIZONS = (21, 30, 60, 90, 120)
DAYS = 120
START = date(2026, 1, 1)
EXAM_PERIODS = (StressPeriod("exam", "Exams", 8, 17), StressPeriod("exam", "Exams", 48, 58), StressPeriod("exam", "Exams", 92, 101))
STRICTURE_COMPONENTS = (Component.INSOLUBLE_FIBRE, Component.SKINS_SEEDS_NUTS)


# ---------------------------------------------------------------- simulated cohort

def food_candidates(menu: list[MenuItem]) -> list[Component]:
    """Components a simulated person can react to: present at a high level in at least three menu dishes."""
    counts = Counter(c for m in menu for c, lvl in m.components.items() if lvl >= Level.HIGH)
    return sorted((c for c, n in counts.items() if n >= 3), key=lambda c: c.value)


def patient_config(i: int, candidates: list[Component]) -> tuple[SimConfig, frozenset[str]]:
    """Settings for simulated patient ``i`` and the set of factors that truly raise their symptoms."""
    rng = random.Random(10_000 + i)

    def effect(**kw) -> Effect:
        return Effect(round(rng.uniform(1.6, 2.6), 2), round(rng.uniform(0.65, 0.9), 2), **kw)

    truth: set[str] = set()
    foods: dict[Component, Effect] = {}
    late = stress = dose = None
    periods: dict[str, Effect] = {}
    if rng.random() >= 0.15:  # 15% of patients have no hidden contributor at all
        for c in rng.sample(candidates, k=rng.choice((0, 1, 1, 1, 2))):
            foods[c] = effect()
            truth.add(f"food:{c.value}")
        if rng.random() < 0.5:
            late = effect()
            truth.add(LATE_NIGHT)
        if rng.random() < 0.35:
            stress = effect()
            truth.add(HIGH_STRESS)
        if rng.random() < 0.35:
            periods["exam"] = Effect(round(rng.uniform(1.0, 1.6), 2), round(rng.uniform(0.65, 0.85), 2), next_day=0.0)
            truth.add("period:exam")
        if rng.random() < 0.2:
            dose = effect()
            truth.add(MISSED_DOSE)
    flare = ((rng.randrange(25, 95),) if rng.random() < 0.5 else ())
    return SimConfig(
        days=DAYS, seed=500 + i, flare_windows=tuple((s, s + rng.randrange(8, 14)) for s in flare),
        food_effects=foods, late_night_effect=late, high_stress_effect=stress, period_effects=periods,
        missed_dose_effect=dose, stress_periods=EXAM_PERIODS,
    ), frozenset(truth)


def records(sim: list[SimDay], menu: dict[str, MenuItem], config: SimConfig) -> list[DayRecord]:
    """Diary days as the Pattern Finder sees them (the same conversion the app does)."""
    scores = {START + timedelta(days=s.offset): hbi(s.items).score for s in sim if s.logged}
    kinds = kind_by_day(detect_periods(scores, "HBI"))
    out, bedtimes = [], []
    for s in sim:
        if not s.logged:
            continue
        d = START + timedelta(days=s.offset)
        comps: dict[Component, Level] = {}
        for f in s.foods:
            for c, lvl in menu[f.name].components.items():
                comps[c] = max(comps.get(c, Level.NONE), lvl)
        out.append(DayRecord(
            d, index=scores[d], food_reaction=any(f.reactions for f in s.foods), components=comps,
            late_night=is_late_night(s.bedtime, bedtimes), sleep_hours=sleep_hours(s.bedtime, s.wake_time),
            sleep_quality=s.sleep_quality, stress=s.stress,
            period_types=frozenset(p.type for p in config.stress_periods if p.start <= s.offset <= p.end),
            medication=s.medication, period_kind=kinds.get(d),
        ))
        bedtimes.append(s.bedtime)
    return out


# In the simulator, as in life, some habits come together: an exam period brings high stress, more late
# nights and more missed doses; a late night means short and often poor sleep; a flare brings poor sleep.
# When one of these truly raises symptoms, its companions really are followed by more bad days, so the
# app is right to call them "linked" (it never says "caused", and it adds an "often happens together
# with" note). They are counted apart as "companion" reports: neither a clean hit nor a false report.
# Food components are independent of all of them, so a wrong food report is always a false report.
HABITS = frozenset({LATE_NIGHT, SHORT_SLEEP, POOR_SLEEP, HIGH_STRESS, "period:exam", MISSED_DOSE})


def is_companion(factor: str, truth: frozenset[str], in_flare: bool, overlaps: tuple[str, ...]) -> bool:
    if factor in HABITS and truth & HABITS:
        return True
    if factor == POOR_SLEEP and in_flare:
        return True
    return any(o in truth for o in overlaps)


def evaluate_patient(args: tuple[int, list[MenuItem], list[Component]]) -> dict:
    i, menu, candidates = args
    config, truth = patient_config(i, candidates)
    sim = simulate(config, menu)
    by_name = {m.name: m for m in menu}
    out: dict = {"truth": sorted(truth), "horizons": {}}
    for h in HORIZONS:
        results = find_patterns(records([s for s in sim if s.offset < h], by_name, replace(config, days=h)))
        flagged = {r.factor for r in results if r.label == LIKELY}
        overlaps = {r.factor: r.overlaps_with for r in results}
        related = {f for f in flagged - truth if is_companion(f, truth, bool(config.flare_windows), overlaps[f])}
        out["horizons"][h] = {"hits": sorted(flagged & truth), "related": sorted(related),
                              "false": sorted(flagged - truth - related), "missed": sorted(truth - flagged)}
    return out


def cohort(patients: int, menu: list[MenuItem], workers: int) -> dict:
    candidates = food_candidates(menu)
    jobs = [(i, menu, candidates) for i in range(patients)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(evaluate_patient, jobs, chunksize=4))
    group = lambda f: f.split(":", 1)[0]  # noqa: E731
    by_horizon = {}
    for h in HORIZONS:
        hits = sum(len(r["horizons"][h]["hits"]) for r in rows)
        related = sum(len(r["horizons"][h]["related"]) for r in rows)
        false = sum(len(r["horizons"][h]["false"]) for r in rows)
        missed = sum(len(r["horizons"][h]["missed"]) for r in rows)
        clean = [r for r in rows if not r["truth"]]
        recall_by_group = {}
        for g in ("food", "sleep", "stress", "period", "medication"):
            found = sum(1 for r in rows for f in r["horizons"][h]["hits"] if group(f) == g)
            total = sum(1 for r in rows for f in r["truth"] if group(f) == g)
            recall_by_group[g] = {"found": found, "of": total, "recall": round(found / total, 3) if total else None}
        food_false = sum(1 for r in rows for f in r["horizons"][h]["false"] if group(f) == "food")
        by_horizon[h] = {
            "food_false_reports": food_false,
            "patients_with_a_false_food_report": sum(1 for r in rows if any(group(f) == "food" for f in r["horizons"][h]["false"])),
            "true_contributors": hits + missed, "found": hits, "related_reports": related, "false_reports": false,
            "precision_strict": round(hits / (hits + related + false), 3) if hits + related + false else None,
            "precision": round(hits / (hits + false), 3) if hits + false else None,
            "recall": round(hits / (hits + missed), 3) if hits + missed else None,
            "patients_with_a_false_report": sum(1 for r in rows if r["horizons"][h]["false"]),
            "no_contributor_patients": len(clean),
            "no_contributor_patients_with_any_report": sum(1 for r in clean if r["horizons"][h]["false"] or r["horizons"][h]["related"]),
            "recall_by_group": recall_by_group,
        }
    return {"patients": patients, "days": DAYS, "food_candidates": [c.value for c in candidates], "by_horizon": by_horizon,
            "contributors_per_patient": round(statistics.mean(len(r["truth"]) for r in rows), 2)}


# ---------------------------------------------------------------- red-flag suite

def red_flags() -> dict:
    suite = json.loads((SETS / "redflag.json").read_text(encoding="utf-8"))
    out: dict = {"by_language": {}, "missed": [], "false_alarms": [], "wrong_category": []}
    for lang in ("en", "bn", "bn_latin"):
        pos = [p for p in suite["positive"] if p["lang"] == lang]
        neg = [n for n in suite["negative"] if n["lang"] == lang]
        caught = 0
        for p in pos:
            result = check_red_flags(p["text"])
            if result.triggered:
                caught += 1
                if p["category"] not in result.categories:
                    out["wrong_category"].append(p["text"])
            else:
                out["missed"].append(p["text"])
        alarms = [n["text"] for n in neg if check_red_flags(n["text"]).triggered]
        out["false_alarms"] += alarms
        out["by_language"][lang] = {"phrases": len(pos), "caught": caught, "ordinary_messages": len(neg), "false_alarms": len(alarms)}
    out["phrases"] = sum(v["phrases"] for v in out["by_language"].values())
    out["caught"] = sum(v["caught"] for v in out["by_language"].values())
    out["ordinary_messages"] = sum(v["ordinary_messages"] for v in out["by_language"].values())
    return out


# ---------------------------------------------------------------- verdict engine on the real seeds

PROFILES = {
    "cd_remission": Profile(Diagnosis.CD, DiseaseState.REMISSION),
    "cd_flare": Profile(Diagnosis.CD, DiseaseState.FLARE),
    "cd_stricturing": Profile(Diagnosis.CD, DiseaseState.REMISSION, frozenset({"stricturing"})),
    "cd_remission_lactose": Profile(Diagnosis.CD, DiseaseState.REMISSION, frozenset({"lactose_intolerant"})),
    "cd_remission_ibs": Profile(Diagnosis.CD, DiseaseState.REMISSION, frozenset({"ibs_like_symptoms"})),
    "uc_remission": Profile(Diagnosis.UC, DiseaseState.REMISSION),
    "uc_flare": Profile(Diagnosis.UC, DiseaseState.FLARE),
}


def verdicts(knowledge: MemoryKnowledge) -> dict:
    rules, pool = knowledge.rules(), knowledge.alternatives_pool()
    dishes = list(knowledge.graph.dishes.values())
    table: dict = {}
    uncited = 0
    assessed = 0
    for key, profile in PROFILES.items():
        counts: Counter = Counter()
        for dish in dishes:
            v = assess_meal([dish.to_evidence()], profile, rules, {}, pool).dishes[0]
            counts[v.verdict.value] += 1
            assessed += 1
            again = assess_meal([dish.to_evidence()], profile, rules, {}, pool).dishes[0]
            if again != v:
                raise AssertionError(f"verdict for {dish.id} changed between two runs")
            if v.verdict in (Verdict.CAUTION, Verdict.LIKELY_TRIGGER) and not any(a.rule_ids for a in v.components):
                uncited += 1
        table[key] = dict(counts)
    stricture = PROFILES["cd_stricturing"]
    risky = [d for d in dishes if any((d.components.get(c) or Level.NONE) >= Level.MEDIUM for c in STRICTURE_COMPONENTS)]
    red = [d for d in risky if assess_meal([d.to_evidence()], stricture, rules, {}, pool).dishes[0].verdict == Verdict.LIKELY_TRIGGER]
    return {"dishes": len(dishes), "assessments": assessed, "by_profile": table, "identical_on_repeat": assessed,
            "caution_or_trigger_without_a_rule": uncited,
            "stricture_rule": {"dishes_with_fibre_skins_seeds_nuts": len(risky), "rated_likely_trigger": len(red),
                               "not_rated_likely_trigger": sorted(d.id for d in risky if d not in red)}}


def dish_names(knowledge: MemoryKnowledge) -> dict:
    """Every stored name and spelling should lead back to its own dish."""
    out = {}
    for label, pick in (("bangla", lambda d: [d.name_bn]), ("english", lambda d: [d.name_en]),
                        ("spellings", lambda d: list(d.raw.get("aliases", []) or []))):
        total = right = 0
        wrong = []
        for dish in knowledge.graph.dishes.values():
            for name in pick(dish):
                if not name:
                    continue
                total += 1
                found = knowledge.resolve(name)
                if found is not None and found.dish_id == dish.id:
                    right += 1
                else:
                    wrong.append(name)
        out[label] = {"names": total, "resolved_to_own_dish": right, "wrong": wrong[:10]}
    return out


def engine_latency(knowledge: MemoryKnowledge, runs: int = 300) -> dict:
    rules, pool = knowledge.rules(), knowledge.alternatives_pool()
    dishes = list(knowledge.graph.dishes.values())
    rng = random.Random(3)
    times = []
    for _ in range(runs):
        meal = [d.to_evidence() for d in rng.sample(dishes, 3)]
        t = time.perf_counter()
        assess_meal(meal, PROFILES["cd_remission"], rules, {}, pool)
        times.append((time.perf_counter() - t) * 1000)
    times.sort()
    return {"runs": runs, "dishes_per_meal": 3, "p50_ms": round(times[len(times) // 2], 2), "p90_ms": round(times[int(len(times) * 0.9)], 2)}


# ---------------------------------------------------------------- report

def pct(n: int, d: int) -> str:
    return f"{100 * n / d:.0f}%" if d else "n/a"


def markdown(s: dict) -> str:
    c, r, v, n = s["cohort"], s["red_flags"], s["verdicts"], s["dish_names"]
    lines = [
        "# Evaluation results",
        "",
        f"Run on {s['date']} with `uv run python -m happygut_api.evaluate` (app {s['version']}, Pattern Finder `{s['pattern_version']}`). "
        "The run is deterministic: the same command gives the same numbers.",
        "",
        "> **Read this first.** Every patient in section 1 is **simulated**. The simulator gives each one hidden contributors "
        "(for example \"high-fat food raises symptoms\"), and we measure whether the Pattern Finder recovers them. "
        "This shows the method works when a real effect exists; it is not evidence about real patients. "
        "No language model is involved in any number on this page.",
        "",
        "## 1. Flare Pattern Finder on a simulated cohort",
        "",
        f"{c['patients']} simulated patients, {c['days']} days each, on a menu built from the {v['dishes']} real dishes in the knowledge layer. "
        f"Each patient has 0-5 hidden contributors (average {c['contributors_per_patient']}): a food component "
        f"({', '.join(c['food_candidates'])}), late nights, high-stress days, exam periods, missed doses. "
        "15% have none. About half also have a flare, which adds noise.",
        "",
        "| Days of diary | Hidden contributors | Found | Recall | Companion reports | False reports | Precision | Precision counting companions as errors |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for h, row in c["by_horizon"].items():
        lines.append(f"| {h} | {row['true_contributors']} | {row['found']} | {pct(row['found'], row['true_contributors'])} | "
                     f"{row['related_reports']} | {row['false_reports']} | {pct(row['found'], row['found'] + row['false_reports'])} | "
                     f"{pct(row['found'], row['found'] + row['false_reports'] + row['related_reports'])} |")
    last = c["by_horizon"][str(HORIZONS[-1])]
    lines += [
        "",
        "- **Found:** the app labels the factor \"likely contributor\" and it is one of that patient's hidden contributors.",
        "- **Companion report:** the app labels a habit that comes together with a true one. In the simulator, as in life, an exam period brings "
        "high stress, late nights and missed doses; a late night means short, poor sleep; a flare brings poor sleep. Those habits really are followed "
        "by more bad days, so \"linked\" is a fair description (the app never says \"caused\" and adds an \"often happens together with\" note), "
        "but the app cannot tell which one is the driver.",
        "- **False report:** labelled \"likely contributor\" with no hidden effect behind it and no companion.",
        f"- **Food only** (foods are independent of the habits, so this is the cleanest check): at {HORIZONS[-1]} days "
        f"{last['recall_by_group']['food']['found']} of {last['recall_by_group']['food']['of']} hidden food contributors were found, with "
        f"{last['food_false_reports']} false food reports across {last['patients_with_a_false_food_report']} of {c['patients']} patients. "
        "Each patient is tested on 13 food components, so some false reports are expected; lowering them is the next piece of work on the method.",
        f"- Patients with no hidden contributor who still got a report at {HORIZONS[-1]} days: "
        f"{last['no_contributor_patients_with_any_report']} of {last['no_contributor_patients']}.",
        "",
        f"Recall by kind of factor at {HORIZONS[-1]} days:",
        "",
        "| Kind | Found | Of | Recall |",
        "|---|---|---|---|",
    ]
    names = {"food": "Food component", "sleep": "Late nights", "stress": "High-stress days", "period": "Exam periods", "medication": "Missed doses"}
    for g, row in last["recall_by_group"].items():
        lines.append(f"| {names[g]} | {row['found']} | {row['of']} | {pct(row['found'], row['of'])} |")
    lines += [
        "",
        "## 2. Red-flag sentinel",
        "",
        f"{r['phrases']} emergency phrases and {r['ordinary_messages']} ordinary messages (`evals/sets/redflag.json`). "
        "The phrases were written by the team, so this is a development suite, not an independent test.",
        "",
        "| Language | Emergency phrases caught | Ordinary messages wrongly flagged |",
        "|---|---|---|",
    ]
    labels = {"en": "English", "bn": "Bangla", "bn_latin": "Bangla in English letters"}
    for lang, row in r["by_language"].items():
        lines.append(f"| {labels[lang]} | {row['caught']} of {row['phrases']} | {row['false_alarms']} of {row['ordinary_messages']} |")
    lines += ["", "Two phrases added on 2026-11-17 (\"I haven't passed urine all day and feel very dizzy\" and a Bangla sentence with a word between "
              "\"stomach\" and \"pain\") were missed on the first run. The detector was extended, and both are now permanent tests."]
    if r["missed"]:
        lines += ["", "Missed: " + "; ".join(f"\"{t}\"" for t in r["missed"])]
    if r["false_alarms"]:
        lines += ["", "Wrongly flagged: " + "; ".join(f"\"{t}\"" for t in r["false_alarms"])]
    sr = v["stricture_rule"]
    lines += [
        "",
        "## 3. Verdict engine on the real dishes",
        "",
        f"{v['dishes']} dishes × {len(v['by_profile'])} patient profiles = {v['assessments']} verdicts, with no personal history.",
        "",
        "| Profile | Likely OK | Caution | Likely trigger | Not sure |",
        "|---|---|---|---|---|",
    ]
    profile_names = {"cd_remission": "Crohn's, remission", "cd_flare": "Crohn's, flare", "cd_stricturing": "Crohn's with a stricture",
                     "cd_remission_lactose": "Crohn's, remission, lactose intolerant", "cd_remission_ibs": "Crohn's, remission, IBS-like symptoms",
                     "uc_remission": "Ulcerative colitis, remission", "uc_flare": "Ulcerative colitis, flare"}
    for key, counts in v["by_profile"].items():
        lines.append(f"| {profile_names[key]} | {counts.get('likely_ok', 0)} | {counts.get('caution', 0)} | "
                     f"{counts.get('likely_trigger', 0)} | {counts.get('not_sure', 0)} |")
    lines += [
        "",
        "In remission with nothing else in the profile, no dish gets a warning from the guidelines alone: the stronger rules belong to a stricture, "
        "lactose intolerance, IBS-like symptoms or a flare. For a person in remission the warnings come from their own diary (the Pattern Finder), "
        "which is the point of the personal layer.",
        "",
        f"- **Same answer every time:** {v['identical_on_repeat']} of {v['assessments']} verdicts were identical when computed twice.",
        f"- **Every warning has a rule behind it:** {v['assessments'] and v['caution_or_trigger_without_a_rule']} \"caution\" or \"likely trigger\" verdicts had no cited Rule Card.",
        f"- **Stricture rule:** {sr['rated_likely_trigger']} of {sr['dishes_with_fibre_skins_seeds_nuts']} dishes with medium or high insoluble fibre, skins, seeds or nuts "
        "are rated \"likely trigger\" for a person with a stricture.",
        f"- **Speed:** the engine rates a three-dish meal in {s['engine_latency']['p50_ms']} ms (median; 90% under {s['engine_latency']['p90_ms']} ms, {s['engine_latency']['runs']} runs). "
        "This is the engine alone, not the full check with a photo and a written explanation.",
        "",
        "## 4. Dish names",
        "",
        "Each stored name is looked up and must return its own dish (this checks the index for clashes; it is not a test on unseen spellings).",
        "",
        "| Kind of name | Names | Lead to their own dish |",
        "|---|---|---|",
        f"| Bangla | {n['bangla']['names']} | {n['bangla']['resolved_to_own_dish']} |",
        f"| English | {n['english']['names']} | {n['english']['resolved_to_own_dish']} |",
        f"| Other spellings (English letters and Bangla variants) | {n['spellings']['names']} | {n['spellings']['resolved_to_own_dish']} |",
        "",
        "## 5. Knowledge layer",
        "",
        f"{s['knowledge']['dishes']} dishes and {s['knowledge']['rule_cards']} Rule Cards, all reviewed by an LLM judge against published sources "
        f"(not by clinicians). {s['knowledge']['rule_cards_with_quote']} of {s['knowledge']['rule_cards']} Rule Cards carry at least one exact sentence "
        "retrieved from a paper confirmed by DOI or PMID.",
        "",
        "## Not measured yet",
        "",
        "- Photo recognition accuracy on Bangladeshi meal photos (needs a labelled photo set).",
        "- Agreement of verdicts with a dietitian-labelled food list.",
        "- Full check time on a phone connection, including the photo and the written explanation.",
        "- Anything on real patients.",
        "",
    ]
    return "\n".join(lines)


def knowledge_counts(knowledge: MemoryKnowledge) -> dict:
    import yaml

    cards = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted((SEEDS / "rule_cards").glob("*.yaml"))]
    with_quote = sum(1 for c in cards if any((src.get("quote") or "").strip() for src in c.get("sources", [])))
    return {"dishes": len(knowledge.graph.dishes), "rule_cards": len(cards), "rule_cards_with_quote": with_quote}


def for_web(s: dict) -> dict:
    """The few numbers the app's "How it works" page shows."""
    c = s["cohort"]
    last = c["by_horizon"][str(HORIZONS[-1])]
    return {
        "date": s["date"],
        "cohort": {
            "patients": c["patients"], "days": c["days"],
            "horizons": [{"days": int(h), "found": r["found"], "of": r["true_contributors"], "false_reports": r["false_reports"]}
                         for h, r in c["by_horizon"].items()],
            "food": {"found": last["recall_by_group"]["food"]["found"], "of": last["recall_by_group"]["food"]["of"]},
        },
        "red_flags": {"caught": s["red_flags"]["caught"], "phrases": s["red_flags"]["phrases"],
                      "false_alarms": len(s["red_flags"]["false_alarms"]), "ordinary": s["red_flags"]["ordinary_messages"]},
        "verdicts": {"assessments": s["verdicts"]["assessments"], "identical": s["verdicts"]["identical_on_repeat"],
                     "dishes": s["verdicts"]["dishes"], "profiles": len(s["verdicts"]["by_profile"]),
                     "stricture": {"rated": s["verdicts"]["stricture_rule"]["rated_likely_trigger"],
                                   "of": s["verdicts"]["stricture_rule"]["dishes_with_fibre_skins_seeds_nuts"]}},
        "knowledge": {"dishes": s["knowledge"]["dishes"], "rule_cards": s["knowledge"]["rule_cards"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patients", type=int, default=200)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    from happygut_engine.patterns import DEFAULT_PATTERN_CONFIG

    knowledge = MemoryKnowledge.from_seeds(SEEDS)
    menu = build_menu(knowledge)
    started = time.time()
    summary = {
        "date": date.today().isoformat(), "version": __version__, "pattern_version": DEFAULT_PATTERN_CONFIG.version,
        "simulated_cohort": True,
        "cohort": cohort(args.patients, menu, args.workers),
        "red_flags": red_flags(),
        "verdicts": verdicts(knowledge),
        "dish_names": dish_names(knowledge),
        "engine_latency": engine_latency(knowledge),
        "knowledge": knowledge_counts(knowledge),
    }
    summary = json.loads(json.dumps(summary))  # horizon keys become strings, as they are when read back
    out = ROOT / "evals"
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "RESULTS.md").write_text(markdown(summary), encoding="utf-8")
    web = ROOT / "apps" / "web" / "src" / "data" / "evaluation.json"
    web.write_text(json.dumps(for_web(summary), indent=2) + "\n", encoding="utf-8")
    print(f"done in {time.time() - started:.0f}s: evals/summary.json, evals/RESULTS.md, {web.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
