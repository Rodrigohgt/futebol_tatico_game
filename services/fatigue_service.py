"""Serviço de fadiga — controla desgaste e recuperação dos jogadores."""

from __future__ import annotations

import json
from pathlib import Path

from domain.player import PlayerDomain, PlayerCondition


class FatigueService:
    """Gerencia fadiga durante e entre partidas."""

    def __init__(self):
        params_path = Path(__file__).resolve().parent.parent / "data" / "match_params.json"
        with open(params_path, encoding="utf-8") as f:
            self._params = json.load(f)["fatigue"]

    @property
    def per_move(self) -> float:
        return self._params["per_move"]

    @property
    def per_pass(self) -> float:
        return self._params["per_pass"]

    @property
    def per_sprint(self) -> float:
        return self._params["per_sprint"]

    @property
    def exhaustion_threshold(self) -> float:
        return self._params["exhaustion_threshold"]

    def apply_move_cost(self, player: PlayerDomain):
        """Aplica custo de fadiga por movimentação."""
        player.condition.fatigue = max(
            0.0, player.condition.fatigue - self.per_move
        )

    def apply_pass_cost(self, player: PlayerDomain):
        """Aplica custo de fadiga por passe."""
        player.condition.fatigue = max(
            0.0, player.condition.fatigue - self.per_pass
        )

    def apply_sprint_cost(self, player: PlayerDomain):
        """Aplica custo de fadiga por sprint."""
        player.condition.fatigue = max(
            0.0, player.condition.fatigue - self.per_sprint
        )

    def recover_bench(self, player: PlayerDomain):
        """Recuperação por turno no banco de reservas."""
        recovery = self._params["recovery_per_turn_bench"]
        player.condition.fatigue = min(
            100.0, player.condition.fatigue + recovery
        )

    def recover_between_matches(self, player: PlayerDomain):
        """Recuperação entre partidas."""
        recovery = self._params["recovery_between_matches"]
        # Engine trait dá recuperação bônus
        if "engine" in player.traits:
            recovery *= 1.2
        player.condition.fatigue = min(
            100.0, player.condition.fatigue + recovery
        )

    def is_exhausted(self, player: PlayerDomain) -> bool:
        return player.condition.fatigue <= self.exhaustion_threshold

    def stat_penalty(self, player: PlayerDomain) -> int:
        """Penalidade de stats por fadiga (a cada 10 abaixo de 100)."""
        missing = 100.0 - player.condition.fatigue
        penalty_per_10 = self._params["stat_penalty_per_10_fatigue"]
        return int(missing / 10) * penalty_per_10
