"""Barramento de eventos para desacoplamento entre sistemas.

Permite que sistemas emitam eventos sem conhecer os listeners.
Usado para comunicar ações de gameplay (gol, falta, cartão)
entre systems, services e rendering sem acoplamento direto.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Any


class EventBus:
    """Pub/Sub global leve para eventos de gameplay."""

    _listeners: dict[str, list[Callable]] = defaultdict(list)

    @classmethod
    def on(cls, event_type: str, callback: Callable):
        """Registra um listener para um tipo de evento."""
        cls._listeners[event_type].append(callback)

    @classmethod
    def off(cls, event_type: str, callback: Callable):
        """Remove um listener específico."""
        listeners = cls._listeners.get(event_type, [])
        if callback in listeners:
            listeners.remove(callback)

    @classmethod
    def emit(cls, event_type: str, data: dict[str, Any] | None = None, **kwargs: Any):
        """Dispara um evento para todos os listeners registrados.

        Aceita dados como dict posicional ou como keyword args.
        """
        payload = data if data is not None else kwargs
        for cb in cls._listeners.get(event_type, []):
            cb(payload)

    @classmethod
    def clear(cls):
        """Remove todos os listeners (útil para testes e reset)."""
        cls._listeners.clear()

    @classmethod
    def clear_event(cls, event_type: str):
        """Remove todos os listeners de um evento específico."""
        cls._listeners.pop(event_type, None)
