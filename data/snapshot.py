"""Snapshot-context helpers for month-based SIGAM queries."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime


AUDIENCE_PUBLIC = "public"
AUDIENCE_MUNICIPAL = "municipal"
AUDIENCE_ADMIN = "admin"
AUDIENCE_OPTIONS = {AUDIENCE_PUBLIC, AUDIENCE_MUNICIPAL, AUDIENCE_ADMIN}


@dataclass(frozen=True)
class SnapshotContext:
    """Represent a month-based reporting snapshot.

    Attributes:
        year: Snapshot year.
        month: Snapshot month in the 1-12 range.
        audience: Consumer audience, such as public, municipal, or admin.
        municipality_code: Optional municipal scope.
    """

    year: int
    month: int
    audience: str
    municipality_code: str | None = None

    def __post_init__(self) -> None:
        """Validate the snapshot fields after dataclass initialization."""

        if self.month < 1 or self.month > 12:
            raise ValueError(f"month must be between 1 and 12: {self.month!r}")
        if self.audience not in AUDIENCE_OPTIONS:
            raise ValueError(f"Unsupported audience: {self.audience!r}")

    @property
    def start_date(self) -> date:
        """Return the first date covered by the snapshot month."""

        return date(self.year, self.month, 1)

    @property
    def end_date(self) -> date:
        """Return the inclusive last date covered by the snapshot month."""

        return date(self.year, self.month, monthrange(self.year, self.month)[1])

    @property
    def label(self) -> str:
        """Return the stable ``YYYY-MM`` label for the snapshot."""

        return f"{self.year:04d}-{self.month:02d}"


def current_snapshot(
    audience: str,
    municipality_code: str | None = None,
    today: date | datetime | None = None,
) -> SnapshotContext:
    """Build the default month snapshot using the current date.

    Args:
        audience: Consumer audience.
        municipality_code: Optional municipal scope.
        today: Optional date override for testing.

    Returns:
        Snapshot context for the current month.
    """

    reference = today.date() if isinstance(today, datetime) else (today or date.today())
    return SnapshotContext(
        year=reference.year,
        month=reference.month,
        audience=audience,
        municipality_code=municipality_code,
    )
