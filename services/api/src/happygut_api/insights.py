"""Personal insights (spec 003): day records from the diary, the Flare Pattern Finder, remission /
flare periods, the flare-risk outlook and the pre-visit report.

All numbers come from deterministic engine code. This module only gathers the inputs and
shapes the outputs; the client turns the numbers into sentences from fixed templates.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from happygut_engine import (
    THRESHOLDS,
    Component,
    DayRecord,
    DiseaseState,
    Level,
    PatternResult,
    PersonalEvidence,
    detect_periods,
    exposure,
    find_patterns,
    flare_risk,
    index_name,
    kind_by_day,
    personal_evidence,
)
from happygut_engine.flare_features import features as flare_features
from happygut_engine.flare_risk import DEFAULT_RISK_CONFIG
from happygut_engine.patterns import DEFAULT_PATTERN_CONFIG, LIKELY, POSSIBLE
from happygut_engine.periods import DEFAULT_PERIOD_CONFIG, FLARE, REMISSION, Period
from happygut_engine.weight import DEFAULT_WEIGHT_CONFIG, WeightEntry, weight_trend
from happygut_engine.weight import SOURCE as WEIGHT_SOURCE

from . import flare_model
from .diary import DiaryEntry, StressPeriodOut
from .knowledge import Knowledge
from .store import NotSupported, Patient, PeriodDecisions, Store

SCOPES = ("all", REMISSION, FLARE)
MIN_DAYS_FOR_PATTERNS = 14
MIN_DAYS_FOR_MODEL = 14  # the model was trained from day 14 of each diary
BEFORE_FLARE_DAYS = 7


@dataclass
class Bundle:
    entries: list[DiaryEntry]
    records: list[DayRecord]
    periods: list[Period]
    decisions: PeriodDecisions
    stress_periods: list[StressPeriodOut]
    index: str
    patterns: dict[str, list[PatternResult]]


class Insights:
    def __init__(self, store: Store, knowledge: Knowledge, timezone: str = "Asia/Dhaka"):
        self.store, self.knowledge = store, knowledge
        self.tz = ZoneInfo(timezone)
        self._cache: dict[str, tuple[int, Bundle]] = {}

    def forget(self, patient_id: str) -> None:
        self._cache.pop(patient_id, None)

    # ------------------------------------------------------------ time

    def now(self) -> datetime:
        return datetime.now(self.tz)

    def today(self) -> date:
        return self.now().date()

    # ------------------------------------------------------------ inputs

    def _components(self, entry: DiaryEntry) -> tuple[dict[Component, Level], bool]:
        comps: dict[Component, Level] = {}
        resolved = False
        for food in entry.foods:
            if not food.dish_id:
                continue
            try:
                evidence = self.knowledge.evidence(food.dish_id, 1.0, 1.0)
            except KeyError:
                continue
            resolved = True
            for comp, level in evidence.components.items():
                if level is not None:
                    comps[comp] = max(comps.get(comp, Level.NONE), level)
        return comps, resolved or not entry.foods

    async def bundle(self, patient: Patient) -> Bundle:
        version = await self.store.data_version(patient.id)
        cached = self._cache.get(patient.id)
        if cached and cached[0] == version:
            return cached[1]
        entries = await self.store.list_diary(patient.id)
        decisions = await self.store.period_decisions(patient.id)
        stress = await self.store.list_stress_periods(patient.id)
        name = index_name(patient.diagnosis)
        scores = {e.day: e.index.score for e in entries}
        periods = detect_periods(scores, name, sorted(decisions.rejected), decisions.manual)
        kinds = kind_by_day(periods)
        records = []
        for e in entries:
            comps, has_food_log = self._components(e)
            records.append(DayRecord(
                day=e.day, index=e.index.score, food_reaction=any(f.reactions for f in e.foods), components=comps,
                has_food_log=has_food_log and bool(e.foods), late_night=e.late_night, sleep_hours=e.sleep_hours,
                sleep_quality=e.sleep.quality, stress=e.stress,
                period_types=frozenset(p.type for p in stress if p.start <= e.day <= p.end),
                medication=e.medication, period_kind=kinds.get(e.day),
            ))
        bundle = Bundle(entries, records, periods, decisions, stress, name, {})
        self._cache[patient.id] = (version, bundle)
        return bundle

    def _patterns(self, b: Bundle, scope: str) -> list[PatternResult]:
        if scope not in b.patterns:
            b.patterns[scope] = find_patterns(b.records, None if scope == "all" else scope)
        return b.patterns[scope]

    # ------------------------------------------------------------ used by the meal check

    async def personal_evidence(self, patient: Patient) -> dict[Component, PersonalEvidence]:
        b = await self.bundle(patient)
        if len(b.records) < MIN_DAYS_FOR_PATTERNS:
            return {}
        return personal_evidence(self._patterns(b, "all"))

    def _flare_status(self, p: Period, d: PeriodDecisions) -> str:
        return "confirmed" if p.source == "user" or p.start in d.confirmed else "pending"

    async def effective_state(self, patient: Patient) -> DiseaseState:
        """A confirmed, ongoing flare sets the verdict's disease state (spec 003 FR-023)."""
        b = await self.bundle(patient)
        if not b.periods:
            return patient.state
        last = b.periods[-1]
        if last.kind == FLARE and self._flare_status(last, b.decisions) == "confirmed":
            return DiseaseState.FLARE
        return DiseaseState.REMISSION

    # ------------------------------------------------------------ outputs

    async def days(self, patient: Patient, limit: int = 180) -> list[dict]:
        b = await self.bundle(patient)
        out = []
        for e, r in list(zip(b.entries, b.records))[-limit:]:
            out.append({
                "date": e.day.isoformat(), "index": e.index.score, "stools": e.stool.count, "pain": e.pain,
                "wellbeing": e.wellbeing, "blood": e.stool.blood, "sleep_hours": e.sleep_hours, "late_night": e.late_night,
                "stress": e.stress, "medication": e.medication, "period_kind": r.period_kind,
                "tags": sorted(r.period_types), "food_reaction": r.food_reaction,
            })
        return out

    async def patterns(self, patient: Patient, scope: str) -> dict:
        b = await self.bundle(patient)
        scoped = [r for r in b.records if scope == "all" or r.period_kind == scope]
        enough = len(scoped) >= MIN_DAYS_FOR_PATTERNS
        results = []
        if enough:
            for p in self._patterns(b, scope):
                on = [r.index for r in scoped if r.index is not None and exposure(r, p.factor, DEFAULT_PATTERN_CONFIG)]
                off = [r.index for r in scoped if r.index is not None and exposure(r, p.factor, DEFAULT_PATTERN_CONFIG) is False]
                results.append({
                    "factor": p.factor, "group": p.group, "label": p.label, "exposures": p.exposures, "hits": p.hits,
                    "baseline_days": p.baseline_days, "baseline_hits": p.baseline_hits,
                    "exposed_rate": p.exposed_rate, "baseline_rate": p.baseline_rate, "probability": p.probability,
                    "ci_low": p.ci_low, "ci_high": p.ci_high, "window_days": list(p.window_days),
                    "overlaps_with": list(p.overlaps_with),
                    "avg_index_exposed": round(statistics.mean(on), 1) if on else None,
                    "avg_index_unexposed": round(statistics.mean(off), 1) if off else None,
                })
        return {
            "scope": scope, "days_logged": len(scoped), "min_days": MIN_DAYS_FOR_PATTERNS, "enough_data": enough,
            "index_name": b.index, "results": results, "version": DEFAULT_PATTERN_CONFIG.version,
            "is_synthetic": patient.is_synthetic,
        }

    def _summary(self, b: Bundle, kind: str) -> dict:
        pairs = [(e, r) for e, r in zip(b.entries, b.records) if r.period_kind == kind]
        if not pairs:
            return {"days": 0, "periods": 0}
        idx = [e.index.score for e, _ in pairs]
        sleep = [e.sleep_hours for e, _ in pairs if e.sleep_hours is not None]
        return {
            "days": len(pairs),
            "periods": sum(1 for p in b.periods if p.kind == kind),
            "avg_index": round(statistics.mean(idx), 1),
            "worst_index": max(idx),
            "avg_stools": round(statistics.mean(e.stool.count for e, _ in pairs), 1),
            "days_with_blood": sum(1 for e, _ in pairs if e.stool.blood != "none"),
            "avg_pain": round(statistics.mean(e.pain for e, _ in pairs), 1),
            "avg_sleep_hours": round(statistics.mean(sleep), 1) if sleep else None,
            "late_nights": sum(1 for _, r in pairs if r.late_night),
            "patterns_available": len(pairs) >= MIN_DAYS_FOR_PATTERNS,
        }

    def _before_flares(self, b: Bundle) -> list[dict]:
        watched = [p.factor for p in self._patterns(b, "all") if p.label in (LIKELY, POSSIBLE)] if len(b.records) >= MIN_DAYS_FOR_PATTERNS else []
        by_day = {r.day: r for r in b.records}
        out = []
        for p in b.periods:
            if p.kind != FLARE:
                continue
            window = [by_day[d] for d in (p.start - timedelta(days=i) for i in range(1, BEFORE_FLARE_DAYS + 1)) if d in by_day]
            factors = []
            for factor in watched:
                count = sum(1 for r in window if exposure(r, factor, DEFAULT_PATTERN_CONFIG))
                if count:
                    factors.append({"factor": factor, "count": count})
            factors.sort(key=lambda f: -f["count"])
            out.append({"flare_start": p.start.isoformat(), "days_logged": len(window), "factors": factors[:6]})
        return out

    async def periods(self, patient: Patient) -> dict:
        b = await self.bundle(patient)
        th = THRESHOLDS[b.index]
        periods = []
        for p in b.periods:
            status = self._flare_status(p, b.decisions) if p.kind == FLARE else "confirmed"
            periods.append({"kind": p.kind, "start": p.start.isoformat(), "end": p.end.isoformat(), "days": p.days,
                            "source": p.source, "ongoing": p.ongoing, "status": status})
        state = await self.effective_state(patient)
        return {
            "index_name": b.index,
            "thresholds": {"active_at": th.active_at, "remission_below": th.remission_below},
            "rules": {"window_days": DEFAULT_PERIOD_CONFIG.window_days, "active_days_needed": DEFAULT_PERIOD_CONFIG.active_days_needed,
                      "calm_days_to_end": DEFAULT_PERIOD_CONFIG.calm_days_to_end, "version": DEFAULT_PERIOD_CONFIG.version},
            "days_logged": len(b.entries), "min_days": DEFAULT_PERIOD_CONFIG.min_days_logged,
            "periods": periods, "pending": [p for p in periods if p["status"] == "pending"],
            "current_kind": b.periods[-1].kind if b.periods else None,
            "current_state": state.value,
            "summaries": {REMISSION: self._summary(b, REMISSION), FLARE: self._summary(b, FLARE)},
            "before_flares": self._before_flares(b),
            "is_synthetic": patient.is_synthetic,
        }

    async def flare_risk(self, patient: Patient) -> dict:
        b = await self.bundle(patient)
        today = self.today()
        horizon = DEFAULT_RISK_CONFIG.horizon_days
        upcoming = [p for p in b.stress_periods if today < p.start <= today + timedelta(days=horizon)]
        enough = len(b.records) >= MIN_DAYS_FOR_PATTERNS
        as_of = max(b.records[-1].day, today - timedelta(days=1)) if b.records else today
        out = flare_risk(b.records, self._patterns(b, "all") if enough else [], [p.type for p in upcoming], as_of)
        return {
            "model": self._flare_model(b, as_of, bool(upcoming)),
            "score": out.score, "level": out.level, "horizon_days": out.horizon_days, "as_of": out.as_of.isoformat(),
            "enough_data": enough, "version": out.version,
            "drivers": [{"code": d.code, "points": d.points, "factor": d.factor, "count": d.count, "value": d.value}
                        for d in out.drivers],
            "upcoming_periods": [{"id": p.id, "type": p.type, "name": p.name, "start": p.start.isoformat(),
                                  "end": p.end.isoformat(), "days_until": (p.start - today).days} for p in upcoming],
            "is_synthetic": patient.is_synthetic,
        }

    def _flare_model(self, b, as_of: date, period_soon: bool) -> dict | None:
        """The v1 estimate (flare_model.py), shown next to v0. None when the model isn't installed."""
        model = flare_model.load()
        if model is None:
            return None
        if b.records and b.records[-1].period_kind == FLARE:
            return {"version": model.card["version"], "in_flare": True}  # it predicts new flares only
        if len(b.records) < MIN_DAYS_FOR_MODEL:
            return {"version": model.card["version"], "in_flare": False, "enough_data": False}
        row = flare_features(b.records, as_of, active_at=THRESHOLDS[b.index].active_at, stressful_period_soon=period_soon,
                             flare_days={r.day for r in b.records if r.period_kind == FLARE})
        return {**model.predict(row), "in_flare": False, "enough_data": True, "index_scale": b.index,
                "scale_checked": b.index == "HBI"}

    async def weight(self, patient: Patient) -> dict:
        """Weigh-ins, the trend and any loss past the GLIM threshold (engine/weight.py)."""
        today = self.today()
        rows = await self.store.list_weights(patient.id)
        trend = weight_trend([WeightEntry(d, kg) for d, kg in rows], today)
        point = lambda e: {"date": e.day.isoformat(), "kg": e.kg}
        c = DEFAULT_WEIGHT_CONFIG
        return {
            "today": today.isoformat(),
            "entries": [{"date": d.isoformat(), "kg": kg} for d, kg in rows],
            "latest": point(trend.latest) if trend.latest else None,
            "changes": [{"days": ch.days, "since": ch.since.isoformat(), "from_kg": ch.from_kg, "kg": ch.kg, "percent": ch.percent}
                        for ch in trend.changes],
            "loss": None if trend.loss is None else {
                "level": trend.loss.level, "window": trend.loss.window, "peak": point(trend.loss.peak),
                "kg": trend.loss.kg, "percent": trend.loss.percent},
            "due": trend.due,
            "thresholds": {"recent_percent": c.recent_loss_percent, "long_percent": c.long_loss_percent,
                           "larger_percent": c.larger_loss_percent, "min_kg": c.min_kg, "max_kg": c.max_kg},
            "source": WEIGHT_SOURCE,
            "version": c.version,
            "is_synthetic": patient.is_synthetic,
        }

    async def report(self, patient: Patient, days: int = 90) -> dict:
        b = await self.bundle(patient)
        today = self.today()
        since = today - timedelta(days=days)
        recent = [e for e in b.entries if e.day >= since]
        with_med = [e for e in recent if e.medication != "na"]
        patterns = await self.patterns(patient, "all")
        periods = await self.periods(patient)
        checks = await self.store.list_meal_checks(patient.id, limit=200)
        verdicts: dict[str, int] = {}
        for c in checks:
            if c.created_at.astimezone(self.tz).date() >= since:
                verdicts[c.verdict] = verdicts.get(c.verdict, 0) + 1
        return {
            "generated_at": self.now().isoformat(), "from": since.isoformat(), "to": today.isoformat(),
            "patient": {"display_name": patient.display_name, "diagnosis": patient.diagnosis.value,
                        "phenotypes": sorted(patient.phenotypes), "current_state": periods["current_state"]},
            "index_name": b.index,
            "days_logged": len(recent), "days_in_range": days,
            "series": [{"date": e.day.isoformat(), "index": e.index.score} for e in recent],
            "avg_index": round(statistics.mean(e.index.score for e in recent), 1) if recent else None,
            "worst_index": max((e.index.score for e in recent), default=None),
            "days_with_blood": sum(1 for e in recent if e.stool.blood != "none"),
            "adherence": {"taken": sum(1 for e in with_med if e.medication == "taken"),
                          "missed": sum(1 for e in with_med if e.medication == "missed"), "logged": len(with_med)},
            "periods": [p for p in periods["periods"] if p["end"] >= since.isoformat()],
            "contributors": [r for r in patterns["results"] if r["label"] in (LIKELY, POSSIBLE)],
            "risk": await self.flare_risk(patient),
            "meal_verdicts": verdicts,
            "weight": await self._report_weight(patient, since),
            **await self._report_care(patient, today),
            "is_synthetic": patient.is_synthetic,
        }

    async def _report_care(self, patient: Patient, today: date) -> dict:
        """The patient's own medicine list and next tests, as they entered them (no advice)."""
        try:
            meds = await self.store.list_medications(patient.id)
            upcoming = [a for a in await self.store.list_appointments(patient.id) if a.date >= today][:4]
        except NotSupported:
            return {"medications": [], "appointments": []}
        return {"medications": [{"name": m.name, "times": m.times, "every_days": m.every_days, "note": m.note} for m in meds],
                "appointments": [a.model_dump(mode="json") for a in upcoming]}

    async def _report_weight(self, patient: Patient, since: date) -> dict | None:
        try:
            w = await self.weight(patient)
        except NotSupported:
            return None
        if w["latest"] is None:
            return None
        in_range = [e for e in w["entries"] if e["date"] >= since.isoformat()]
        return {"latest": w["latest"], "first_in_range": in_range[0] if in_range else None, "weigh_ins": len(in_range),
                "changes": w["changes"], "loss": w["loss"]}
