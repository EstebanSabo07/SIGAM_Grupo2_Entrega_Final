from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import func, inspect, select

from database.bootstrap import ensure_database_ready
from database.models import DMMunicipality, FactIndicatorResponse
from database.session import get_engine, get_session_factory, session_scope


ROOT = Path(__file__).resolve().parents[1]


class DatabaseBootstrapTests(unittest.TestCase):
    """Validate runtime bootstrap behavior for local database recovery."""

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
        """Dispose cached engines and remove the temporary database file.

        Args:
            database_url: Database URL used by the test.
        """

        get_engine(database_url).dispose()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        db_path = self._database_path(database_url)
        if db_path.exists():
            try:
                db_path.unlink()
            except PermissionError:
                pass

    def test_ensure_database_ready_creates_schema_and_reference_data(self) -> None:
        """Validate bootstrap recreates schema and seeds dimensions."""

        database_url = self._database_url(f"bootstrap_{uuid4().hex}.sqlite3")
        try:
            summary = ensure_database_ready(database_url=database_url)

            self.assertFalse(summary["baseline_loaded"])
            self.assertEqual(summary["response_count"], 0)

            inspector = inspect(get_engine(database_url))
            self.assertIn("fact_indicator_response", inspector.get_table_names())

            with session_scope(database_url) as session:
                municipality = session.execute(select(DMMunicipality)).scalars().first()
                response_count = int(session.scalar(select(func.count()).select_from(FactIndicatorResponse)) or 0)

            self.assertIsNotNone(municipality)
            self.assertEqual(response_count, 0)
        finally:
            self._dispose(database_url)

    def test_ensure_database_ready_imports_baseline_for_empty_local_dev_database(self) -> None:
        """Validate empty local-development databases trigger the baseline import."""

        database_url = self._database_url(f"bootstrap_local_{uuid4().hex}.sqlite3")
        try:
            with patch("database.bootstrap._is_default_local_sqlite_url", return_value=True):
                with patch("database.bootstrap.load_source_baseline", return_value={"facts_inserted": 0}) as mocked_load:
                    summary = ensure_database_ready(database_url=database_url)

            self.assertTrue(summary["baseline_loaded"])
            mocked_load.assert_called_once_with(replace=False, database_url=database_url)
        finally:
            self._dispose(database_url)
