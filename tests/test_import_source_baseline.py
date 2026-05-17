from __future__ import annotations

import csv
import shutil
import unittest
from datetime import date
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select

from database.import_source_baseline import load_source_baseline
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
from database.repositories import (
    get_latest_indicator_responses,
    get_latest_maturity_thresholds,
    get_latest_stage_weights,
    get_municipality_completion_statistics,
    get_national_statistics,
    submit_indicator_responses,
)
from database.seed import seed_all
from database.session import get_engine, get_session_factory, session_scope


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "database" / "source"
TEMP_PARENT = ROOT / ".test_tmp"
BASELINE_END_DATE = date(2025, 12, 31)


class SourceBaselineImportTests(unittest.TestCase):
    """Tests for loading the source baseline into the simplified ORM."""

    def _database_url(self, case_dir: Path) -> str:
        """Build a temporary SQLite URL.

        Args:
            case_dir: Temporary case directory.

        Returns:
            SQLite database URL.
        """

        db_path = (case_dir / "baseline.sqlite3").resolve()
        return f"sqlite:///{db_path.as_posix()}"

    def _make_case_dir(self, prefix: str) -> Path:
        """Create a unique case directory inside the workspace.

        Args:
            prefix: Directory name prefix.

        Returns:
            Created directory path.
        """

        TEMP_PARENT.mkdir(exist_ok=True)
        case_dir = TEMP_PARENT / f"{prefix}_{uuid4().hex}"
        case_dir.mkdir(exist_ok=True)
        return case_dir

    def _count(self, session, model) -> int:
        """Count rows for an ORM model.

        Args:
            session: Active SQLAlchemy session.
            model: ORM model class.

        Returns:
            Row count.
        """

        return session.scalar(select(func.count()).select_from(model))

    def _dispose(self, database_url: str, case_dir: Path) -> None:
        """Dispose test engines and clean temporary files.

        Args:
            database_url: Database URL used by the test.
            case_dir: Case directory to remove.
        """

        get_engine(database_url).dispose()
        try:
            get_engine().dispose()
        except Exception:
            pass
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        shutil.rmtree(case_dir, ignore_errors=True)

    def test_fresh_import_loads_baseline_counts_and_completion(self) -> None:
        """Validate source counts and completion after a fresh import."""

        case_dir = self._make_case_dir("baseline_fresh")
        database_url = self._database_url(case_dir)
        try:
            summary = load_source_baseline(database_url=database_url)

            self.assertFalse(summary["skipped"])
            self.assertEqual(summary["municipalities"], 84)
            self.assertEqual(summary["source_indicators"], 159)
            self.assertEqual(summary["facts_inserted"], 8840)

            with session_scope(database_url) as session:
                self.assertEqual(self._count(session, DMMunicipality), 84)
                self.assertEqual(self._count(session, DMAxis), 3)
                self.assertEqual(self._count(session, DMService), 10)
                self.assertEqual(self._count(session, DMStage), 3)
                self.assertEqual(self._count(session, DMIndicator), 159)
                self.assertEqual(self._count(session, FactIndicatorResponse), 8840)
                self.assertGreater(self._count(session, DMMunicipalityDiversifiedService), 0)

                stats = get_national_statistics(end_date=BASELINE_END_DATE, session=session)
                self.assertEqual(stats["end_date"], "2025-12-31")
                self.assertEqual(stats["total_municipalidades"], 84)
                self.assertEqual(stats["total_indicadores"], 159)
                self.assertEqual(stats["respuestas_esperadas"], 84 * 159)
                self.assertEqual(stats["respuestas_recibidas"], 8840)
                self.assertAlmostEqual(stats["pct_completitud"], round(8840 / (84 * 159) * 100, 2))
                self.assertEqual(len(get_latest_indicator_responses(end_date=BASELINE_END_DATE, session=session)), 8840)

                municipality = session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars().first()
                municipality_stats = get_municipality_completion_statistics(
                    municipality.code,
                    end_date=BASELINE_END_DATE,
                    session=session,
                )
                municipality_responses = int(
                    session.scalar(
                        select(func.count(FactIndicatorResponse.indicator_id.distinct())).where(
                            FactIndicatorResponse.municipality_id == municipality.municipality_id
                        )
                    )
                    or 0
                )
                self.assertEqual(municipality_stats["codigo"], municipality.code)
                self.assertEqual(municipality_stats["total_indicadores"], 159)
                self.assertEqual(municipality_stats["respuestas_esperadas"], 159)
                self.assertEqual(municipality_stats["respuestas_recibidas"], municipality_responses)

                weights = get_latest_stage_weights(end_date=BASELINE_END_DATE, session=session)
                thresholds = get_latest_maturity_thresholds(end_date=BASELINE_END_DATE, session=session)
                self.assertEqual(set(weights), {"Planificación", "Ejecución", "Evaluación"})
                self.assertAlmostEqual(sum(weights.values()), 1.0)
                self.assertEqual(
                    set(thresholds),
                    {
                        "initial_upper",
                        "basic_upper",
                        "intermediate_upper",
                        "advanced_upper",
                        "optimizing_upper",
                    },
                )
        finally:
            self._dispose(database_url, case_dir)

    def test_replacement_import_is_idempotent(self) -> None:
        """Validate replacement imports do not duplicate facts."""

        case_dir = self._make_case_dir("baseline_replace")
        database_url = self._database_url(case_dir)
        try:
            first = load_source_baseline(database_url=database_url)
            second = load_source_baseline(database_url=database_url)

            self.assertEqual(first["facts_inserted"], 8840)
            self.assertEqual(second["facts_inserted"], 8840)
            self.assertEqual(second["facts_deleted"], 8840)

            with session_scope(database_url) as session:
                self.assertEqual(self._count(session, FactIndicatorResponse), 8840)
                self.assertEqual(self._count(session, DMService), 10)
                self.assertEqual(self._count(session, DMStage), 3)
        finally:
            self._dispose(database_url, case_dir)

    def test_init_then_import_keeps_single_business_structure(self) -> None:
        """Validate init seeding and baseline import share one structure."""

        case_dir = self._make_case_dir("baseline_init_import")
        database_url = self._database_url(case_dir)
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            with session_scope(database_url) as session:
                seed_all(session=session)

            load_source_baseline(database_url=database_url)

            with session_scope(database_url) as session:
                self.assertEqual(self._count(session, DMAxis), 3)
                self.assertEqual(self._count(session, DMService), 10)
                self.assertEqual(self._count(session, DMStage), 3)
                self.assertEqual(self._count(session, DMIndicator), 159)
                self.assertEqual(self._count(session, FactIndicatorResponse), 8840)
        finally:
            self._dispose(database_url, case_dir)

    def test_skip_existing_leaves_existing_baseline(self) -> None:
        """Validate skip mode leaves existing baseline facts untouched."""

        case_dir = self._make_case_dir("baseline_skip")
        database_url = self._database_url(case_dir)
        try:
            load_source_baseline(database_url=database_url)
            summary = load_source_baseline(database_url=database_url, replace=False)

            self.assertTrue(summary["skipped"])
            self.assertEqual(summary["existing_baseline_facts"], 8840)
            with session_scope(database_url) as session:
                self.assertEqual(self._count(session, FactIndicatorResponse), 8840)
        finally:
            self._dispose(database_url, case_dir)

    def test_submit_indicator_responses_writes_fact_rows_only(self) -> None:
        """Validate repository submissions persist directly to facts."""

        case_dir = self._make_case_dir("baseline_submit")
        database_url = self._database_url(case_dir)
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            with session_scope(database_url) as session:
                seed_all(session=session)
                municipality = session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars().first()
                indicators = list(session.execute(select(DMIndicator).order_by(DMIndicator.code)).scalars())[:3]
                responses = {indicator.code: 1 for indicator in indicators}
                result = submit_indicator_responses(
                    municipality.code,
                    date(2025, 1, 1),
                    responses,
                    session=session,
                )

                self.assertEqual(len(result["fact_response_ids"]), 3)
                self.assertEqual(result["end_date"], "2025-01-01")
                self.assertEqual(result["responses_count"], 3)
                self.assertNotIn("score_total", result)
                self.assertNotIn("nivel", result)
                self.assertNotIn("calculation", result)
                self.assertEqual(self._count(session, FactIndicatorResponse), 3)

                stats = get_national_statistics(end_date=date(2025, 1, 31), session=session)
                municipality_stats = get_municipality_completion_statistics(
                    municipality.code,
                    end_date=date(2025, 1, 31),
                    session=session,
                )
                total_municipalities = self._count(session, DMMunicipality)
                total_indicators = self._count(session, DMIndicator)
                self.assertEqual(stats["respuestas_esperadas"], total_municipalities * total_indicators)
                self.assertEqual(stats["respuestas_recibidas"], 3)
                self.assertAlmostEqual(
                    stats["pct_completitud"],
                    round(3 / (total_municipalities * total_indicators) * 100, 2),
                )
                self.assertEqual(municipality_stats["respuestas_esperadas"], total_indicators)
                self.assertEqual(municipality_stats["respuestas_recibidas"], 3)
                self.assertAlmostEqual(
                    municipality_stats["pct_completitud"],
                    round(3 / total_indicators * 100, 2),
                )

                duplicate_pair_result = submit_indicator_responses(
                    municipality.code,
                    date(2025, 2, 1),
                    {indicators[0].code: 0},
                    session=session,
                )
                self.assertEqual(duplicate_pair_result["responses_count"], 1)
                self.assertEqual(self._count(session, FactIndicatorResponse), 4)

                january_stats = get_national_statistics(end_date=date(2025, 1, 31), session=session)
                january_latest = get_latest_indicator_responses(end_date=date(2025, 1, 31), session=session)
                year_end_latest = get_latest_indicator_responses(end_date=BASELINE_END_DATE, session=session)

                stats = get_national_statistics(end_date=BASELINE_END_DATE, session=session)
                municipality_stats = get_municipality_completion_statistics(
                    municipality.code,
                    end_date=BASELINE_END_DATE,
                    session=session,
                )
                self.assertEqual(january_stats["respuestas_recibidas"], 3)
                self.assertEqual(stats["respuestas_recibidas"], 3)
                self.assertEqual(municipality_stats["respuestas_recibidas"], 3)
                self.assertEqual(len(january_latest), 3)
                self.assertEqual(len(year_end_latest), 3)
                self.assertEqual(
                    next(row for row in january_latest if row["codigo_indicador"] == indicators[0].code)["valor"],
                    1.0,
                )
                self.assertEqual(
                    next(row for row in year_end_latest if row["codigo_indicador"] == indicators[0].code)["valor"],
                    0.0,
                )
        finally:
            self._dispose(database_url, case_dir)

    def test_invalid_source_rows_fail_loudly(self) -> None:
        """Validate source data errors raise clear exceptions."""

        cases = [
            ("Código", "9.9.9.9", "Unknown indicator code"),
            ("Valor", "not-a-number", "Nonnumeric Valor"),
            ("Cantón", "Cantón Fantasma", "Unknown municipality"),
        ]

        for column, value, message in cases:
            with self.subTest(column=column):
                case_dir = self._make_case_dir(f"baseline_invalid_{column}")
                source_dir = case_dir / "source"
                shutil.copytree(SOURCE_DIR, source_dir)
                results_path = source_dir / "igsm_2025_results_long.csv"
                self._rewrite_first_data_row(results_path, column, value)

                try:
                    with self.assertRaisesRegex(ValueError, message):
                        load_source_baseline(
                            source_dir=source_dir,
                            database_url=self._database_url(case_dir),
                        )
                finally:
                    shutil.rmtree(case_dir, ignore_errors=True)

    def _rewrite_first_data_row(self, path: Path, column: str, value: str) -> None:
        """Rewrite one source CSV row for negative tests.

        Args:
            path: CSV path to rewrite.
            column: Column name to alter.
            value: Replacement value.
        """

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
            fieldnames = list(rows[0].keys())

        row_index = 0
        if column == "Valor":
            row_index = next(index for index, row in enumerate(rows) if row["Valor"].strip())
        rows[row_index][column] = value

        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
