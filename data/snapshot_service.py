"""Snapshot-resolution helpers for month-based SIGAM reporting."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import extract, select

from database.models import FactIndicatorResponse
from database.repositories import get_latest_indicator_snapshots
from database.session import session_scope
from data.snapshot import SnapshotContext


def resolve_indicator_values(
    municipality_code: str,
    snapshot: SnapshotContext,
) -> dict[str, dict[str, Any]]:
    """Resolve the latest indicator values valid for a snapshot cutoff.

    Args:
        municipality_code: Municipal code.
        snapshot: Snapshot context.

    Returns:
        Mapping from indicator code to snapshot metadata.
    """

    return get_latest_indicator_snapshots(
        municipality_code=municipality_code,
        end_date=snapshot.end_date,
    )


def list_available_periods() -> list[dict[str, Any]]:
    """List available response periods across the full dataset.

    Returns:
        Period dictionaries sorted from newest to oldest.
    """

    with session_scope() as session:
        statement = (
            select(
                extract("year", FactIndicatorResponse.date_time).label("year"),
                extract("month", FactIndicatorResponse.date_time).label("month"),
            )
            .distinct()
            .order_by(
                extract("year", FactIndicatorResponse.date_time).desc(),
                extract("month", FactIndicatorResponse.date_time).desc(),
            )
        )
        rows = session.execute(statement)
        periods = []
        for year, month in rows:
            year_int = int(year)
            month_int = int(month)
            periods.append(
                {
                    "year": year_int,
                    "month": month_int,
                    "label": f"{year_int:04d}-{month_int:02d}",
                }
            )
        return periods


def _iter_month_periods(start_year: int, start_month: int, end_year: int, end_month: int) -> list[dict[str, Any]]:
    """Build a continuous monthly period range.

    Args:
        start_year: Inclusive start year.
        start_month: Inclusive start month.
        end_year: Inclusive end year.
        end_month: Inclusive end month.

    Returns:
        Period dictionaries in ascending order.
    """

    periods: list[dict[str, Any]] = []
    year = start_year
    month = start_month
    while (year, month) <= (end_year, end_month):
        periods.append(
            {
                "year": year,
                "month": month,
                "label": f"{year:04d}-{month:02d}",
            }
        )
        month += 1
        if month > 12:
            month = 1
            year += 1
    return periods


def resolve_snapshot_period(
    requested_year: int | None = None,
    requested_month: int | None = None,
    periods: list[dict[str, Any]] | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Resolve a valid period selection from the periods present in data.

    Args:
        requested_year: Optional requested year.
        requested_month: Optional requested month.
        periods: Optional preloaded periods.
        today: Optional date override when no periods exist.

    Returns:
        Selector metadata with the chosen period and available options.
    """

    available_real_periods = sorted(
        periods if periods is not None else list_available_periods(),
        key=lambda item: (item["year"], item["month"]),
    )
    reference = today or date.today()
    month_labels = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }

    if not available_real_periods:
        return {
            "has_data": False,
            "selected_period": {
                "year": reference.year,
                "month": reference.month,
                "label": f"{reference.year:04d}-{reference.month:02d}",
            },
            "first_real_period": None,
            "latest_real_period": None,
            "available_periods": [],
            "available_years": [reference.year],
            "months_for_year": [{"month": reference.month, "label": month_labels[reference.month]}],
        }

    first_real_period = available_real_periods[0]
    latest_real_period = available_real_periods[-1]
    available_periods = _iter_month_periods(
        first_real_period["year"],
        first_real_period["month"],
        reference.year,
        reference.month,
    )

    lookup = {(item["year"], item["month"]): item for item in available_periods}
    selected_period = lookup.get((requested_year, requested_month), latest_real_period)
    selected_year = selected_period["year"]
    months_for_year = [
        {"month": item["month"], "label": month_labels[item["month"]]}
        for item in available_periods
        if item["year"] == selected_year
    ]

    return {
        "has_data": True,
        "selected_period": selected_period,
        "first_real_period": first_real_period,
        "latest_real_period": latest_real_period,
        "available_periods": available_periods,
        "available_years": sorted({item["year"] for item in available_periods}),
        "months_for_year": months_for_year,
    }


def month_age(cutoff: date, reference: date | None) -> int | None:
    """Calculate the age in whole months between two dates.

    Args:
        cutoff: Snapshot cutoff date.
        reference: Reference date to age.

    Returns:
        Whole-month difference, or None when the reference date is missing.
    """

    if reference is None:
        return None
    return (cutoff.year - reference.year) * 12 + (cutoff.month - reference.month)
