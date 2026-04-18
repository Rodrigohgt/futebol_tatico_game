"""Repositório de estatísticas e eventos de partida."""

from __future__ import annotations

import json

from domain.events import MatchEvent
from domain.enums import EventType
from domain.value_objects import StatLine
from repositories.base import BaseRepository


class StatsRepository(BaseRepository):

    # ── Eventos de partida ──

    def record_event(self, event: MatchEvent):
        self._execute("""
            INSERT INTO match_events (match_id, turn, event_type, actor_id,
                                      target_id, data_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event.match_id, event.turn, event.event_type.value,
              event.actor_id, event.target_id, event.to_json()))

    def get_match_events(self, match_id: int) -> list[MatchEvent]:
        rows = self._fetchall(
            "SELECT * FROM match_events WHERE match_id = ? ORDER BY turn, id",
            (match_id,),
        )
        result = []
        for r in rows:
            data = json.loads(r["data_json"]) if r["data_json"] else {}
            result.append(MatchEvent(
                match_id=r["match_id"],
                turn=r["turn"],
                event_type=EventType(r["event_type"]),
                actor_id=r["actor_id"],
                target_id=r["target_id"],
                data=data,
            ))
        return result

    # ── Stats por jogador por partida ──

    def record_player_stats(self, match_id: int, player_id: int,
                            team_id: int, stat_line: StatLine):
        self._execute("""
            INSERT INTO match_player_stats
                (match_id, player_id, team_id, minutes, goals, assists,
                 shots, passes_att, passes_cmp, tackles, fouls, saves, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(match_id, player_id) DO UPDATE SET
                minutes=?, goals=?, assists=?, shots=?, passes_att=?,
                passes_cmp=?, tackles=?, fouls=?, saves=?, rating=?
        """, (
            match_id, player_id, team_id,
            stat_line.minutes, stat_line.goals, stat_line.assists,
            stat_line.shots, stat_line.passes_attempted, stat_line.passes_completed,
            stat_line.tackles, stat_line.fouls, stat_line.saves, stat_line.rating,
            stat_line.minutes, stat_line.goals, stat_line.assists,
            stat_line.shots, stat_line.passes_attempted, stat_line.passes_completed,
            stat_line.tackles, stat_line.fouls, stat_line.saves, stat_line.rating,
        ))

    def get_player_match_stats(self, match_id: int, player_id: int) -> StatLine | None:
        row = self._fetchone("""
            SELECT * FROM match_player_stats
            WHERE match_id = ? AND player_id = ?
        """, (match_id, player_id))
        if not row:
            return None
        return StatLine(
            minutes=row["minutes"],
            goals=row["goals"],
            assists=row["assists"],
            shots=row["shots"],
            passes_attempted=row["passes_att"],
            passes_completed=row["passes_cmp"],
            tackles=row["tackles"],
            fouls=row["fouls"],
            saves=row["saves"],
            rating=row["rating"] or 0.0,
        )

    def get_player_season_totals(self, player_id: int, season_id: int) -> StatLine:
        row = self._fetchone("""
            SELECT
                COALESCE(SUM(mps.minutes), 0) as minutes,
                COALESCE(SUM(mps.goals), 0) as goals,
                COALESCE(SUM(mps.assists), 0) as assists,
                COALESCE(SUM(mps.shots), 0) as shots,
                COALESCE(SUM(mps.passes_att), 0) as passes_att,
                COALESCE(SUM(mps.passes_cmp), 0) as passes_cmp,
                COALESCE(SUM(mps.tackles), 0) as tackles,
                COALESCE(SUM(mps.fouls), 0) as fouls,
                COALESCE(SUM(mps.saves), 0) as saves,
                AVG(mps.rating) as avg_rating
            FROM match_player_stats mps
            JOIN matches m ON m.id = mps.match_id
            WHERE mps.player_id = ? AND m.season_id = ?
        """, (player_id, season_id))
        if not row or row["minutes"] == 0:
            return StatLine()
        return StatLine(
            minutes=row["minutes"],
            goals=row["goals"],
            assists=row["assists"],
            shots=row["shots"],
            passes_attempted=row["passes_att"],
            passes_completed=row["passes_cmp"],
            tackles=row["tackles"],
            fouls=row["fouls"],
            saves=row["saves"],
            rating=row["avg_rating"] or 0.0,
        )

    # ── Cartões ──

    def record_card(self, match_id: int, player_id: int,
                    card_type: str, turn: int, reason: str = ""):
        self._execute("""
            INSERT INTO cards (match_id, player_id, card_type, turn, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (match_id, player_id, card_type, turn, reason))

    def count_yellows_season(self, player_id: int, season_id: int) -> int:
        row = self._fetchone("""
            SELECT COUNT(*) as cnt
            FROM cards c
            JOIN matches m ON m.id = c.match_id
            WHERE c.player_id = ? AND m.season_id = ? AND c.card_type = 'yellow'
        """, (player_id, season_id))
        return row["cnt"] if row else 0

    # ── Lesões ──

    def record_injury(self, player_id: int, match_id: int | None,
                      injury_type: str, severity: int, games_out: int):
        self._execute("""
            INSERT INTO injuries (player_id, match_id, injury_type, severity, games_out)
            VALUES (?, ?, ?, ?, ?)
        """, (player_id, match_id, injury_type, severity, games_out))

    def get_active_injuries(self, player_id: int) -> list[dict]:
        rows = self._fetchall("""
            SELECT * FROM injuries
            WHERE player_id = ? AND recovered_at IS NULL
            ORDER BY occurred_at DESC
        """, (player_id,))
        return [dict(r) for r in rows]

    def recover_injury(self, injury_id: int):
        self._execute("""
            UPDATE injuries SET recovered_at = datetime('now')
            WHERE id = ?
        """, (injury_id,))
