from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
import os
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select

from data.catalog_service import get_form_tree
from data.presentation_service import (
    get_admin_municipality_comparison_view,
    get_municipality_snapshot_view,
    get_national_snapshot_view,
)
from data.reporting_service import export_csv, export_pdf
from data.response_service import save_section_changes
from data.scoring_service import get_municipality_snapshot
from data.snapshot import AUDIENCE_ADMIN, AUDIENCE_MUNICIPAL, AUDIENCE_PUBLIC, SnapshotContext
from data.snapshot_service import resolve_indicator_values, resolve_snapshot_period
from data.text_utils import normalize_search_text, normalized_contains
from database.models import Base, DMMunicipality, DMService, FactIndicatorResponse, FactServiceReviewStatus
from database.repositories import save_indicator_response_versions
from database.seed import seed_all
from database.session import get_engine, get_session_factory, session_scope
from views.muni_form import _can_navigate_without_prompt
from views.muni_results import _build_service_maturity_frame, _normalize_priority_label


ROOT = Path(__file__).resolve().parents[1]


class SigamV2SnapshotServiceTests(unittest.TestCase):
    """Integration tests for the SIGAM v2 snapshot and presentation services."""

    def _database_url(self, filename: str) -> str:
        """Build a temporary SQLite URL inside the workspace test folder.

        Args:
            filename: SQLite file name.

        Returns:
            SQLite database URL.
        """

        temp_root = ROOT / ".test_tmp"
        temp_root.mkdir(exist_ok=True)
        db_path = (temp_root / filename).resolve()
        return f"sqlite:///{db_path.as_posix()}"

    def _database_path(self, database_url: str) -> Path:
        """Convert a SQLite URL back into a filesystem path.

        Args:
            database_url: SQLite database URL.

        Returns:
            Database path.
        """

        return Path(database_url.removeprefix("sqlite:///"))

    def _dispose(self, database_url: str) -> None:
        """Dispose a cached SQLAlchemy engine.

        Args:
            database_url: Database URL used by the test.
        """

        get_engine(database_url).dispose()
        try:
            get_engine().dispose()
        except Exception:
            pass
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        db_path = self._database_path(database_url)
        if db_path.exists():
            try:
                db_path.unlink()
            except PermissionError:
                pass

    def _activate_database(self, database_url: str) -> None:
        """Activate a temporary database URL for service-layer calls.

        Args:
            database_url: Database URL used by the test.
        """

        os.environ["DATABASE_URL"] = database_url
        get_engine.cache_clear()
        get_session_factory.cache_clear()

    def test_normalized_search_text_handles_accents_and_spacing(self) -> None:
        """Validate tolerant normalization for public text search."""

        self.assertEqual(normalize_search_text("  San  José  "), "sanjose")
        self.assertEqual(normalize_search_text("Pérez-Zeledón"), "perezzeledon")
        self.assertTrue(normalized_contains("Municipalidad de Pérez Zeledón", "perez zeledon"))
        self.assertTrue(normalized_contains("San José", "SANJOSE"))

    def test_resolve_snapshot_period_uses_available_periods(self) -> None:
        """Validate snapshot period resolution uses only loaded periods."""

        periods = [
            {"year": 2025, "month": 1, "label": "2025-01"},
            {"year": 2026, "month": 3, "label": "2026-03"},
            {"year": 2026, "month": 4, "label": "2026-04"},
        ]
        resolved = resolve_snapshot_period(2023, 8, periods=periods, today=date(2026, 4, 26))
        self.assertTrue(resolved["has_data"])
        self.assertEqual(resolved["selected_period"]["label"], "2026-04")
        self.assertEqual(resolved["first_real_period"]["label"], "2025-01")
        self.assertEqual(resolved["latest_real_period"]["label"], "2026-04")
        self.assertEqual(resolved["available_years"], [2025, 2026])
        self.assertEqual(
            [item["month"] for item in resolved["months_for_year"]],
            [1, 2, 3, 4],
        )

        empty_resolved = resolve_snapshot_period(None, None, periods=[], today=date(2026, 4, 26))
        self.assertFalse(empty_resolved["has_data"])
        self.assertEqual(empty_resolved["selected_period"]["label"], "2026-04")

    def test_snapshot_uses_latest_response_before_cutoff(self) -> None:
        """Validate cutoff resolution keeps the latest value before month end."""

        database_url = self._database_url(f"sigam_v2_{uuid4().hex}.sqlite3")
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            self._activate_database(database_url)
            with session_scope(database_url) as session:
                seed_all(session=session)
                municipality = session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars().first()
                indicator_code = "1.1.1.1"
                save_indicator_response_versions(
                    municipality.code,
                    [{"indicator_code": indicator_code, "value": 1.0, "evidence_files": []}],
                    submitted_at=date(2026, 4, 10),
                    session=session,
                )
                save_indicator_response_versions(
                    municipality.code,
                    [{"indicator_code": indicator_code, "value": 0.0, "evidence_files": []}],
                    submitted_at=date(2026, 5, 1),
                    session=session,
                )

            april_snapshot = SnapshotContext(2026, 4, AUDIENCE_ADMIN, municipality.code)
            may_snapshot = SnapshotContext(2026, 5, AUDIENCE_ADMIN, municipality.code)
            april_values = resolve_indicator_values(municipality.code, april_snapshot)
            may_values = resolve_indicator_values(municipality.code, may_snapshot)

            self.assertEqual(april_values[indicator_code]["value"], 1.0)
            self.assertEqual(may_values[indicator_code]["value"], 0.0)
        finally:
            self._dispose(database_url)

    def test_public_and_municipal_views_hide_numeric_scores(self) -> None:
        """Validate masked audiences do not receive sensitive numeric fields."""

        database_url = self._database_url(f"sigam_v2_{uuid4().hex}.sqlite3")
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            self._activate_database(database_url)
            with session_scope(database_url) as session:
                seed_all(session=session)
                municipality = session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars().first()
                save_indicator_response_versions(
                    municipality.code,
                    [{"indicator_code": "1.1.1.1", "value": 1.0, "evidence_files": []}],
                    submitted_at=date(2026, 4, 10),
                    session=session,
                )

            snapshot = SnapshotContext(2026, 4, AUDIENCE_PUBLIC, municipality.code)
            municipal_view = get_municipality_snapshot_view(municipality.code, snapshot, AUDIENCE_MUNICIPAL)
            public_view = get_national_snapshot_view(SnapshotContext(2026, 4, AUDIENCE_PUBLIC), AUDIENCE_PUBLIC)
            admin_view = get_national_snapshot_view(SnapshotContext(2026, 4, AUDIENCE_ADMIN), AUDIENCE_ADMIN)

            self.assertNotIn("score_total", municipal_view)
            self.assertNotIn("puntaje_pct", municipal_view)
            self.assertNotIn("average_score", public_view)
            self.assertIn("average_score", admin_view)
            self.assertNotIn("update_date", public_view["municipalities"][0])
            self.assertNotIn("data_age_months", public_view["municipalities"][0])
            self.assertNotIn("operational_status", public_view["comparison_candidates"][0])

            csv_output = export_csv(SnapshotContext(2026, 4, AUDIENCE_PUBLIC), AUDIENCE_PUBLIC).decode("utf-8")
            self.assertNotIn("fecha_actualizacion", csv_output)
            self.assertNotIn("antiguedad_meses", csv_output)
            self.assertNotIn("servicios_observados", csv_output)
        finally:
            self._dispose(database_url)

    def test_service_statuses_include_ready_and_observed(self) -> None:
        """Validate operational status, update date, and aging metadata."""

        database_url = self._database_url(f"sigam_v2_{uuid4().hex}.sqlite3")
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            self._activate_database(database_url)
            with session_scope(database_url) as session:
                seed_all(session=session)
                municipality = session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars().first()
            tree = get_form_tree(municipality.code, SnapshotContext(2026, 4, AUDIENCE_ADMIN, municipality.code))
            first_service = tree["axes"][0]["services"][0]
            second_service = tree["axes"][0]["services"][1]

            with session_scope(database_url) as session:
                municipality = session.execute(
                    select(DMMunicipality).where(DMMunicipality.code == municipality.code)
                ).scalar_one()
                complete_rows = []
                for stage in first_service["stages"]:
                    for indicator in stage["indicators"]:
                        evidence_files = []
                        if indicator["evidence_required"]:
                            evidence_files = [{"file_name": f"{indicator['indicator_code']}.pdf", "file_type": "application/pdf"}]
                        complete_rows.append(
                            {
                                "indicator_code": indicator["indicator_code"],
                                "value": 1.0,
                                "evidence_files": evidence_files,
                            }
                        )
                save_indicator_response_versions(
                    municipality.code,
                    complete_rows,
                    submitted_at=date(2026, 2, 15),
                    session=session,
                )
                partial_indicator = second_service["stages"][0]["indicators"][0]
                save_indicator_response_versions(
                    municipality.code,
                    [{"indicator_code": partial_indicator["indicator_code"], "value": 1.0, "evidence_files": []}],
                    submitted_at=date(2026, 4, 3),
                    session=session,
                )

                observed_service = session.execute(
                    select(DMService).where(DMService.service_code == second_service["service_code"])
                ).scalar_one()
                session.add(
                    FactServiceReviewStatus(
                        municipality_id=municipality.municipality_id,
                        service_id=observed_service.service_id,
                        status="Observado",
                        note="Observación activa de prueba",
                        created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
                    )
                )

            snapshot = SnapshotContext(2026, 4, AUDIENCE_ADMIN, municipality.code)
            municipality_snapshot = get_municipality_snapshot(municipality.code, snapshot, AUDIENCE_ADMIN)
            services_by_code = {service["service_code"]: service for service in municipality_snapshot["services"]}
            ready_service = services_by_code[first_service["service_code"]]
            observed_service = services_by_code[second_service["service_code"]]

            self.assertEqual(ready_service["operational_status"], "Listo para revisión")
            self.assertEqual(ready_service["update_date"], date(2026, 2, 15))
            self.assertEqual(ready_service["data_age_months"], 2)
            self.assertEqual(observed_service["operational_status"], "Observado")
        finally:
            self._dispose(database_url)

    def test_municipal_view_includes_progress_and_benchmark_metadata(self) -> None:
        """Validate municipal presentation metrics and benchmark fields."""

        database_url = self._database_url(f"sigam_v2_{uuid4().hex}.sqlite3")
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            self._activate_database(database_url)
            with session_scope(database_url) as session:
                seed_all(session=session)
                municipality = session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars().first()
                save_indicator_response_versions(
                    municipality.code,
                    [{"indicator_code": "1.1.1.1", "value": 1.0, "evidence_files": []}],
                    submitted_at=date(2026, 4, 10),
                    session=session,
                )

            snapshot = SnapshotContext(2026, 4, AUDIENCE_MUNICIPAL, municipality.code)
            municipal_view = get_municipality_snapshot_view(municipality.code, snapshot, AUDIENCE_MUNICIPAL)

            self.assertGreater(municipal_view["completion_pct"], 0.0)
            self.assertIn("benchmark_summary", municipal_view)
            self.assertIn("benchmark_by_service", municipal_view)
            self.assertIn("available_periods", municipal_view)
            self.assertIn("service_progress_pct", municipal_view["services"][0])
            self.assertIn("position_province", municipal_view["benchmark_summary"])
            self.assertIn("freshness_status", municipal_view["services"][0])
            self.assertIn("national_ranking", municipal_view["benchmark_summary"])
            self.assertIn("province_ranking", municipal_view["benchmark_summary"])
            self.assertIn("regional_ranking", municipal_view["benchmark_summary"])
        finally:
            self._dispose(database_url)

    def test_admin_views_include_regional_history_and_comparison_counts(self) -> None:
        """Validate admin regional history and multi-municipality comparison data."""

        database_url = self._database_url(f"sigam_v2_{uuid4().hex}.sqlite3")
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            self._activate_database(database_url)
            with session_scope(database_url) as session:
                seed_all(session=session)
                municipalities = list(session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars())[:2]
                save_indicator_response_versions(
                    municipalities[0].code,
                    [{"indicator_code": "1.1.1.1", "value": 1.0, "evidence_files": []}],
                    submitted_at=date(2026, 3, 15),
                    session=session,
                )
                save_indicator_response_versions(
                    municipalities[0].code,
                    [{"indicator_code": "1.1.1.2", "value": 1.0, "evidence_files": []}],
                    submitted_at=date(2026, 4, 15),
                    session=session,
                )
                save_indicator_response_versions(
                    municipalities[1].code,
                    [{"indicator_code": "1.1.1.1", "value": 0.0, "evidence_files": []}],
                    submitted_at=date(2026, 4, 15),
                    session=session,
                )

            snapshot = SnapshotContext(2026, 4, AUDIENCE_ADMIN)
            national_view = get_national_snapshot_view(snapshot, AUDIENCE_ADMIN)
            comparison_view = get_admin_municipality_comparison_view(
                snapshot,
                [municipalities[0].code, municipalities[1].code],
            )

            self.assertGreaterEqual(
                national_view["municipalities"][0]["score_total"],
                national_view["municipalities"][1]["score_total"],
            )
            self.assertTrue(national_view["regional_history"])
            self.assertEqual(len(comparison_view["selected_municipalities"]), 2)
            self.assertTrue(comparison_view["service_heatmap_rows"])
            self.assertTrue(comparison_view["service_score_table"])
            self.assertEqual(len(comparison_view["update_status_counts"]), 2)
            self.assertIn("Urgente", comparison_view["update_status_counts"][0])
        finally:
            self._dispose(database_url)

    def test_exports_use_utf8_bom_and_public_pdf_includes_filters(self) -> None:
        """Validate CSV encoding and summarized public PDF content."""

        database_url = self._database_url(f"sigam_v2_{uuid4().hex}.sqlite3")
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            self._activate_database(database_url)
            with session_scope(database_url) as session:
                seed_all(session=session)
                municipality = session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars().first()
                save_indicator_response_versions(
                    municipality.code,
                    [{"indicator_code": "1.1.1.1", "value": 1.0, "evidence_files": []}],
                    submitted_at=date(2026, 4, 10),
                    session=session,
                )

            snapshot = SnapshotContext(2026, 4, AUDIENCE_PUBLIC)
            csv_output = export_csv(snapshot, AUDIENCE_PUBLIC)
            pdf_output = export_pdf(
                snapshot,
                AUDIENCE_PUBLIC,
                filters={
                    "search": "San",
                    "region": "Todas",
                    "province": "Todas",
                    "level": "Todos",
                },
            )
            pdf_text = pdf_output.decode("latin-1", errors="ignore")

            self.assertTrue(csv_output.startswith(b"\xef\xbb\xbf"))
            self.assertTrue(pdf_output.startswith(b"%PDF"))
            self.assertGreater(len(pdf_output), 3000)
            self.assertIn("SIGAM", pdf_text)
            self.assertTrue("Filtros aplicados" in pdf_text or "B\\372squeda" in pdf_text)
            self.assertTrue(
                "Dashboard P\\372blico" in pdf_text
                or "Dashboard Público" in pdf_text
                or "SIGAM Público" in pdf_text
                or "SIGAM P\\372blico" in pdf_text
            )
        finally:
            self._dispose(database_url)

    def test_public_and_municipal_pdf_require_formal_backend(self) -> None:
        """Validate public and municipal PDF exports refuse degraded fallback generation."""

        with patch("data.reporting_service.pdf_export_available", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "backend de PDF formal"):
                export_pdf(SnapshotContext(2026, 4, AUDIENCE_PUBLIC), AUDIENCE_PUBLIC)
            with self.assertRaisesRegex(RuntimeError, "backend de PDF formal"):
                export_pdf(
                    SnapshotContext(2026, 4, AUDIENCE_MUNICIPAL, "MUNI-TEST"),
                    AUDIENCE_MUNICIPAL,
                    {"municipality_code": "MUNI-TEST"},
                )

    def test_municipal_results_helpers_normalize_labels_and_chart_frame(self) -> None:
        """Validate municipal results helpers keep labels and chart rows consistent."""

        urgent_service = {
            "service_name": "Acueducto",
            "level": "Intermedio",
            "needs_update": True,
        }
        current_service = {
            "service_name": "Aseo de vías",
            "level": "Avanzado",
            "needs_update": False,
        }

        self.assertEqual(_normalize_priority_label(urgent_service), "Necesitan actualización")
        self.assertEqual(_normalize_priority_label(current_service), "Avanzado")

        chart_df = _build_service_maturity_frame([urgent_service, current_service])
        self.assertEqual(chart_df.iloc[0]["service_name"], "Acueducto")
        self.assertEqual(chart_df.iloc[0]["maturity_index"], 3)
        self.assertEqual(chart_df.iloc[1]["maturity_label"], "Avanzado")

    def test_form_navigation_helper_blocks_only_when_service_is_dirty(self) -> None:
        """Validate clean service navigation can proceed without the dialog."""

        with patch("views.muni_form._service_has_dirty", return_value=False):
            self.assertTrue(_can_navigate_without_prompt({"stages": []}))
        with patch("views.muni_form._service_has_dirty", return_value=True):
            self.assertFalse(_can_navigate_without_prompt({"stages": []}))
        self.assertTrue(_can_navigate_without_prompt(None))

    def test_save_section_changes_uses_server_timestamp(self) -> None:
        """Validate form saves persist with the current server timestamp."""

        database_url = self._database_url(f"sigam_v2_{uuid4().hex}.sqlite3")
        try:
            engine = get_engine(database_url)
            Base.metadata.create_all(engine)
            self._activate_database(database_url)
            with session_scope(database_url) as session:
                seed_all(session=session)
                municipality = session.execute(select(DMMunicipality).order_by(DMMunicipality.code)).scalars().first()

            snapshot = SnapshotContext(2026, 4, AUDIENCE_MUNICIPAL, municipality.code)
            form_tree = get_form_tree(municipality.code, snapshot)
            first_stage = form_tree["axes"][0]["services"][0]["stages"][0]
            first_indicator = first_stage["indicators"][0]
            result = save_section_changes(
                municipality.code,
                first_stage["section_id"],
                {first_indicator["indicator_code"]: {"value": 1.0, "evidence_files": []}},
                {"actor_subject": municipality.code},
                snapshot=snapshot,
            )

            self.assertEqual(result["validation_errors"], [])
            with session_scope(database_url) as session:
                latest_response = session.execute(
                    select(FactIndicatorResponse).order_by(
                        FactIndicatorResponse.date_time.desc(),
                        FactIndicatorResponse.response_id.desc(),
                    )
                ).scalars().first()

            self.assertIsNotNone(latest_response)
            self.assertEqual(latest_response.date_time.date(), date.today())
            self.assertNotEqual(latest_response.date_time.date(), snapshot.end_date)
        finally:
            self._dispose(database_url)


if __name__ == "__main__":
    unittest.main()
