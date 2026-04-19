"""Tela de partida — wrapper do Game existente para integrar no ScreenManager.

Adapta o core/game.py para funcionar como uma Screen dentro do FSM,
mantendo compatibilidade total com o código existente.
"""

from __future__ import annotations

import pygame

from config import settings
from core.game import Game
from screens.screen_manager import Screen
from screens.ui_components import PauseOverlay


class MatchScreen(Screen):
    """Tela de partida — delega para o Game existente."""

    def __init__(self, screen_manager):
        self._sm = screen_manager
        self._game: Game | None = None
        self._event_queue: list[pygame.event.Event] = []
        self._pause_overlay = PauseOverlay(
            settings.WINDOW_WIDTH,
            settings.WINDOW_HEIGHT,
            on_resume=self._resume,
            on_main_menu=self._go_main_menu,
            on_quit=self._quit_game,
        )

    def on_enter(self, **kwargs):
        """Inicializa uma nova partida reutilizando a surface do display."""
        surface = pygame.display.get_surface()
        self._game = Game(surface=surface)
        self._event_queue.clear()
        self._pause_overlay.hide()

    def on_exit(self):
        """Limpa recursos da partida."""
        self._game = None
        self._event_queue.clear()

    def handle_event(self, event: pygame.event.Event):
        """Acumula eventos para o Game processar no update."""
        # ESC abre o overlay quando o jogo não está em pass_mode
        if (event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
                and not self._pause_overlay.visible):
            if self._game and self._game.passer.pass_mode:
                self._event_queue.append(event)
            else:
                self._pause_overlay.show()
            return

        # Overlay consome todos os eventos enquanto visível
        if self._pause_overlay.handle_event(event):
            return

        self._event_queue.append(event)

    def update(self, dt: float):
        if self._game is None:
            return
        # Não atualiza o jogo enquanto pausado
        if self._pause_overlay.visible:
            self._event_queue.clear()
            return
        events = self._event_queue.copy()
        self._event_queue.clear()
        self._game._process_input(events)
        self._game._update()

        if not self._game.running:
            self._sm.switch("main_menu")

    def render(self, surface: pygame.Surface):
        if self._game is None:
            return
        self._game._render()
        self._pause_overlay.render(surface)

    # ── Callbacks do PauseOverlay ──

    def _resume(self):
        pass

    def _go_main_menu(self):
        self._sm.switch("main_menu")

    def _quit_game(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
