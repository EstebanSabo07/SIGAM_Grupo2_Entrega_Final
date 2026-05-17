"""Audience-specific presentation models for SIGAM views."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from data.scoring_service import get_monthly_history, get_municipality_snapshot, get_national_snapshot
from data.snapshot import AUDIENCE_ADMIN, AUDIENCE_MUNICIPAL, AUDIENCE_PUBLIC, SnapshotContext
from data.snapshot_service import list_available_periods


LEVEL_ORDER = ["Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"]
LEVEL_INDEX = {level: index for index, level in enumerate(LEVEL_ORDER)}


def _serialize_date(value: Any) -> str | None:
    """Serialize a date-like value to ISO format when available.

    Args:
        value: Date or datetime-like value.

    Returns:
        ISO string representation, or ``None``.
    """

    return value.isoformat() if value is not None else None


def _percentage(numerator: int, denominator: int) -> float:
    """Calculate a rounded percentage.

    Args:
        numerator: Completed count.
        denominator: Total count.

    Returns:
        Rounded percentage between 0 and 100.
    """

    if denominator <= 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


def _top_percentile(position: int, total: int) -> float:
    """Return a top-oriented percentile for ranking displays.

    Args:
        position: One-based ranking position.
        total: Total ranked items.

    Returns:
        Percentile where higher is better.
    """

    if total <= 0:
        return 0.0
    return round(((total - position + 1) / total) * 100, 2)


def _level_band(percentile: float) -> str:
    """Map a percentile to a human-readable benchmark band.

    Args:
        percentile: Top-oriented percentile score.

    Returns:
        Display band label.
    """

    if percentile >= 75:
        return "Cuartil superior"
    if percentile >= 50:
        return "Mitad superior"
    if percentile >= 25:
        return "Mitad inferior"
    return "Cuartil rezagado"


def _mode_level(levels: list[str], default: str = "Inicial") -> str:
    """Return the most common level from a list.

    Args:
        levels: Level labels.
        default: Default label when the list is empty.

    Returns:
        Most frequent level label.
    """

    if not levels:
        return default
    return Counter(levels).most_common(1)[0][0]


def _level_number(level: str) -> int:
    """Convert a maturity level label into its ordinal position.

    Args:
        level: Maturity level label.

    Returns:
        One-based ordinal value for the level.
    """

    return LEVEL_INDEX.get(level, 0) + 1


def _level_axis_label(value: float) -> str:
    """Return a compact axis label for an ordinal maturity value.

    Args:
        value: Ordinal maturity value.

    Returns:
        Readable maturity label.
    """

    rounded = min(max(int(round(value)), 1), len(LEVEL_ORDER))
    return LEVEL_ORDER[rounded - 1]


def _level_alignment(level: str, reference_level: str) -> str:
    """Describe whether a level is above or below a reference level.

    Args:
        level: Current level.
        reference_level: Reference level.

    Returns:
        Relative alignment label.
    """

    current_index = LEVEL_INDEX.get(level, 0)
    reference_index = LEVEL_INDEX.get(reference_level, 0)
    if current_index > reference_index:
        return "Por encima de la referencia"
    if current_index < reference_index:
        return "Por debajo de la referencia"
    return "Alineado con la referencia"


def _ranking_context(
    rows: list[dict[str, Any]],
    municipality_code: str,
    limit: int = 7,
) -> list[dict[str, Any]]:
    """Build a compact ranking context list around one municipality.

    Args:
        rows: Ranked municipality rows for one scope.
        municipality_code: Municipality code in focus.
        limit: Maximum number of rows to return.

    Returns:
        Ranking rows centered on the municipality when possible.
    """

    if not rows:
        return []

    focus_index = next(
        (index for index, item in enumerate(rows) if item["municipality"]["codigo"] == municipality_code),
        0,
    )
    half_window = limit // 2
    start = max(0, focus_index - half_window)
    end = min(len(rows), start + limit)
    start = max(0, end - limit)
    return [
        {
            "position": item["position"],
            "municipality_name": item["municipality"]["nombre"],
            "level": item["level"],
            "is_current": item["municipality"]["codigo"] == municipality_code,
        }
        for item in rows[start:end]
    ]


def _service_recommendation(
    operational_status: str,
    progress_pct: float,
    age_months: int | None,
    percentile: float,
) -> str:
    """Build a short action recommendation for one service.

    Args:
        operational_status: Current operational status.
        progress_pct: Completion percentage for the service.
        age_months: Data age in months.
        percentile: Service benchmark percentile.

    Returns:
        Action recommendation sentence.
    """

    if operational_status == "Sin iniciar":
        return "Inicie la carga base del servicio para entrar al seguimiento comparativo."
    if operational_status == "Con evidencias incompletas":
        return "Complete las evidencias faltantes para respaldar el avance reportado."
    if progress_pct < 100 and age_months is not None and age_months >= 12:
        return "Complete lo pendiente y actualice este servicio cuanto antes."
    if progress_pct < 50:
        return "Priorice completar indicadores pendientes antes de optimizar el servicio."
    if age_months is not None and age_months >= 12:
        return "Actualice respuestas antiguas para recuperar vigencia en este servicio."
    if age_months is not None and age_months >= 6:
        return "Revise este servicio pronto para evitar que la información pierda vigencia."
    if percentile < 35:
        return "Enfoque recursos en la etapa más rezagada para cerrar la brecha competitiva."
    return "Mantenga la vigencia del servicio y fortalezca la etapa con menor cobertura."


def _service_freshness_status(progress_pct: float, age_months: int | None) -> str:
    """Classify a service by data freshness for non-technical users.

    Args:
        progress_pct: Service completion percentage.
        age_months: Data age in months.

    Returns:
        Freshness status label.
    """

    if progress_pct < 100 or age_months is None or age_months >= 12:
        return "Urgente"
    if age_months >= 6:
        return "Próximo a vencer"
    return "Al día"


def _service_priority_score(progress_pct: float, age_months: int | None) -> float:
    """Score how urgently a service should be reviewed.

    Args:
        progress_pct: Service completion percentage.
        age_months: Data age in months.

    Returns:
        Priority score where higher means more urgent.
    """

    age_component = min((age_months or 0) * 8, 100)
    return round((100 - progress_pct) * 0.65 + age_component * 0.35, 2)


def _service_maturity_index(level_counts: Counter) -> float:
    """Build an ordinal maturity index from categorical level counts.

    Args:
        level_counts: Counter keyed by maturity level.

    Returns:
        Weighted average maturity position in the 1-5 range.
    """

    total = sum(level_counts.values())
    if total <= 0:
        return 0.0
    weighted_sum = sum(_level_number(level) * count for level, count in level_counts.items())
    return round(weighted_sum / total, 2)


def _service_public_view(service: dict[str, Any]) -> dict[str, Any]:
    """Build the sanitized public view for one service.

    Args:
        service: Raw service snapshot.

    Returns:
        Audience-safe service dictionary.
    """

    return {
        "service_code": service["service_code"],
        "service_name": service["service_name"],
        "service_grouping": service["service_grouping"],
        "axis_name": service["axis_name"],
        "level": service["level"],
        "stages": [
            {
                "stage_name": stage["stage_name"],
                "level": stage["level"],
                "answered_indicators": stage["answered_indicators"],
                "indicator_count": stage["indicator_count"],
            }
            for stage in service["stages"]
        ],
    }


def _build_regional_history(periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build average score history by region for administrator views.

    Args:
        periods: Available reporting periods.

    Returns:
        Rows with period, region, and average score percentage.
    """

    regional_history: list[dict[str, Any]] = []
    for period in sorted(periods, key=lambda item: (item["year"], item["month"])):
        snapshot = SnapshotContext(period["year"], period["month"], AUDIENCE_ADMIN)
        current = get_national_snapshot(snapshot, audience=AUDIENCE_ADMIN)
        scores_by_region: dict[str, list[float]] = defaultdict(list)
        for municipality in current["municipalities"]:
            region = municipality["municipality"].get("region") or "Sin región"
            scores_by_region[region].append(municipality["score_total"])
        for region, values in sorted(scores_by_region.items()):
            average_score = round(sum(values) / len(values) * 100, 2) if values else 0.0
            regional_history.append(
                {
                    "period_label": period["label"],
                    "region": region,
                    "puntaje_pct": average_score,
                }
            )
    return regional_history


def get_admin_municipality_comparison_view(
    snapshot: SnapshotContext,
    municipality_codes: list[str],
) -> dict[str, Any]:
    """Build comparison data for several municipalities in the admin portal.

    Args:
        snapshot: Snapshot context.
        municipality_codes: Municipal codes selected for comparison.

    Returns:
        View model with comparison-ready rows, tables, and counts.
    """

    national = get_national_snapshot(snapshot, audience=AUDIENCE_ADMIN)
    selected_codes = set(municipality_codes)
    selected_rows = [
        item for item in national["municipalities"] if item["municipality"]["codigo"] in selected_codes
    ]
    selected_rows.sort(key=lambda item: item["municipality"]["nombre"])

    heatmap_rows: list[dict[str, Any]] = []
    score_table_rows: list[dict[str, Any]] = []
    service_scores_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    status_count_rows: list[dict[str, Any]] = []

    for municipality in selected_rows:
        municipality_name = municipality["municipality"]["nombre"]
        freshness_counter: Counter = Counter()
        for service in municipality["services"]:
            progress_pct = _percentage(service["answered_indicators"], service["total_indicators"])
            freshness_status = _service_freshness_status(progress_pct, service["data_age_months"])
            freshness_counter[freshness_status] += 1
            heatmap_rows.append(
                {
                    "Municipalidad": municipality_name,
                    "Servicio": service["service_name"],
                    "Nivel": service["level"],
                }
            )
            key = (service["axis_name"], service["service_name"])
            if key not in service_scores_by_key:
                service_scores_by_key[key] = {
                    "Eje": service["axis_name"],
                    "Servicio": service["service_name"],
                }
            service_scores_by_key[key][f"{municipality_name} Puntaje (%)"] = round(service["score"] * 100, 2)
            service_scores_by_key[key][f"{municipality_name} Nivel"] = service["level"]
            score_table_rows.append(
                {
                    "Municipalidad": municipality_name,
                    "Eje": service["axis_name"],
                    "Servicio": service["service_name"],
                    "Puntaje (%)": round(service["score"] * 100, 2),
                    "Nivel": service["level"],
                    "Estado de actualización": freshness_status,
                    "Estado operativo": service["operational_status"],
                    "Antigüedad (meses)": service["data_age_months"],
                }
            )
        status_count_rows.append(
            {
                "Municipalidad": municipality_name,
                "Urgente": freshness_counter.get("Urgente", 0),
                "Próximo a vencer": freshness_counter.get("Próximo a vencer", 0),
                "Al día": freshness_counter.get("Al día", 0),
            }
        )

    comparison_table = sorted(
        service_scores_by_key.values(),
        key=lambda item: (item["Eje"], item["Servicio"]),
    )
    return {
        "selected_municipalities": [
            {
                "codigo": row["municipality"]["codigo"],
                "municipalidad": row["municipality"]["nombre"],
                "region": row["municipality"].get("region"),
                "provincia": row["municipality"].get("provincia"),
                "puntaje_pct": row["puntaje_pct"],
                "nivel": row["level"],
                "posicion": row["position"],
            }
            for row in selected_rows
        ],
        "service_heatmap_rows": heatmap_rows,
        "service_score_rows": score_table_rows,
        "service_score_table": comparison_table,
        "update_status_counts": status_count_rows,
    }


def _build_service_benchmarks(
    national_rows: list[dict[str, Any]],
    municipality_code: str,
    municipality_region: str | None,
) -> dict[str, dict[str, Any]]:
    """Build service-level benchmark metadata for one municipality.

    Args:
        national_rows: Ranked national municipality snapshots.
        municipality_code: Municipality code in focus.
        municipality_region: Region of the municipality in focus.

    Returns:
        Benchmark data keyed by service code.
    """

    by_service: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for municipality in national_rows:
        for service in municipality["services"]:
            by_service[service["service_code"]].append(
                {
                    "municipality_code": municipality["municipality"]["codigo"],
                    "municipality_name": municipality["municipality"]["nombre"],
                    "region": municipality["municipality"].get("region"),
                    "service_code": service["service_code"],
                    "service_name": service["service_name"],
                    "axis_name": service["axis_name"],
                    "score": service["score"],
                    "level": service["level"],
                }
            )

    benchmarks: dict[str, dict[str, Any]] = {}
    for service_code, entries in by_service.items():
        ranked_entries = sorted(entries, key=lambda item: item["score"], reverse=True)
        region_entries = [item for item in ranked_entries if item["region"] == municipality_region]
        reference_level = _mode_level([item["level"] for item in ranked_entries])
        region_reference = _mode_level([item["level"] for item in region_entries], default=reference_level)

        for position, entry in enumerate(ranked_entries, start=1):
            if entry["municipality_code"] != municipality_code:
                continue
            region_position = next(
                (
                    index
                    for index, region_entry in enumerate(region_entries, start=1)
                    if region_entry["municipality_code"] == municipality_code
                ),
                None,
            )
            percentile = _top_percentile(position, len(ranked_entries))
            benchmarks[service_code] = {
                "service_code": service_code,
                "service_name": entry["service_name"],
                "axis_name": entry["axis_name"],
                "position": position,
                "total": len(ranked_entries),
                "percentile": percentile,
                "comparison_band": _level_band(percentile),
                "reference_level": reference_level,
                "region_reference_level": region_reference,
                "region_position": region_position,
                "region_total": len(region_entries),
                "level_alignment": _level_alignment(entry["level"], reference_level),
            }
            break

    return benchmarks


def _service_municipal_view(service: dict[str, Any], benchmark: dict[str, Any] | None) -> dict[str, Any]:
    """Build the municipal view for one service.

    Args:
        service: Raw service snapshot.
        benchmark: Optional benchmark metadata for the same service.

    Returns:
        Municipal service dictionary ready for UI rendering.
    """

    progress_pct = _percentage(service["answered_indicators"], service["total_indicators"])
    percentile = round((benchmark or {}).get("percentile", 0.0), 2)
    freshness_status = _service_freshness_status(progress_pct, service["data_age_months"])
    recommendation = _service_recommendation(
        service["operational_status"],
        progress_pct,
        service["data_age_months"],
        percentile,
    )

    return {
        "service_code": service["service_code"],
        "service_name": service["service_name"],
        "service_grouping": service["service_grouping"],
        "axis_name": service["axis_name"],
        "level": service["level"],
        "operational_status": service["operational_status"],
        "update_date": _serialize_date(service["update_date"]),
        "data_age_months": service["data_age_months"],
        "review_status": service["review_status"],
        "answered_indicators": service["answered_indicators"],
        "total_indicators": service["total_indicators"],
        "service_progress_pct": progress_pct,
        "benchmark_percentile": percentile,
        "benchmark_position": (benchmark or {}).get("position"),
        "benchmark_total": (benchmark or {}).get("total"),
        "comparison_band": (benchmark or {}).get("comparison_band"),
        "reference_level": (benchmark or {}).get("reference_level"),
        "region_reference_level": (benchmark or {}).get("region_reference_level"),
        "level_alignment": (benchmark or {}).get("level_alignment"),
        "freshness_status": freshness_status,
        "needs_update": freshness_status != "Al día",
        "kanban_column": "Necesitan actualización" if freshness_status != "Al día" else service["level"],
        "recommendation": recommendation,
        "priority_score": _service_priority_score(progress_pct, service["data_age_months"]),
        "stages": [
            {
                "stage_name": stage["stage_name"],
                "level": stage["level"],
                "answered_indicators": stage["answered_indicators"],
                "indicator_count": stage["indicator_count"],
                "stage_progress_pct": _percentage(stage["answered_indicators"], stage["indicator_count"]),
            }
            for stage in service["stages"]
        ],
    }


def get_municipality_snapshot_view(
    municipality_code: str,
    snapshot: SnapshotContext,
    audience: str,
) -> dict[str, Any]:
    """Return the audience-specific municipality view model.

    Args:
        municipality_code: Municipal code.
        snapshot: Snapshot context.
        audience: Consumer audience.

    Returns:
        Municipality view model shaped for the requested audience.
    """

    raw = get_municipality_snapshot(municipality_code, snapshot, audience=audience)
    history = get_monthly_history(municipality_code, audience=audience)
    available_periods = list_available_periods()

    if audience == AUDIENCE_ADMIN:
        return {
            **raw,
            "history": history,
            "services_by_name": {service["service_name"]: service for service in raw["services"]},
            "available_periods": available_periods,
        }

    if audience == AUDIENCE_PUBLIC:
        return {
            "snapshot": raw["snapshot"],
            "municipality": raw["municipality"],
            "level": raw["level"],
            "services": [_service_public_view(service) for service in raw["services"]],
            "history": [{"label": item["label"], "level": item["level"]} for item in history],
            "available_periods": available_periods,
        }

    national = get_national_snapshot(snapshot, audience=AUDIENCE_ADMIN)
    national_rows = national["municipalities"]
    benchmark_row = next(
        (item for item in national_rows if item["municipality"]["codigo"] == municipality_code),
        None,
    )
    municipality_region = raw["municipality"].get("region")
    municipality_province = raw["municipality"].get("provincia")
    regional_rows = [
        item for item in national_rows if item["municipality"].get("region") == municipality_region
    ]
    province_rows = [
        item for item in national_rows if item["municipality"].get("provincia") == municipality_province
    ]
    service_benchmarks = _build_service_benchmarks(national_rows, municipality_code, municipality_region)
    services = [
        _service_municipal_view(service, service_benchmarks.get(service["service_code"]))
        for service in raw["services"]
    ]
    services.sort(key=lambda item: item["service_name"])

    priority_services = sorted(
        services,
        key=lambda item: item["priority_score"],
        reverse=True,
    )
    benchmark_by_service = [
        {
            "service_code": service["service_code"],
            "service_name": service["service_name"],
            "axis_name": service["axis_name"],
            "level": service["level"],
            "percentile": service["benchmark_percentile"],
            "position": service["benchmark_position"],
            "total": service["benchmark_total"],
            "comparison_band": service["comparison_band"],
            "reference_level": service["reference_level"],
            "region_reference_level": service["region_reference_level"],
            "level_alignment": service["level_alignment"],
        }
        for service in services
    ]

    stage_matrix = [
        {
            "Servicio": service["service_name"],
            "Etapa": stage["stage_name"],
            "Progreso (%)": stage["stage_progress_pct"],
            "Nivel": stage["level"],
        }
        for service in services
        for stage in service["stages"]
    ]
    services_started = sum(1 for service in services if service["service_progress_pct"] > 0)
    services_ready = sum(1 for service in services if service["operational_status"] == "Listo para revisión")
    services_up_to_date = sum(1 for service in services if service["freshness_status"] == "Al día")
    services_due_soon = sum(1 for service in services if service["freshness_status"] == "Próximo a vencer")
    services_urgent = sum(1 for service in services if service["freshness_status"] == "Urgente")
    benchmark_summary = {
        "position_national": benchmark_row["position"] if benchmark_row else None,
        "total_national": len(national_rows),
        "percentile_national": (
            _top_percentile(benchmark_row["position"], len(national_rows))
            if benchmark_row
            else 0.0
        ),
        "position_province": (
            next(
                (
                    index
                    for index, item in enumerate(province_rows, start=1)
                    if item["municipality"]["codigo"] == municipality_code
                ),
                None,
            )
        ),
        "total_province": len(province_rows),
        "province_name": municipality_province,
        "position_region": (
            next(
                (
                    index
                    for index, item in enumerate(regional_rows, start=1)
                    if item["municipality"]["codigo"] == municipality_code
                ),
                None,
            )
        ),
        "total_region": len(regional_rows),
        "region_name": municipality_region,
        "reference_level_national": _mode_level([item["level"] for item in national_rows]),
        "reference_level_province": _mode_level(
            [item["level"] for item in province_rows],
            default=_mode_level([item["level"] for item in national_rows]),
        ),
        "reference_level_region": _mode_level(
            [item["level"] for item in regional_rows],
            default=_mode_level([item["level"] for item in national_rows]),
        ),
        "national_ranking": _ranking_context(national_rows, municipality_code),
        "province_ranking": _ranking_context(province_rows, municipality_code),
        "regional_ranking": _ranking_context(regional_rows, municipality_code),
    }

    return {
        "snapshot": raw["snapshot"],
        "municipality": raw["municipality"],
        "level": raw["level"],
        "update_date": raw["update_date"],
        "data_age_months": raw["data_age_months"],
        "answered_services": raw["answered_services"],
        "total_services": raw["total_services"],
        "answered_indicators": raw["answered_indicators"],
        "total_indicators": raw["total_indicators"],
        "completion_pct": _percentage(raw["answered_indicators"], raw["total_indicators"]),
        "services_started": services_started,
        "services_started_pct": _percentage(services_started, len(services)),
        "services_ready": services_ready,
        "services_pending": len(services) - services_ready,
        "services_up_to_date": services_up_to_date,
        "services_due_soon": services_due_soon,
        "services_urgent": services_urgent,
        "services": services,
        "benchmark_summary": benchmark_summary,
        "benchmark_by_service": benchmark_by_service,
        "priority_services": priority_services,
        "stage_matrix": stage_matrix,
        "history": [{"label": item["label"], "level": item["level"]} for item in history],
        "available_periods": available_periods,
    }


def get_national_snapshot_view(snapshot: SnapshotContext, audience: str) -> dict[str, Any]:
    """Return the audience-specific national view model.

    Args:
        snapshot: Snapshot context.
        audience: Consumer audience.

    Returns:
        National view model shaped for the requested audience.
    """

    raw = get_national_snapshot(snapshot, audience=audience)
    service_level_counts: dict[str, Counter] = defaultdict(Counter)
    service_score_totals: dict[str, list[float]] = defaultdict(list)
    operational_status_counts: Counter = Counter()

    for municipality in raw["municipalities"]:
        for service in municipality["services"]:
            service_level_counts[service["service_name"]][service["level"]] += 1
            service_score_totals[service["service_name"]].append(service["score"])
            operational_status_counts[service["operational_status"]] += 1

    service_summaries = []
    for service_name, level_counts in sorted(service_level_counts.items()):
        predominant_level = max(level_counts, key=level_counts.get)
        summary = {
            "service_name": service_name,
            "predominant_level": predominant_level,
            "level_distribution": dict(level_counts),
            "maturity_index": _service_maturity_index(level_counts),
            "maturity_label": _level_axis_label(_service_maturity_index(level_counts)),
        }
        if audience == AUDIENCE_ADMIN:
            score_values = service_score_totals.get(service_name, [])
            average_score = round(sum(score_values) / len(score_values), 4) if score_values else 0.0
            summary["average_score"] = average_score
            summary["puntaje_pct"] = round(average_score * 100, 2)
        service_summaries.append(summary)

    available_periods = list_available_periods()
    if audience == AUDIENCE_ADMIN:
        return {
            **raw,
            "service_summaries": service_summaries,
            "operational_status_distribution": dict(operational_status_counts),
            "regional_history": _build_regional_history(available_periods),
            "available_periods": available_periods,
        }

    municipalities = []
    map_points = []
    comparison_candidates = []
    for municipality in raw["municipalities"]:
        row = {
            "codigo": municipality["municipality"]["codigo"],
            "municipalidad": municipality["municipality"]["nombre"],
            "provincia": municipality["municipality"].get("provincia"),
            "region": municipality["municipality"].get("region"),
            "nivel": municipality["level"],
        }
        municipalities.append(row)
        map_points.append(
            {
                **row,
                "lat": municipality["municipality"].get("lat"),
                "lon": municipality["municipality"].get("lon"),
            }
        )
        comparison_candidates.append(
            {
                **row,
                "service_levels": {
                    service["service_name"]: service["level"]
                    for service in municipality["services"]
                },
            }
        )

    history = get_monthly_history(None, audience=AUDIENCE_PUBLIC)
    return {
        "snapshot": raw["snapshot"],
        "total_municipalities": raw["total_municipalities"],
        "distribution_by_level": raw["distribution_by_level"],
        "service_summaries": service_summaries,
        "municipalities": municipalities,
        "map_points": map_points,
        "comparison_candidates": comparison_candidates,
        "history": history,
        "available_periods": available_periods,
    }
