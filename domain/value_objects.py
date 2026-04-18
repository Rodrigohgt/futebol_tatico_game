"""Value objects imutáveis do domínio."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Coord:
    """Coordenada 2D genérica (metros ou pixels)."""
    x: float
    y: float

    def distance_to(self, other: Coord) -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def lerp(self, other: Coord, t: float) -> Coord:
        return Coord(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
        )

    def __add__(self, other: Coord) -> Coord:
        return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Coord) -> Coord:
        return Coord(self.x - other.x, self.y - other.y)


@dataclass(frozen=True)
class Attribute:
    """Atributo de jogador com valor base e modificadores."""
    base: int
    modifier: int = 0

    @property
    def effective(self) -> int:
        return max(1, min(99, self.base + self.modifier))


@dataclass(frozen=True)
class StatLine:
    """Linha de estatísticas de uma partida para um jogador."""
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    shots: int = 0
    passes_attempted: int = 0
    passes_completed: int = 0
    tackles: int = 0
    fouls: int = 0
    saves: int = 0
    rating: float = 0.0

    @property
    def pass_accuracy(self) -> float:
        if self.passes_attempted == 0:
            return 0.0
        return self.passes_completed / self.passes_attempted


@dataclass(frozen=True)
class FormationSlot:
    """Posição dentro de uma formação tática (metros relativos)."""
    position: str
    x_meters: float
    y_meters: float


@dataclass(frozen=True)
class SeasonStanding:
    """Classificação de um time numa temporada."""
    team_id: int
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def points(self) -> int:
        return self.won * 3 + self.drawn

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against
