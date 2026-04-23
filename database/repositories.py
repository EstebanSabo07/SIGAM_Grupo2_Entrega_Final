"""Repository functions for the IGSM ORM package."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from database.models import (
    DMIndicator,
    DMMunicipality,
    DMMunicipalityDiversifiedService,
    DMService,
    FactIndicatorResponse,
    FactMaturityThreshold,
    FactStageWeight,
    utcnow,
)
from database.session import session_scope


DEFAULT_STAGE_WEIGHTS = {"Planificación": 0.50, "Ejecución": 0.30, "Evaluación": 0.20}
EndDate = date | datetime | str | None


def _managed_session(session: Session | None = None):
    """Return a caller-owned session or create a managed session.

    Args:
        session: Optional SQLAlchemy session supplied by the caller.

    Returns:
        Context manager that yields a SQLAlchemy session.
    """

    return nullcontext(session) if session is not None else session_scope()


def _one_or_none(session: Session, statement: Select):
    """Execute a scalar statement and return its first row.

    Args:
        session: Active SQLAlchemy session.
        statement: SQLAlchemy select statement.

    Returns:
        First scalar result, or None when no row matches.
    """

    return session.execute(statement).scalars().first()


def _parse_end_date(end_date: EndDate) -> date | datetime | None:
    """Parse an end-date value.

    Args:
        end_date: Optional cutoff date as a date, datetime, ``YYYY-MM-DD``, or
            legacy ``YYYY`` string.

    Returns:
        Parsed date or datetime. A legacy year string maps to December 31 of
        that year.

    Raises:
        ValueError: If the value cannot be parsed as a date.
    """

    if end_date is None or end_date == "":
        return None
    if isinstance(end_date, datetime):
        return end_date
    if isinstance(end_date, date):
        return end_date
    if not isinstance(end_date, str):
        raise ValueError(f"Unsupported end_date value: {end_date!r}")

    value = end_date.strip()
    try:
        if len(value) == 4 and value.isdigit():
            return date(int(value), 12, 31)
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"end_date must be an ISO date like YYYY-MM-DD: {end_date!r}") from exc


def _end_datetime(end_date: EndDate) -> datetime:
    """Build an inclusive datetime cutoff for an end date.

    Args:
        end_date: Optional cutoff date.

    Returns:
        Datetime cutoff at the end of the requested day.
    """

    parsed = _parse_end_date(end_date) or date.today()
    if isinstance(parsed, datetime):
        return parsed
    return datetime.combine(parsed, time.max)


def _timestamp_for_end_date(end_date: EndDate) -> datetime:
    """Build a response timestamp for an end date.

    Args:
        end_date: Optional response date.

    Returns:
        Datetime assigned to submitted fact rows.
    """

    parsed = _parse_end_date(end_date)
    if parsed is None:
        return utcnow()
    if isinstance(parsed, datetime):
        return parsed
    return datetime.combine(parsed, time.min)


def _date_label(end_date: EndDate) -> str:
    """Return a stable ISO label for an end date.

    Args:
        end_date: Optional cutoff date.

    Returns:
        ISO date or datetime label.
    """

    parsed = _parse_end_date(end_date)
    if parsed is None:
        return date.today().isoformat()
    return parsed.isoformat()


def _end_date_filter(statement: Select, end_date: EndDate) -> Select:
    """Apply an inclusive end-date filter to a fact-response statement.

    Args:
        statement: SQLAlchemy select statement.
        end_date: Optional cutoff date.

    Returns:
        Statement filtered by ``date_time``.
    """

    cutoff = _end_datetime(end_date)
    return statement.where(FactIndicatorResponse.date_time <= cutoff)


def _municipality_or_raise(session: Session, code: str) -> DMMunicipality:
    """Return a municipality by code or raise a clear error.

    Args:
        session: Active SQLAlchemy session.
        code: Municipal code.

    Returns:
        Matching municipality ORM row.

    Raises:
        ValueError: If the municipality code is unknown.
    """

    municipality = _one_or_none(
        session,
        select(DMMunicipality)
        .options(
            joinedload(DMMunicipality.diversified_services).joinedload(
                DMMunicipalityDiversifiedService.service
            )
        )
        .where(DMMunicipality.code == code),
    )
    if municipality is None:
        raise ValueError(f"Municipality not found for code: {code}")
    return municipality


def _municipality_to_dict(municipality: DMMunicipality) -> dict[str, Any]:
    """Convert a municipality ORM row into the app dictionary shape.

    Args:
        municipality: Municipality ORM row.

    Returns:
        Municipality dictionary.
    """

    diversified = [
        row.service.diversified_key
        for row in municipality.diversified_services
        if row.service is not None and row.service.diversified_key
    ]
    return {
        "codigo": municipality.code,
        "nombre": municipality.name,
        "municipalidad": municipality.name,
        "provincia": municipality.province,
        "region": municipality.region,
        "lat": municipality.latitude,
        "lon": municipality.longitude,
        "diversificados": sorted(diversified),
    }


def _service_to_dict(service: DMService) -> dict[str, Any]:
    """Convert a service ORM row into the app dictionary shape.

    Args:
        service: Service ORM row.

    Returns:
        Service dictionary.
    """

    return {
        "service_id": service.service_id,
        "codigo_servicio": service.service_code,
        "service_code": service.service_code,
        "name": service.name,
        "nombre": service.name,
        "agrupacion": service.grouping,
        "grouping": service.grouping,
        "diversificado_key": service.diversified_key,
        "eje": service.axis.name if service.axis else None,
        "axis": service.axis.name if service.axis else None,
    }


def _applicable_service_ids(municipality: DMMunicipality) -> set[int]:
    """Return service ids that apply to a municipality.

    Args:
        municipality: Municipality ORM row.

    Returns:
        Set of applicable service ids.
    """

    diversified_ids = {row.service_id for row in municipality.diversified_services}
    return diversified_ids


def _latest_response_values(
    session: Session,
    municipality_id: int,
    end_date: EndDate = None,
) -> dict[str, float]:
    """Return latest numeric values by indicator code for a municipality.

    Args:
        session: Active SQLAlchemy session.
        municipality_id: Municipality primary key.
        end_date: Optional inclusive cutoff date.

    Returns:
        Mapping from indicator code to numeric value.
    """

    statement = (
        select(FactIndicatorResponse)
        .options(joinedload(FactIndicatorResponse.indicator))
        .where(FactIndicatorResponse.municipality_id == municipality_id)
        .order_by(FactIndicatorResponse.date_time.desc(), FactIndicatorResponse.response_id.desc())
    )
    statement = _end_date_filter(statement, end_date)
    responses: dict[str, float] = {}
    for row in session.execute(statement).unique().scalars():
        responses.setdefault(row.indicator.code, float(row.value))
    return responses


def _count_indicators(session: Session) -> int:
    """Count configured IGSM indicators.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        Number of indicator rows.
    """

    return int(session.scalar(select(func.count()).select_from(DMIndicator)) or 0)


def _count_municipalities(session: Session) -> int:
    """Count configured municipalities.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        Number of municipality rows.
    """

    return int(session.scalar(select(func.count()).select_from(DMMunicipality)) or 0)


def _count_distinct_response_pairs(
    session: Session,
    end_date: EndDate = None,
    municipality_id: int | None = None,
) -> int:
    """Count unique municipality-indicator response pairs.

    Multiple fact rows for the same municipality and indicator before the same
    cutoff date count as one submitted response.

    Args:
        session: Active SQLAlchemy session.
        end_date: Optional inclusive cutoff date.
        municipality_id: Optional municipality primary key filter.

    Returns:
        Number of distinct response pairs.
    """

    statement = select(
        FactIndicatorResponse.municipality_id,
        FactIndicatorResponse.indicator_id,
    ).distinct()
    statement = _end_date_filter(statement, end_date)
    if municipality_id is not None:
        statement = statement.where(FactIndicatorResponse.municipality_id == municipality_id)

    response_pairs = statement.subquery()
    return int(session.scalar(select(func.count()).select_from(response_pairs)) or 0)


def _completion_percentage(responses_received: int, responses_expected: int) -> float:
    """Calculate a data-completion percentage.

    Args:
        responses_received: Count of unique submitted responses.
        responses_expected: Count of expected responses.

    Returns:
        Completion percentage rounded to two decimals.
    """

    if responses_expected == 0:
        return 0.0
    return round(responses_received / responses_expected * 100, 2)


def list_municipalities(session: Session | None = None) -> list[dict[str, Any]]:
    """List municipalities in display order.

    Args:
        session: Optional SQLAlchemy session.

    Returns:
        Municipality dictionaries.
    """

    with _managed_session(session) as db:
        rows = db.execute(
            select(DMMunicipality)
            .options(
                joinedload(DMMunicipality.diversified_services).joinedload(
                    DMMunicipalityDiversifiedService.service
                )
            )
            .order_by(DMMunicipality.name)
        ).unique().scalars()
        return [_municipality_to_dict(row) for row in rows]


def get_municipality_by_code(code: str, session: Session | None = None) -> dict[str, Any] | None:
    """Return one municipality by code.

    Args:
        code: Municipal code.
        session: Optional SQLAlchemy session.

    Returns:
        Municipality dictionary, or None.
    """

    with _managed_session(session) as db:
        municipality = _one_or_none(
            db,
            select(DMMunicipality)
            .options(
                joinedload(DMMunicipality.diversified_services).joinedload(
                    DMMunicipalityDiversifiedService.service
                )
            )
            .where(DMMunicipality.code == code),
        )
        return _municipality_to_dict(municipality) if municipality else None


def get_municipality_by_name(name: str, session: Session | None = None) -> dict[str, Any] | None:
    """Return one municipality by exact name.

    Args:
        name: Municipality name.
        session: Optional SQLAlchemy session.

    Returns:
        Municipality dictionary, or None.
    """

    with _managed_session(session) as db:
        municipality = _one_or_none(
            db,
            select(DMMunicipality)
            .options(
                joinedload(DMMunicipality.diversified_services).joinedload(
                    DMMunicipalityDiversifiedService.service
                )
            )
            .where(DMMunicipality.name == name),
        )
        return _municipality_to_dict(municipality) if municipality else None


def get_municipality_names(session: Session | None = None) -> list[str]:
    """Return municipality names.

    Args:
        session: Optional SQLAlchemy session.

    Returns:
        Sorted municipality names.
    """

    with _managed_session(session) as db:
        return list(db.execute(select(DMMunicipality.name).order_by(DMMunicipality.name)).scalars())


def list_municipalities_by_region(region: str, session: Session | None = None) -> list[dict[str, Any]]:
    """List municipalities for a region.

    Args:
        region: Region name.
        session: Optional SQLAlchemy session.

    Returns:
        Municipality dictionaries.
    """

    with _managed_session(session) as db:
        rows = db.execute(
            select(DMMunicipality)
            .options(
                joinedload(DMMunicipality.diversified_services).joinedload(
                    DMMunicipalityDiversifiedService.service
                )
            )
            .where(DMMunicipality.region == region)
            .order_by(DMMunicipality.name)
        ).unique().scalars()
        return [_municipality_to_dict(row) for row in rows]


def get_services_for_municipality(municipality_code: str, session: Session | None = None) -> dict[str, dict[str, Any]]:
    """Return services applicable to one municipality.

    Args:
        municipality_code: Municipal code.
        session: Optional SQLAlchemy session.

    Returns:
        Mapping from service name to service dictionary.
    """

    with _managed_session(session) as db:
        municipality = _municipality_or_raise(db, municipality_code)
        diversified_service_ids = _applicable_service_ids(municipality)
        rows = (
            db.execute(select(DMService).options(joinedload(DMService.axis)).order_by(DMService.service_code))
            .unique()
            .scalars()
        )
        services: dict[str, dict[str, Any]] = {}
        for service in rows:
            if service.grouping == "Básico" or service.service_id in diversified_service_ids:
                services[service.name] = _service_to_dict(service)
        return services


def get_indicators_for_service(service_code: str, session: Session | None = None) -> list[dict[str, Any]]:
    """Return indicators for a service code.

    Args:
        service_code: Service code.
        session: Optional SQLAlchemy session.

    Returns:
        Indicator dictionaries.
    """

    with _managed_session(session) as db:
        service = _one_or_none(
            db,
            select(DMService)
            .options(joinedload(DMService.indicators).joinedload(DMIndicator.stage))
            .where(DMService.service_code == service_code),
        )
        if service is None:
            return []
        return [
            {
                "codigo": indicator.code,
                "nombre": indicator.name,
                "tipo": indicator.type,
                "evidencia": indicator.evidence_required,
                "doc": indicator.documentation,
                "etapa": indicator.stage.name,
                "servicio": service.name,
            }
            for indicator in sorted(service.indicators, key=lambda item: item.code)
        ]


def get_latest_stage_weights(end_date: EndDate = None, session: Session | None = None) -> dict[str, float]:
    """Return the latest stage weights as of a date.

    Args:
        end_date: Inclusive cutoff date. Defaults to today.
        session: Optional SQLAlchemy session.

    Returns:
        Stage weights keyed by Spanish stage name.
    """

    cutoff = _parse_end_date(end_date)
    effective_date = cutoff.date() if isinstance(cutoff, datetime) else cutoff
    effective_date = effective_date or date.today()
    with _managed_session(session) as db:
        row = _one_or_none(
            db,
            select(FactStageWeight)
            .where(FactStageWeight.effective_from <= effective_date)
            .order_by(FactStageWeight.effective_from.desc(), FactStageWeight.stage_weight_id.desc()),
        )
        if row is None:
            return dict(DEFAULT_STAGE_WEIGHTS)
        return {
            "Planificación": row.planning_weight,
            "Ejecución": row.execution_weight,
            "Evaluación": row.evaluation_weight,
        }


def get_current_stage_weights(as_of: date | None = None, session: Session | None = None) -> dict[str, float]:
    """Return the effective stage weights.

    Args:
        as_of: Effective date. Defaults to today.
        session: Optional SQLAlchemy session.

    Returns:
        Stage weights keyed by Spanish stage name.
    """

    return get_latest_stage_weights(end_date=as_of, session=session)


def save_stage_weights(
    planning: float,
    execution: float,
    evaluation: float,
    effective_from: date,
    description: str | None = None,
    session: Session | None = None,
) -> dict[str, Any]:
    """Save a new effective-dated stage-weight row.

    Args:
        planning: Planning weight.
        execution: Execution weight.
        evaluation: Evaluation weight.
        effective_from: Effective date.
        description: Ignored compatibility field; no app metadata table exists.
        session: Optional SQLAlchemy session.

    Returns:
        Saved stage-weight fields.

    Raises:
        ValueError: If weights do not sum to 1.0.
    """

    _ = description
    if round(planning + execution + evaluation, 6) != 1.0:
        raise ValueError("Stage weights must sum to 1.0")
    with _managed_session(session) as db:
        row = FactStageWeight(
            planning_weight=planning,
            execution_weight=execution,
            evaluation_weight=evaluation,
            effective_from=effective_from,
        )
        db.add(row)
        db.flush()
        return {
            "stage_weight_id": row.stage_weight_id,
            "Planificación": row.planning_weight,
            "Ejecución": row.execution_weight,
            "Evaluación": row.evaluation_weight,
            "effective_from": row.effective_from,
        }


def get_latest_maturity_thresholds(end_date: EndDate = None, session: Session | None = None) -> dict[str, float]:
    """Return the latest maturity thresholds as of a date.

    Args:
        end_date: Inclusive cutoff date. Defaults to today.
        session: Optional SQLAlchemy session.

    Returns:
        Threshold values keyed by maturity boundary name.
    """

    cutoff = _parse_end_date(end_date)
    effective_date = cutoff.date() if isinstance(cutoff, datetime) else cutoff
    effective_date = effective_date or date.today()
    with _managed_session(session) as db:
        row = _one_or_none(
            db,
            select(FactMaturityThreshold)
            .where(FactMaturityThreshold.effective_from <= effective_date)
            .order_by(FactMaturityThreshold.effective_from.desc(), FactMaturityThreshold.threshold_id.desc()),
        )
        if row is None:
            return {
                "initial_upper": 0.31,
                "basic_upper": 0.56,
                "intermediate_upper": 0.76,
                "advanced_upper": 0.91,
                "optimizing_upper": 1.00,
            }
        return {
            "initial_upper": row.initial_upper,
            "basic_upper": row.basic_upper,
            "intermediate_upper": row.intermediate_upper,
            "advanced_upper": row.advanced_upper,
            "optimizing_upper": row.optimizing_upper,
        }


def get_current_maturity_thresholds(as_of: date | None = None, session: Session | None = None) -> dict[str, float]:
    """Return the effective maturity thresholds.

    Args:
        as_of: Effective date. Defaults to today.
        session: Optional SQLAlchemy session.

    Returns:
        Threshold values keyed by maturity boundary name.
    """

    return get_latest_maturity_thresholds(end_date=as_of, session=session)


def submit_indicator_responses(
    municipality_code: str,
    end_date: EndDate,
    responses: dict[str, Any],
    evidence: dict[str, Any] | None = None,
    actor_subject: str | None = None,
    session: Session | None = None,
) -> dict[str, Any]:
    """Persist numeric indicator responses as fact rows.

    Args:
        municipality_code: Municipal code.
        end_date: Response date assigned to the fact rows.
        responses: Mapping from indicator code to submitted value.
        evidence: Ignored compatibility field; evidence metadata is external.
        actor_subject: Ignored compatibility field; identity is external.
        session: Optional SQLAlchemy session.

    Returns:
        Submission-style summary containing fact ids and row counts.
    """

    _ = (evidence, actor_subject)
    with _managed_session(session) as db:
        municipality = _municipality_or_raise(db, municipality_code)
        indicators = {row.code: row for row in db.execute(select(DMIndicator)).scalars()}
        now = _timestamp_for_end_date(end_date)

        numeric_responses: dict[str, float] = {}
        for code, value in responses.items():
            if code not in indicators:
                continue
            try:
                numeric_responses[code] = float(value)
            except (TypeError, ValueError):
                numeric_responses[code] = 0.0

        fact_ids: list[int] = []
        for code, value in numeric_responses.items():
            indicator = indicators[code]
            existing = _one_or_none(
                db,
                select(FactIndicatorResponse).where(
                    FactIndicatorResponse.municipality_id == municipality.municipality_id,
                    FactIndicatorResponse.indicator_id == indicator.indicator_id,
                    FactIndicatorResponse.value == value,
                ),
            )
            if existing is None:
                existing = FactIndicatorResponse(
                    date_time=now,
                    municipality_id=municipality.municipality_id,
                    indicator_id=indicator.indicator_id,
                    value=value,
                )
                db.add(existing)
            else:
                existing.date_time = now
            db.flush()
            fact_ids.append(existing.response_id)

        return {
            "municipality_code": municipality.code,
            "end_date": _date_label(end_date),
            "fact_response_ids": fact_ids,
            "responses_count": len(numeric_responses),
        }


def get_latest_responses_for_municipality(
    municipality_code: str,
    end_date: EndDate = None,
    session: Session | None = None,
) -> dict[str, Any]:
    """Return latest fact responses for a municipality.

    Args:
        municipality_code: Municipal code.
        end_date: Optional inclusive cutoff date.
        session: Optional SQLAlchemy session.

    Returns:
        Mapping from indicator code to value.
    """

    with _managed_session(session) as db:
        municipality = _municipality_or_raise(db, municipality_code)
        return _latest_response_values(db, municipality.municipality_id, end_date)


def get_latest_indicator_responses(end_date: EndDate = None, session: Session | None = None) -> list[dict[str, Any]]:
    """Return latest fact responses for all municipalities.

    Args:
        end_date: Optional inclusive cutoff date.
        session: Optional SQLAlchemy session.

    Returns:
        Latest response rows by municipality and indicator.
    """

    with _managed_session(session) as db:
        statement = (
            select(FactIndicatorResponse)
            .options(
                joinedload(FactIndicatorResponse.municipality),
                joinedload(FactIndicatorResponse.indicator),
            )
            .order_by(FactIndicatorResponse.date_time.desc(), FactIndicatorResponse.response_id.desc())
        )
        statement = _end_date_filter(statement, end_date)
        seen_pairs: set[tuple[int, int]] = set()
        rows: list[dict[str, Any]] = []

        for response in db.execute(statement).unique().scalars():
            pair = (response.municipality_id, response.indicator_id)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            rows.append(
                {
                    "response_id": response.response_id,
                    "fecha_respuesta": response.date_time,
                    "codigo_municipalidad": response.municipality.code,
                    "municipalidad": response.municipality.name,
                    "codigo_indicador": response.indicator.code,
                    "indicador": response.indicator.name,
                    "valor": float(response.value),
                }
            )

        rows.sort(key=lambda item: (item["codigo_municipalidad"], item["codigo_indicador"]))
        return rows


def get_national_statistics(end_date: EndDate = None, session: Session | None = None) -> dict[str, Any]:
    """Return national data-completion statistics.

    Args:
        end_date: Optional inclusive cutoff date.
        session: Optional SQLAlchemy session.

    Returns:
        National completion statistics dictionary.
    """

    with _managed_session(session) as db:
        total_municipalities = _count_municipalities(db)
        total_indicators = _count_indicators(db)
        expected_responses = total_municipalities * total_indicators
        received_responses = _count_distinct_response_pairs(db, end_date)
        return {
            "end_date": _date_label(end_date),
            "total_municipalidades": total_municipalities,
            "total_indicadores": total_indicators,
            "respuestas_esperadas": expected_responses,
            "respuestas_recibidas": received_responses,
            "pct_completitud": _completion_percentage(received_responses, expected_responses),
        }


def get_municipality_completion_statistics(
    municipality_code: str,
    end_date: EndDate = None,
    session: Session | None = None,
) -> dict[str, Any]:
    """Return data-completion statistics for one municipality.

    Args:
        municipality_code: Municipal code.
        end_date: Optional inclusive cutoff date.
        session: Optional SQLAlchemy session.

    Returns:
        Municipality completion statistics dictionary.
    """

    with _managed_session(session) as db:
        municipality = _municipality_or_raise(db, municipality_code)
        expected_responses = _count_indicators(db)
        received_responses = _count_distinct_response_pairs(
            db,
            end_date,
            municipality_id=municipality.municipality_id,
        )
        return {
            "end_date": _date_label(end_date),
            "codigo": municipality.code,
            "municipalidad": municipality.name,
            "total_indicadores": expected_responses,
            "respuestas_esperadas": expected_responses,
            "respuestas_recibidas": received_responses,
            "pct_completitud": _completion_percentage(received_responses, expected_responses),
        }
