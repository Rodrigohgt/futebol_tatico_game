"""Snapshot do estado de campo para decisões da IA.

Passado como parâmetro único aos comportamentos, evitando
acoplamento direto entre IA e entidades do jogo.

Usa TYPE_CHECKING para referências tipadas sem importar em runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from entities.player import Player


@dataclass
class FieldContext:
    """Estado do campo em um dado instante — imutável por frame."""
    ball_pos: pygame.Vector2
    ball_is_held: bool
    ball_owner: Player | None
    ball_owner_is_human: bool
    human_players: list[Player]
    rival_players: list[Player]
    rival_goal_center: tuple[float, float]
    human_goal_center: tuple[float, float]
