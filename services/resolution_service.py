"""Serviço de resolução de ações — sistema d100 + stats + traits + modifiers.

Centraliza toda a aleatoriedade de gameplay. Nenhum system ou renderer
deve gerar resultados aleatórios diretamente — tudo passa por aqui.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.player import PlayerDomain
from domain.match_state import MatchState
from loaders.rules_loader import RulesLoader
from loaders.trait_loader import TraitLoader
from utils.dice import d100, DiceResult, chance, roll_range


@dataclass
class PassResult:
    """Resultado de uma tentativa de passe."""
    dice: DiceResult
    success: bool
    error_angle: float
    speed: float
    intercepted: bool = False


@dataclass
class ShotResult:
    """Resultado de uma tentativa de chute."""
    dice: DiceResult
    success: bool  # se acertou o gol (antes do goleiro)
    power: float
    saved: bool = False
    blocked: bool = False


@dataclass
class TackleResult:
    """Resultado de uma tentativa de desarme."""
    dice: DiceResult
    success: bool
    foul: bool
    card: str | None  # "yellow", "red", None
    injury: bool


class ResolutionService:
    """Resolve ações de gameplay via d100 + atributos + contexto."""

    def resolve_pass(self, passer: PlayerDomain, target_distance: float,
                     power: float, state: MatchState) -> PassResult:
        rules = RulesLoader.pass_rules()

        # Alvo base
        target_value = rules.base_success

        # Bônus de stat
        stat_bonus = int(passer.stats.passing * rules.stat_weight)
        target_value += stat_bonus

        # Bônus de traits
        trait_bonus = TraitLoader.stat_bonus_for(passer.traits, "passing")
        target_value += trait_bonus

        # Penalidade de distância
        dist_penalty = int(target_distance * rules.distance_penalty_per_meter)
        target_value -= dist_penalty

        # Penalidade de força
        power_penalty = int(power * 100 * rules.power_penalty_factor)
        target_value -= power_penalty

        # Penalidade de pressão (baseada em marcação)
        pressure = state.pressure_map.get(passer.id, 0.0)
        if pressure > 0:
            target_value -= int(rules.pressure_penalty * pressure)

        # Modificadores contextuais
        mod = state.get_modifier_total("passing")
        target_value += mod

        # Clamp
        target_value = max(5, min(95, target_value))

        # Rola d100
        result = d100(target_value)

        # Ângulo de erro em caso de falha
        error_angle = 0.0
        if not result.success:
            import random
            error_angle = random.uniform(
                -rules.error_max_radians, rules.error_max_radians
            )

        # Velocidade baseada na força
        speed = 3.0 + 9.0 * power

        return PassResult(
            dice=result,
            success=result.success,
            error_angle=error_angle,
            speed=speed,
        )

    def resolve_shot(self, shooter: PlayerDomain, target_distance: float,
                     angle_quality: float, state: MatchState) -> ShotResult:
        rules = RulesLoader.shot_rules()

        target_value = rules.base_success
        target_value += int(shooter.stats.finishing * rules.stat_weight)
        target_value += TraitLoader.stat_bonus_for(shooter.traits, "finishing")
        target_value -= int(target_distance * rules.distance_penalty_per_meter)
        target_value -= int((1.0 - angle_quality) * 100 * rules.angle_penalty_factor)

        pressure = state.pressure_map.get(shooter.id, 0.0)
        if pressure > 0:
            target_value -= int(rules.pressure_penalty * pressure)

        target_value += state.get_modifier_total("finishing")
        target_value = max(5, min(95, target_value))

        result = d100(target_value)

        power = 0.5 + (shooter.stats.finishing / 200)

        return ShotResult(
            dice=result,
            success=result.success,
            power=power,
        )

    def resolve_tackle(self, tackler: PlayerDomain, target: PlayerDomain,
                       distance: float, state: MatchState) -> TackleResult:
        rules = RulesLoader.tackle_rules()

        target_value = rules.base_success
        target_value += int(tackler.stats.defending * rules.stat_weight)
        target_value += TraitLoader.stat_bonus_for(tackler.traits, "defending")
        target_value -= int(target.stats.dribbling * 0.3)
        target_value -= int(distance * rules.distance_factor)
        target_value += state.get_modifier_total("defending")
        target_value = max(5, min(95, target_value))

        result = d100(target_value)

        # Chance de falta
        foul = chance(rules.injury_risk_base + tackler.stats.defending * 0.05)

        # Cartão
        card = None
        if foul:
            if chance(rules.card_risk_red):
                card = "red"
            elif chance(rules.card_risk_yellow):
                card = "yellow"

        # Lesão
        injury = False
        if foul:
            injury = chance(rules.injury_risk_base)

        return TackleResult(
            dice=result,
            success=result.success,
            foul=foul,
            card=card,
            injury=injury,
        )
