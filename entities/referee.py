"""Entidade do árbitro — influencia decisões de falta, cartão e rigor."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "referees.json"


@dataclass
class RefereeStats:
    """Atributos do árbitro (0-100).

    strictness    — tendência a marcar faltas (alto = mais faltas)
    accuracy      — qualidade geral das decisões (alto = menos erros)
    card_tendency — inclinação a mostrar cartões (alto = mais cartões)
    consistency   — estabilidade das decisões ao longo da partida
    composure     — resistência a pressão / lances polêmicos
    """
    strictness: int = 50
    accuracy: int = 50
    card_tendency: int = 50
    consistency: int = 50
    composure: int = 50

    @property
    def overall(self) -> int:
        vals = [self.strictness, self.accuracy, self.card_tendency,
                self.consistency, self.composure]
        return round(sum(vals) / len(vals))

    @property
    def tier_label(self) -> str:
        ovr = self.overall
        if ovr >= 70:
            return "FIFA"
        if ovr >= 55:
            return "Série A"
        return "Série B"

    def foul_chance_modifier(self) -> float:
        """Multiplicador sobre a chance base de falta.

        strictness 50 → 1.0 (neutro)
        strictness 80 → 1.3 (mais rígido)
        strictness 30 → 0.8 (mais permissivo)
        """
        return 1.0 + (self.strictness - 50) / 100

    def card_chance_modifier(self) -> float:
        """Multiplicador sobre a chance de cartão quando falta é marcada."""
        return 1.0 + (self.card_tendency - 50) / 100

    def missed_call_chance(self) -> float:
        """Chance (0-1) de o árbitro NÃO marcar uma falta real.

        accuracy 90 → 5% de erro
        accuracy 50 → 25% de erro
        accuracy 30 → 35% de erro
        """
        return max(0.0, min(0.50, (100 - self.accuracy) / 200))

    def phantom_foul_chance(self) -> float:
        """Chance (0-1) de marcar falta onde não houve (erro contra).

        accuracy 90 → 2%
        accuracy 50 → 10%
        accuracy 30 → 18%
        """
        return max(0.0, min(0.25, (100 - self.accuracy) / 500))

    def composure_modifier(self, pressure_level: float = 0.0) -> float:
        """Ajuste de qualidade sob pressão (0-1).

        Retorna multiplicador: 1.0 = calmo, <1.0 = mais propenso a errar.
        """
        pressure_effect = pressure_level * (1.0 - self.composure / 100)
        return max(0.5, 1.0 - pressure_effect * 0.3)


@dataclass
class Referee:
    """Árbitro de uma partida."""
    name: str
    stats: RefereeStats
    tier: str = ""

    # Controle de partida
    fouls_called: int = 0
    cards_given: int = 0
    yellows_given: dict[int, int] | None = None  # player_id → count

    def __post_init__(self):
        if self.yellows_given is None:
            self.yellows_given = {}

    def record_foul(self):
        self.fouls_called += 1

    def record_card(self, player_id: int, card_type: str):
        self.cards_given += 1
        if card_type == "yellow":
            self.yellows_given[player_id] = self.yellows_given.get(player_id, 0) + 1

    def player_yellow_count(self, player_id: int) -> int:
        return self.yellows_given.get(player_id, 0)

    def reset_match(self):
        self.fouls_called = 0
        self.cards_given = 0
        self.yellows_given = {}


def _load_data() -> dict:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _rand_in(rng: list[int]) -> int:
    return random.randint(rng[0], rng[1])


def generate_referee(tier: str | None = None) -> Referee:
    """Gera um árbitro aleatório a partir do pool de nomes e tiers."""
    data = _load_data()
    names = data["names"]
    tiers = data["tiers"]

    # Escolhe tier se não fornecido
    if tier is None:
        tier = random.choice(list(tiers.keys()))

    tier_cfg = tiers[tier]

    name = random.choice(names)
    stats = RefereeStats(
        strictness=_rand_in(tier_cfg["strictness"]),
        accuracy=_rand_in(tier_cfg["accuracy"]),
        card_tendency=_rand_in(tier_cfg["card_tendency"]),
        consistency=_rand_in(tier_cfg["consistency"]),
        composure=_rand_in(tier_cfg["composure"]),
    )

    return Referee(name=name, stats=stats, tier=tier)
