"""Serviço de save/load — cada slot é um arquivo SQLite completo."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path


class SaveService:
    """Gerencia save slots como cópias completas do banco SQLite."""

    SAVE_DIR = Path(__file__).resolve().parent.parent / "db" / "saves"
    MAX_SLOTS = 5

    def __init__(self):
        self.SAVE_DIR.mkdir(parents=True, exist_ok=True)

    def save(self, slot: int, source_db: Path):
        """Salva o estado atual copiando o banco para o slot."""
        if slot < 1 or slot > self.MAX_SLOTS:
            raise ValueError(f"Slot deve ser entre 1 e {self.MAX_SLOTS}")

        # Checkpoint WAL para garantir consistência
        conn = sqlite3.connect(str(source_db))
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()

        target = self.SAVE_DIR / f"slot_{slot}.db"
        shutil.copy2(source_db, target)

    def load(self, slot: int, target_db: Path):
        """Carrega um save slot para o banco ativo."""
        source = self.SAVE_DIR / f"slot_{slot}.db"
        if not source.exists():
            raise FileNotFoundError(f"Save slot {slot} não encontrado")
        shutil.copy2(source, target_db)

    def delete(self, slot: int):
        """Remove um save slot."""
        target = self.SAVE_DIR / f"slot_{slot}.db"
        if target.exists():
            target.unlink()

    def list_slots(self) -> list[dict]:
        """Lista os save slots disponíveis com metadados."""
        slots = []
        for i in range(1, self.MAX_SLOTS + 1):
            path = self.SAVE_DIR / f"slot_{i}.db"
            if path.exists():
                meta = self._read_meta(path)
                meta["slot"] = i
                meta["exists"] = True
                slots.append(meta)
            else:
                slots.append({"slot": i, "exists": False})
        return slots

    def _read_meta(self, db_path: Path) -> dict:
        """Lê metadados básicos de um save para exibição."""
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row

            # Temporada ativa
            season_row = conn.execute(
                "SELECT label FROM seasons WHERE status = 'active' LIMIT 1"
            ).fetchone()

            # Time do jogador (time 1 por convenção)
            team_row = conn.execute(
                "SELECT name FROM teams WHERE id = 1 LIMIT 1"
            ).fetchone()

            conn.close()

            return {
                "season": season_row["label"] if season_row else "—",
                "team": team_row["name"] if team_row else "—",
            }
        except Exception:
            return {"season": "?", "team": "?"}
