"""Perfis de estratégia tática da IA rival.

Cada estratégia é um dicionário de pesos que define a prioridade
de cada comportamento. Trocar de estratégia = trocar o dicionário.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class TacticMode(Enum):
    OFFENSIVE = auto()
    BALANCED = auto()
    DEFENSIVE = auto()


@dataclass(frozen=True)
class StrategyProfile:
    """Conjunto de pesos para cada comportamento."""
    name: str
    mode: TacticMode
    weights: dict[str, float]
    description: str = ""


# ── Perfis pré-definidos ──

OFFENSIVE = StrategyProfile(
    name="Ofensivo",
    mode=TacticMode.OFFENSIVE,
    description="Pressão alta total, todos caçam a bola, marcação individual",
    weights={
        "press_ball_carrier": 1.00,
        "press_attacker":     0.95,
        "cover_space":        0.20,
        "fall_back":          0.05,
        "hold_formation":     0.05,
        "intercept_lane":     0.60,
        "spread_width":       0.15,
    },
)

BALANCED = StrategyProfile(
    name="Equilibrado",
    mode=TacticMode.BALANCED,
    description="Pressão na bola com cobertura tática",
    weights={
        "press_ball_carrier": 0.90,
        "press_attacker":     0.70,
        "cover_space":        0.45,
        "fall_back":          0.30,
        "hold_formation":     0.25,
        "intercept_lane":     0.65,
        "spread_width":       0.35,
    },
)

DEFENSIVE = StrategyProfile(
    name="Defensivo",
    mode=TacticMode.DEFENSIVE,
    description="Bloco baixo com pressão no portador da bola",
    weights={
        "press_ball_carrier": 0.80,
        "press_attacker":     0.35,
        "cover_space":        0.60,
        "fall_back":          0.70,
        "hold_formation":     0.50,
        "intercept_lane":     0.85,
        "spread_width":       0.25,
    },
)

# Mapa rápido para lookup
PROFILES: dict[TacticMode, StrategyProfile] = {
    TacticMode.OFFENSIVE: OFFENSIVE,
    TacticMode.BALANCED: BALANCED,
    TacticMode.DEFENSIVE: DEFENSIVE,
}
