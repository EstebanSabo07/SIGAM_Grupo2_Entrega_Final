"""Catalog-service helpers backed by the ORM repository layer."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from database.repositories import get_form_catalog


def build_section_id(service_code: str, stage_name: str) -> str:
    """Build a stable section identifier for one service stage.

    Args:
        service_code: Service code.
        stage_name: Stage display name.

    Returns:
        Stable section identifier.
    """

    return f"{service_code}::{stage_name}"


def parse_section_id(section_id: str) -> tuple[str, str]:
    """Split a section identifier into service code and stage name.

    Args:
        section_id: Encoded section identifier.

    Returns:
        Tuple of service code and stage name.
    """

    service_code, stage_name = section_id.split("::", 1)
    return service_code, stage_name


def get_form_tree(municipality_code: str, snapshot: Any) -> dict[str, Any]:
    """Return the form tree applicable to a municipality.

    Args:
        municipality_code: Municipal code.
        snapshot: Snapshot context, accepted for interface consistency.

    Returns:
        Nested axis-service-stage catalog tree.
    """

    _ = snapshot
    rows = get_form_catalog(municipality_code)
    axes: OrderedDict[str, dict[str, Any]] = OrderedDict()

    for row in rows:
        axis = axes.setdefault(
            row["axis_name"],
            {
                "axis_id": row["axis_id"],
                "axis_name": row["axis_name"],
                "services": OrderedDict(),
            },
        )
        service = axis["services"].setdefault(
            row["service_code"],
            {
                "service_id": row["service_id"],
                "service_code": row["service_code"],
                "service_name": row["service_name"],
                "service_grouping": row["service_grouping"],
                "diversified_key": row["diversified_key"],
                "stages": OrderedDict(),
            },
        )
        section_id = build_section_id(row["service_code"], row["stage_name"])
        stage = service["stages"].setdefault(
            row["stage_name"],
            {
                "section_id": section_id,
                "stage_id": row["stage_id"],
                "stage_name": row["stage_name"],
                "indicators": [],
            },
        )
        stage["indicators"].append(
            {
                "indicator_id": row["indicator_id"],
                "indicator_code": row["indicator_code"],
                "indicator_name": row["indicator_name"],
                "indicator_type": row["indicator_type"] or "binario",
                "evidence_required": bool(row["evidence_required"]),
                "documentation": row["documentation"],
            }
        )

    return {
        "municipality_code": municipality_code,
        "axes": [
            {
                **axis,
                "services": [
                    {
                        **service,
                        "stages": list(service["stages"].values()),
                    }
                    for service in axis["services"].values()
                ],
            }
            for axis in axes.values()
        ],
    }


def get_section_catalog(municipality_code: str, section_id: str, snapshot: Any) -> dict[str, Any]:
    """Return one stage section from the form tree.

    Args:
        municipality_code: Municipal code.
        section_id: Encoded section identifier.
        snapshot: Snapshot context.

    Returns:
        Section catalog with indicator metadata.

    Raises:
        ValueError: If the section does not exist.
    """

    form_tree = get_form_tree(municipality_code, snapshot)
    for axis in form_tree["axes"]:
        for service in axis["services"]:
            for stage in service["stages"]:
                if stage["section_id"] == section_id:
                    return {
                        "axis_name": axis["axis_name"],
                        "service_code": service["service_code"],
                        "service_name": service["service_name"],
                        "service_grouping": service["service_grouping"],
                        "stage_name": stage["stage_name"],
                        "section_id": stage["section_id"],
                        "indicators": stage["indicators"],
                    }
    raise ValueError(f"Unknown section_id: {section_id}")
