"""Elementos de interface: HUD inferior, botões de ação, painel de turno."""

import pygame

from config import settings


class Button:
    """Botão clicável genérico com cores customizáveis e estado ativo."""

    def __init__(self, x, y, w, h, text,
                 idle_color=settings.BUTTON_IDLE,
                 hover_color=settings.BUTTON_HOVER,
                 border_color=settings.BUTTON_BORDER,
                 active_color=None,
                 active_hover_color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.idle_color = idle_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.active_color = active_color
        self.active_hover_color = active_hover_color
        self.hovered = False
        self.active = False
        self._font = pygame.font.SysFont(None, 26, bold=True)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface):
        if self.active and self.active_color:
            color = (self.active_hover_color or self.active_color) if self.hovered else self.active_color
            border = settings.WHITE
        elif self.hovered:
            color = self.hover_color
            border = self.border_color
        else:
            color = self.idle_color
            border = self.border_color

        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=8)

        txt = self._font.render(self.text, True, settings.BUTTON_TEXT)
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)


class UIRenderer:
    """Gerencia o HUD inferior e todos os elementos de interface."""

    def __init__(self):
        sw = settings.WINDOW_WIDTH
        sh = settings.WINDOW_HEIGHT
        hud_h = settings.HUD_BOTTOM_HEIGHT

        # Área do HUD inferior
        self.hud_rect = pygame.Rect(0, sh - hud_h, sw, hud_h)

        # Botões dentro do HUD
        btn_w, btn_h = 160, 42
        btn_y = sh - hud_h + (hud_h - btn_h) // 2
        margin = 24

        self.btn_finish = Button(
            margin, btn_y, btn_w, btn_h, "Finalizar",
            idle_color=settings.BTN_FINISH_COLOR,
            hover_color=settings.BTN_FINISH_HOVER,
        )

        btn_small_w = 100
        self.btn_reset = Button(
            margin + btn_w + 16, btn_y, btn_small_w, btn_h, "Reset",
            idle_color=settings.BTN_RESET_COLOR,
            hover_color=settings.BTN_RESET_HOVER,
        )

        self.btn_pass_ball = Button(
            (sw - btn_w) // 2, btn_y, btn_w, btn_h, "Tocar",
            idle_color=settings.BTN_PASS_BALL_COLOR,
            hover_color=settings.BTN_PASS_BALL_HOVER,
            active_color=settings.BTN_PASS_BALL_ACTIVE,
            active_hover_color=settings.BTN_PASS_BALL_ACTIVE_HOVER,
        )
        self.btn_end_turn = Button(
            sw - btn_w - margin, btn_y, btn_w, btn_h, "Passar turno",
            idle_color=settings.BTN_END_TURN_COLOR,
            hover_color=settings.BTN_END_TURN_HOVER,
        )

        self._all_buttons = [self.btn_finish, self.btn_reset, self.btn_pass_ball, self.btn_end_turn]
        self._font_turn = pygame.font.SysFont(None, 24, bold=True)
        self._font_info = pygame.font.SysFont(None, 18)
        self._font_strategy = pygame.font.SysFont(None, 18)

    def update(self, mouse_pos):
        for btn in self._all_buttons:
            btn.update(mouse_pos)

    def draw(self, surface: pygame.Surface, turn: int, moved_count: int,
             total: int, strategy_name: str = ""):
        self._draw_hud_bar(surface)

        for btn in self._all_buttons:
            btn.draw(surface)

        self._draw_turn_panel(surface, turn, moved_count, total, strategy_name)

    def _draw_hud_bar(self, surface: pygame.Surface):
        pygame.draw.rect(surface, settings.HUD_BG, self.hud_rect)
        # Linha superior da borda
        pygame.draw.line(
            surface, settings.HUD_BORDER_COLOR,
            (0, self.hud_rect.top), (settings.WINDOW_WIDTH, self.hud_rect.top),
            settings.HUD_BORDER_WIDTH,
        )

    def _draw_turn_panel(self, surface, turn, moved, total, strategy_name):
        panel_w, panel_h = 210, 54
        px = settings.WINDOW_WIDTH - panel_w - 12
        py = 6

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, settings.TURN_COUNTER_BG,
                         (0, 0, panel_w, panel_h), border_radius=8)

        line1 = self._font_turn.render(f"Turno {turn}", True, settings.TURN_LABEL_COLOR)
        info_parts = f"Movidos: {moved}/{total}"
        if strategy_name:
            info_parts += f"  •  IA: {strategy_name}"
        line2 = self._font_info.render(info_parts, True, (170, 170, 180))

        panel.blit(line1, (12, 6))
        panel.blit(line2, (12, 30))
        surface.blit(panel, (px, py))
