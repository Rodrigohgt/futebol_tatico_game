"""Popup de informações do jogador exibido ao manter o mouse sobre ele."""

import pygame
import time

from config import settings
from entities.player import Player


class PlayerPopup:
    """Tooltip que aparece após hover prolongado sobre um jogador."""

    POPUP_W = 230
    POPUP_H = 385
    PADDING = 12
    BAR_H = 10
    BAR_W = 120
    LINE_H = 22

    def __init__(self):
        self._hover_player: Player | None = None
        self._hover_start: float = 0.0
        self._visible = False

        self._font_header = pygame.font.SysFont(None, 22, bold=True)
        self._font_body = pygame.font.SysFont(None, 19)
        self._font_small = pygame.font.SysFont(None, 17)

    def update(self, mouse_pos: tuple[int, int], players: list[Player]):
        hovered = None
        for p in players:
            if p.contains_point(mouse_pos):
                hovered = p
                break

        if hovered is None:
            self._reset()
            return

        if hovered is not self._hover_player:
            self._hover_player = hovered
            self._hover_start = time.time()
            self._visible = False
            return

        elapsed = time.time() - self._hover_start
        if elapsed >= settings.POPUP_HOVER_DELAY:
            self._visible = True

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        if not self._visible or self._hover_player is None:
            return

        p = self._hover_player
        x, y = self._calc_position(surface, mouse_pos)

        # Fundo
        popup_surf = pygame.Surface((self.POPUP_W, self.POPUP_H), pygame.SRCALPHA)
        pygame.draw.rect(popup_surf, settings.POPUP_BG,
                         (0, 0, self.POPUP_W, self.POPUP_H), border_radius=8)
        pygame.draw.rect(popup_surf, settings.POPUP_BORDER,
                         (0, 0, self.POPUP_W, self.POPUP_H), 2, border_radius=8)

        pad = self.PADDING
        cy = pad

        # Nome e número
        header = f"#{p.info.number}  {p.info.name}"
        h_surf = self._font_header.render(header, True, settings.POPUP_HEADER)
        popup_surf.blit(h_surf, (pad, cy))
        cy += self.LINE_H + 2

        # Posição / Idade / Status
        sub = f"{p.info.position}  •  {p.info.age} anos  •  {p.info.status}"
        s_surf = self._font_small.render(sub, True, (170, 170, 180))
        popup_surf.blit(s_surf, (pad, cy))
        cy += self.LINE_H + 6

        # Separador
        pygame.draw.line(popup_surf, (80, 80, 100),
                         (pad, cy), (self.POPUP_W - pad, cy), 1)
        cy += 8

        # Barras de atributos
        stats_data = [
            ("FIN", p.stats.finishing),
            ("PAS", p.stats.passing),
            ("DRI", p.stats.dribbling),
            ("DEF", p.stats.defending),
            ("CAB", p.stats.heading),
            ("COM", p.stats.composure),
            ("POS", p.stats.positioning),
            ("VIS", p.stats.vision),
            ("VIG", p.stats.stamina),
            ("VEL", p.stats.pace),
        ]
        for label, value in stats_data:
            self._draw_stat_bar(popup_surf, pad, cy, label, value)
            cy += self.LINE_H

        # Overall
        cy += 4
        ovr_label = f"OVR: {p.stats.overall}"
        ovr_surf = self._font_header.render(ovr_label, True, self._stat_color(p.stats.overall))
        popup_surf.blit(ovr_surf, (pad, cy))
        cy += self.LINE_H + 4

        # Separador antes de movimento
        pygame.draw.line(popup_surf, (80, 80, 100),
                         (pad, cy), (self.POPUP_W - pad, cy), 1)
        cy += 6

        # Movimento disponível
        pts = p.move_meters_remaining
        max_pts = p.max_move_meters
        ratio = p.move_ratio
        mov_text = f"MOV: {pts:.0f}/{max_pts:.0f}M"
        mov_surf = self._font_body.render(mov_text, True, settings.POPUP_TEXT)
        popup_surf.blit(mov_surf, (pad, cy))

        # Barra de movimento
        bar_x = pad
        bar_y_pos = cy + 20
        bar_w = self.POPUP_W - pad * 2
        bar_h = self.BAR_H
        pygame.draw.rect(popup_surf, settings.POPUP_STAT_BAR_BG,
                         (bar_x, bar_y_pos, bar_w, bar_h), border_radius=3)
        fill_w = max(0, int(bar_w * ratio))
        if ratio > 0.6:
            mv_color = (60, 200, 80)
        elif ratio > 0.3:
            mv_color = (220, 200, 50)
        else:
            mv_color = (220, 70, 50)
        if fill_w > 0:
            pygame.draw.rect(popup_surf, mv_color,
                             (bar_x, bar_y_pos, fill_w, bar_h), border_radius=3)

        surface.blit(popup_surf, (x, y))

    def _draw_stat_bar(self, surface, x, y, label, value):
        # Label
        lbl = self._font_body.render(label, True, settings.POPUP_TEXT)
        surface.blit(lbl, (x, y))

        # Barra de fundo
        bar_x = x + 42
        pygame.draw.rect(surface, settings.POPUP_STAT_BAR_BG,
                         (bar_x, y + 2, self.BAR_W, self.BAR_H), border_radius=3)

        # Barra de preenchimento
        fill_w = int(self.BAR_W * value / 100)
        color = self._stat_color(value)
        pygame.draw.rect(surface, color,
                         (bar_x, y + 2, fill_w, self.BAR_H), border_radius=3)

        # Valor numérico
        val_surf = self._font_small.render(str(value), True, settings.POPUP_TEXT)
        surface.blit(val_surf, (bar_x + self.BAR_W + 8, y + 1))

    @staticmethod
    def _stat_color(value: int) -> tuple[int, int, int]:
        if value >= 80:
            return (60, 180, 80)
        if value >= 60:
            return (80, 160, 220)
        if value >= 40:
            return (220, 180, 50)
        return (200, 70, 70)

    def _calc_position(self, surface, mouse_pos):
        mx, my = mouse_pos
        x = mx + 20
        y = my - self.POPUP_H // 2

        sw, sh = surface.get_size()
        if x + self.POPUP_W > sw - 10:
            x = mx - self.POPUP_W - 20
        if y < 10:
            y = 10
        if y + self.POPUP_H > sh - 10:
            y = sh - self.POPUP_H - 10
        return x, y

    def _reset(self):
        self._hover_player = None
        self._hover_start = 0.0
        self._visible = False
