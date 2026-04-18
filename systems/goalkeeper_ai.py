"""IA especializada para goleiros.

Lógica isolada: posicionamento dinâmico baseado na bola,
movimentação restrita à zona defensiva, fechamento de ângulo.
"""

from __future__ import annotations

import math
import pygame

from entities.player import Player
from utils.coordinates import CoordinateSystem
from config import settings


class GoalkeeperAI:
    """Controla o posicionamento automático do goleiro rival."""

    def __init__(self, coords: CoordinateSystem, side: str = "right"):
        self.coords = coords
        self.side = side

        # Calcula a zona de atuação do GK em pixels
        if side == "right":
            goal_line_x = coords.origin_x + coords.field_px_w
            self.zone_min_x = goal_line_x - coords.m2px_w(settings.GK_ZONE_DEPTH)
            self.zone_max_x = goal_line_x - coords.m2px_w(1.0)
        else:
            goal_line_x = coords.origin_x
            self.zone_min_x = goal_line_x + coords.m2px_w(1.0)
            self.zone_max_x = goal_line_x + coords.m2px_w(settings.GK_ZONE_DEPTH)

        goal_center_y = coords.origin_y + coords.field_px_h / 2
        half_zone_h = coords.m2px_h(settings.GK_ZONE_WIDTH / 2)
        self.zone_min_y = goal_center_y - half_zone_h
        self.zone_max_y = goal_center_y + half_zone_h

        self.goal_center = pygame.Vector2(
            goal_line_x if side == "right" else goal_line_x,
            goal_center_y,
        )

    def update_position(self, gk: Player, ball_pos: pygame.Vector2):
        """Calcula e aplica a posição ideal do goleiro.

        Usa reposition() para permitir atualização contínua
        sem consumir a ação de turno do GK.
        Aplica dead zone: só move se o alvo ideal estiver longe o suficiente.
        """
        target = self._calc_ideal_position(ball_pos)

        # Dead zone — evita micro-movimentos constantes
        dx = target[0] - gk.pos.x
        dy = target[1] - gk.pos.y
        if dx * dx + dy * dy < 64:  # < 8px
            return

        gk.reposition(target)

    def _calc_ideal_position(self, ball_pos: pygame.Vector2) -> tuple[float, float]:
        """Posiciona o GK na linha entre a bola e o centro do gol,
        restrito à zona defensiva."""

        # Vetor bola → gol
        to_goal = self.goal_center - ball_pos
        dist_to_goal = to_goal.length()

        if dist_to_goal < 1:
            return (self.goal_center.x, self.goal_center.y)

        # Quanto mais perto a bola, mais o GK avança (até o limite da zona)
        # Fator de avanço: 0.0 (bola longe) a 0.85 (bola na área)
        field_diag = math.sqrt(
            self.coords.field_px_w ** 2 + self.coords.field_px_h ** 2
        )
        proximity = max(0.0, 1.0 - dist_to_goal / field_diag)
        advance_factor = proximity ** 1.5 * settings.GK_ADVANCE_FACTOR

        # Posição na linha bola-gol
        ideal = self.goal_center - to_goal.normalize() * (
            dist_to_goal * advance_factor
        )

        # Restringe à zona
        x = max(self.zone_min_x, min(ideal.x, self.zone_max_x))
        y = max(self.zone_min_y, min(ideal.y, self.zone_max_y))

        return (x, y)

    @staticmethod
    def is_goalkeeper(player: Player) -> bool:
        return player.info.position == "GK"
