"""Repositório de temporadas — CRUD entre domain e SQLite."""

from __future__ import annotations

from domain.enums import SeasonStatus
from domain.season import Season, Standing
from repositories.base import BaseRepository
from repositories.match_repo import MatchRepository


class SeasonRepository(BaseRepository):

    def __init__(self, db_path):
        super().__init__(db_path)
        self._match_repo = MatchRepository(db_path)

    # ── Leitura ──

    def find_by_id(self, season_id: int) -> Season | None:
        row = self._fetchone("SELECT * FROM seasons WHERE id = ?", (season_id,))
        if not row:
            return None
        return self._to_domain(row)

    def find_active(self) -> Season | None:
        row = self._fetchone("SELECT * FROM seasons WHERE status = 'active' LIMIT 1")
        if not row:
            return None
        return self._to_domain(row)

    def find_all(self) -> list[Season]:
        rows = self._fetchall("SELECT * FROM seasons ORDER BY id DESC")
        return [self._to_domain(r) for r in rows]

    # ── Escrita ──

    def insert(self, season: Season) -> int:
        self._execute("""
            INSERT INTO seasons (label, status, started_at)
            VALUES (?, ?, datetime('now'))
        """, (season.label, season.status.value))
        return self._last_id()

    def finish(self, season_id: int):
        self._execute("""
            UPDATE seasons SET status=?, finished_at=datetime('now')
            WHERE id=?
        """, (SeasonStatus.FINISHED.value, season_id))

    # ── Standings ──

    def get_standings(self, season_id: int) -> list[Standing]:
        rows = self._fetchall("""
            SELECT s.*, t.name as team_name
            FROM standings s
            JOIN teams t ON t.id = s.team_id
            WHERE s.season_id = ?
            ORDER BY s.points DESC, (s.gf - s.ga) DESC, s.gf DESC
        """, (season_id,))
        return [
            Standing(
                team_id=r["team_id"],
                team_name=r["team_name"],
                played=r["played"],
                won=r["won"],
                drawn=r["drawn"],
                lost=r["lost"],
                goals_for=r["gf"],
                goals_against=r["ga"],
            )
            for r in rows
        ]

    def upsert_standing(self, season_id: int, standing: Standing):
        self._execute("""
            INSERT INTO standings (season_id, team_id, played, won, drawn, lost, gf, ga, points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, team_id) DO UPDATE SET
                played=?, won=?, drawn=?, lost=?, gf=?, ga=?, points=?
        """, (
            season_id, standing.team_id,
            standing.played, standing.won, standing.drawn, standing.lost,
            standing.goals_for, standing.goals_against, standing.points,
            standing.played, standing.won, standing.drawn, standing.lost,
            standing.goals_for, standing.goals_against, standing.points,
        ))

    # ── Mapping ──

    def _to_domain(self, row) -> Season:
        fixtures = self._match_repo.find_by_season(row["id"])
        standings = self.get_standings(row["id"])
        return Season(
            id=row["id"],
            label=row["label"],
            status=SeasonStatus(row["status"]),
            fixtures=fixtures,
            standings=standings,
        )
