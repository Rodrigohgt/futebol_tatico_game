"""Gerenciador de telas — FSM para transição entre estados do jogo.

Permite adicionar telas (menu, partida, elenco, mercado, etc.) sem
alterar o loop principal. Cada tela implementa a interface Screen.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pygame


class Screen(ABC):
    """Interface base para todas as telas do jogo."""

    @abstractmethod
    def on_enter(self, **kwargs):
        """Chamado quando a tela se torna ativa."""
        ...

    @abstractmethod
    def on_exit(self):
        """Chamado quando a tela deixa de ser ativa."""
        ...

    @abstractmethod
    def handle_event(self, event: pygame.event.Event):
        """Processa um evento de input."""
        ...

    @abstractmethod
    def update(self, dt: float):
        """Atualiza a lógica da tela."""
        ...

    @abstractmethod
    def render(self, surface: pygame.Surface):
        """Renderiza a tela."""
        ...


class ScreenManager:
    """Máquina de estados finita de telas."""

    def __init__(self):
        self._screens: dict[str, Screen] = {}
        self._active: Screen | None = None
        self._active_name: str = ""
        self._pending_switch: tuple[str, dict] | None = None

    @property
    def active_name(self) -> str:
        return self._active_name

    def register(self, name: str, screen: Screen):
        """Registra uma tela com um nome."""
        self._screens[name] = screen

    def switch(self, name: str, **kwargs):
        """Agenda troca de tela (aplicada no início do próximo frame)."""
        self._pending_switch = (name, kwargs)

    def _apply_switch(self):
        if self._pending_switch is None:
            return
        name, kwargs = self._pending_switch
        self._pending_switch = None

        if name not in self._screens:
            raise KeyError(f"Tela '{name}' não registrada")

        if self._active:
            self._active.on_exit()

        self._active = self._screens[name]
        self._active_name = name
        self._active.on_enter(**kwargs)

    def handle_event(self, event: pygame.event.Event):
        if self._active:
            self._active.handle_event(event)

    def update(self, dt: float):
        self._apply_switch()
        if self._active:
            self._active.update(dt)

    def render(self, surface: pygame.Surface):
        if self._active:
            self._active.render(surface)
