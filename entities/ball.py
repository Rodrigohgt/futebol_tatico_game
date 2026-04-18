"""Entidade da bola com física vetorial e sistema de estados.

Estados:
- HELD: em posse de um jogador (segue o atleta com offset)
- TRAVELING: em movimento livre (passe, chute, rebote)
- FREE: parada no campo, sem dono
"""

from __future__ import annotations

import math
import random
from enum import Enum, auto

import pygame

from config import settings
from utils.helpers import clamp


class BallState(Enum):
    HELD = auto()
    TRAVELING = auto()
    FREE = auto()


class Ball:
    """Bola com física de velocidade + fricção e sistema de posse."""

    def __init__(self, x: float, y: float, coord_system):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.coord_system = coord_system

        self.state = BallState.FREE
        self.owner = None

        self.radius = settings.BALL_RADIUS
        self.friction = settings.BALL_FRICTION
        self.min_speed = settings.BALL_MIN_SPEED

    def give_to(self, player):
        self.owner = player
        self.state = BallState.HELD
        self.vel = pygame.Vector2(0, 0)

    def release(self):
        self.owner = None
        self.state = BallState.FREE
        self.vel = pygame.Vector2(0, 0)

    def is_held(self) -> bool:
        return self.state == BallState.HELD

    def is_moving(self) -> bool:
        return self.state == BallState.TRAVELING

    def is_free(self) -> bool:
        return self.state == BallState.FREE

    def kick_towards(self, target: tuple[float, float], speed: float,
                     success: bool = True, error_angle: float = 0.0):
        direction = pygame.Vector2(target[0] - self.pos.x,
                                   target[1] - self.pos.y)
        if direction.length() < 1:
            return

        direction.normalize_ip()

        if not success and error_angle != 0:
            angle = math.atan2(direction.y, direction.x) + error_angle
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))

        self.vel = direction * speed
        self.owner = None
        self.state = BallState.TRAVELING

    def update(self):
        if self.state == BallState.HELD and self.owner is not None:
            self._follow_owner()
            return

        if self.state == BallState.TRAVELING:
            self._apply_physics()

    def _follow_owner(self):
        owner = self.owner
        offset_dist = settings.BALL_CARRY_OFFSET
        if owner.facing.length_squared() > 0.01:
            offset = owner.facing * offset_dist
        else:
            offset = pygame.Vector2(offset_dist, 0)
        self.pos = owner.pos + offset

    def _apply_physics(self):
        self.pos += self.vel

        speed = self.vel.length()
        if speed > self.min_speed:
            self.vel *= self.friction
        else:
            self.vel = pygame.Vector2(0, 0)
            self.state = BallState.FREE

        bounds = self.coord_system.field_bounds()
        if self.pos.x <= bounds[0]:
            self.pos.x = bounds[0]
            self.vel.x = abs(self.vel.x) * 0.4
        elif self.pos.x >= bounds[2]:
            self.pos.x = bounds[2]
            self.vel.x = -abs(self.vel.x) * 0.4

        if self.pos.y <= bounds[1]:
            self.pos.y = bounds[1]
            self.vel.y = abs(self.vel.y) * 0.4
        elif self.pos.y >= bounds[3]:
            self.pos.y = bounds[3]
            self.vel.y = -abs(self.vel.y) * 0.4

    def check_pickup(self, players: list) -> bool:
        if self.state == BallState.HELD:
            return False

        pickup_dist = settings.BALL_PICKUP_RADIUS

        # Ordena por distância — jogador mais próximo tem prioridade
        ranked = sorted(players, key=lambda p: self.pos.distance_to(p.pos))
        for p in ranked:
            dist = self.pos.distance_to(p.pos)
            if dist <= pickup_dist:
                self.give_to(p)
                return True
        return False

    def draw(self, surface: pygame.Surface):
        BallRenderer.draw(surface, self)

    def draw_pass_preview(self, surface: pygame.Surface,
                          mouse_pos: tuple[int, int],
                          power: float = 0.0):
        BallRenderer.draw_pass_preview(surface, self, mouse_pos, power)


# ── Renderização isolada ──

class BallRenderer:
    """Renderização pura da bola — não modifica estado."""

    @staticmethod
    def draw(surface: pygame.Surface, ball: Ball):
        cx, cy = int(ball.pos.x), int(ball.pos.y)
        r = ball.radius

        shadow_surf = pygame.Surface((r * 2 + 4, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 40), shadow_surf.get_rect())
        surface.blit(shadow_surf, (cx - r - 2, cy + r))

        pygame.draw.circle(surface, settings.BALL_COLOR, (cx, cy), r)
        pygame.draw.circle(surface, settings.BALL_BORDER_COLOR, (cx, cy), r, 1)

        detail_color = settings.BALL_DETAIL_COLOR
        pygame.draw.line(surface, detail_color,
                         (cx - r // 2, cy - r // 3),
                         (cx + r // 2, cy - r // 3), 1)
        pygame.draw.line(surface, detail_color,
                         (cx - r // 3, cy + r // 4),
                         (cx + r // 3, cy + r // 4), 1)

    @staticmethod
    def draw_pass_preview(surface: pygame.Surface, ball: Ball,
                          mouse_pos: tuple[int, int],
                          power: float = 0.0):
        if not ball.is_held() or ball.owner is None:
            return

        start = (int(ball.pos.x), int(ball.pos.y))
        end = mouse_pos

        direction = pygame.Vector2(end[0] - start[0], end[1] - start[1])
        length = direction.length()
        if length < 5:
            return

        direction.normalize_ip()
        dash_len = 8
        gap_len = 6
        traveled = 0.0

        # Cor e espessura baseadas na força
        if power > 0:
            t = min(1.0, power)
            r = int(100 + 155 * t)
            g = int(255 - 155 * t)
            color = (r, g, 60, 220)
            thickness = int(2 + t * 2)
        else:
            color = settings.PASS_PREVIEW_COLOR
            thickness = 2

        while traveled < length:
            seg_start = (
                start[0] + direction.x * traveled,
                start[1] + direction.y * traveled,
            )
            seg_end_dist = min(traveled + dash_len, length)
            seg_end = (
                start[0] + direction.x * seg_end_dist,
                start[1] + direction.y * seg_end_dist,
            )
            pygame.draw.line(surface, color,
                             seg_start, seg_end, thickness)
            traveled += dash_len + gap_len

        pygame.draw.circle(surface, color, end, 5 + int(power * 2), 2)
