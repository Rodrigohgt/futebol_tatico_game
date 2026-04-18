"""Eventos de partida — registros imutáveis de ações ocorridas."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from domain.enums import EventType, CardType, InjuryType


@dataclass(frozen=True)
class MatchEvent:
    """Registro de um evento ocorrido durante a partida."""
    match_id: int
    turn: int
    event_type: EventType
    actor_id: int | None = None
    target_id: int | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(self.data, ensure_ascii=False)

    @classmethod
    def goal(cls, match_id: int, turn: int, scorer_id: int,
             assist_id: int | None = None, **extra) -> MatchEvent:
        return cls(
            match_id=match_id, turn=turn,
            event_type=EventType.GOAL,
            actor_id=scorer_id, target_id=assist_id,
            data={"assist_id": assist_id, **extra},
        )

    @classmethod
    def card(cls, match_id: int, turn: int, player_id: int,
             card_type: CardType, reason: str = "foul") -> MatchEvent:
        return cls(
            match_id=match_id, turn=turn,
            event_type=EventType.CARD,
            actor_id=player_id,
            data={"card_type": card_type.value, "reason": reason},
        )

    @classmethod
    def injury(cls, match_id: int, turn: int, player_id: int,
               injury_type: InjuryType, severity: int,
               games_out: int) -> MatchEvent:
        return cls(
            match_id=match_id, turn=turn,
            event_type=EventType.INJURY,
            actor_id=player_id,
            data={
                "injury_type": injury_type.value,
                "severity": severity,
                "games_out": games_out,
            },
        )

    @classmethod
    def pass_event(cls, match_id: int, turn: int, passer_id: int,
                   target_id: int | None, success: bool,
                   **extra) -> MatchEvent:
        return cls(
            match_id=match_id, turn=turn,
            event_type=EventType.PASS,
            actor_id=passer_id, target_id=target_id,
            data={"success": success, **extra},
        )

    @classmethod
    def foul(cls, match_id: int, turn: int, fouler_id: int,
             victim_id: int, **extra) -> MatchEvent:
        return cls(
            match_id=match_id, turn=turn,
            event_type=EventType.FOUL,
            actor_id=fouler_id, target_id=victim_id,
            data=extra,
        )
