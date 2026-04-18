"""Sistema de dados para resolução de ações.

Centraliza toda aleatoriedade do jogo em funções tipadas,
facilitando testes, balanceamento e replay.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class DiceResult:
    """Resultado de uma rolagem de dado."""
    roll: int
    target: int
    success: bool
    margin: int  # positivo = sucesso por margem, negativo = falha

    @property
    def critical_success(self) -> bool:
        return self.roll <= 5

    @property
    def critical_failure(self) -> bool:
        return self.roll >= 96


def d100(target: int) -> DiceResult:
    """Rola 1d100 contra um valor-alvo. Menor ou igual = sucesso."""
    roll = random.randint(1, 100)
    return DiceResult(
        roll=roll,
        target=target,
        success=roll <= target,
        margin=target - roll,
    )


def d6(count: int = 2) -> int:
    """Rola N dados de 6 faces e retorna a soma."""
    return sum(random.randint(1, 6) for _ in range(count))


def roll_range(lo: int, hi: int) -> int:
    """Retorna um inteiro aleatório no intervalo [lo, hi]."""
    return random.randint(lo, hi)


def chance(percent: float) -> bool:
    """Retorna True com probabilidade `percent` (0-100)."""
    return random.random() * 100 < percent


def weighted_choice(options: list[tuple[object, float]]) -> object:
    """Escolhe um item de uma lista ponderada [(item, peso), ...]."""
    items, weights = zip(*options)
    return random.choices(items, weights=weights, k=1)[0]
