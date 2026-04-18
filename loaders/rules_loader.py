"""Carrega regras de resolução a partir de data/rules.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PassRules:
    base_success: int
    stat_weight: float
    distance_penalty_per_meter: float
    pressure_penalty: int
    power_penalty_factor: float
    error_max_radians: float
    trait_bonus: dict[str, int]


@dataclass(frozen=True)
class ShotRules:
    base_success: int
    stat_weight: float
    distance_penalty_per_meter: float
    pressure_penalty: int
    angle_penalty_factor: float
    trait_bonus: dict[str, int]


@dataclass(frozen=True)
class TackleRules:
    base_success: int
    stat_weight: float
    distance_factor: float
    card_risk_yellow: int
    card_risk_red: int
    injury_risk_base: int
    trait_bonus: dict[str, int]


@dataclass(frozen=True)
class FoulRules:
    base_chance: int
    aggression_factor: float
    fatigue_factor: float
    existing_yellow_red_chance: int
    repeated_foul_yellow_chance: int


@dataclass(frozen=True)
class InjuryRules:
    base_chance: int
    foul_multiplier: float
    fatigue_multiplier: float
    severity_weights: dict[int, int]
    games_out_by_severity: dict[int, tuple[int, int]]


class RulesLoader:
    """Cache singleton de regras de resolução."""

    _raw: dict = {}
    _DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "rules.json"

    @classmethod
    def _load_raw(cls) -> dict:
        if not cls._raw:
            with open(cls._DATA_PATH, encoding="utf-8") as f:
                cls._raw = json.load(f)
        return cls._raw

    @classmethod
    def pass_rules(cls) -> PassRules:
        r = cls._load_raw()["pass"]
        return PassRules(
            base_success=r["base_success"],
            stat_weight=r["stat_weight"],
            distance_penalty_per_meter=r["distance_penalty_per_meter"],
            pressure_penalty=r["pressure_penalty"],
            power_penalty_factor=r["power_penalty_factor"],
            error_max_radians=r["error_max_radians"],
            trait_bonus=r["trait_bonus"],
        )

    @classmethod
    def shot_rules(cls) -> ShotRules:
        r = cls._load_raw()["shot"]
        return ShotRules(
            base_success=r["base_success"],
            stat_weight=r["stat_weight"],
            distance_penalty_per_meter=r["distance_penalty_per_meter"],
            pressure_penalty=r["pressure_penalty"],
            angle_penalty_factor=r["angle_penalty_factor"],
            trait_bonus=r["trait_bonus"],
        )

    @classmethod
    def tackle_rules(cls) -> TackleRules:
        r = cls._load_raw()["tackle"]
        return TackleRules(
            base_success=r["base_success"],
            stat_weight=r["stat_weight"],
            distance_factor=r["distance_factor"],
            card_risk_yellow=r["card_risk"]["yellow"],
            card_risk_red=r["card_risk"]["red"],
            injury_risk_base=r["injury_risk_base"],
            trait_bonus=r["trait_bonus"],
        )

    @classmethod
    def foul_rules(cls) -> FoulRules:
        r = cls._load_raw()["foul"]
        return FoulRules(
            base_chance=r["base_chance"],
            aggression_factor=r["aggression_factor"],
            fatigue_factor=r["fatigue_factor"],
            existing_yellow_red_chance=r["card_escalation"]["existing_yellow_red_chance"],
            repeated_foul_yellow_chance=r["card_escalation"]["repeated_foul_yellow_chance"],
        )

    @classmethod
    def injury_rules(cls) -> InjuryRules:
        r = cls._load_raw()["injury"]
        sev = {int(k): v for k, v in r["severity_weights"].items()}
        gout = {int(k): tuple(v) for k, v in r["games_out_by_severity"].items()}
        return InjuryRules(
            base_chance=r["base_chance"],
            foul_multiplier=r["foul_multiplier"],
            fatigue_multiplier=r["fatigue_multiplier"],
            severity_weights=sev,
            games_out_by_severity=gout,
        )

    @classmethod
    def raw(cls) -> dict:
        return cls._load_raw()
