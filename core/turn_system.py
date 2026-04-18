"""Gerenciamento de turnos do jogo.

Responsabilidades:
- Contar turnos e reseta estado do time ao passar
- Consultar quantos jogadores já se moveram
- Emitir eventos de turno via EventBus (quando disponível)
"""

from __future__ import annotations

from utils.event_bus import EventBus


class TurnSystem:
    """Controla o ciclo de turnos e reseta o estado dos times."""

    def __init__(self, event_bus: EventBus | None = None):
        self.current_turn = 1
        self._bus = event_bus

    def pass_turn(self, team):
        """Reseta o time e avança o turno."""
        team.reset_turn()
        self.current_turn += 1
        if self._bus:
            self._bus.emit("turn_started", {"turn": self.current_turn})

    def moved_count(self, team) -> int:
        """Conta jogadores que esgotaram seus pontos de movimento."""
        return sum(1 for p in team.players if not p.can_move())

    def total_players(self, team) -> int:
        return len(team.players)
