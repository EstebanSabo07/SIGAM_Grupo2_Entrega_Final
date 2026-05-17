"""Domain scoring and snapshot aggregation for SIGAM."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from data.catalog_service import get_form_tree
from data.snapshot import SnapshotContext
from data.snapshot_service import list_available_periods, month_age, resolve_indicator_values
from database.repositories import (
    get_latest_maturity_thresholds,
    get_latest_stage_weights,
    get_service_review_statuses,
    list_municipalities,
)


def _classify_level(score: float, thresholds: dict[str, float]) -> str:
    """Classify a score using effective-dated maturity thresholds.

    Args:
        score: Score in the 0-1 range.
        thresholds: Thresholds returned by the repository layer.

    Returns:
        Maturity level label.
    """

    if score < thresholds["initial_upper"]:
        return "Inicial"
    if score < thresholds["basic_upper"]:
        return "Básico"
    if score < thresholds["intermediate_upper"]:
        return "Intermedio"
    if score < thresholds["advanced_upper"]:
        return "Avanzado"
    return "Optimizando"


def _service_operational_status(
    service_snapshot: dict[str, Any],
    review_status: dict[str, Any] | None,
) -> str:
    """Resolve the operational status for a service snapshot.

    Args:
        service_snapshot: Service snapshot structure.
        review_status: Optional active review status.

    Returns:
        Operational status label.
    """

    if review_status and review_status.get("status") == "Observado":
        return "Observado"

    total_indicators = service_snapshot["total_indicators"]
    answered_indicators = service_snapshot["answered_indicators"]
    evidence_required = service_snapshot["evidence_required_indicators"]
    evidence_complete = service_snapshot["evidence_complete_indicators"]

    if answered_indicators == 0:
        return "Sin iniciar"
    if answered_indicators < total_indicators:
        return "En progreso"
    if evidence_complete < evidence_required:
        return "Con evidencias incompletas"
    return "Listo para revisión"


def _service_update_date(service_snapshot: dict[str, Any]) -> date | None:
    """Return the oldest current-indicator snapshot date within a service.

    Args:
        service_snapshot: Service snapshot structure.

    Returns:
        Oldest latest-response date across answered indicators, or None.
    """

    indicator_dates = [
        indicator["last_response_date"].date()
        for stage in service_snapshot["stages"]
        for indicator in stage["indicators"]
        if indicator["last_response_date"] is not None
    ]
    return min(indicator_dates) if indicator_dates else None


def get_municipality_snapshot(
    municipality_code: str,
    snapshot: SnapshotContext,
    audience: str | None = None,
) -> dict[str, Any]:
    """Build the raw municipal snapshot for one month cutoff.

    Args:
        municipality_code: Municipal code.
        snapshot: Snapshot context.
        audience: Optional audience hint kept for interface compatibility.

    Returns:
        Raw municipal snapshot with numeric scores and service metadata.
    """

    _ = audience
    form_tree = get_form_tree(municipality_code, snapshot)
    snapshot_values = resolve_indicator_values(municipality_code, snapshot)
    review_statuses = get_service_review_statuses(municipality_code, snapshot.end_date)
    stage_weights = get_latest_stage_weights(snapshot.end_date)
    thresholds = get_latest_maturity_thresholds(snapshot.end_date)
    municipality_meta = next(
        (item for item in list_municipalities() if item["codigo"] == municipality_code),
        None,
    )
    if municipality_meta is None:
        raise ValueError(f"Municipality not found: {municipality_code}")

    services: list[dict[str, Any]] = []
    stage_totals = {name: {"value_sum": 0.0, "count": 0} for name in stage_weights}

    for axis in form_tree["axes"]:
        for service in axis["services"]:
            service_stages: list[dict[str, Any]] = []
            total_indicators = 0
            answered_indicators = 0
            evidence_required = 0
            evidence_complete = 0
            service_score = 0.0

            for stage in service["stages"]:
                stage_indicator_views = []
                value_sum = 0.0
                indicator_count = len(stage["indicators"])
                for indicator in stage["indicators"]:
                    current = snapshot_values.get(indicator["indicator_code"], {})
                    value = current.get("value")
                    evidence_files = current.get("evidence_files", [])
                    numeric_value = float(value) if value is not None else 0.0
                    value_sum += numeric_value
                    total_indicators += 1
                    if value is not None:
                        answered_indicators += 1
                    if indicator["evidence_required"]:
                        evidence_required += 1
                        if evidence_files:
                            evidence_complete += 1
                    stage_indicator_views.append(
                        {
                            **indicator,
                            "value": value,
                            "evidence_files": evidence_files,
                            "last_response_date": current.get("date_time"),
                            "response_id": current.get("response_id"),
                        }
                    )
                stage_score = round(value_sum / indicator_count, 4) if indicator_count else 0.0
                stage_totals[stage["stage_name"]]["value_sum"] += value_sum
                stage_totals[stage["stage_name"]]["count"] += indicator_count
                service_score += stage_weights.get(stage["stage_name"], 0.0) * stage_score
                service_stages.append(
                    {
                        "stage_id": stage["stage_id"],
                        "stage_name": stage["stage_name"],
                        "section_id": stage["section_id"],
                        "score": stage_score,
                        "level": _classify_level(stage_score, thresholds),
                        "indicator_count": indicator_count,
                        "answered_indicators": sum(
                            1 for item in stage_indicator_views if item["value"] is not None
                        ),
                        "indicators": stage_indicator_views,
                    }
                )

            service_snapshot = {
                "service_id": service["service_id"],
                "service_code": service["service_code"],
                "service_name": service["service_name"],
                "service_grouping": service["service_grouping"],
                "axis_name": axis["axis_name"],
                "score": round(service_score, 4),
                "level": _classify_level(service_score, thresholds),
                "total_indicators": total_indicators,
                "answered_indicators": answered_indicators,
                "evidence_required_indicators": evidence_required,
                "evidence_complete_indicators": evidence_complete,
                "stages": service_stages,
            }
            service_snapshot["update_date"] = _service_update_date(service_snapshot)
            service_snapshot["data_age_months"] = month_age(snapshot.end_date, service_snapshot["update_date"])
            service_snapshot["review_status"] = review_statuses.get(service["service_code"])
            service_snapshot["operational_status"] = _service_operational_status(
                service_snapshot,
                service_snapshot["review_status"],
            )
            services.append(service_snapshot)

    municipality_stage_scores = {
        stage_name: (
            round(values["value_sum"] / values["count"], 4) if values["count"] else 0.0
        )
        for stage_name, values in stage_totals.items()
    }
    total_score = round(
        sum(municipality_stage_scores[name] * stage_weights.get(name, 0.0) for name in stage_weights),
        4,
    )
    answered_services = sum(1 for service in services if service["answered_indicators"] > 0)
    update_candidates = [service["update_date"] for service in services if service["update_date"] is not None]
    update_date = min(update_candidates) if update_candidates else None

    return {
        "snapshot": {
            "year": snapshot.year,
            "month": snapshot.month,
            "label": snapshot.label,
            "end_date": snapshot.end_date.isoformat(),
        },
        "municipality": municipality_meta,
        "score_total": total_score,
        "puntaje_pct": round(total_score * 100, 2),
        "level": _classify_level(total_score, thresholds),
        "stage_scores": municipality_stage_scores,
        "services": services,
        "total_services": len(services),
        "answered_services": answered_services,
        "total_indicators": sum(service["total_indicators"] for service in services),
        "answered_indicators": sum(service["answered_indicators"] for service in services),
        "update_date": update_date.isoformat() if update_date else None,
        "data_age_months": month_age(snapshot.end_date, update_date),
    }


def get_national_snapshot(snapshot: SnapshotContext, audience: str | None = None) -> dict[str, Any]:
    """Build the raw national snapshot for a month cutoff.

    Args:
        snapshot: Snapshot context.
        audience: Optional audience hint kept for interface compatibility.

    Returns:
        Raw national snapshot with municipality rows and aggregates.
    """

    _ = audience
    municipalities = list_municipalities()
    rows = [
        get_municipality_snapshot(municipality["codigo"], snapshot, audience="admin")
        for municipality in municipalities
    ]
    rows.sort(key=lambda item: item["score_total"], reverse=True)
    for position, row in enumerate(rows, start=1):
        row["position"] = position
        row["posicion"] = position

    level_counts = Counter(row["level"] for row in rows)
    score_values = [row["score_total"] for row in rows]

    return {
        "snapshot": {
            "year": snapshot.year,
            "month": snapshot.month,
            "label": snapshot.label,
            "end_date": snapshot.end_date.isoformat(),
        },
        "municipalities": rows,
        "total_municipalities": len(rows),
        "distribution_by_level": dict(level_counts),
        "average_score": round(sum(score_values) / len(score_values), 4) if score_values else 0.0,
        "max_score": max(score_values) if score_values else 0.0,
        "min_score": min(score_values) if score_values else 0.0,
    }


def get_monthly_history(municipality_code: str | None, audience: str) -> list[dict[str, Any]]:
    """Build monthly history snapshots for a municipality or the whole country.

    Args:
        municipality_code: Optional municipal code. When omitted, returns
            national history.
        audience: Consumer audience.

    Returns:
        Monthly history snapshots ordered from oldest to newest.
    """

    periods = sorted(list_available_periods(), key=lambda item: (item["year"], item["month"]))
    history = []
    for period in periods:
        snapshot = SnapshotContext(
            year=period["year"],
            month=period["month"],
            audience=audience,
            municipality_code=municipality_code,
        )
        if municipality_code:
            current = get_municipality_snapshot(municipality_code, snapshot, audience=audience)
            history.append(
                {
                    "label": period["label"],
                    "level": current["level"],
                    "score_total": current["score_total"],
                    "puntaje_pct": current["puntaje_pct"],
                }
            )
        else:
            current = get_national_snapshot(snapshot, audience=audience)
            history.append(
                {
                    "label": period["label"],
                    "level_distribution": current["distribution_by_level"],
                    "score_total": current["average_score"],
                    "puntaje_pct": round(current["average_score"] * 100, 2),
                }
            )
    return history
