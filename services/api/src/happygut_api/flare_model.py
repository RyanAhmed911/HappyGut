"""Flare-risk model v1: gradient-boosted trees (LightGBM), trained only on the simulated cohort.

Question (spec 003 SC-005): "does a flare start within the next 3 days?", asked on days the person
is not already in a flare. Features come from ``happygut_engine.flare_features`` (the diary up to
that day, nothing later). Drivers are exact per-prediction SHAP values from LightGBM's TreeSHAP
(``pred_contrib``), so the app can show what raised the estimate.

    uv run python -m happygut_api.flare_model train          # ~3 minutes on 4 cores

writes the model (``models/flare-risk-v1.txt``), its card (``models/flare-risk-v1.json``) and
``evals/FLARE_MODEL.md``. Training is deterministic.

Limits, said wherever the model is shown: it learned from simulated patients, so its numbers say
the method works when the effects exist, not how it will do on real patients; it is an estimate,
never a diagnosis, and never a reason to change a medicine.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from happygut_engine import (
    THRESHOLDS,
    detect_periods,
    find_patterns,
    flare_risk,
    kind_by_day,
)
from happygut_engine.flare_features import FEATURES, features
from happygut_engine.simulate import simulate

VERSION = "flare-risk-v1.0"
MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "flare-risk-v1.txt"
CARD_PATH = MODEL_DIR / "flare-risk-v1.json"
HORIZON = 3
WARM_UP_DAYS = 14  # the first two weeks have too little history to say anything
PATTERN_EVERY = 7  # v0 re-runs the Pattern Finder weekly in the comparison (it is the slow part)
PATIENTS = 200
PARAMS = {
    "objective": "binary", "learning_rate": 0.03, "num_leaves": 15, "min_data_in_leaf": 40, "feature_fraction": 0.8,
    "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 1.0, "seed": 7, "deterministic": True,
    "force_row_wise": True, "num_threads": 1, "verbose": -1,
}


# ---------------------------------------------------------------- data

def split_of(i: int) -> str:
    """Patients are split, never days: test patients are never seen in training."""
    return {0: "test", 1: "valid"}.get(i % 4, "train")


def patient_rows(args: tuple) -> list[dict]:
    """Feature rows, labels and the v0 score for one simulated patient."""
    from . import evaluate

    i, menu, candidates, with_v0 = args
    config, _ = evaluate.patient_config(i, candidates)
    sim = simulate(config, menu)
    recs = evaluate.records(sim, {m.name: m for m in menu}, config)
    scores = {r.day: r.index for r in recs if r.index is not None}
    active_at = THRESHOLDS["HBI"].active_at
    starts = sorted(p.start for p in detect_periods(scores, "HBI") if p.kind == "flare")  # ground truth: the full history
    periods = [(evaluate.START + timedelta(days=p.start), p.type) for p in config.stress_periods]
    rows, patterns, patterns_at = [], [], None
    for r in recs:
        t = r.day
        if (t - evaluate.START).days < WARM_UP_DAYS:
            continue
        known = kind_by_day(detect_periods({d: v for d, v in scores.items() if d <= t}, "HBI"))  # as known on day t
        if known.get(t) == "flare":
            continue  # already in a flare: the question is about new ones
        soon = [kind for start, kind in periods if t < start <= t + timedelta(days=HORIZON)]
        x = features(recs, t, active_at=active_at, stressful_period_soon=bool(soon),
                     flare_days={d for d, k in known.items() if k == "flare"})
        row = {"patient": i, "split": split_of(i), "day": t.isoformat(), "x": [x[f] for f in FEATURES],
               "y": int(any(t < s <= t + timedelta(days=HORIZON) for s in starts))}
        if with_v0:
            past = [x for x in recs if x.day <= t]
            past[-1] = replace(past[-1], period_kind=known.get(t))  # no peeking at the later verdict for today
            if patterns_at is None or (t - patterns_at).days >= PATTERN_EVERY:
                patterns, patterns_at = find_patterns(past), t
            row["v0"] = flare_risk(past, patterns, soon, as_of=t).score / 100
        rows.append(row)
    return rows


def cohort_rows(patients: int, workers: int) -> list[dict]:
    from . import evaluate
    from .demo import build_menu
    from .knowledge import MemoryKnowledge

    knowledge = MemoryKnowledge.from_seeds(evaluate.SEEDS)
    menu = build_menu(knowledge)
    candidates = evaluate.food_candidates(menu)
    jobs = [(i, menu, candidates, split_of(i) == "test") for i in range(patients)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return [row for rows in pool.map(patient_rows, jobs, chunksize=2) for row in rows]


# ---------------------------------------------------------------- metrics (no extra dependencies)

def roc_auc(y: list[int], s: list[float]) -> float | None:
    """Probability that a random positive day scores above a random negative day (ties count half)."""
    pairs = sorted(zip(s, y))
    pos = sum(y)
    neg = len(y) - pos
    if not pos or not neg:
        return None
    rank_sum, i = 0.0, 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        rank_sum += avg_rank * sum(label for _, label in pairs[i:j])
        i = j
    return round((rank_sum - pos * (pos + 1) / 2) / (pos * neg), 3)


def average_precision(y: list[int], s: list[float]) -> float | None:
    order = sorted(range(len(y)), key=lambda k: -s[k])
    pos = sum(y)
    if not pos:
        return None
    hits, total = 0, 0.0
    for rank, k in enumerate(order, 1):
        if y[k]:
            hits += 1
            total += hits / rank
    return round(total / pos, 3)


def at_flag_rate(y: list[int], s: list[float], rate: float) -> dict:
    """Flag the top ``rate`` share of days: how many flare starts are caught, and how many flags are right."""
    n = max(1, round(len(s) * rate))
    top = sorted(range(len(s)), key=lambda k: -s[k])[:n]
    caught = sum(y[k] for k in top)
    return {"flagged_share": rate, "caught": caught, "of": sum(y), "recall": round(caught / max(1, sum(y)), 3),
            "precision": round(caught / n, 3)}


# ---------------------------------------------------------------- training

def train(patients: int = PATIENTS, workers: int = 4) -> dict:
    import lightgbm as lgb
    import numpy as np

    started = time.time()
    rows = cohort_rows(patients, workers)
    part = {k: [r for r in rows if r["split"] == k] for k in ("train", "valid", "test")}
    as_xy = lambda rs: (np.array([r["x"] for r in rs], dtype=float), np.array([r["y"] for r in rs]))
    (xt, yt), (xv, yv), (xs, ys) = as_xy(part["train"]), as_xy(part["valid"]), as_xy(part["test"])

    # 1. Pick the number of trees on the validation patients, 2. refit on train + validation.
    probe = lgb.train(PARAMS, lgb.Dataset(xt, yt, feature_name=list(FEATURES)), num_boost_round=1500,
                      valid_sets=[lgb.Dataset(xv, yv, feature_name=list(FEATURES))],
                      callbacks=[lgb.early_stopping(100, verbose=False)])
    rounds = max(50, probe.best_iteration)
    model = lgb.train(PARAMS, lgb.Dataset(np.vstack([xt, xv]), np.concatenate([yt, yv]), feature_name=list(FEATURES)),
                      num_boost_round=rounds)

    # Levels for the app, from the training-time predictions: "high" = the top 5% of days, "raised" = the top 20%.
    fitted = sorted(model.predict(np.vstack([xt, xv])))
    raised_at, high_at = fitted[int(len(fitted) * 0.80)], fitted[int(len(fitted) * 0.95)]

    p_test = [float(v) for v in model.predict(xs)]
    v0 = [r["v0"] for r in part["test"]]
    y = [int(v) for v in ys]
    base = sum(y) / len(y)
    brier = round(sum((p - t) ** 2 for p, t in zip(p_test, y)) / len(y), 4)
    gain = model.feature_importance("gain")
    card = {
        "version": VERSION,
        "question": f"Does a flare start within the next {HORIZON} days? (asked on days not already in a flare)",
        "trained_on": "simulated patients only",
        "features": list(FEATURES),
        "params": {**PARAMS, "num_boost_round": rounds},
        "levels": {"raised_at": round(raised_at, 4), "high_at": round(high_at, 4)},
        "data": {"patients": patients, "days_per_patient": 120, "warm_up_days": WARM_UP_DAYS,
                 **{f"{k}_patients": len({r["patient"] for r in v}) for k, v in part.items()},
                 **{f"{k}_days": len(v) for k, v in part.items()},
                 **{f"{k}_flare_start_days": sum(r["y"] for r in v) for k, v in part.items()}},
        "test": {
            "base_rate": round(base, 4),
            "v1": {"roc_auc": roc_auc(y, p_test), "average_precision": average_precision(y, p_test), "brier": brier,
                   "top_10_percent": at_flag_rate(y, p_test, 0.10), "top_20_percent": at_flag_rate(y, p_test, 0.20)},
            "v0": {"roc_auc": roc_auc(y, v0), "average_precision": average_precision(y, v0),
                   "top_10_percent": at_flag_rate(y, v0, 0.10), "top_20_percent": at_flag_rate(y, v0, 0.20)},
        },
        "importance": [{"feature": f, "gain": round(float(g), 1)} for f, g in sorted(zip(FEATURES, gain), key=lambda t: -t[1])],
        "trained": date.today().isoformat(),
        "seconds": round(time.time() - started),
    }
    MODEL_DIR.mkdir(exist_ok=True)
    model.save_model(str(MODEL_PATH))
    CARD_PATH.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    (Path(__file__).resolve().parents[4] / "evals" / "FLARE_MODEL.md").write_text(report(card), encoding="utf-8")
    return card


def report(c: dict) -> str:
    t, d = c["test"], c["data"]
    v1, v0 = t["v1"], t["v0"]
    better = v1["roc_auc"] is not None and v0["roc_auc"] is not None and v1["roc_auc"] > v0["roc_auc"]
    lines = [
        "# Flare-risk model v1 (LightGBM)",
        "",
        f"Trained {c['trained']} with `uv run python -m happygut_api.flare_model train` (deterministic). Model card: "
        "`services/api/src/happygut_api/models/flare-risk-v1.json`.",
        "",
        "> **Read this first.** The model learned from **simulated** patients and is tested on other simulated patients. "
        "It shows the method works when the effects exist in the data; it says nothing yet about real patients. "
        "In the app it is an estimate shown next to the rule-based outlook, never a diagnosis and never a reason to change a medicine.",
        "",
        f"**Question:** {c['question']}",
        "",
        f"**Data:** {d['patients']} simulated patients × {d['days_per_patient']} days. Patients are split, never days: "
        f"{d['train_patients']} train, {d['valid_patients']} pick the number of trees, {d['test_patients']} are held out. "
        f"The first {d['warm_up_days']} days of each patient are skipped. "
        f"Held-out: {d['test_days']} days, {d['test_flare_start_days']} of them with a flare starting within 3 days "
        f"({100 * t['base_rate']:.1f}%). Flare history is used only as it was known on each day.",
        "",
        "## v1 against the rule-based v0, on the held-out patients",
        "",
        "| | ROC AUC | Average precision | Flagging the top 10% of days: flare starts caught | Top 20%: caught |",
        "|---|---|---|---|---|",
        f"| **v1 (LightGBM)** | **{v1['roc_auc']}** | **{v1['average_precision']}** | {v1['top_10_percent']['caught']} of "
        f"{v1['top_10_percent']['of']} ({100 * v1['top_10_percent']['recall']:.0f}%) | {v1['top_20_percent']['caught']} of "
        f"{v1['top_20_percent']['of']} ({100 * v1['top_20_percent']['recall']:.0f}%) |",
        f"| v0 (rules) | {v0['roc_auc']} | {v0['average_precision']} | {v0['top_10_percent']['caught']} of "
        f"{v0['top_10_percent']['of']} ({100 * v0['top_10_percent']['recall']:.0f}%) | {v0['top_20_percent']['caught']} of "
        f"{v0['top_20_percent']['of']} ({100 * v0['top_20_percent']['recall']:.0f}%) |",
        f"| Chance | 0.5 | {t['base_rate']:.3f} | 10% | 20% |",
        "",
        f"Spec 003 SC-005 (v1 beats v0 on ROC AUC): **{'met' if better else 'not met'}**. "
        f"v1 Brier score {v1['brier']} (lower is better; always guessing the base rate scores "
        f"{t['base_rate'] * (1 - t['base_rate']):.4f}).",
        "",
        "## What the model relies on most",
        "",
        "| Feature | Gain |",
        "|---|---|",
        *[f"| {f['feature']} | {f['gain']} |" for f in c["importance"][:10]],
        "",
        "In the app each estimate shows its own top three drivers: exact SHAP values from LightGBM's TreeSHAP.",
        "",
        "## Limits",
        "",
        "- Simulated patients only; the simulator's flares start at random times, so part of every flare can't be predicted by any model.",
        "- The cohort uses the Harvey-Bradshaw Index (Crohn's). For ulcerative colitis (SCCAI) the app still shows the estimate, "
        "but the model has not been checked on that scale.",
        "- Not used on days already in a flare: the question is about new flares.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- serving

class FlareModel:
    def __init__(self, booster, card: dict):
        self.booster, self.card = booster, card

    def predict(self, row: dict[str, float]) -> dict:
        import numpy as np

        x = np.array([[row[f] for f in FEATURES]], dtype=float)
        p = float(self.booster.predict(x)[0])
        contrib = self.booster.predict(x, pred_contrib=True)[0][:-1]  # last column is the expected value
        drivers = sorted(((f, float(c)) for f, c in zip(FEATURES, contrib) if c > 0), key=lambda t: -t[1])[:3]
        levels = self.card["levels"]
        level = "high" if p >= levels["high_at"] else "raised" if p >= levels["raised_at"] else "low"
        return {
            "version": self.card["version"], "probability": round(p, 3), "level": level,
            "drivers": [{"feature": f, "value": None if math.isnan(row[f]) else row[f], "effect": round(c, 3)} for f, c in drivers],
            "trained_on": self.card["trained_on"],
            "test_roc_auc": self.card["test"]["v1"]["roc_auc"], "v0_test_roc_auc": self.card["test"]["v0"]["roc_auc"],
        }


@lru_cache(maxsize=1)
def load() -> FlareModel | None:
    """The trained model, or None when it (or LightGBM) isn't installed: the app then shows v0 only."""
    if not MODEL_PATH.exists() or not CARD_PATH.exists():
        return None
    try:
        import lightgbm as lgb
    except ImportError:
        return None
    return FlareModel(lgb.Booster(model_file=str(MODEL_PATH)), json.loads(CARD_PATH.read_text(encoding="utf-8")))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["train"])
    parser.add_argument("--patients", type=int, default=PATIENTS)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    card = train(args.patients, args.workers)
    print(json.dumps({"test": card["test"], "data": card["data"], "seconds": card["seconds"]}, indent=1))


if __name__ == "__main__":
    main()
