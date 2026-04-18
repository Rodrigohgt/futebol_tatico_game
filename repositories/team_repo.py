"""Repositório de times — CRUD entre domain e SQLite."""

from __future__ import annotations

from domain.team import TeamDomain
from repositories.base import BaseRepository
from repositories.player_repo import PlayerRepository


class TeamRepository(BaseRepository):

    def __init__(self, db_path):
        super().__init__(db_path)
        self._player_repo = PlayerRepository(db_path)

    # ── Leitura ──

    def find_by_id(self, team_id: int) -> TeamDomain | None:
        row = self._fetchone("SELECT * FROM teams WHERE id = ?", (team_id,))
        if not row:
            return None
        return self._to_domain(row)

    def find_all(self) -> list[TeamDomain]:
        rows = self._fetchall("SELECT * FROM teams ORDER BY id")
        return [self._to_domain(r) for r in rows]

    # ── Escrita ──

    def insert(self, team: TeamDomain) -> int:
        self._execute("""
            INSERT INTO teams (name, short_name, color_hex, reputation, budget, formation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (team.name, team.short_name, team.color_hex,
              team.reputation, team.budget, team.formation_key))
        return self._last_id()

    def update(self, team: TeamDomain):
        self._execute("""
            UPDATE teams
            SET name=?, short_name=?, color_hex=?, reputation=?, budget=?, formation=?
            WHERE id=?
        """, (team.name, team.short_name, team.color_hex,
              team.reputation, team.budget, team.formation_key, team.id))

    # ── Mapping ──

    def _to_domain(self, row) -> TeamDomain:
        roster = self._player_repo.find_by_team(row["id"])
        return TeamDomain(
            id=row["id"],
            name=row["name"],
            short_name=row["short_name"],
            color_hex=row["color_hex"],
            reputation=row["reputation"],
            budget=row["budget"],
            formation_key=row["formation"],
            roster=roster,
        )
