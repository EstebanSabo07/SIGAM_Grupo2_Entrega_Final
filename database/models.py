"""SQLAlchemy models for the IGSM dimensional and fact data model."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Return the current timezone-aware UTC timestamp.

    Returns:
        Current UTC datetime with timezone information.
    """

    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all IGSM ORM models."""


class DMMunicipality(Base):
    """Municipality dimension row.

    Attributes:
        municipality_id: Primary key.
        code: Official municipality code.
        name: Municipality display name.
        province: Province name.
        region: Planning region name.
        latitude: Latitude used for map visualizations.
        longitude: Longitude used for map visualizations.
        diversified_services: Diversified-service links for the municipality.
        responses: Indicator response fact rows submitted by the municipality.
    """

    __tablename__ = "dm_municipality"

    municipality_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    province: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    diversified_services: Mapped[list["DMMunicipalityDiversifiedService"]] = relationship(
        back_populates="municipality", cascade="all, delete-orphan"
    )
    responses: Mapped[list["FactIndicatorResponse"]] = relationship(back_populates="municipality")


class DMMunicipalityDiversifiedService(Base):
    """Diversified-service link for a municipality.

    Attributes:
        municipality_id: Municipality primary key.
        service_id: Service primary key.
        municipality: Linked municipality row.
        service: Linked service row.
    """

    __tablename__ = "dm_municipality_diversified_service"

    municipality_id: Mapped[int] = mapped_column(
        ForeignKey("dm_municipality.municipality_id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("dm_service.service_id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    municipality: Mapped[DMMunicipality] = relationship(back_populates="diversified_services")
    service: Mapped["DMService"] = relationship(back_populates="municipality_links")


class DMAxis(Base):
    """IGSM management axis dimension row.

    Attributes:
        axis_id: Primary key.
        name: Axis display name.
        services: Services assigned to the axis.
    """

    __tablename__ = "dm_axis"

    axis_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    services: Mapped[list["DMService"]] = relationship(back_populates="axis", cascade="all, delete-orphan")


class DMService(Base):
    """IGSM service dimension row.

    Attributes:
        service_id: Primary key.
        axis_id: Parent axis primary key.
        name: Service display name.
        service_code: Official service code.
        grouping: Service grouping, such as basic or diversified.
        diversified_key: Optional diversified-service key used by municipalities.
        axis: Parent axis row.
        indicators: Indicators assigned to the service.
        municipality_links: Municipality links for diversified services.
    """

    __tablename__ = "dm_service"
    __table_args__ = (UniqueConstraint("axis_id", "name", name="uq_dm_service_axis_name"),)

    service_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    axis_id: Mapped[int] = mapped_column(
        ForeignKey("dm_axis.axis_id", deferrable=True, initially="IMMEDIATE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    service_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    grouping: Mapped[str | None] = mapped_column(String(50))
    diversified_key: Mapped[str | None] = mapped_column(String(50))

    axis: Mapped[DMAxis] = relationship(back_populates="services")
    indicators: Mapped[list["DMIndicator"]] = relationship(back_populates="service", cascade="all, delete-orphan")
    municipality_links: Mapped[list[DMMunicipalityDiversifiedService]] = relationship(back_populates="service")


class DMStage(Base):
    """Global IGSM stage dimension row.

    Attributes:
        stage_id: Primary key.
        name: Stage display name.
        indicators: Indicators assigned to the stage.
    """

    __tablename__ = "dm_stage"

    stage_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    indicators: Mapped[list["DMIndicator"]] = relationship(back_populates="stage", cascade="all, delete-orphan")


class DMIndicator(Base):
    """IGSM indicator dimension row.

    Attributes:
        indicator_id: Primary key.
        service_id: Parent service primary key.
        stage_id: Parent stage primary key.
        code: Official indicator code.
        name: Indicator display name.
        type: Indicator response type.
        evidence_required: Whether the indicator requires supporting evidence.
        documentation: Evidence or documentation guidance.
        service: Parent service row.
        stage: Parent stage row.
        responses: Response fact rows for the indicator.
    """

    __tablename__ = "dm_indicator"

    indicator_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(
        ForeignKey("dm_service.service_id", deferrable=True, initially="IMMEDIATE"), nullable=False
    )
    stage_id: Mapped[int] = mapped_column(
        ForeignKey("dm_stage.stage_id", deferrable=True, initially="IMMEDIATE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    type: Mapped[str | None] = mapped_column(String(50))
    evidence_required: Mapped[bool | None] = mapped_column(Boolean)
    documentation: Mapped[str | None] = mapped_column(String(300))

    service: Mapped[DMService] = relationship(back_populates="indicators")
    stage: Mapped[DMStage] = relationship(back_populates="indicators")
    responses: Mapped[list["FactIndicatorResponse"]] = relationship(back_populates="indicator")


class FactIndicatorResponse(Base):
    """Numeric indicator answer submitted by a municipality.

    Attributes:
        response_id: Primary key.
        date_time: Submission timestamp.
        municipality_id: Municipality primary key.
        indicator_id: Indicator primary key.
        value: Numeric answer value.
        municipality: Linked municipality row.
        indicator: Linked indicator row.
    """

    __tablename__ = "fact_indicator_response"
    __table_args__ = (
        UniqueConstraint(
            "municipality_id",
            "indicator_id",
            "value",
            name="uq_fact_indicator_response_municipality_indicator_value",
        ),
        Index(
            "ix_fact_indicator_response_municipality_indicator_date_time",
            "municipality_id",
            "indicator_id",
            "date_time",
        ),
        Index("ix_fact_indicator_response_date_time", "date_time"),
    )

    response_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    municipality_id: Mapped[int] = mapped_column(
        ForeignKey("dm_municipality.municipality_id", deferrable=True, initially="IMMEDIATE"), nullable=False
    )
    indicator_id: Mapped[int] = mapped_column(
        ForeignKey("dm_indicator.indicator_id", deferrable=True, initially="IMMEDIATE"), nullable=False
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)

    municipality: Mapped[DMMunicipality] = relationship(back_populates="responses")
    indicator: Mapped[DMIndicator] = relationship(back_populates="responses")


class FactStageWeight(Base):
    """Effective-dated global stage weights.

    Attributes:
        stage_weight_id: Primary key.
        planning_weight: Weight for the planning stage.
        execution_weight: Weight for the execution stage.
        evaluation_weight: Weight for the evaluation stage.
        effective_from: First date when the weights apply.
    """

    __tablename__ = "fact_stage_weight"

    stage_weight_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    planning_weight: Mapped[float] = mapped_column(Float, nullable=False)
    execution_weight: Mapped[float] = mapped_column(Float, nullable=False)
    evaluation_weight: Mapped[float] = mapped_column(Float, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)


class FactMaturityThreshold(Base):
    """Effective-dated maturity-level thresholds.

    Attributes:
        threshold_id: Primary key.
        initial_upper: Upper bound for the initial level.
        basic_upper: Upper bound for the basic level.
        intermediate_upper: Upper bound for the intermediate level.
        advanced_upper: Upper bound for the advanced level.
        optimizing_upper: Upper bound for the optimizing level.
        effective_from: First date when the thresholds apply.
    """

    __tablename__ = "fact_maturity_threshold"

    threshold_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    initial_upper: Mapped[float] = mapped_column(Float, nullable=False)
    basic_upper: Mapped[float] = mapped_column(Float, nullable=False)
    intermediate_upper: Mapped[float] = mapped_column(Float, nullable=False)
    advanced_upper: Mapped[float] = mapped_column(Float, nullable=False)
    optimizing_upper: Mapped[float] = mapped_column(Float, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
