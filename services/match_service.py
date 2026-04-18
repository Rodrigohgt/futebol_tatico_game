"""Serviço de partida — orquestra início, fim e persistência."""

from __future__ import annotations

from domain.match_state import MatchState
from domain.events import MatchEvent
from domain.enums import MatchStatus, EventType
from domain.value_objects import StatLine
from repositories.player_repo import PlayerRepository
from repositories.match_repo import MatchRepository
from repositories.stats_repo import StatsRepository
from services.fatigue_service import FatigueService
from services.morale_service import MoraleService
from services.progression_service import ProgressionService


class MatchService:
    """Orquestra o fluxo completo de uma partida.

    - start_match: carrega jogadores do DB → cria MatchState
    - finish_match: persiste todos os resultados no DB
    """

    def __init__(self, player_repo: PlayerRepository,
                 match_repo: MatchRepository,
                 stats_repo: StatsRepository):
        self._players = player_repo
        self._matches = match_repo
        self._stats = stats_repo
        self._fatigue = FatigueService()
        self._morale = MoraleService()
        self._progression = ProgressionService()

    def start_match(self, match_id: int) -> MatchState:
        """Prepara o estado inicial da partida a partir do DB."""
        fixture = self._matches.find_by_id(match_id)
        if not fixture:
            raise ValueError(f"Partida {match_id} não encontrada")

        self._matches.update_status(match_id, MatchStatus.IN_PROGRESS)
        self._matches.commit()

        return MatchState(
            match_id=match_id,
            turn=1,
        )

    def finish_match(self, state: MatchState, home_team_id: int,
                     away_team_id: int):
        """Persiste todos os resultados da partida no banco.

        Chamado uma única vez ao final da partida. Batch write.
        """
        # 1. Atualiza placar
        self._matches.update_score(
            state.match_id, state.home_score, state.away_score
        )

        # 2. Registra todos os eventos
        for event in state.all_events:
            self._stats.record_event(event)

        # 3. Registra stats por jogador
        for player_id, raw_stats in state.player_stats.items():
            stat_line = StatLine(
                minutes=raw_stats.get("minutes", 0),
                goals=raw_stats.get("goals", 0),
                assists=raw_stats.get("assists", 0),
                shots=raw_stats.get("shots", 0),
                passes_attempted=raw_stats.get("passes_att", 0),
                passes_completed=raw_stats.get("passes_cmp", 0),
                tackles=raw_stats.get("tackles", 0),
                fouls=raw_stats.get("fouls", 0),
                saves=raw_stats.get("saves", 0),
            )
            # Determina time do jogador
            team_id = home_team_id  # default
            player = self._players.find_by_id(player_id)
            if player and player.identity.team_id == away_team_id:
                team_id = away_team_id

            self._stats.record_player_stats(
                state.match_id, player_id, team_id, stat_line
            )

        # 4. Atualiza condição dos jogadores (fadiga, moral)
        home_players = self._players.find_by_team(home_team_id)
        away_players = self._players.find_by_team(away_team_id)

        # Resultado para moral
        if state.home_score > state.away_score:
            home_result, away_result = "win", "loss"
        elif state.home_score < state.away_score:
            home_result, away_result = "loss", "win"
        else:
            home_result, away_result = "draw", "draw"

        self._morale.on_match_result(home_players, home_result)
        self._morale.on_match_result(away_players, away_result)

        # Persistir condição
        for p in home_players + away_players:
            self._fatigue.recover_between_matches(p)
            self._players.update_condition(p.id, p.condition)

            # XP e progressão
            ps = state.player_stats.get(p.id, {})
            self._progression.award_match_xp(
                p,
                goals=ps.get("goals", 0),
                assists=ps.get("assists", 0),
                won=(home_result == "win" if p.identity.team_id == home_team_id
                     else away_result == "win"),
            )
            improved = self._progression.check_level_up(p)
            if improved:
                self._players.update_stats(p.id, p.stats)
            self._players.update_condition(p.id, p.condition)

        # 5. Commit único
        self._matches.commit()
        self._stats.commit()
        self._players.commit()
