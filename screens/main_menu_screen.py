"""Tela de menu principal."""

from __future__ import annotations

import pygame

from config import settings
from screens.screen_manager import Screen


class MainMenuScreen(Screen):
    """Menu principal com opções de jogo."""

    def __init__(self, screen_manager):
        self._sm = screen_manager
        self._font_title = None
        self._font_option = None
        self._font_sub = None
        self._options = [
            ("Jogar Partida", "pre_match"),
            ("Sair", "quit"),
        ]
        self._selected = 0

    def on_enter(self, **kwargs):
        if self._font_title is None:
            self._font_title = pygame.font.SysFont(None, 64, bold=True)
            self._font_option = pygame.font.SysFont(None, 36)
            self._font_sub = pygame.font.SysFont(None, 22)

    def on_exit(self):
        pass

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._selected = (self._selected - 1) % len(self._options)
            elif event.key == pygame.K_DOWN:
                self._selected = (self._selected + 1) % len(self._options)
            elif event.key == pygame.K_RETURN:
                self._activate()
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._check_mouse_click(event.pos)

        elif event.type == pygame.MOUSEMOTION:
            self._check_mouse_hover(event.pos)

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        sw, sh = settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT

        # Fundo
        surface.fill((20, 30, 20))

        # Gradiente sutil no fundo
        for i in range(sh):
            alpha = int(15 + 10 * (i / sh))
            pygame.draw.line(surface, (alpha, alpha + 10, alpha), (0, i), (sw, i))

        # Título
        title = self._font_title.render("Football Tactics", True, (220, 220, 200))
        title_rect = title.get_rect(center=(sw // 2, sh // 4))
        surface.blit(title, title_rect)

        # Subtítulo
        sub = self._font_sub.render(
            "Jogo tático por turnos", True, (140, 150, 130)
        )
        sub_rect = sub.get_rect(center=(sw // 2, sh // 4 + 45))
        surface.blit(sub, sub_rect)

        # Opções
        start_y = sh // 2
        for i, (label, _) in enumerate(self._options):
            color = (255, 220, 80) if i == self._selected else (180, 180, 170)
            text = self._font_option.render(label, True, color)
            rect = text.get_rect(center=(sw // 2, start_y + i * 50))
            self._options_rects = getattr(self, '_options_rects', [])
            if len(self._options_rects) <= i:
                self._options_rects.append(rect)
            else:
                self._options_rects[i] = rect

            # Indicador de seleção
            if i == self._selected:
                indicator = self._font_option.render("▸ ", True, (255, 220, 80))
                surface.blit(indicator, (rect.left - 30, rect.top))

            surface.blit(text, rect)

        # Versão
        ver = self._font_sub.render("v0.1.0", True, (80, 80, 80))
        surface.blit(ver, (sw - 70, sh - 30))

    def _activate(self):
        _, action = self._options[self._selected]
        if action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        else:
            self._sm.switch(action)

    def _check_mouse_click(self, pos):
        rects = getattr(self, '_options_rects', [])
        for i, rect in enumerate(rects):
            expanded = rect.inflate(40, 10)
            if expanded.collidepoint(pos):
                self._selected = i
                self._activate()
                return

    def _check_mouse_hover(self, pos):
        rects = getattr(self, '_options_rects', [])
        for i, rect in enumerate(rects):
            expanded = rect.inflate(40, 10)
            if expanded.collidepoint(pos):
                self._selected = i
                return
