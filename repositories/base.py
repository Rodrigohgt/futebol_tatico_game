"""Repositório base com gerenciamento de conexão SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class BaseRepository:
    """Base para todos os repositórios. Gerencia conexão e helpers SQL."""

    def __init__(self, db_path: Path | str):
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _fetchone(self, sql: str, params=()) -> sqlite3.Row | None:
        return self.conn.execute(sql, params).fetchone()

    def _fetchall(self, sql: str, params=()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def _execute(self, sql: str, params=()):
        self.conn.execute(sql, params)

    def _executemany(self, sql: str, params_list: list):
        self.conn.executemany(sql, params_list)

    def _last_id(self) -> int:
        row = self._fetchone("SELECT last_insert_rowid()")
        return row[0] if row else 0

    def commit(self):
        if self._conn:
            self._conn.commit()

    def rollback(self):
        if self._conn:
            self._conn.rollback()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def init_schema(self):
        """Aplica o schema SQL inicial (idempotente via IF NOT EXISTS)."""
        schema_path = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            sql = f.read()
        self.conn.executescript(sql)
