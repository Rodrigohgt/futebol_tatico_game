"""Repositório de partidas — CRUD entre domain e SQLite."""

from __future__ import annotations

from domain.enums import MatchStatus
from domain.season import MatchFixture
from repositories.base import BaseRepository


class MatchRepository(BaseRepository):

    # ── Leitura ──

    def find_by_id(self, match_id: int) -> MatchFixture | None:
        row = self._fetchone("SELECT * FROM matches WHERE id = ?", (match_id,))
        if not row:
            return None
        return self._to_domain(row)

    def find_by_season(self, season_id: int) -> list[MatchFixture]:
        rows = self._fetchall(
            "SELECT * FROM matches WHERE season_id = ? ORDER BY match_day",
            (season_id,),
        )
        return [self._to_domain(r) for r in rows]

    def find_by_team(self, team_id: int, season_id: int | None = None) -> list[MatchFixture]:
        if season_id:
            rows = self._fetchall(
                "SELECT * FROM matches WHERE (home_id=? OR away_id=?) AND season_id=? ORDER BY match_day",
                (team_id, team_id, season_id),
            )
        else:
            rows = self._fetchall(
                "SELECT * FROM matches WHERE home_id=? OR away_id=? ORDER BY match_day",
                (team_id, team_id),
            )
        return [self._to_domain(r) for r in rows]

    # ── Escrita ──

    def insert(self, fixture: MatchFixture) -> int:
        self._execute("""
            INSERT INTO matches (season_id, home_id, away_id, home_score,
                                 away_score, status, match_day)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (fixture.season_id, fixture.home_id, fixture.away_id,
              fixture.home_score, fixture.away_score,
              fixture.status.value, fixture.match_day))
        return self._last_id()

    def update_score(self, match_id: int, home_score: int, away_score: int):
        self._execute("""
            UPDATE matches
            SET home_score=?, away_score=?, status=?, played_at=datetime('now')
            WHERE id=?
        """, (home_score, away_score, MatchStatus.FINISHED.value, match_id))

    def update_status(self, match_id: int, status: MatchStatus):
        self._execute(
            "UPDATE matches SET status=? WHERE id=?",
            (status.value, match_id),
        )

    # ── Mapping ──

    def _to_domain(self, row) -> MatchFixture:
        return MatchFixture(
            id=row["id"],
            season_id=row["season_id"],
            home_id=row["home_id"],
            away_id=row["away_id"],
            match_day=row["match_day"],
            home_score=row["home_score"],
            away_score=row["away_score"],
            status=MatchStatus(row["status"]),
        )
