"""Seed helpers for the IGSM ORM package."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    DMMunicipality,
    DMMunicipalityDiversifiedService,
    DMService,
    FactMaturityThreshold,
    FactStageWeight,
)
from database.session import session_scope


def seed_all(include_demo_results: bool = False, session: Session | None = None) -> None:
    """Seed all reference data into the configured database.

    Args:
        include_demo_results: Deprecated compatibility flag.
        session: Optional caller-managed SQLAlchemy session.
    """

    if session is not None:
        seed_reference_data(session)
        if include_demo_results:
            seed_demo_results(session)
        return

    with session_scope() as db:
        seed_reference_data(db)
        if include_demo_results:
            seed_demo_results(db)


def seed_reference_data(session: Session) -> None:
    """Seed the complete IGSM reference dataset.

    Args:
        session: Active SQLAlchemy session.
    """

    seed_igsm_structure(session)
    seed_municipalities(session)
    seed_stage_weights(session)
    seed_maturity_thresholds(session)
    session.flush()


def seed_municipalities(session: Session) -> None:
    """Seed municipality rows and diversified-service links.

    Args:
        session: Active SQLAlchemy session.
    """

    from data.municipalities import MUNICIPALIDADES

    for item in MUNICIPALIDADES:
        municipality = session.execute(
            select(DMMunicipality).where(DMMunicipality.code == item["codigo"])
        ).scalar_one_or_none()
        if municipality is None:
            municipality = DMMunicipality(code=item["codigo"], name=item["nombre"])
            session.add(municipality)

        municipality.name = item["nombre"]
        municipality.province = item.get("provincia")
        municipality.region = item.get("region")
        municipality.latitude = item.get("lat")
        municipality.longitude = item.get("lon")
        session.flush()

        services_by_key = {
            row.diversified_key: row
            for row in session.execute(select(DMService).where(DMService.diversified_key.is_not(None))).scalars()
            if row.diversified_key
        }
        existing = set(
            session.execute(
                select(DMMunicipalityDiversifiedService.service_id).where(
                    DMMunicipalityDiversifiedService.municipality_id == municipality.municipality_id
                )
            ).scalars()
        )
        for diversified_key in item.get("diversificados", []):
            service = services_by_key.get(diversified_key)
            if service is not None and service.service_id not in existing:
                session.add(
                    DMMunicipalityDiversifiedService(
                        municipality_id=municipality.municipality_id,
                        service_id=service.service_id,
                    )
                )


def seed_igsm_structure(session: Session) -> None:
    """Seed IGSM axes, services, stages, and indicators from source CSV.

    Args:
        session: Active SQLAlchemy session.
    """

    from database.import_source_baseline import DEFAULT_SOURCE_DIR, _read_dictionary, _upsert_igsm_structure

    dictionary = _read_dictionary(DEFAULT_SOURCE_DIR / "dictionary.csv")
    _upsert_igsm_structure(session, dictionary)


def seed_stage_weights(session: Session) -> None:
    """Seed the default stage weights.

    Args:
        session: Active SQLAlchemy session.
    """

    from data.indicators import PESOS_ETAPA

    existing = session.execute(
        select(FactStageWeight).where(FactStageWeight.effective_from == date(2025, 1, 1))
    ).scalar_one_or_none()
    if existing is not None:
        return

    row = FactStageWeight(
        planning_weight=PESOS_ETAPA["Planificación"],
        execution_weight=PESOS_ETAPA["Ejecución"],
        evaluation_weight=PESOS_ETAPA["Evaluación"],
        effective_from=date(2025, 1, 1),
    )
    session.add(row)


def seed_maturity_thresholds(session: Session) -> None:
    """Seed the default maturity thresholds.

    Args:
        session: Active SQLAlchemy session.
    """

    from data.indicators import UMBRALES_NIVEL

    existing = session.execute(
        select(FactMaturityThreshold).where(FactMaturityThreshold.effective_from == date(2025, 1, 1))
    ).scalar_one_or_none()
    if existing is not None:
        return

    upper_by_level = {level: upper for _, upper, level in UMBRALES_NIVEL}
    session.add(
        FactMaturityThreshold(
            initial_upper=upper_by_level["Inicial"],
            basic_upper=upper_by_level["Básico"],
            intermediate_upper=upper_by_level["Intermedio"],
            advanced_upper=upper_by_level["Avanzado"],
            optimizing_upper=upper_by_level["Optimizando"],
            effective_from=date(2025, 1, 1),
        )
    )
    session.flush()


def seed_demo_results(session: Session, period: str = "2025") -> None:
    """Keep the legacy demo hook as a no-op after app tables were removed.

    Args:
        session: Active SQLAlchemy session.
        period: Requested demo period.
    """

    _ = (session, period)
