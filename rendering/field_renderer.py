"""Renderização do campo de futebol com medidas oficiais FIFA."""

import math
import pygame

from config import settings, field_specs
from utils.coordinates import CoordinateSystem


class FieldRenderer:
    """Desenha o campo completo: grama, linhas e gols."""

    def __init__(self, coord: CoordinateSystem):
        self.c = coord
        self._stripe_w = coord.field_px_w / settings.GRASS_STRIPE_COUNT
        self._line_width = 3
        self._post_width = 4

    def draw(self, surface: pygame.Surface):
        self._draw_grass(surface)
        self._draw_lines(surface)
        self._draw_goals(surface)

    # ── Grama ──

    def _draw_grass(self, surface: pygame.Surface):
        surface.fill(settings.GRASS_DARK)
        for i in range(settings.GRASS_STRIPE_COUNT):
            color = settings.GRASS_LIGHT if i % 2 == 0 else settings.GRASS_DARK
            x = self.c.origin_x + i * self._stripe_w
            pygame.draw.rect(
                surface, color,
                (x, self.c.origin_y, self._stripe_w + 1, self.c.field_px_h),
            )

    # ── Linhas ──

    def _draw_lines(self, surface: pygame.Surface):
        W = settings.WHITE
        lw = self._line_width
        fs = field_specs
        c = self.c

        # Contorno
        pygame.draw.rect(surface, W,
                         (c.origin_x, c.origin_y, c.field_px_w, c.field_px_h), lw)

        # Meio-campo
        mx = c.m2px_x(fs.FIELD_LENGTH / 2)
        pygame.draw.line(surface, W,
                         (mx, c.origin_y), (mx, c.origin_y + c.field_px_h), lw)

        # Círculo central
        cr = int(c.m2px_w(fs.CENTER_CIRCLE_RADIUS))
        cx_px = int(c.m2px_x(fs.FIELD_LENGTH / 2))
        cy_px = int(c.m2px_y(fs.FIELD_WIDTH / 2))
        pygame.draw.circle(surface, W, (cx_px, cy_px), cr, lw)
        pygame.draw.circle(surface, W, (cx_px, cy_px), 5)

        # Áreas e meias-luas (esquerda e direita)
        self._draw_penalty_area(surface, "left")
        self._draw_penalty_area(surface, "right")

        # Escanteios
        self._draw_corner_arcs(surface)

    def _draw_penalty_area(self, surface: pygame.Surface, side: str):
        W = settings.WHITE
        lw = self._line_width
        fs = field_specs
        c = self.c

        # Grande área
        pa_w = c.m2px_w(fs.PENALTY_AREA_LENGTH)
        pa_h = c.m2px_h(fs.PENALTY_AREA_WIDTH)
        pa_y = c.m2px_y((fs.FIELD_WIDTH - fs.PENALTY_AREA_WIDTH) / 2)

        # Pequena área
        ga_w = c.m2px_w(fs.GOAL_AREA_LENGTH)
        ga_h = c.m2px_h(fs.GOAL_AREA_WIDTH)
        ga_y = c.m2px_y((fs.FIELD_WIDTH - fs.GOAL_AREA_WIDTH) / 2)

        # Pênalti
        ps_y = int(c.m2px_y(fs.FIELD_WIDTH / 2))
        arc_r = int(c.m2px_w(fs.CENTER_CIRCLE_RADIUS))

        if side == "left":
            pygame.draw.rect(surface, W, (c.origin_x, pa_y, pa_w, pa_h), lw)
            pygame.draw.rect(surface, W, (c.origin_x, ga_y, ga_w, ga_h), lw)
            ps_x = int(c.m2px_x(fs.PENALTY_SPOT_DISTANCE))
            pygame.draw.circle(surface, W, (ps_x, ps_y), 5)
            self._draw_half_moon(surface, ps_x, ps_y, arc_r,
                                 c.origin_x + pa_w, side="left")
        else:
            pa_x = c.m2px_x(fs.FIELD_LENGTH - fs.PENALTY_AREA_LENGTH)
            ga_x = c.m2px_x(fs.FIELD_LENGTH - fs.GOAL_AREA_LENGTH)
            pygame.draw.rect(surface, W, (pa_x, pa_y, pa_w, pa_h), lw)
            pygame.draw.rect(surface, W, (ga_x, ga_y, ga_w, ga_h), lw)
            ps_x = int(c.m2px_x(fs.FIELD_LENGTH - fs.PENALTY_SPOT_DISTANCE))
            pygame.draw.circle(surface, W, (ps_x, ps_y), 5)
            self._draw_half_moon(surface, ps_x, ps_y, arc_r, pa_x, side="right")

    def _draw_half_moon(self, surface, cx, cy, r, edge_x, side):
        W = settings.WHITE
        lw = self._line_width
        steps = 60

        ratio = (edge_x - cx) / r if side == "left" else (cx - edge_x) / r
        ratio = max(-1.0, min(1.0, ratio))
        start = math.acos(ratio)

        points = []
        for i in range(steps + 1):
            angle = -start + (2 * start) * i / steps
            if side == "right":
                angle = math.pi - start + (2 * start) * i / steps
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            if (side == "left" and px >= edge_x) or (side == "right" and px <= edge_x):
                points.append((px, py))

        if len(points) > 1:
            pygame.draw.lines(surface, W, False, points, lw)

    def _draw_corner_arcs(self, surface: pygame.Surface):
        W = settings.WHITE
        lw = self._line_width
        cr = int(self.c.m2px_w(field_specs.CORNER_ARC_RADIUS))
        ox, oy = self.c.origin_x, self.c.origin_y
        fw, fh = self.c.field_px_w, self.c.field_px_h
        pi = math.pi

        arcs = [
            (ox - cr, oy - cr, -pi / 2, 0),
            (ox + fw - cr, oy - cr, pi, pi * 1.5),
            (ox - cr, oy + fh - cr, 0, pi / 2),
            (ox + fw - cr, oy + fh - cr, pi / 2, pi),
        ]
        for x, y, a1, a2 in arcs:
            pygame.draw.arc(surface, W, (x, y, cr * 2, cr * 2), a1, a2, lw)

    # ── Gols ──

    def _draw_goals(self, surface: pygame.Surface):
        self._draw_single_goal(surface, "left")
        self._draw_single_goal(surface, "right")

    def _draw_single_goal(self, surface: pygame.Surface, side: str):
        c = self.c
        fs = field_specs
        W = settings.WHITE
        pw = self._post_width

        goal_h = c.m2px_h(fs.GOAL_WIDTH)
        goal_d = c.m2px_w(fs.GOAL_DEPTH)
        goal_y = c.m2px_y((fs.FIELD_WIDTH - fs.GOAL_WIDTH) / 2)

        if side == "left":
            gx = c.origin_x - goal_d
            far_x = gx
            line_x = c.origin_x
        else:
            gx = c.origin_x + c.field_px_w
            far_x = gx + goal_d
            line_x = gx

        # Rede
        for i in range(11):
            frac = i / 10
            y = goal_y + frac * goal_h
            pygame.draw.line(surface, settings.GOAL_NET_COLOR,
                             (min(gx, far_x), y), (max(gx, far_x), y), 1)
        step = 8
        for i in range(int(goal_d) // step + 1):
            x = min(gx, far_x) + i * step
            if x <= max(gx, far_x):
                pygame.draw.line(surface, settings.GOAL_NET_COLOR,
                                 (x, goal_y), (x, goal_y + goal_h), 1)

        # Travessões
        pygame.draw.line(surface, W, (min(gx, far_x), goal_y),
                         (max(gx, far_x), goal_y), pw)
        pygame.draw.line(surface, W, (min(gx, far_x), goal_y + goal_h),
                         (max(gx, far_x), goal_y + goal_h), pw)
        # Poste traseiro
        pygame.draw.line(surface, settings.GOAL_POST_COLOR,
                         (far_x, goal_y), (far_x, goal_y + goal_h), pw)
