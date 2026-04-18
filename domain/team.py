"""Modelo de domínio do time — puro Python, sem Pygame."""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.player import PlayerDomain


@dataclass
class TeamDomain:
    """Modelo completo de domínio de um time."""
    id: int = 0
    name: str = ""
    short_name: str = ""
    color_hex: str = "#CC3333"
    reputation: int = 50
    budget: int = 0
    formation_key: str = "4-3-3"
    roster: list[PlayerDomain] = field(default_factory=list)

    @property
    def starters(self) -> list[PlayerDomain]:
        return [p for p in self.roster if p.is_available][:11]

    @property
    def bench(self) -> list[PlayerDomain]:
        available = [p for p in self.roster if p.is_available]
        return available[11:]

    def get_player(self, player_id: int) -> PlayerDomain | None:
        for p in self.roster:
            if p.id == player_id:
                return p
        return None

    @property
    def average_overall(self) -> float:
        starters = self.starters
        if not starters:
            return 0.0
        return sum(p.stats.overall for p in starters) / len(starters)
