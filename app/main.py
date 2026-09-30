"""Console entry point for PET."""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.database import DatabaseManager
from core.user_manager import UserManager
from ui.cli import run_console
from app.web import run_web_server


def build_user_manager() -> UserManager:
    """Build the application user manager with the default database path."""

    database_path = project_root / "tests" / "pet.db"
    database_manager = DatabaseManager(database_path)
    database_manager.initialize()
    return UserManager(database_manager)


def main(arguments: list[str] | None = None) -> None:
    """Start the console or local web application."""

    parser = argparse.ArgumentParser(description="Run PET.")
    parser.add_argument(
        "--web",
        action="store_true",
        help="start the local HTTPS web application instead of the CLI",
    )
    options = parser.parse_args(arguments)

    user_manager = build_user_manager()
    if options.web:
        run_web_server(user_manager)
        return
    run_console(user_manager)


if __name__ == "__main__":
    main()
