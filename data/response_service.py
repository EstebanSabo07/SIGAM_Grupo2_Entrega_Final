"""Response-editing helpers for the navigable municipal form."""

from __future__ import annotations

from datetime import date
from typing import Any

from data.catalog_service import get_section_catalog
from data.snapshot import SnapshotContext
from data.snapshot_service import resolve_indicator_values
from database.models import utcnow
from database.repositories import save_indicator_response_versions


def get_section_responses(
    municipality_code: str,
    section_id: str,
    snapshot: SnapshotContext,
) -> dict[str, Any]:
    """Return one form section with its persisted snapshot values.

    Args:
        municipality_code: Municipal code.
        section_id: Encoded section identifier.
        snapshot: Snapshot context.

    Returns:
        Section catalog merged with persisted values.
    """

    section = get_section_catalog(municipality_code, section_id, snapshot)
    snapshot_values = resolve_indicator_values(municipality_code, snapshot)
    indicators = []
    for indicator in section["indicators"]:
        current = snapshot_values.get(indicator["indicator_code"], {})
        indicators.append(
            {
                **indicator,
                "value": current.get("value"),
                "response_id": current.get("response_id"),
                "date_time": current.get("date_time"),
                "evidence_files": current.get("evidence_files", []),
            }
        )
    return {**section, "indicators": indicators}


def validate_section_payload(section: dict[str, Any], payload: dict[str, dict[str, Any]]) -> list[str]:
    """Validate a staged form-section payload before saving.

    Args:
        section: Section catalog and current values.
        payload: Proposed values keyed by indicator code.

    Returns:
        Validation error messages.
    """

    errors: list[str] = []
    for indicator in section["indicators"]:
        code = indicator["indicator_code"]
        item = payload.get(code, {})
        value = item.get("value")
        indicator_type = indicator["indicator_type"]
        current_value = indicator.get("value")
        if current_value is not None and value is None:
            errors.append(f"{code}: no se puede eliminar una respuesta ya registrada; actualícela con un nuevo valor.")
            continue
        if value is None:
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            errors.append(f"{code}: el valor debe ser numérico.")
            continue

        if indicator_type in {"binario", "decision"} and numeric_value not in {0.0, 1.0}:
            errors.append(f"{code}: el valor debe ser 0 o 1.")
        elif indicator_type in {"cobertura", "porcentaje"} and not 0.0 <= numeric_value <= 1.0:
            errors.append(f"{code}: el valor debe estar entre 0 y 1.")
        elif not 0.0 <= numeric_value <= 1.0:
            errors.append(f"{code}: el valor debe estar entre 0 y 1.")

        evidence_files = item.get("evidence_files", [])
        if indicator["evidence_required"] and value is not None and not evidence_files:
            errors.append(f"{code}: debe adjuntar al menos una evidencia.")

    return errors


def save_section_changes(
    municipality_code: str,
    section_id: str,
    payload: dict[str, dict[str, Any]],
    actor_context: dict[str, Any] | None = None,
    snapshot: SnapshotContext | None = None,
) -> dict[str, Any]:
    """Persist changed indicator versions for one form section.

    Args:
        municipality_code: Municipal code.
        section_id: Encoded section identifier.
        payload: Proposed values keyed by indicator code.
        actor_context: Optional actor metadata.
        snapshot: Optional snapshot context used to resolve current values.

    Returns:
        Save summary with validation errors and write counts.
    """

    active_snapshot = snapshot or SnapshotContext(
        year=date.today().year,
        month=date.today().month,
        audience="municipal",
        municipality_code=municipality_code,
    )
    section = get_section_responses(municipality_code, section_id, active_snapshot)
    validation_errors = validate_section_payload(section, payload)
    if validation_errors:
        return {
            "saved_rows": 0,
            "validation_errors": validation_errors,
            "section_id": section_id,
        }

    changed_rows: list[dict[str, Any]] = []
    current_by_code = {indicator["indicator_code"]: indicator for indicator in section["indicators"]}
    for code, proposed in payload.items():
        current = current_by_code.get(code)
        if current is None:
            continue
        current_value = current.get("value")
        new_value = proposed.get("value")
        current_evidence = [item.get("file_name") for item in current.get("evidence_files", [])]
        new_evidence = [item.get("file_name") for item in proposed.get("evidence_files", [])]
        if current_value == new_value and current_evidence == new_evidence:
            continue
        changed_rows.append(
            {
                "indicator_code": code,
                "value": float(new_value) if new_value is not None else 0.0,
                "evidence_files": proposed.get("evidence_files", []),
            }
        )

    if not changed_rows:
        return {
            "saved_rows": 0,
            "validation_errors": [],
            "section_id": section_id,
        }

    result = save_indicator_response_versions(
        municipality_code=municipality_code,
        responses=changed_rows,
        submitted_at=utcnow(),
        actor_subject=(actor_context or {}).get("actor_subject"),
    )
    return {
        **result,
        "validation_errors": [],
        "section_id": section_id,
    }
