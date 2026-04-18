"""Command-line initializer for the IGSM database."""

from __future__ import annotations

import argparse

from database.models import Base
from database.seed import seed_all
from database.session import get_engine


def init_database(include_demo_results: bool = False) -> None:
    """Create the configured database schema and seed reference data.

    Args:
        include_demo_results: Deprecated compatibility flag. Demo app tables are
            no longer created by the ORM.
    """

    engine = get_engine()
    Base.metadata.create_all(engine)
    seed_all(include_demo_results=include_demo_results)


def main() -> None:
    """Run the database initializer CLI."""

    parser = argparse.ArgumentParser(description="Initialize the IGSM database schema and seed reference data.")
    parser.add_argument(
        "--include-demo-results",
        action="store_true",
        help="Deprecated no-op kept for CLI compatibility.",
    )
    args = parser.parse_args()
    init_database(include_demo_results=args.include_demo_results)
    print("IGSM database initialized.")


if __name__ == "__main__":
    main()
