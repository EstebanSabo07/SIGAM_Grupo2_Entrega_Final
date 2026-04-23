"""Import the CSV source files as the ORM baseline dataset."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from database.models import (
    Base,
    DMAxis,
    DMIndicator,
    DMMunicipality,
    DMMunicipalityDiversifiedService,
    DMService,
    DMStage,
    FactIndicatorResponse,
)
from database.session import get_engine, session_scope


BASELINE_SUBMITTED_AT = datetime(2025, 1, 1, tzinfo=timezone.utc)
DEFAULT_SOURCE_DIR = Path(__file__).resolve().parent / "source"

AXIS_CODES = {
    "Salubridad Pública": "1",
    "Desarrollo Urbano": "2",
    "Servicios Sociales": "3",
}
STAGE_WEIGHTS = {
    "Planificación": 0.50,
    "Ejecución": 0.30,
    "Evaluación": 0.20,
}
GROUPING_NORMALIZATION = {
    "Básicos": "Básico",
    "Básico": "Básico",
    "Diversificados": "Diversificado",
    "Diversificado": "Diversificado",
}
DIVERSIFIED_KEYS = {
    "Agua potable": "agua_potable",
    "Zona Marítimo Terrestre": "zmt",
    "Seguridad y vigilancia en la comunidad": "seguridad",
}


@dataclass(frozen=True)
class SourceIndicator:
    """Indicator row parsed from the source dictionary CSV.

    Attributes:
        code: Official indicator code.
        name: Indicator display name.
        grouping: Normalized grouping label.
        axis: Axis display name.
        axis_code: Official axis code.
        service: Service display name.
        service_code: Official service code derived from the indicator code.
        stage: Stage display name.
        diversified_key: Diversified-service key when applicable.
    """

    code: str
    name: str
    grouping: str
    axis: str
    axis_code: str
    service: str
    service_code: str
    stage: str
    diversified_key: str | None


@dataclass(frozen=True)
class SourceValue:
    """Numeric source response parsed from the results CSV.

    Attributes:
        municipality_code: Municipality code matched from source labels.
        indicator_code: Indicator code.
        value: Numeric response value.
    """

    municipality_code: str
    indicator_code: str
    value: float


@dataclass(frozen=True)
class SourceMunicipality:
    """Municipality metadata parsed from baseline results.

    Attributes:
        code: Municipality code.
        name: Municipality name from the source or reference catalog.
        province: Province name.
        region: Planning region name.
        latitude: Latitude from the reference catalog.
        longitude: Longitude from the reference catalog.
        diversified_keys: Diversified-service keys assigned to the municipality.
    """

    code: str
    name: str
    province: str | None
    region: str | None
    latitude: float | None
    longitude: float | None
    diversified_keys: tuple[str, ...]


def load_source_baseline(
    period: str = "2025",
    replace: bool = True,
    source_dir: str | Path | None = None,
    database_url: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Load the source CSV files into the configured ORM database.

    The import is intentionally idempotent by default: previous fact rows
    created by this source-baseline importer are replaced while unrelated facts
    are left untouched.

    Args:
        period: Submission period label assigned to the summary.
        replace: Whether to replace existing baseline fact rows.
        source_dir: Optional directory containing the source CSV files.
        database_url: Optional database URL override.
        dry_run: Whether to validate and summarize without writing to the
            database.

    Returns:
        Import summary with source counts, database counts, and write counts.

    Raises:
        ValueError: If the CSV contents are invalid or reference unknown codes.
        FileNotFoundError: If required source CSV files are missing.
    """

    source_path = Path(source_dir) if source_dir is not None else DEFAULT_SOURCE_DIR
    dictionary = _read_dictionary(source_path / "dictionary.csv")
    source_municipalities, municipality_lookup = _source_municipalities_from_results(
        source_path / "igsm_2025_results_long.csv"
    )
    values, result_stats = _read_results(
        source_path / "igsm_2025_results_long.csv",
        indicators_by_code={item.code: item for item in dictionary},
        municipality_lookup=municipality_lookup,
    )

    summary: dict[str, Any] = {
        "period": period,
        "source_dir": str(source_path),
        "dry_run": dry_run,
        "skipped": False,
        "source_indicators": len(dictionary),
        "source_values_total": result_stats["total_rows"],
        "blank_values_skipped": result_stats["blank_rows"],
        "nonblank_values": len(values),
        "source_municipalities": len(source_municipalities),
    }

    if dry_run:
        return summary

    engine = get_engine(database_url)
    Base.metadata.create_all(engine)

    with session_scope(database_url) as session:
        existing_baseline_facts = _baseline_fact_count(session)
        summary["existing_baseline_facts"] = existing_baseline_facts

        if existing_baseline_facts and not replace:
            summary["skipped"] = True
            return summary

        summary.update(_delete_existing_baseline(session))
        derived_diversified = _derive_diversified_keys(values, {item.code: item for item in dictionary})
        structure_counts = _upsert_igsm_structure(session, dictionary)
        municipalities = _upsert_municipalities(session, source_municipalities, derived_diversified)
        summary.update(structure_counts)

        db_municipalities = {
            row.code: row
            for row in session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars()
        }
        db_indicators = {row.code: row for row in session.execute(select(DMIndicator)).scalars()}
        values_by_municipality: dict[str, list[SourceValue]] = {}
        for item in values:
            values_by_municipality.setdefault(item.municipality_code, []).append(item)

        inserted_facts = 0
        for municipality_code in sorted(municipalities):
            municipality = db_municipalities[municipality_code]
            municipality_values = values_by_municipality.get(municipality_code, [])

            for value in municipality_values:
                indicator = db_indicators.get(value.indicator_code)
                if indicator is None:
                    raise ValueError(f"Indicator disappeared during import: {value.indicator_code}")
                session.add(
                    FactIndicatorResponse(
                        date_time=BASELINE_SUBMITTED_AT,
                        municipality_id=municipality.municipality_id,
                        indicator_id=indicator.indicator_id,
                        value=value.value,
                    )
                )
            inserted_facts += len(municipality_values)

        session.flush()
        summary.update(
            {
                "municipalities": len(municipalities),
                "facts_inserted": inserted_facts,
            }
        )

    return summary


def _read_dictionary(path: Path) -> list[SourceIndicator]:
    """Read and validate the indicator dictionary CSV.

    Args:
        path: Path to ``dictionary.csv``.

    Returns:
        Parsed source indicator rows.

    Raises:
        ValueError: If required fields are missing or invalid.
        FileNotFoundError: If the CSV file is missing.
    """

    required = {"Código", "Indicador", "Agrupación", "Eje", "Servicio", "Etapa"}
    rows = _read_csv_rows(path, required)
    indicators: list[SourceIndicator] = []
    seen_codes: set[str] = set()

    for index, row in enumerate(rows, start=2):
        code = row["Código"].strip()
        if not code:
            raise ValueError(f"Missing indicator code in {path} line {index}")
        if code in seen_codes:
            raise ValueError(f"Duplicate indicator code in dictionary.csv: {code}")
        seen_codes.add(code)

        axis = row["Eje"].strip()
        if axis not in AXIS_CODES:
            raise ValueError(f"Unknown axis for indicator {code}: {axis}")

        grouping_label = row["Agrupación"].strip()
        grouping = GROUPING_NORMALIZATION.get(grouping_label)
        if grouping is None:
            raise ValueError(f"Unknown grouping for indicator {code}: {grouping_label}")

        stage = row["Etapa"].strip()
        if stage not in STAGE_WEIGHTS:
            raise ValueError(f"Unknown stage for indicator {code}: {stage}")

        service = row["Servicio"].strip()
        diversified_key = DIVERSIFIED_KEYS.get(service) if grouping == "Diversificado" else None
        indicators.append(
            SourceIndicator(
                code=code,
                name=row["Indicador"].strip(),
                grouping=grouping,
                axis=axis,
                axis_code=AXIS_CODES[axis],
                service=service,
                service_code=_service_code_from_indicator_code(code),
                stage=stage,
                diversified_key=diversified_key,
            )
        )

    return indicators


def _read_results(
    path: Path,
    indicators_by_code: dict[str, SourceIndicator],
    municipality_lookup: dict[str, str],
) -> tuple[list[SourceValue], dict[str, int]]:
    """Read and validate baseline result values.

    Args:
        path: Path to the long-form results CSV.
        indicators_by_code: Source indicators keyed by indicator code.
        municipality_lookup: Municipality code lookup keyed by normalized labels.

    Returns:
        Parsed source values and row-count statistics.

    Raises:
        ValueError: If the file references unknown indicators or nonnumeric
            values.
        FileNotFoundError: If the CSV file is missing.
    """

    required = {"Municipalidad", "Código", "Valor", "Cantón"}
    rows = _read_csv_rows(path, required)
    values: list[SourceValue] = []
    blank_rows = 0

    for index, row in enumerate(rows, start=2):
        indicator_code = row["Código"].strip()
        if indicator_code not in indicators_by_code:
            raise ValueError(f"Unknown indicator code in results line {index}: {indicator_code}")

        municipality_code = _municipality_code_for_result(row, municipality_lookup)
        raw_value = row["Valor"].strip()
        if raw_value == "":
            blank_rows += 1
            continue

        try:
            value = float(raw_value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(
                f"Nonnumeric Valor in results line {index} "
                f"for municipality {row['Municipalidad']!r}, indicator {indicator_code}: {raw_value!r}"
            ) from exc

        values.append(
            SourceValue(
                municipality_code=municipality_code,
                indicator_code=indicator_code,
                value=value,
            )
        )

    return values, {"total_rows": len(rows), "blank_rows": blank_rows}


def _read_csv_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    """Read a CSV file as dictionaries and validate required columns.

    Args:
        path: CSV file path.
        required_columns: Column names that must exist in the file.

    Returns:
        CSV rows with missing cell values normalized to empty strings.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """

    if not path.exists():
        raise FileNotFoundError(f"Source CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or [])
        missing = required_columns - columns
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"{path.name} is missing required columns: {missing_list}")
        return [{key: value or "" for key, value in row.items()} for row in reader]


def _service_code_from_indicator_code(code: str) -> str:
    """Derive a service code from an indicator code.

    Args:
        code: Dot-separated indicator code.

    Returns:
        First three code segments joined as a service code.

    Raises:
        ValueError: If the indicator code has fewer than three segments.
    """

    parts = code.split(".")
    if len(parts) < 3:
        raise ValueError(f"Indicator code must have at least three segments: {code}")
    return ".".join(parts[:3])


def _normalize_name(value: str) -> str:
    """Normalize a municipality label for matching.

    Args:
        value: Raw municipality label.

    Returns:
        Lowercase ASCII label with punctuation and extra whitespace removed.
    """

    value = value.strip()
    value = re.sub(r"^municipalidad\s+de\s+", "", value, flags=re.IGNORECASE)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def _reference_municipalities_by_normalized_name() -> dict[str, dict[str, Any]]:
    """Build the reference municipality lookup by normalized name.

    Returns:
        Municipality dictionaries keyed by normalized aliases.
    """

    from data.municipalities import MUNICIPALIDADES

    aliases = {
        "sarchi": "valverde vega",
        "zarcero": "alfaro ruiz",
        "vazquez de coronado": "vasquez de coronado",
    }
    lookup: dict[str, dict[str, Any]] = {}
    for item in MUNICIPALIDADES:
        name = item["nombre"]
        lookup[_normalize_name(name)] = item
        lookup[_normalize_name(f"Municipalidad de {name}")] = item
    for source_name, reference_name in aliases.items():
        reference = lookup.get(reference_name)
        if reference is not None:
            lookup[source_name] = reference
    return lookup


FALLBACK_MUNICIPALITIES = {
    "puerto jimenez": {
        "codigo": "613",
        "nombre": "Puerto Jiménez",
        "provincia": "Puntarenas",
        "region": "Brunca",
        "lat": None,
        "lon": None,
        "diversificados": ["zmt"],
    },
}


def _source_municipalities_from_results(path: Path) -> tuple[dict[str, SourceMunicipality], dict[str, str]]:
    """Extract municipality metadata and lookup aliases from results.

    Args:
        path: Path to the long-form results CSV.

    Returns:
        Source municipalities keyed by code and normalized-name lookup mapping.

    Raises:
        ValueError: If a source municipality cannot be matched.
        FileNotFoundError: If the CSV file is missing.
    """

    rows = _read_csv_rows(path, {"Municipalidad", "Código", "Valor", "Cantón"})
    reference_by_name = _reference_municipalities_by_normalized_name()
    source_municipalities: dict[str, SourceMunicipality] = {}
    lookup: dict[str, str] = {}

    for row in rows:
        canton = row["Cantón"].strip()
        municipality_label = row["Municipalidad"].strip()
        normalized = _normalize_name(canton or municipality_label)
        reference = reference_by_name.get(normalized) or FALLBACK_MUNICIPALITIES.get(normalized)
        if reference is None:
            raise ValueError(
                "Unknown municipality in results: "
                f"Municipalidad={municipality_label!r}, Cantón={canton!r}"
            )

        code = reference["codigo"]
        if code not in source_municipalities:
            source_municipalities[code] = SourceMunicipality(
                code=code,
                name=canton or reference["nombre"],
                province=reference.get("provincia"),
                region=reference.get("region"),
                latitude=reference.get("lat"),
                longitude=reference.get("lon"),
                diversified_keys=tuple(reference.get("diversificados", [])),
            )
        lookup[_normalize_name(canton)] = code
        lookup[_normalize_name(municipality_label)] = code
        lookup[_normalize_name(reference["nombre"])] = code

    return source_municipalities, lookup


def _municipality_code_for_result(row: dict[str, str], municipality_lookup: dict[str, str]) -> str:
    """Resolve a municipality code for one result row.

    Args:
        row: CSV result row.
        municipality_lookup: Municipality code lookup keyed by normalized labels.

    Returns:
        Matched municipality code.

    Raises:
        ValueError: If the row cannot be matched to a municipality.
    """

    candidates = [row["Cantón"], row["Municipalidad"]]
    for candidate in candidates:
        code = municipality_lookup.get(_normalize_name(candidate))
        if code is not None:
            return code
    raise ValueError(
        "Unknown municipality in results: "
        f"Municipalidad={row['Municipalidad']!r}, Cantón={row['Cantón']!r}"
    )


def _baseline_fact_count(session: Session) -> int:
    """Count fact rows created by the baseline importer.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        Number of fact rows using the baseline import timestamp.
    """

    return int(
        session.scalar(
            select(func.count()).select_from(FactIndicatorResponse).where(
                FactIndicatorResponse.date_time == BASELINE_SUBMITTED_AT
            )
        )
        or 0
    )


def _delete_existing_baseline(session: Session) -> dict[str, int]:
    """Delete fact rows created by a previous baseline import.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        Summary counts for deleted rows.
    """

    fact_result = session.execute(
        delete(FactIndicatorResponse).where(FactIndicatorResponse.date_time == BASELINE_SUBMITTED_AT)
    )
    session.flush()
    return {"facts_deleted": int(fact_result.rowcount or 0)}


def _derive_diversified_keys(
    values: list[SourceValue],
    dictionary_by_code: dict[str, SourceIndicator],
) -> dict[str, set[str]]:
    """Infer diversified-service keys from submitted source values.

    Args:
        values: Parsed source response values.
        dictionary_by_code: Source indicators keyed by indicator code.

    Returns:
        Diversified-service keys keyed by municipality code.
    """

    diversified: dict[str, set[str]] = {}
    for item in values:
        diversified_key = dictionary_by_code[item.indicator_code].diversified_key
        if diversified_key:
            diversified.setdefault(item.municipality_code, set()).add(diversified_key)
    return diversified


def _upsert_municipalities(
    session: Session,
    source_municipalities: dict[str, SourceMunicipality],
    derived_diversified: dict[str, set[str]],
) -> set[str]:
    """Insert or update municipalities and diversified-service links.

    Args:
        session: Active SQLAlchemy session.
        source_municipalities: Municipality metadata keyed by municipal code.
        derived_diversified: Diversified keys inferred from baseline values.

    Returns:
        Set of municipal codes touched by the import.
    """

    diversified_services = {
        row.diversified_key: row
        for row in session.execute(select(DMService).where(DMService.diversified_key.is_not(None))).scalars()
        if row.diversified_key
    }
    municipality_codes: set[str] = set()
    for item in source_municipalities.values():
        municipality_codes.add(item.code)
        municipality = session.execute(
            select(DMMunicipality).where(DMMunicipality.code == item.code)
        ).scalar_one_or_none()
        if municipality is None:
            municipality = DMMunicipality(code=item.code, name=item.name)
            session.add(municipality)

        municipality.name = item.name
        municipality.province = item.province
        municipality.region = item.region
        municipality.latitude = item.latitude
        municipality.longitude = item.longitude
        session.flush()

        existing_service_ids = set(
            session.execute(
                select(DMMunicipalityDiversifiedService.service_id).where(
                    DMMunicipalityDiversifiedService.municipality_id == municipality.municipality_id
                )
            ).scalars()
        )
        desired_keys = set(item.diversified_keys) | derived_diversified.get(item.code, set())
        desired_service_ids = {
            diversified_services[key].service_id for key in desired_keys if key in diversified_services
        }
        for service_id in desired_service_ids - existing_service_ids:
            session.add(
                DMMunicipalityDiversifiedService(
                    municipality_id=municipality.municipality_id,
                    service_id=service_id,
                )
            )

    session.flush()
    return municipality_codes


def _upsert_igsm_structure(session: Session, dictionary: list[SourceIndicator]) -> dict[str, int]:
    """Insert or update axes, services, stages, and indicators.

    Args:
        session: Active SQLAlchemy session.
        dictionary: Parsed source dictionary rows.

    Returns:
        Current table counts for the IGSM structure.
    """

    axes_by_name: dict[str, DMAxis] = {}
    services_by_code: dict[str, DMService] = {}
    stages_by_name: dict[str, DMStage] = {}

    for item in dictionary:
        axis = axes_by_name.get(item.axis)
        if axis is None:
            axis = session.execute(select(DMAxis).where(DMAxis.name == item.axis)).scalar_one_or_none()
            if axis is None:
                axis = DMAxis(name=item.axis)
                session.add(axis)
            axis.name = item.axis
            session.flush()
            axes_by_name[item.axis] = axis

        service = services_by_code.get(item.service_code)
        if service is None:
            service = session.execute(
                select(DMService).where(DMService.service_code == item.service_code)
            ).scalar_one_or_none()
            if service is None:
                service = DMService(
                    axis_id=axis.axis_id,
                    service_code=item.service_code,
                    name=item.service,
                )
                session.add(service)
            services_by_code[item.service_code] = service
        service.axis_id = axis.axis_id
        service.name = item.service
        service.grouping = item.grouping
        service.diversified_key = item.diversified_key
        session.flush()

        stage = stages_by_name.get(item.stage)
        if stage is None:
            stage = session.execute(select(DMStage).where(DMStage.name == item.stage)).scalar_one_or_none()
            if stage is None:
                stage = DMStage(name=item.stage)
                session.add(stage)
            stages_by_name[item.stage] = stage
            session.flush()

        indicator = session.execute(select(DMIndicator).where(DMIndicator.code == item.code)).scalar_one_or_none()
        if indicator is None:
            indicator = DMIndicator(
                service_id=service.service_id,
                stage_id=stage.stage_id,
                code=item.code,
                name=item.name,
            )
            session.add(indicator)
        indicator.service_id = service.service_id
        indicator.stage_id = stage.stage_id
        indicator.name = item.name

    session.flush()
    return {
        "axes": session.scalar(select(func.count()).select_from(DMAxis)) or 0,
        "services": session.scalar(select(func.count()).select_from(DMService)) or 0,
        "stages": session.scalar(select(func.count()).select_from(DMStage)) or 0,
        "indicators": session.scalar(select(func.count()).select_from(DMIndicator)) or 0,
    }


def main() -> None:
    """Run the source-baseline importer CLI."""

    parser = argparse.ArgumentParser(description="Import database/source CSV files as the ORM baseline dataset.")
    parser.add_argument("--period", default="2025", help="Submission period to assign to imported baseline rows.")
    parser.add_argument("--source-dir", default=None, help="Directory containing dictionary.csv and results CSV.")
    parser.add_argument("--database-url", default=None, help="Override DATABASE_URL for this import.")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip import if source-baseline submissions already exist for the period.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate source files and print the planned counts.")
    args = parser.parse_args()

    summary = load_source_baseline(
        period=args.period,
        replace=not args.skip_existing,
        source_dir=args.source_dir,
        database_url=args.database_url,
        dry_run=args.dry_run,
    )
    for key in sorted(summary):
        print(f"{key}: {summary[key]}")


if __name__ == "__main__":
    main()
