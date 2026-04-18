"""Modelo de domínio do jogador — puro Python, sem Pygame."""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.enums import Position, Foot, PlayerStatus


@dataclass
class PlayerStats:
    """Atributos técnicos do jogador (1-99)."""
    finishing: int = 50
    passing: int = 50
    pace: int = 50
    dribbling: int = 50
    defending: int = 50
    heading: int = 50
    stamina: int = 50
    composure: int = 50
    positioning: int = 50
    vision: int = 50

    def as_dict(self) -> dict[str, int]:
        return {
            "finishing": self.finishing,
            "passing": self.passing,
            "pace": self.pace,
            "dribbling": self.dribbling,
            "defending": self.defending,
            "heading": self.heading,
            "stamina": self.stamina,
            "composure": self.composure,
            "positioning": self.positioning,
            "vision": self.vision,
        }

    @property
    def overall(self) -> int:
        vals = list(self.as_dict().values())
        return round(sum(vals) / len(vals))


@dataclass
class PlayerCondition:
    """Estado físico/mental entre partidas."""
    fatigue: float = 100.0   # 0=exausto, 100=fresco
    morale: float = 70.0     # 0-100
    form: float = 50.0       # 0-100, média móvel de ratings
    xp: int = 0


@dataclass
class PlayerIdentity:
    """Dados de identidade do jogador."""
    id: int = 0
    name: str = "Jogador"
    age: int = 25
    number: int = 1
    position: Position = Position.CM
    foot: Foot = Foot.RIGHT
    archetype: str = ""
    status: PlayerStatus = PlayerStatus.ACTIVE
    team_id: int = 0
    market_value: int = 0
    contract_end_season: int = 0


@dataclass
class PlayerDomain:
    """Modelo completo de domínio de um jogador.

    Contém identidade, stats e condição. Não contém nada visual.
    Serve como fonte de verdade para repositórios e services.
    """
    identity: PlayerIdentity = field(default_factory=PlayerIdentity)
    stats: PlayerStats = field(default_factory=PlayerStats)
    condition: PlayerCondition = field(default_factory=PlayerCondition)
    traits: list[str] = field(default_factory=list)

    @property
    def id(self) -> int:
        return self.identity.id

    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def position(self) -> Position:
        return self.identity.position

    @property
    def is_available(self) -> bool:
        return self.identity.status == PlayerStatus.ACTIVE

    @property
    def is_fit(self) -> bool:
        return self.condition.fatigue > 20.0 and self.is_available
