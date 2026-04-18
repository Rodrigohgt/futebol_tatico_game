"""Tela de partida — wrapper do Game existente para integrar no ScreenManager.

Adapta o core/game.py para funcionar como uma Screen dentro do FSM,
mantendo compatibilidade total com o código existente.
"""

from __future__ import annotations

import pygame

from config import settings
from core.game import Game
from screens.screen_manager import Screen


class MatchScreen(Screen):
    """Tela de partida — delega para o Game existente."""

    def __init__(self, screen_manager):
        self._sm = screen_manager
        self._game: Game | None = None
        self._event_queue: list[pygame.event.Event] = []

    def on_enter(self, **kwargs):
        """Inicializa uma nova partida reutilizando a surface do display."""
        surface = pygame.display.get_surface()
        self._game = Game(surface=surface)
        self._event_queue.clear()

    def on_exit(self):
        """Limpa recursos da partida."""
        self._game = None
        self._event_queue.clear()

    def handle_event(self, event: pygame.event.Event):
        """Acumula eventos para o Game processar no update."""
        self._event_queue.append(event)

    def update(self, dt: float):
        if self._game is None:
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
