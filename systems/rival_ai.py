"""Inteligência artificial reativa da equipe rival.

Usa um sistema de decisão baseado em pesos: cada comportamento calcula
um score de relevância, que é multiplicado pelo peso da estratégia ativa.
O comportamento com maior score ponderado vence e define o movimento.

Fluxo:
1. Estratégia ativa fornece os pesos
2. Para cada rival disponível, todos os comportamentos avaliam (score, alvo)
3. Score × peso da estratégia = score ponderado
4. Maior score ponderado vence
5. Rival se move para a posição-alvo do comportamento vencedor
"""

from __future__ import annotations

import math
import random

from entities.player import Player
from utils.coordinates import CoordinateSystem
from systems.behaviors import ALL_BEHAVIORS, Behavior
from systems.strategy import (
    StrategyProfile, TacticMode, PROFILES, OFFENSIVE,
)


class RivalAI:
    """Controlador de decisões da equipe rival com estratégias táticas."""

    def __init__(self, coord_system: CoordinateSystem):
        self.coords = coord_system
        self._behaviors: list[Behavior] = list(ALL_BEHAVIORS)
        self._strategy: StrategyProfile = OFFENSIVE

    @property
    def strategy(self) -> StrategyProfile:
        return self._strategy

    def set_strategy(self, mode: TacticMode):
        """Altera a estratégia tática ativa."""
        self._strategy = PROFILES[mode]

    def react(
        self,
        rival_players: list[Player],
        human_players: list[Player],
        context=None,
    ) -> Player | None:
        """Escolhe um rival e executa a melhor ação segundo a estratégia."""
        available = [p for p in rival_players
                     if p.can_move() and p.info.position != "GK"]
        if not available:
            return None

        best_rival = None
        best_score = -1.0
        best_target = None

        for rival in available:
            score, target = self._best_action(rival, human_players,
                                               rival_players, context)

            # Bônus de proximidade à bola: jogador mais perto ganha prioridade
            if context is not None and context.ball_pos is not None:
                dist_to_ball = rival.pos.distance_to(context.ball_pos)
                max_field = math.sqrt(
                    self.coords.field_px_w ** 2 + self.coords.field_px_h ** 2
                )
                proximity = max(0.0, 1.0 - dist_to_ball / max_field)
                score += proximity * 0.4

            score += random.uniform(0, 0.02)
            if score > best_score:
                best_score = score
                best_rival = rival
                best_target = target

        if best_rival is not None and best_target is not None:
            best_rival.set_target(best_target)

        return best_rival

    def _best_action(
        self,
        rival: Player,
        human_players: list[Player],
        all_rivals: list[Player],
        context=None,
    ) -> tuple[float, tuple[float, float]]:
        """Avalia todos os comportamentos e retorna o melhor (score, alvo)."""
        weights = self._strategy.weights
        best_score = -1.0
        best_target = (rival.pos.x, rival.pos.y)

        for behavior in self._behaviors:
            weight = weights.get(behavior.name, 0.0)
            if weight <= 0:
                continue

            raw_score, target = behavior.evaluate(
                rival, human_players, all_rivals, self.coords,
                context=context,
            )
            weighted = raw_score * weight

            if weighted > best_score:
                best_score = weighted
                best_target = target

        return best_score, best_target
