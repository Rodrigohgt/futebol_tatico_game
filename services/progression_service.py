"""Serviço de progressão — evolução e envelhecimento dos jogadores."""

from __future__ import annotations

import random

from domain.player import PlayerDomain, PlayerStats


class ProgressionService:
    """Gerencia XP, evolução de stats e envelhecimento."""

    # XP por tipo de ação
    XP_GOAL = 30
    XP_ASSIST = 20
    XP_MATCH_PLAYED = 10
    XP_WIN = 15
    XP_CLEAN_SHEET_GK = 25

    # XP necessário por nível de melhoria
    XP_PER_LEVEL = 100

    def award_match_xp(self, player: PlayerDomain, goals: int = 0,
                       assists: int = 0, won: bool = False,
                       clean_sheet: bool = False):
        """Concede XP com base na performance da partida."""
        xp = self.XP_MATCH_PLAYED
        xp += goals * self.XP_GOAL
        xp += assists * self.XP_ASSIST
        if won:
            xp += self.XP_WIN
        if clean_sheet and player.identity.position.value == "GK":
            xp += self.XP_CLEAN_SHEET_GK

        player.condition.xp += xp

    def check_level_up(self, player: PlayerDomain) -> list[str]:
        """Verifica se o jogador acumulou XP suficiente para evoluir.

        Retorna lista de stats que melhoraram.
        """
        improved = []
        while player.condition.xp >= self.XP_PER_LEVEL:
            player.condition.xp -= self.XP_PER_LEVEL
            stat_name = self._pick_stat_to_improve(player)
            if stat_name:
                current = getattr(player.stats, stat_name)
                if current < 95:
                    setattr(player.stats, stat_name, current + 1)
                    improved.append(stat_name)
        return improved

    def apply_aging(self, player: PlayerDomain):
        """Aplica efeitos de envelhecimento no início de cada temporada."""
        age = player.identity.age
        player.identity.age = age + 1

        if age >= 33:
            # Declínio físico
            self._decay_stat(player.stats, "pace", 2)
            self._decay_stat(player.stats, "stamina", 2)
            self._decay_stat(player.stats, "dribbling", 1)
        elif age >= 30:
            self._decay_stat(player.stats, "pace", 1)
            self._decay_stat(player.stats, "stamina", 1)
        elif age <= 23:
            # Crescimento natural
            self._grow_stat(player.stats, "composure", 1)
            self._grow_stat(player.stats, "positioning", 1)

    def _pick_stat_to_improve(self, player: PlayerDomain) -> str | None:
        """Escolhe qual stat melhorar baseado na posição e arquétipo."""
        # Stats prioritários por posição
        position_priority = {
            "GK": ["composure", "positioning"],
            "CB": ["defending", "heading", "positioning"],
            "LB": ["pace", "stamina", "defending"],
            "RB": ["pace", "stamina", "defending"],
            "CDM": ["defending", "passing", "stamina"],
            "CM": ["passing", "stamina", "vision"],
            "CAM": ["passing", "vision", "dribbling"],
            "LW": ["pace", "dribbling", "finishing"],
            "RW": ["pace", "dribbling", "finishing"],
            "ST": ["finishing", "composure", "positioning"],
            "CF": ["finishing", "passing", "composure"],
        }
        pos = player.identity.position.value
        candidates = position_priority.get(pos, list(player.stats.as_dict().keys()))

        # Adiciona aleatoriedade
        all_stats = list(player.stats.as_dict().keys())
        weights = []
        for s in all_stats:
            w = 3 if s in candidates else 1
            weights.append(w)

        return random.choices(all_stats, weights=weights, k=1)[0]

    @staticmethod
    def _decay_stat(stats: PlayerStats, stat_name: str, amount: int):
        current = getattr(stats, stat_name)
        setattr(stats, stat_name, max(20, current - amount))

    @staticmethod
    def _grow_stat(stats: PlayerStats, stat_name: str, amount: int):
        current = getattr(stats, stat_name)
        setattr(stats, stat_name, min(95, current + amount))
