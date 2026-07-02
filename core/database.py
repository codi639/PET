"""SQLite database management for PET."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Callable

RowMapper = Callable[[sqlite3.Row], Any]


class DatabaseManager:
    """Create the database, create tables, and execute queries."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        """Create the database file and required tables."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.database_path.touch(exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    public_key TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """)
            self._ensure_users_public_key_column(connection)
            connection.commit()

    def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> int:
        """Execute a write query and return the affected row count."""

        with self._connect() as connection:
            cursor = connection.execute(query, parameters)
            connection.commit()
            return cursor.rowcount

    def fetch_one(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
        mapper: RowMapper | None = None,
    ) -> Any | None:
        """Fetch one row and optionally map it to an object."""

        with self._connect() as connection:
            cursor = connection.execute(query, parameters)
            row = cursor.fetchone()
            if row is None:
                return None
            if mapper is None:
                return row
            return mapper(row)

    def fetch_all(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
        mapper: RowMapper | None = None,
    ) -> list[Any]:
        """Fetch all matching rows and optionally map them to objects."""

        with self._connect() as connection:
            cursor = connection.execute(query, parameters)
            rows = cursor.fetchall()
            if mapper is None:
                return list(rows)
            return [mapper(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_users_public_key_column(self, connection: sqlite3.Connection) -> None:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        if "public_key" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN public_key TEXT NOT NULL DEFAULT ''"
            )
