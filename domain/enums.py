"""Enumerações do domínio de jogo."""

from enum import Enum, auto


class Position(Enum):
    GK = "GK"
    CB = "CB"
    LB = "LB"
    RB = "RB"
    CDM = "CDM"
    CM = "CM"
    CAM = "CAM"
    LW = "LW"
    RW = "RW"
    ST = "ST"
    CF = "CF"


class Side(Enum):
    HOME = "home"
    AWAY = "away"


class Foot(Enum):
    RIGHT = "right"
    LEFT = "left"
    BOTH = "both"


class CardType(Enum):
    YELLOW = "yellow"
    RED = "red"
    SECOND_YELLOW = "second_yellow"


class InjuryType(Enum):
    MUSCLE = "muscle"
    LIGAMENT = "ligament"
    FRACTURE = "fracture"
    CONCUSSION = "concussion"
    BRUISE = "bruise"


class InjurySeverity(Enum):
    MINOR = 1
    MODERATE = 2
    SERIOUS = 3
    SEVERE = 4
    CRITICAL = 5


class PlayerStatus(Enum):
    ACTIVE = "active"
    INJURED = "injured"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class MatchStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class SeasonStatus(Enum):
    ACTIVE = "active"
    FINISHED = "finished"


class Phase(Enum):
    """Fases dentro de um turno de partida."""
    PLAYER_MOVE = auto()
    PLAYER_PASS = auto()
    AI_REACT = auto()
    AI_TURN = auto()
    RESOLVE = auto()
    ANIMATION = auto()


class EventType(Enum):
    GOAL = "goal"
    PASS = "pass"
    SHOT = "shot"
    FOUL = "foul"
    CARD = "card"
    INJURY = "injury"
    SUBSTITUTION = "substitution"
    TACKLE = "tackle"
    INTERCEPTION = "interception"
    SAVE = "save"
    OFFSIDE = "offside"


class TacticMode(Enum):
    OFFENSIVE = auto()
    BALANCED = auto()
    DEFENSIVE = auto()
