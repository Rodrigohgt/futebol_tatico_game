"""Repositório de jogadores — CRUD entre domain e SQLite."""

from __future__ import annotations

from domain.player import (
    PlayerDomain, PlayerIdentity, PlayerStats, PlayerCondition,
)
from domain.enums import Position, Foot, PlayerStatus
from repositories.base import BaseRepository


class PlayerRepository(BaseRepository):

    # ── Leitura ──

    def find_by_id(self, player_id: int) -> PlayerDomain | None:
        row = self._fetchone("""
            SELECT p.*, ps.finishing, ps.passing, ps.pace, ps.dribbling,
                   ps.defending, ps.heading, ps.stamina, ps.composure,
                   ps.positioning, ps.vision,
                   pc.fatigue, pc.morale, pc.form, pc.xp
            FROM players p
            JOIN player_stats ps ON ps.player_id = p.id
            LEFT JOIN player_condition pc ON pc.player_id = p.id
            WHERE p.id = ?
        """, (player_id,))
        if not row:
            return None
        return self._to_domain(row)

    def find_by_team(self, team_id: int) -> list[PlayerDomain]:
        rows = self._fetchall("""
            SELECT p.*, ps.finishing, ps.passing, ps.pace, ps.dribbling,
                   ps.defending, ps.heading, ps.stamina, ps.composure,
                   ps.positioning, ps.vision,
                   pc.fatigue, pc.morale, pc.form, pc.xp
            FROM players p
            JOIN player_stats ps ON ps.player_id = p.id
            LEFT JOIN player_condition pc ON pc.player_id = p.id
            WHERE p.team_id = ? AND p.status = 'active'
            ORDER BY p.id
        """, (team_id,))
        return [self._to_domain(r) for r in rows]

    def find_all(self) -> list[PlayerDomain]:
        rows = self._fetchall("""
            SELECT p.*, ps.finishing, ps.passing, ps.pace, ps.dribbling,
                   ps.defending, ps.heading, ps.stamina, ps.composure,
                   ps.positioning, ps.vision,
                   pc.fatigue, pc.morale, pc.form, pc.xp
            FROM players p
            JOIN player_stats ps ON ps.player_id = p.id
            LEFT JOIN player_condition pc ON pc.player_id = p.id
            ORDER BY p.team_id, p.id
        """)
        return [self._to_domain(r) for r in rows]

    def find_traits(self, player_id: int) -> list[str]:
        rows = self._fetchall(
            "SELECT trait_key FROM player_traits WHERE player_id = ?",
            (player_id,),
        )
        return [r["trait_key"] for r in rows]

    # ── Escrita ──

    def insert(self, player: PlayerDomain) -> int:
        ident = player.identity
        self._execute("""
            INSERT INTO players (team_id, name, age, number, position,
                                 archetype, foot, status, contract_end, market_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ident.team_id, ident.name, ident.age, ident.number,
            ident.position.value, ident.archetype, ident.foot.value,
            ident.status.value, ident.contract_end_season, ident.market_value,
        ))
        pid = self._last_id()

        s = player.stats
        self._execute("""
            INSERT INTO player_stats (player_id, finishing, passing, pace,
                                      dribbling, defending, heading, stamina,
                                      composure, positioning, vision)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, s.finishing, s.passing, s.pace, s.dribbling, s.defending,
              s.heading, s.stamina, s.composure, s.positioning, s.vision))

        c = player.condition
        self._execute("""
            INSERT INTO player_condition (player_id, fatigue, morale, form, xp)
            VALUES (?, ?, ?, ?, ?)
        """, (pid, c.fatigue, c.morale, c.form, c.xp))

        for trait in player.traits:
            self._execute(
                "INSERT INTO player_traits (player_id, trait_key) VALUES (?, ?)",
                (pid, trait),
            )

        return pid

    def update_stats(self, player_id: int, stats: PlayerStats):
        self._execute("""
            UPDATE player_stats
            SET finishing=?, passing=?, pace=?, dribbling=?, defending=?,
                heading=?, stamina=?, composure=?, positioning=?, vision=?
            WHERE player_id = ?
        """, (stats.finishing, stats.passing, stats.pace, stats.dribbling,
              stats.defending, stats.heading, stats.stamina, stats.composure,
              stats.positioning, stats.vision, player_id))

    def update_condition(self, player_id: int, condition: PlayerCondition):
        self._execute("""
            UPDATE player_condition
            SET fatigue=?, morale=?, form=?, xp=?
            WHERE player_id = ?
        """, (condition.fatigue, condition.morale, condition.form,
              condition.xp, player_id))

    def update_status(self, player_id: int, status: PlayerStatus):
        self._execute(
            "UPDATE players SET status=? WHERE id=?",
            (status.value, player_id),
        )

    # ── Mapping ──

    def _to_domain(self, row) -> PlayerDomain:
        identity = PlayerIdentity(
            id=row["id"],
            name=row["name"],
            age=row["age"],
            number=row["number"],
            position=Position(row["position"]),
            foot=Foot(row["foot"]),
            archetype=row["archetype"] or "",
            status=PlayerStatus(row["status"]),
            team_id=row["team_id"] or 0,
            market_value=row["market_value"],
            contract_end_season=row["contract_end"] or 0,
        )
        stats = PlayerStats(
            finishing=row["finishing"],
            passing=row["passing"],
            pace=row["pace"],
            dribbling=row["dribbling"],
            defending=row["defending"],
            heading=row["heading"],
            stamina=row["stamina"],
            composure=row["composure"],
            positioning=row["positioning"],
            vision=row["vision"],
        )
        condition = PlayerCondition(
            fatigue=row["fatigue"] if row["fatigue"] is not None else 100.0,
            morale=row["morale"] if row["morale"] is not None else 70.0,
            form=row["form"] if row["form"] is not None else 50.0,
            xp=row["xp"] if row["xp"] is not None else 0,
        )
        traits = self.find_traits(row["id"])
        return PlayerDomain(
            identity=identity, stats=stats, condition=condition, traits=traits,
        )
