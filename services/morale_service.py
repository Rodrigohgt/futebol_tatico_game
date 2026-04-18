"""Serviço de moral — controla o estado mental dos jogadores."""

from __future__ import annotations

import json
from pathlib import Path

from domain.player import PlayerDomain


class MoraleService:
    """Gerencia moral dos jogadores durante e entre partidas."""

    def __init__(self):
        params_path = Path(__file__).resolve().parent.parent / "data" / "match_params.json"
        with open(params_path, encoding="utf-8") as f:
            self._params = json.load(f)["morale"]

    def _clamp(self, value: float) -> float:
        return max(self._params["min"], min(self._params["max"], value))

    def on_goal_scored(self, scorer: PlayerDomain, teammates: list[PlayerDomain]):
        """Boost quando o jogador marca um gol."""
        scorer.condition.morale = self._clamp(
            scorer.condition.morale + self._params["goal_scored_boost"]
        )
        # Boost menor para companheiros
        for p in teammates:
            if p.id != scorer.id:
                p.condition.morale = self._clamp(
                    p.condition.morale + self._params["goal_scored_boost"] * 0.3
                )

    def on_goal_conceded(self, players: list[PlayerDomain]):
        """Queda de moral quando o time sofre gol."""
        drop = self._params["goal_conceded_drop"]
        for p in players:
            p.condition.morale = self._clamp(p.condition.morale - drop)

    def on_card(self, player: PlayerDomain):
        """Queda de moral por cartão."""
        player.condition.morale = self._clamp(
            player.condition.morale - self._params["card_drop"]
        )

    def on_injury(self, player: PlayerDomain):
        """Queda de moral por lesão."""
        player.condition.morale = self._clamp(
            player.condition.morale - self._params["injury_drop"]
        )

    def on_match_result(self, players: list[PlayerDomain], result: str):
        """Ajusta moral com base no resultado da partida."""
        if result == "win":
            delta = self._params["win_boost"]
        elif result == "loss":
            delta = -self._params["loss_drop"]
        else:
            delta = self._params["draw_change"]

        for p in players:
            p.condition.morale = self._clamp(p.condition.morale + delta)

    def decay(self, player: PlayerDomain):
        """Decaimento natural de moral entre partidas."""
        player.condition.morale = self._clamp(
            player.condition.morale - self._params["decay_per_match"]
        )

    def morale_modifier(self, player: PlayerDomain) -> int:
        """Modificador de stats baseado na moral atual."""
        morale = player.condition.morale
        if morale >= 85:
            return 5
        if morale >= 70:
            return 2
        if morale >= 50:
            return 0
        if morale >= 30:
            return -3
        return -6
