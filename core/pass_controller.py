"""Controlador de passes — lógica extraída do Game.

Gerencia:
- Modo de passe (ativação, cancelamento)
- Barra de força
- Cálculo de potência automática
- Execução do passe (chance, erro, facing)
- Contagem de passes por turno
"""

from __future__ import annotations

import math
import random

import pygame

from config import settings
from entities.ball import Ball
from entities.player import Player
from rendering.power_bar import PowerBar
from utils.event_bus import EventBus


class PassController:
    """Encapsula toda a lógica de passe, removendo responsabilidade do Game."""

    def __init__(self, event_bus: EventBus | None = None):
        self.pass_mode = False
        self.pass_charging = False
        self.passes_this_turn = 0
        self.power_bar = PowerBar()
        self._bus = event_bus

    def can_pass(self, ball: Ball, home_players: list[Player]) -> bool:
        if not ball.is_held():
            return False
        return ball.owner in home_players

    def activate(self):
        self.pass_mode = True

    def cancel(self):
        self.pass_mode = False
        self.pass_charging = False
        self.power_bar.cancel()

    def reset_turn(self):
        self.passes_this_turn = 0
        self.cancel()

    def start_charge(self):
        self.pass_charging = True
        self.power_bar.start_charge()

    def stop_charge(self) -> float:
        self.pass_charging = False
        return self.power_bar.stop_charge()

    def auto_power(self, ball: Ball, target: tuple[float, float]) -> float:
        """Calcula power ideal para a bola chegar ao target (fórmula de fricção)."""
        dx = target[0] - ball.pos.x
        dy = target[1] - ball.pos.y
        dist = math.sqrt(dx * dx + dy * dy)
        ideal_speed = dist * (1 - settings.BALL_FRICTION)
        clamped = max(settings.PASS_MIN_SPEED,
                      min(settings.PASS_MAX_SPEED, ideal_speed))
        return (clamped - settings.PASS_MIN_SPEED) / (
            settings.PASS_MAX_SPEED - settings.PASS_MIN_SPEED
        )

    def execute(self, ball: Ball, target: tuple[float, float],
                power: float, coords) -> bool:
        """Executa o passe. Retorna True se consumiu ação do jogador."""
        if not ball.is_held():
            return False

        passer = ball.owner

        # Velocidade baseada na força
        speed = settings.PASS_MIN_SPEED + (
            settings.PASS_MAX_SPEED - settings.PASS_MIN_SPEED
        ) * power

        # Chance de sucesso (base + stat + penalidades)
        base_rate = settings.BALL_PASS_SUCCESS_RATE
        stat_bonus = (passer.stats.passing - 50) / 500

        # Penalidade por distância: até -15% para passe máximo
        dx = target[0] - passer.pos.x
        dy = target[1] - passer.pos.y
        dist = math.sqrt(dx * dx + dy * dy)
        max_field = math.sqrt(coords.field_px_w ** 2 + coords.field_px_h ** 2)
        dist_penalty = (dist / max_field) * 0.15

        # Penalidade por força: até -10% com força máxima
        power_penalty = power * 0.10

        success_rate = max(0.3, min(0.99,
                                    base_rate + stat_bonus - dist_penalty - power_penalty))
        success = random.random() < success_rate

        error_angle = 0.0
        if not success:
            max_err = settings.BALL_PASS_ERROR_MAX
            error_angle = random.uniform(-max_err, max_err)

        # Facing do passador
        direction = pygame.Vector2(dx, dy)
        if direction.length() > 0:
            passer.facing = direction.normalize()

        ball.kick_towards(
            target=target,
            speed=speed,
            success=success,
            error_angle=error_angle,
        )

        self.passes_this_turn += 1

        # Emite evento
        if self._bus:
            self._bus.emit("pass_executed", {
                "passer": passer, "target": target,
                "power": power, "success": success,
            })

        # Retorna True se o passe custa ação
        cost_action = (passer.has_moved or
                       self.passes_this_turn > settings.BALL_FREE_PASSES_PER_TURN)
        if cost_action:
            passer.has_moved = True

        return cost_action

    def teammate_at(self, pos: tuple[int, int], ball: Ball,
                    home_players: list[Player]) -> Player | None:
        """Retorna o companheiro de time na posição clicada (exceto o portador)."""
        for p in home_players:
            if p is ball.owner:
                continue
            if p.contains_point(pos):
                return p
        return None
