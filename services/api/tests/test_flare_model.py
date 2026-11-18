"""Flare-risk model v1: the features never look ahead, the metrics are right, and the served model explains itself."""

from __future__ import annotations

import math
from datetime import timedelta

import pytest
from happygut_engine import THRESHOLDS, detect_periods, kind_by_day
from happygut_engine.flare_features import FEATURES, features
from happygut_engine.simulate import simulate

from happygut_api import evaluate, flare_model
from happygut_api.demo import build_menu
from happygut_api.knowledge import MemoryKnowledge

KNOWLEDGE = MemoryKnowledge.from_seeds(evaluate.SEEDS)
MENU = build_menu(KNOWLEDGE)


def patient_records(i: int):
    config, _ = evaluate.patient_config(i, evaluate.food_candidates(MENU))
    return evaluate.records(simulate(config, MENU), {m.name: m for m in MENU}, config)


def test_features_never_use_days_after_the_one_asked_about():
    recs = patient_records(5)
    scores = {r.day: r.index for r in recs if r.index is not None}
    for r in recs[20::17]:
        t = r.day
        known = kind_by_day(detect_periods({d: v for d, v in scores.items() if d <= t}, "HBI"))
        flare_days = {d for d, k in known.items() if k == "flare"}
        full = features(recs, t, active_at=5, stressful_period_soon=False, flare_days=flare_days)
        cut = features([x for x in recs if x.day <= t], t, active_at=5, stressful_period_soon=False, flare_days=flare_days)
        assert full.keys() == set(FEATURES)
        assert all((math.isnan(full[f]) and math.isnan(cut[f])) or full[f] == cut[f] for f in FEATURES), t


def test_flare_history_only_counts_what_was_known_that_day():
    recs = patient_records(5)
    t = recs[60].day
    later_flare = {t + timedelta(days=1)}  # a flare recognised after day t must not show up on day t
    row = features(recs, t, active_at=5, stressful_period_soon=False, flare_days=later_flare)
    assert row["flare_days_30"] == 0 and row["days_since_flare"] == 180


def test_metrics_on_known_values():
    assert flare_model.roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]) == 0.75
    assert flare_model.roc_auc([0, 1], [0.5, 0.5]) == 0.5  # ties count half
    assert flare_model.roc_auc([1, 1], [0.2, 0.3]) is None
    assert flare_model.average_precision([1, 0, 1], [0.9, 0.8, 0.1]) == round((1 + 2 / 3) / 2, 3)
    top = flare_model.at_flag_rate([1, 0, 0, 1, 0], [0.9, 0.1, 0.2, 0.3, 0.8], 0.4)
    assert top["caught"] == 1 and top["of"] == 2 and top["precision"] == 0.5


def test_patients_are_split_never_days():
    splits = {i: flare_model.split_of(i) for i in range(200)}
    assert sum(v == "test" for v in splits.values()) == 50 and sum(v == "train" for v in splits.values()) == 100


MODEL = flare_model.load()
needs_model = pytest.mark.skipif(MODEL is None, reason="trained model not present")


@needs_model
def test_the_shipped_model_beats_the_rules_on_held_out_patients():
    test = MODEL.card["test"]
    assert MODEL.card["trained_on"] == "simulated patients only"
    assert test["v1"]["roc_auc"] > test["v0"]["roc_auc"]  # spec 003 SC-005
    assert MODEL.card["features"] == list(FEATURES)


@needs_model
def test_a_prediction_explains_itself():
    recs = patient_records(9)
    row = features(recs, recs[-1].day, active_at=THRESHOLDS["HBI"].active_at, stressful_period_soon=True, flare_days=set())
    out = MODEL.predict(row)
    assert 0 <= out["probability"] <= 1 and out["level"] in ("low", "raised", "high")
    assert len(out["drivers"]) <= 3 and all(d["effect"] > 0 and d["feature"] in FEATURES for d in out["drivers"])
    # SHAP values add up to the model's raw score, so the drivers are exact, not a guess.
    import numpy as np

    x = np.array([[row[f] for f in FEATURES]])
    contrib = MODEL.booster.predict(x, pred_contrib=True)[0]
    raw = MODEL.booster.predict(x, raw_score=True)[0]
    assert abs(contrib.sum() - raw) < 1e-6
