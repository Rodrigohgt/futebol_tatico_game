"""Controlador de alto nível da IA rival.

Orquestra a fase de decisão completa da IA, gerenciando:
- Budget de ações (movimentos + passes) por turno
- Pressão prioritária sobre o portador da bola
- Decisão tática de quantos jogadores mover
- Fase reativa (resposta a cada ação do player)
- Fase de turno (quando o player encerra o turno)
"""

from __future__ import annotations

import random

import pygame

from config import settings
from entities.player import Player
from entities.ball import Ball
from utils.coordinates import CoordinateSystem
from systems.rival_ai import RivalAI
from systems.field_context import FieldContext


class AIController:
    """Cérebro tático da equipe rival."""

    def __init__(self, rival_ai: RivalAI, coords: CoordinateSystem):
        self.ai = rival_ai
        self.coords = coords
        self.moves_remaining = settings.AI_MOVES_PER_TURN
        self.passes_remaining = settings.AI_PASSES_PER_TURN

    # ── Contexto ──

    def build_context(
        self,
        ball: Ball,
        human_players: list[Player],
        rival_players: list[Player],
    ) -> FieldContext:
        goal_x_rival = self.coords.origin_x + self.coords.field_px_w
        goal_y = self.coords.origin_y + self.coords.field_px_h / 2
        goal_x_human = self.coords.origin_x

        return FieldContext(
            ball_pos=ball.pos.copy(),
            ball_is_held=ball.is_held(),
            ball_owner=ball.owner,
            ball_owner_is_human=(ball.owner in human_players) if ball.owner else False,
            human_players=human_players,
            rival_players=rival_players,
            rival_goal_center=(goal_x_rival, goal_y),
            human_goal_center=(goal_x_human, goal_y),
        )

    # ── Reação a cada ação do player ──

    def react_to_move(
        self,
        ball: Ball,
        human_players: list[Player],
        rival_players: list[Player],
    ):
        """Resposta reativa: 1 movimento rival após cada ação do player."""
        if self.moves_remaining <= 0:
            return

        ctx = self.build_context(ball, human_players, rival_players)

        # Prioridade absoluta: pressionar o portador da bola
        if ctx.ball_owner_is_human and ctx.ball_is_held:
            moved = self._pressure_ball_carrier(ctx)
            if moved:
                self.moves_remaining -= 1
                return

        # Fallback: melhor ação tática via sistema de pesos
        moved = self.ai.react(rival_players, human_players, ctx)
        if moved:
            self.moves_remaining -= 1

    # ── Fase completa de turno da IA ──

    def execute_turn_phase(
        self,
        ball: Ball,
        human_players: list[Player],
        rival_players: list[Player],
    ):
        """Fase de decisão completa ao fim do turno do player.

        A IA decide quantos jogadores mover baseado no contexto:
        - Se a bola está em posse humana: move mais jogadores (defesa urgente)
        - Se a bola está livre ou em posse rival: move menos (economia tática)
        """
        ctx = self.build_context(ball, human_players, rival_players)

        # Calcula quantos jogadores a IA decide mover neste turno
        budget = self._calc_turn_budget(ctx)

        # 1) Pressão sobre portador da bola (se aplicável)
        if ctx.ball_owner_is_human and ctx.ball_is_held and budget > 0:
            if self._pressure_ball_carrier(ctx):
                budget -= 1

        # 2) Movimentos táticos restantes (react prioriza proximidade à bola)
        moved_count = 0

        for _ in range(budget):
            ctx = self.build_context(ball, human_players, rival_players)
            result = self.ai.react(rival_players, human_players, ctx)
            if result is None:
                break
            moved_count += 1

        return moved_count

    def calc_turn_budget(
        self,
        ball: Ball,
        human_players: list[Player],
        rival_players: list[Player],
    ) -> int:
        """Calcula e retorna o budget de ações para a fase de turno da IA."""
        ctx = self.build_context(ball, human_players, rival_players)
        return self._calc_turn_budget(ctx)

    def execute_single_action(
        self,
        ball: Ball,
        human_players: list[Player],
        rival_players: list[Player],
    ) -> Player | None:
        """Executa uma única ação da IA (pressão ou tática). Retorna o jogador movido."""
        ctx = self.build_context(ball, human_players, rival_players)

        # Prioridade: pressionar portador da bola
        if ctx.ball_owner_is_human and ctx.ball_is_held:
            moved = self._pressure_ball_carrier(ctx)
            if moved:
                return self._find_moved_player(ctx.rival_players)

        # Fallback: melhor ação tática
        result = self.ai.react(rival_players, human_players, ctx)
        return result

    def _find_moved_player(self, rival_players: list[Player]) -> Player | None:
        """Encontra o jogador que acabou de se mover (menor meters remaining)."""
        moved = [p for p in rival_players if not p.can_move() and p.info.position != "GK"]
        return moved[-1] if moved else None

    def reset_turn(self):
        self.moves_remaining = settings.AI_MOVES_PER_TURN
        self.passes_remaining = settings.AI_PASSES_PER_TURN

    # ── Pressão sobre o portador da bola ──

    def _pressure_ball_carrier(self, ctx: FieldContext) -> bool:
        """Move o rival mais próximo da bola em direção ao portador."""
        if ctx.ball_owner is None:
            return False

        available = [p for p in ctx.rival_players
                     if p.can_move() and p.info.position != "GK"]
        if not available:
            return False

        ball_target = ctx.ball_pos

        # Encontra o rival disponível mais próximo da bola
        closest = min(available, key=lambda p: p.pos.distance_to(ball_target))

        # Calcula destino: avança em direção à bola, para ~15px antes
        direction = pygame.Vector2(
            ball_target.x - closest.pos.x,
            ball_target.y - closest.pos.y,
        )
        dist = direction.length()
        if dist < 5:
            return False

        max_move = self.coords.max_move_px
        move_dist = min(dist - 15, max_move)
        move_dist = max(move_dist, 0)
        if move_dist <= 0:
            return False

        direction.scale_to_length(move_dist)
        tx = closest.pos.x + direction.x
        ty = closest.pos.y + direction.y

        bounds = self.coords.field_bounds()
        tx = max(bounds[0], min(tx, bounds[2]))
        ty = max(bounds[1], min(ty, bounds[3]))

        old_m = closest.move_meters_remaining
        closest.set_target((tx, ty))
        return closest.move_meters_remaining < old_m

    # ── Cálculo de budget tático ──

    def _calc_turn_budget(self, ctx: FieldContext) -> int:
        """Decide quantos jogadores a IA vai mover neste turno.

        Fatores:
        - Bola em posse humana → urgência alta → move 8-11
        - Bola livre → urgência média → move 5-8
        - Bola em posse rival → calma → move 3-6
        """
        available = sum(1 for p in ctx.rival_players if p.can_move())

        if ctx.ball_owner_is_human and ctx.ball_is_held:
            # Urgência defensiva
            min_moves = min(8, available)
            max_moves = available
        elif not ctx.ball_is_held:
            # Bola livre — disputa
            min_moves = min(5, available)
            max_moves = min(8, available)
        else:
            # IA tem a bola — reposicionamento calmo
            min_moves = min(3, available)
            max_moves = min(6, available)

        return random.randint(min_moves, max_moves)
