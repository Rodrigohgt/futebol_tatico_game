"""Barra de força para passes e chutes.

Componente de UI reutilizável que exibe uma barra de carregamento
durante ações que requerem controle de força.
"""

from __future__ import annotations

import pygame

from config import settings


class PowerBar:
    """Barra de força visual com estado de carregamento."""

    def __init__(self):
        self.charging = False
        self.power = 0.0        # 0.0 a 1.0
        self._charge_speed = settings.PASS_CHARGE_SPEED

        # Dimensões e posição (lateral direita, acima do HUD)
        self.bar_w = settings.POWER_BAR_WIDTH
        self.bar_h = settings.POWER_BAR_HEIGHT
        self.x = settings.WINDOW_WIDTH - self.bar_w - 20
        self.y = settings.WINDOW_HEIGHT - settings.HUD_BOTTOM_HEIGHT - self.bar_h - 16

        self._font = pygame.font.SysFont(None, 18, bold=True)

    def start_charge(self):
        self.charging = True
        self.power = 0.0

    def stop_charge(self) -> float:
        """Para o carregamento e retorna a força acumulada (0-1)."""
        self.charging = False
        final = self.power
        self.power = 0.0
        return final

    def cancel(self):
        self.charging = False
        self.power = 0.0

    def update(self):
        if not self.charging:
            return
        self.power = min(1.0, self.power + self._charge_speed)

    def draw(self, surface: pygame.Surface):
        if not self.charging and self.power <= 0:
            return

        x, y, w, h = self.x, self.y, self.bar_w, self.bar_h

        # Fundo
        bg_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (20, 20, 30, 200), (0, 0, w, h),
                         border_radius=4)
        surface.blit(bg_surf, (x, y))

        # Barra de preenchimento (de baixo para cima)
        inner_margin = 3
        inner_w = w - inner_margin * 2
        inner_max_h = h - inner_margin * 2
        fill_h = int(inner_max_h * self.power)

        if fill_h > 0:
            fill_y = y + inner_margin + (inner_max_h - fill_h)
            color = self._power_color()
            pygame.draw.rect(surface, color,
                             (x + inner_margin, fill_y, inner_w, fill_h),
                             border_radius=3)

        # Borda
        pygame.draw.rect(surface, (120, 130, 150), (x, y, w, h), 2,
                         border_radius=4)

        # Percentual
        pct = int(self.power * 100)
        txt = self._font.render(f"{pct}%", True, (220, 220, 230))
        txt_rect = txt.get_rect(centerx=x + w // 2, top=y + h + 4)
        surface.blit(txt, txt_rect)

    def _power_color(self) -> tuple[int, int, int]:
        if self.power < 0.4:
            # Verde → amarelo
            t = self.power / 0.4
            return (int(60 + 160 * t), int(200 - 60 * t), 60)
        elif self.power < 0.75:
            # Amarelo → laranja
            t = (self.power - 0.4) / 0.35
            return (int(220 + 30 * t), int(140 - 70 * t), 40)
        else:
            # Laranja → vermelho
            t = (self.power - 0.75) / 0.25
            return (int(250), int(70 - 50 * t), int(40 - 20 * t))
