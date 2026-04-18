"""Comportamentos unitários da IA rival.

Cada comportamento analisa o estado do campo e retorna um score de
relevância (0.0–1.0) e uma posição-alvo. O sistema de decisão
multiplica o score pelo peso da estratégia ativa para escolher a ação.

Para criar novos comportamentos, basta implementar a interface:
    evaluate(rival, human_players, coord_system) -> (score, target_pos)
"""

from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod

import pygame

from entities.player import Player
from utils.coordinates import CoordinateSystem
from systems.field_context import FieldContext


class Behavior(ABC):
    """Interface base para todos os comportamentos."""

    name: str = "base"

    @abstractmethod
    def evaluate(
        self,
        rival: Player,
        human_players: list[Player],
        all_rivals: list[Player],
        coords: CoordinateSystem,
        context: FieldContext | None = None,
    ) -> tuple[float, tuple[float, float]]:
        """Retorna (score 0-1, posição-alvo em pixels)."""
        ...

    def _clamp(self, x, y, coords: CoordinateSystem):
        b = coords.field_bounds()
        return max(b[0], min(x, b[2])), max(b[1], min(y, b[3]))

    def _dist(self, a: Player, b: Player) -> float:
        return a.pos.distance_to(b.pos)

    def _is_goalkeeper(self, player: Player) -> bool:
        return player.info.position == "GK"


class PressBallCarrier(Behavior):
    """Avança diretamente em direção à posição da bola.

    Diferente de PressAttacker que mira no jogador mais próximo,
    este comportamento foca especificamente na bola — ativado
    com peso alto quando o humano tem a posse.
    """

    name = "press_ball_carrier"

    def evaluate(self, rival, human_players, all_rivals, coords,
                 context=None):
        if self._is_goalkeeper(rival):
            return 0.0, (rival.pos.x, rival.pos.y)

        if context is None or not context.ball_owner_is_human:
            return 0.0, (rival.pos.x, rival.pos.y)

        ball_pos = context.ball_pos
        dist = rival.pos.distance_to(ball_pos)
        max_field = math.sqrt(coords.field_px_w ** 2 + coords.field_px_h ** 2)

        # Score altíssimo para o rival mais próximo da bola
        score = max(0.0, 1.0 - (dist / max_field)) ** 0.6

        direction = pygame.Vector2(ball_pos.x - rival.pos.x,
                                   ball_pos.y - rival.pos.y)
        if direction.length() < 1:
            return score, (rival.pos.x, rival.pos.y)

        move = min(direction.length() - 12, coords.max_move_px)
        move = max(0, move)
        if move <= 0:
            return score, (rival.pos.x, rival.pos.y)

        direction.scale_to_length(move)
        tx, ty = rival.pos.x + direction.x, rival.pos.y + direction.y
        return score, self._clamp(tx, ty, coords)


class PressAttacker(Behavior):
    """Avança em direção ao jogador humano mais próximo."""

    name = "press_attacker"

    def evaluate(self, rival, human_players, all_rivals, coords, context=None):
        if self._is_goalkeeper(rival):
            return 0.0, (rival.pos.x, rival.pos.y)

        if not human_players:
            return 0.0, (rival.pos.x, rival.pos.y)

        closest = min(human_players, key=lambda h: self._dist(rival, h))
        dist = self._dist(rival, closest)
        max_field = math.sqrt(coords.field_px_w ** 2 + coords.field_px_h ** 2)

        # Quanto mais perto, maior o score (inverso normalizado)
        score = max(0.0, 1.0 - (dist / max_field)) ** 0.8

        direction = pygame.Vector2(closest.pos.x - rival.pos.x,
                                   closest.pos.y - rival.pos.y)
        if direction.length() < 1:
            return score, (rival.pos.x, rival.pos.y)

        move = min(direction.length() - 16, coords.max_move_px)
        move = max(0, move)
        if move <= 0:
            return score, (rival.pos.x, rival.pos.y)

        direction.scale_to_length(move)
        tx, ty = rival.pos.x + direction.x, rival.pos.y + direction.y
        return score, self._clamp(tx, ty, coords)


class CoverSpace(Behavior):
    """Move para cobrir espaços vazios entre a defesa e o meio."""

    name = "cover_space"

    def evaluate(self, rival, human_players, all_rivals, coords, context=None):
        if self._is_goalkeeper(rival):
            return 0.0, (rival.pos.x, rival.pos.y)

        if not human_players:
            return 0.0, (rival.pos.x, rival.pos.y)

        # Centro de massa dos humanos
        avg_hx = sum(h.pos.x for h in human_players) / len(human_players)
        avg_hy = sum(h.pos.y for h in human_players) / len(human_players)

        # Ponto médio entre o rival e o centróide humano
        mid_x = (rival.pos.x + avg_hx) / 2
        mid_y = (rival.pos.y + avg_hy) / 2

        # Score baseado em quão longe o rival está desse ponto ideal
        dist_to_mid = math.sqrt((rival.pos.x - mid_x) ** 2 +
                                (rival.pos.y - mid_y) ** 2)
        max_move = coords.max_move_px
        score = min(1.0, dist_to_mid / (max_move * 3)) * 0.7

        direction = pygame.Vector2(mid_x - rival.pos.x, mid_y - rival.pos.y)
        if direction.length() < 1:
            return 0.1, (rival.pos.x, rival.pos.y)

        move = min(direction.length(), max_move)
        direction.scale_to_length(move)
        tx, ty = rival.pos.x + direction.x, rival.pos.y + direction.y
        return score, self._clamp(tx, ty, coords)


class FallBack(Behavior):
    """Recua em direção ao próprio gol para reforçar a defesa."""

    name = "fall_back"

    def evaluate(self, rival, human_players, all_rivals, coords, context=None):
        if self._is_goalkeeper(rival):
            return 0.0, (rival.pos.x, rival.pos.y)

        # Gol do rival fica no lado direito (x máximo do campo)
        goal_x = coords.origin_x + coords.field_px_w
        goal_y = coords.origin_y + coords.field_px_h / 2

        dist_to_goal = math.sqrt((rival.pos.x - goal_x) ** 2 +
                                 (rival.pos.y - goal_y) ** 2)

        # Quanto mais longe do gol, maior a urgência de recuar
        max_diag = math.sqrt(coords.field_px_w ** 2 + coords.field_px_h ** 2)
        score = max(0.0, dist_to_goal / max_diag)

        direction = pygame.Vector2(goal_x - rival.pos.x, goal_y - rival.pos.y)
        if direction.length() < 1:
            return 0.0, (rival.pos.x, rival.pos.y)

        # Recua parcialmente — não volta até o gol, para a ~40% do caminho
        move = min(direction.length() * 0.4, coords.max_move_px)
        direction.scale_to_length(move)
        tx, ty = rival.pos.x + direction.x, rival.pos.y + direction.y
        return score, self._clamp(tx, ty, coords)


class HoldFormation(Behavior):
    """Mantém a posição tática original da formação."""

    name = "hold_formation"

    def evaluate(self, rival, human_players, all_rivals, coords, context=None):
        if self._is_goalkeeper(rival):
            return 0.0, (rival.pos.x, rival.pos.y)

        # O jogador guarda sua posição original no target quando reseta turno
        # Aqui usamos a posição atual como referência de "casa"
        # Score é constante — funciona como âncora moderada
        score = 0.4

        # Movimento mínimo: leve ajuste aleatório próximo da posição
        angle = random.uniform(0, 2 * math.pi)
        jitter = coords.max_move_px * 0.15
        tx = rival.pos.x + math.cos(angle) * jitter
        ty = rival.pos.y + math.sin(angle) * jitter
        return score, self._clamp(tx, ty, coords)


class InterceptLane(Behavior):
    """Posiciona-se entre o atacante mais avançado e o gol."""

    name = "intercept_lane"

    def evaluate(self, rival, human_players, all_rivals, coords, context=None):
        if self._is_goalkeeper(rival):
            return 0.0, (rival.pos.x, rival.pos.y)

        if not human_players:
            return 0.0, (rival.pos.x, rival.pos.y)

        # Gol do rival (direita)
        goal_x = coords.origin_x + coords.field_px_w
        goal_y = coords.origin_y + coords.field_px_h / 2

        # Atacante humano mais avançado (mais próximo do gol rival)
        most_advanced = max(human_players, key=lambda h: h.pos.x)

        # Ponto ideal: entre o atacante e o gol, mais perto do atacante
        ideal_x = most_advanced.pos.x + (goal_x - most_advanced.pos.x) * 0.3
        ideal_y = most_advanced.pos.y + (goal_y - most_advanced.pos.y) * 0.2

        dist_to_ideal = math.sqrt((rival.pos.x - ideal_x) ** 2 +
                                  (rival.pos.y - ideal_y) ** 2)
        max_diag = math.sqrt(coords.field_px_w ** 2 + coords.field_px_h ** 2)
        score = min(1.0, dist_to_ideal / max_diag) * 0.85

        direction = pygame.Vector2(ideal_x - rival.pos.x, ideal_y - rival.pos.y)
        if direction.length() < 1:
            return 0.3, (rival.pos.x, rival.pos.y)

        move = min(direction.length(), coords.max_move_px)
        direction.scale_to_length(move)
        tx, ty = rival.pos.x + direction.x, rival.pos.y + direction.y
        return score, self._clamp(tx, ty, coords)


class SpreadWidth(Behavior):
    """Espalha lateralmente para evitar concentração de jogadores."""

    name = "spread_width"

    def evaluate(self, rival, human_players, all_rivals, coords, context=None):
        if self._is_goalkeeper(rival):
            return 0.0, (rival.pos.x, rival.pos.y)

        available = [r for r in all_rivals if r is not rival]
        if not available:
            return 0.1, (rival.pos.x, rival.pos.y)

        # Distância média para os companheiros
        avg_dist = sum(self._dist(rival, r) for r in available) / len(available)
        min_desired = coords.max_move_px * 2.5

        # Se está muito perto dos companheiros, precisa se espalhar
        if avg_dist >= min_desired:
            return 0.1, (rival.pos.x, rival.pos.y)

        score = max(0.0, 1.0 - avg_dist / min_desired) * 0.6

        # Move na direção oposta ao centróide dos companheiros
        cx = sum(r.pos.x for r in available) / len(available)
        cy = sum(r.pos.y for r in available) / len(available)
        direction = pygame.Vector2(rival.pos.x - cx, rival.pos.y - cy)

        if direction.length() < 1:
            angle = random.uniform(0, 2 * math.pi)
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))

        move = min(direction.length(), coords.max_move_px * 0.6)
        move = max(move, coords.max_move_px * 0.2)
        direction.scale_to_length(move)
        tx, ty = rival.pos.x + direction.x, rival.pos.y + direction.y
        return score, self._clamp(tx, ty, coords)


# Registro central de todos os comportamentos disponíveis
ALL_BEHAVIORS: list[Behavior] = [
    PressBallCarrier(),
    PressAttacker(),
    CoverSpace(),
    FallBack(),
    HoldFormation(),
    InterceptLane(),
    SpreadWidth(),
]
