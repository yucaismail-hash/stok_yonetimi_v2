"""Cutoff-safe, read-only temporal Event/Actual association calculation.

This boundary deliberately reports association evidence, never a causal claim.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from hashlib import sha256
import json
import statistics

from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation, ActualWeeklyRevision
from app.models.company import UserMaterial
from app.models.event_observation import EventObservation, EventRevision
from app.models.forecast_vintage import ForecastVintage, ForecastVintagePoint
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period


FEATURE_SCHEMA_VERSION = "event_association_features_v1"
BASELINE_POLICY_VERSION = "event_baseline_v1"
LAG_POLICY_VERSION = "event_lag_v1"
ASSOCIATION_POLICY_VERSION = "event_association_policy_v1"
CONFIDENCE_POLICY_VERSION = "event_confidence_v1"
HISTORICAL_WINDOW = 4
MIN_BASELINE_PERIODS = 3
MIN_RECURRING_OCCURRENCES = 2
LAG_WEEKS = (1, 2)
EFFECT_THRESHOLD = 0.15


class EventAssociationError(ValueError): pass


@dataclass(frozen=True)
class EventAssociationResult:
    company_id: object
    material_code: str
    demand_type: str
    event_identity: str
    event_type_snapshot: str | None
    cutoff_period: str
    as_of: datetime
    feature_schema_version: str
    baseline_policy_version: str
    lag_policy_version: str
    association_policy_version: str
    confidence_policy_version: str
    product_level: str | None
    product_group: str | None
    product_class: str | None
    occurrence_count: int
    included_occurrence_ids: tuple
    included_revision_ids: tuple
    source_event_scope_metadata: tuple
    baseline_method: str | None
    baseline_source_vintage_ids: tuple
    baseline_source_periods: tuple
    actual_observation_ids: tuple
    actual_revision_ids: tuple
    event_actual_mean: float | None
    baseline_mean: float | None
    absolute_effect: float | None
    relative_effect: float | None
    pre_event_mean: float | None
    post_event_mean: float | None
    pre_change: float | None
    post_decay: float | None
    strongest_lag_weeks: int | None
    strongest_lag_relative_effect: float | None
    mean_relative_effect: float | None
    median_relative_effect: float | None
    effect_dispersion: float | None
    direction_consistency: float | None
    classification: str
    confidence: float
    overlap_confounded: bool
    confounded_occurrence_ids: tuple
    per_occurrence: tuple
    source_fingerprint: str


def _json(value):
    if isinstance(value, (datetime, date)): return value.isoformat()
    if isinstance(value, Decimal): return str(value)
    return str(value) if value is not None and not isinstance(value, (str, int, float, bool, list, tuple, dict)) else value


def _digest(value):
    return sha256(json.dumps(value, default=_json, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _period_date(period):
    item = parse_weekly_period(period)
    return date.fromisocalendar(item.year, item.week, 1)


class EventAssociationService:
    """Read canonical event/actual evidence without writing any application state."""
    def __init__(self, session_factory=SessionLocal): self._sf = session_factory

    def calculate(self, company_id, material_code, demand_type, event_identity, cutoff, *, as_of=None):
        demand = validate_demand_type(demand_type)
        if demand is None: raise EventAssociationError("demand_type is required")
        cutoff_period, cutoff_date = self._cutoff(cutoff)
        as_of = self._as_of(as_of, cutoff_date)
        s = self._sf()
        try:
            metadata = self._metadata(s, company_id, material_code, demand)
            actuals, actual_revisions = self._actuals_as_of(s, company_id, material_code, demand, cutoff_period, as_of)
            snapshots = self._event_snapshots_as_of(s, company_id, as_of)
            applicable = [x for x in snapshots if x["event_identity"] == event_identity and x["demand_type"] == demand and x["start_date"] <= cutoff_date and self._scope_matches(x, material_code, metadata)]
            applicable.sort(key=lambda x: (x["start_date"], x["end_date"], str(x["event_id"])))
            all_applicable = [x for x in snapshots if x["demand_type"] == demand and x["start_date"] <= cutoff_date and self._scope_matches(x, material_code, metadata)]
            rows = {x["period"]: x for x in actuals}
            occurrences, used_periods, vintage_ids, baseline_periods = [], set(), set(), set()
            confounded = []
            for snap in applicable:
                if snap["status"] != "ACTIVE": continue
                occurrence = self._occurrence(s, company_id, material_code, snap, all_applicable, rows, cutoff_period, cutoff_date, as_of)
                used_periods.update(occurrence["used_periods"])
                vintage_ids.update(occurrence["vintage_ids"])
                baseline_periods.update(occurrence["baseline_periods"])
                if occurrence["confounded"]: confounded.append(snap["event_id"])
                occurrences.append(occurrence)
            eligible = [x for x in occurrences if x["relative_effect"] is not None and not x["confounded"]]
            effects = [x["relative_effect"] for x in eligible]
            classification, consistency = self._classification(effects, len(occurrences))
            confidence = self._confidence(eligible, occurrences, consistency, metadata)
            event_values = [v for x in eligible for v in x["event_values"]]
            baseline_values = [x["baseline_mean"] for x in eligible if x["baseline_mean"] is not None]
            pre_values = [x["pre_event_mean"] for x in eligible if x["pre_event_mean"] is not None]
            post_values = [x["post_event_mean"] for x in eligible if x["post_event_mean"] is not None]
            lag_candidates = [(abs(x["strongest_lag_relative_effect"]), x["strongest_lag_weeks"], x["strongest_lag_relative_effect"]) for x in eligible if x["strongest_lag_relative_effect"] is not None]
            lag = max(lag_candidates) if lag_candidates else None
            actual_ids = tuple(sorted((str(rows[p]["id"]) for p in used_periods if p in rows)))
            used_revision_ids = tuple(sorted(revision_id for observation_id, revision_id in actual_revisions if observation_id in set(actual_ids)))
            payload = {
                "company_id": company_id, "material_code": material_code, "demand_type": demand, "event_identity": event_identity,
                "cutoff_period": cutoff_period, "event_revisions": [(str(x["event_id"]), str(x["revision_id"])) for x in applicable],
                "actual_ids": actual_ids, "actual_revision_ids": used_revision_ids, "vintage_ids": sorted(str(x) for x in vintage_ids),
                "baseline_periods": sorted(baseline_periods), "versions": [FEATURE_SCHEMA_VERSION, BASELINE_POLICY_VERSION, LAG_POLICY_VERSION, ASSOCIATION_POLICY_VERSION, CONFIDENCE_POLICY_VERSION],
            }
            average = lambda values: float(sum(values) / len(values)) if values else None
            baseline = average(baseline_values)
            event_mean = average(event_values)
            absolute = event_mean - baseline if event_mean is not None and baseline is not None else None
            relative = absolute / baseline if absolute is not None and baseline not in (None, 0) else None
            pre, post = average(pre_values), average(post_values)
            event_types = sorted({x["event_type"] for x in occurrences})
            return EventAssociationResult(company_id, material_code, demand, event_identity, event_types[0] if len(event_types) == 1 else ("multiple" if event_types else None), cutoff_period, as_of,
                FEATURE_SCHEMA_VERSION, BASELINE_POLICY_VERSION, LAG_POLICY_VERSION, ASSOCIATION_POLICY_VERSION, CONFIDENCE_POLICY_VERSION,
                metadata["product_level"], metadata["product_group"], metadata["product_class"], len(occurrences),
                tuple(str(x["event_id"]) for x in occurrences), tuple(str(x["revision_id"]) for x in occurrences),
                tuple(sorted((str(x["event_id"]), x["scope_type"], x.get("scope_value"), x["authority_type"], x["source_system"]) for x in applicable if x["status"] == "ACTIVE")),
                self._baseline_method(eligible), tuple(sorted(str(x) for x in vintage_ids)), tuple(sorted(baseline_periods)), actual_ids, used_revision_ids,
                event_mean, baseline, absolute, relative, pre, post, (post - pre if pre is not None and post is not None else None),
                (post - baseline if post is not None and baseline is not None else None), lag[1] if lag else None, lag[2] if lag else None,
                average(effects), float(statistics.median(effects)) if effects else None, float(statistics.pstdev(effects)) if len(effects) > 1 else (0.0 if effects else None),
                consistency, classification, confidence, bool(confounded), tuple(sorted(str(x) for x in confounded)),
                tuple(self._public_occurrence(x) for x in occurrences), _digest(payload))
        finally: s.close()

    @staticmethod
    def _cutoff(cutoff):
        if isinstance(cutoff, str):
            period = parse_weekly_period(cutoff).period; return period, _period_date(period).fromordinal(_period_date(period).toordinal() + 6)
        if isinstance(cutoff, datetime): cutoff = cutoff.date()
        if isinstance(cutoff, date):
            iso = cutoff.isocalendar(); return f"{iso.year:04d}-W{iso.week:02d}", cutoff
        raise EventAssociationError("cutoff must be a canonical period or date")

    @staticmethod
    def _as_of(value, cutoff_date):
        if value is None: return datetime.combine(cutoff_date, time.max, timezone.utc)
        if isinstance(value, date) and not isinstance(value, datetime): return datetime.combine(value, time.max, timezone.utc)
        if isinstance(value, datetime): return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        raise EventAssociationError("as_of must be a date or datetime")

    def _metadata(self, s, cid, material, demand):
        row = s.query(UserMaterial).filter_by(company_id=cid, material_code=material).order_by(UserMaterial.id).first()
        actual = s.query(ActualWeeklyObservation).filter_by(company_id=cid, material_code=material, demand_type=demand).order_by(ActualWeeklyObservation.period).first()
        if row: return {"product_level": row.product_level, "product_group": row.group, "product_class": row.product_class}
        if actual: return {"product_level": actual.product_level, "product_group": actual.product_group, "product_class": actual.product_class}
        return {"product_level": None, "product_group": None, "product_class": None}

    def _actuals_as_of(self, s, cid, material, demand, cutoff, as_of):
        observations = s.query(ActualWeeklyObservation).filter_by(company_id=cid, material_code=material, demand_type=demand).filter(ActualWeeklyObservation.period <= cutoff).order_by(ActualWeeklyObservation.period, ActualWeeklyObservation.id).all()
        observation_ids = [x.id for x in observations]
        all_revisions = s.query(ActualWeeklyRevision).filter(ActualWeeklyRevision.company_id == cid, ActualWeeklyRevision.observation_id.in_(observation_ids), ActualWeeklyRevision.approval_status == "accepted").order_by(ActualWeeklyRevision.observation_id, ActualWeeklyRevision.approved_at, ActualWeeklyRevision.id).all() if observation_ids else []
        by_observation = {}
        for revision in all_revisions: by_observation.setdefault(revision.observation_id, []).append(revision)
        out, revision_pairs = [], []
        for o in observations:
            revisions = by_observation.get(o.id, [])
            accepted = [r for r in revisions if r.approved_at and r.approved_at <= as_of]
            if not accepted: continue
            later = [r for r in revisions if r.approved_at and r.approved_at > as_of]
            quantity = later[0].previous_quantity if later else o.quantity
            if quantity is None: continue
            for r in accepted: revision_pairs.append((str(o.id), str(r.id)))
            out.append({"id": o.id, "period": o.period, "quantity": float(quantity), "product_level": o.product_level, "product_group": o.product_group, "product_class": o.product_class})
        return out, tuple(revision_pairs)

    def _event_snapshots_as_of(self, s, cid, as_of):
        rows = s.query(EventRevision).filter_by(company_id=cid, approval_status="accepted").filter(EventRevision.approved_at <= as_of).order_by(EventRevision.event_observation_id, EventRevision.approved_at, EventRevision.id).all()
        latest = {}
        for r in rows: latest[r.event_observation_id] = r
        out = []
        for eid, r in latest.items():
            snap = dict(r.proposed_snapshot)
            snap.update({"event_id": eid, "revision_id": r.id, "start_date": date.fromisoformat(snap["start_date"]), "end_date": date.fromisoformat(snap["end_date"])})
            out.append(snap)
        return out

    @staticmethod
    def _scope_matches(snap, material, metadata):
        scope, value = snap["scope_type"], snap.get("scope_value")
        return scope == "COMPANY" or (scope == "MATERIAL" and value == material) or (scope == "PRODUCT_GROUP" and value == metadata["product_group"]) or (scope == "PRODUCT_CLASS" and value == metadata["product_class"])

    def _occurrence(self, s, company_id, material_code, snap, all_events, rows, cutoff_period, cutoff_date, as_of):
        periods = [p for p in sorted(rows) if snap["start_date"] <= _period_date(p) <= min(snap["end_date"], cutoff_date)]
        event_values = [rows[p]["quantity"] for p in periods]
        overlap = any(other["event_id"] != snap["event_id"] and other["status"] == "ACTIVE" and other["start_date"] <= min(snap["end_date"], cutoff_date) and other["end_date"] >= snap["start_date"] for other in all_events)
        baseline, method, source_periods, vintage_ids = self._baseline(s, company_id, material_code, snap, rows, all_events, cutoff_period, as_of)
        pre = self._mean([rows[p]["quantity"] for p in sorted(rows) if _period_date(p) < snap["start_date"]][-2:])
        post_periods = [p for p in sorted(rows) if snap["end_date"] < _period_date(p) <= cutoff_date][:2]
        post = self._mean([rows[p]["quantity"] for p in post_periods])
        effects = []
        for lag in LAG_WEEKS:
            start = snap["end_date"].fromordinal(snap["end_date"].toordinal() + 7 * lag)
            lag_values = [rows[p]["quantity"] for p in sorted(rows) if start <= _period_date(p) < start.fromordinal(start.toordinal() + 7)]
            if baseline not in (None, 0) and lag_values: effects.append((lag, self._mean(lag_values) / baseline - 1))
        strongest = max(effects, key=lambda x: abs(x[1])) if effects else (None, None)
        event_mean = self._mean(event_values)
        absolute = event_mean - baseline if event_mean is not None and baseline is not None else None
        relative = absolute / baseline if absolute is not None and baseline not in (None, 0) else None
        return {"event_id": snap["event_id"], "revision_id": snap["revision_id"], "event_type": snap["event_type"], "event_values": event_values, "event_periods": periods, "baseline_mean": baseline, "baseline_method": method, "baseline_periods": source_periods, "vintage_ids": vintage_ids, "confounded": overlap, "relative_effect": relative, "pre_event_mean": pre, "post_event_mean": post, "strongest_lag_weeks": strongest[0], "strongest_lag_relative_effect": strongest[1], "used_periods": set(periods) | set(source_periods) | set(post_periods)}

    def _baseline(self, s, company_id, material_code, snap, rows, all_events, cutoff_period, as_of):
        # Query by point owner to avoid trusting a post-event/current forecast.
        points = s.query(ForecastVintagePoint, ForecastVintage).join(ForecastVintage, ForecastVintagePoint.forecast_vintage_id == ForecastVintage.id).filter(ForecastVintage.company_id == company_id, ForecastVintage.demand_type == snap["demand_type"], ForecastVintage.forecast_available_at <= datetime.combine(snap["start_date"], time.min, timezone.utc), ForecastVintage.forecast_available_at <= as_of, ForecastVintagePoint.material_code == material_code).all()
        target = [p for p in points if snap["start_date"] <= _period_date(p[0].target_period) <= snap["end_date"] and p[1].input_cutoff_period <= cutoff_period]
        if target:
            return self._mean([float(p[0].forecast_value) for p in target]), "forecast_vintage", tuple(sorted(p[0].target_period for p in target)), tuple(sorted({p[1].id for p in target}, key=str))
        blocked = [(x["start_date"], x["end_date"]) for x in all_events if x["status"] == "ACTIVE"]
        candidates = [p for p in sorted(rows) if _period_date(p) < snap["start_date"] and not any(a <= _period_date(p) <= b for a,b in blocked)]
        source = tuple(candidates[-HISTORICAL_WINDOW:])
        if len(source) < MIN_BASELINE_PERIODS: return None, None, source, tuple()
        return self._mean([rows[p]["quantity"] for p in source]), "historical_pre_event", source, tuple()

    @staticmethod
    def _mean(values): return float(sum(values) / len(values)) if values else None
    @staticmethod
    def _baseline_method(eligible):
        methods = {x["baseline_method"] for x in eligible}
        return next(iter(methods)) if len(methods) == 1 else ("mixed" if methods else None)
    @staticmethod
    def _public_occurrence(x):
        return tuple(sorted((k, tuple(v) if isinstance(v, list) else v) for k,v in x.items() if k not in {"event_values", "used_periods", "vintage_ids"}))
    @staticmethod
    def _classification(effects, total):
        if total < MIN_RECURRING_OCCURRENCES or len(effects) < MIN_RECURRING_OCCURRENCES: return "INSUFFICIENT_EVIDENCE", None
        signs = [1 if x >= EFFECT_THRESHOLD else -1 if x <= -EFFECT_THRESHOLD else 0 for x in effects]
        if 1 in signs and -1 in signs: return "INCONSISTENT_EFFECT", 0.0
        direction = 1 if 1 in signs else -1 if -1 in signs else 0
        consistency = signs.count(direction) / len(signs)
        if direction == 1 and consistency >= .75: return "POSITIVE_ASSOCIATION", consistency
        if direction == -1 and consistency >= .75: return "NEGATIVE_ASSOCIATION", consistency
        if direction == 0: return "NO_CLEAR_EFFECT", 1.0
        return "INCONSISTENT_EFFECT", consistency
    @staticmethod
    def _confidence(eligible, occurrences, consistency, metadata):
        if not eligible or consistency is None: return 0.0
        baseline_quality = sum(1.0 if x["baseline_method"] == "forecast_vintage" else .75 for x in eligible) / len(eligible)
        specificity = {"product_level": .10, "product_group": .12, "product_class": .12}.get("product_level" if metadata["product_level"] else "", .05)
        return round(min(.95, .25 + min(len(eligible), 3) * .15 + (len(eligible) / max(1, len(occurrences))) * .2 + baseline_quality * .15 + consistency * .15 + specificity), 4)
