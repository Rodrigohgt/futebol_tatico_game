"""Estado temporário da partida — existe apenas em memória durante o jogo."""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.enums import Side, Phase, EventType
from domain.events import MatchEvent
from domain.value_objects import Coord


@dataclass
class TurnModifier:
    """Modificador contextual ativo durante a partida."""
    source: str          # "rain", "crowd_pressure", "red_card_shock"
    stat: str            # "passing", "finishing", "*"
    delta: int           # -10, +5...
    turns_remaining: int # 0 = permanente nesta partida

    def tick(self):
        """Decrementa a duração. Retorna True se expirou."""
        if self.turns_remaining <= 0:
            return False
        self.turns_remaining -= 1
        return self.turns_remaining <= 0


@dataclass
class MatchState:
    """Estado completo de uma partida em andamento — só existe em RAM.

    Nenhum dado aqui é persistido diretamente. Ao final da partida,
    os services extraem o que precisa ir para o banco.
    """
    match_id: int = 0
    turn: int = 1
    phase: Phase = Phase.PLAYER_MOVE
    half: int = 1  # 1 ou 2

    # Posse
    possession: Side | None = None
    ball_pos: Coord = field(default_factory=lambda: Coord(0, 0))
    ball_owner_id: int | None = None

    # Posições dos jogadores em campo (player_id → coord em pixels)
    home_positions: dict[int, Coord] = field(default_factory=dict)
    away_positions: dict[int, Coord] = field(default_factory=dict)

    # Mapas táticos
    pressure_map: dict[int, float] = field(default_factory=dict)
    marking_pairs: dict[int, int] = field(default_factory=dict)

    # Modificadores contextuais ativos
    modifiers: list[TurnModifier] = field(default_factory=list)

    # Budget do turno
    moves_used: int = 0
    passes_used: int = 0
    moves_budget: int = 2

    # Placar
    home_score: int = 0
    away_score: int = 0

    # Faltas por lado
    fouls_this_half: dict[str, int] = field(default_factory=lambda: {"home": 0, "away": 0})

    # Eventos registrados
    events_this_turn: list[MatchEvent] = field(default_factory=list)
    all_events: list[MatchEvent] = field(default_factory=list)

    # Stats acumuladas por jogador (player_id → dict de contadores)
    player_stats: dict[int, dict[str, int]] = field(default_factory=dict)

    def record_event(self, event: MatchEvent):
        """Registra um evento no turno atual e no histórico completo."""
        self.events_this_turn.append(event)
        self.all_events.append(event)

    def advance_turn(self):
        """Avança para o próximo turno, processa expiração de modificadores."""
        self.turn += 1
        self.moves_used = 0
        self.passes_used = 0
        self.events_this_turn.clear()

        # Expira modificadores
        self.modifiers = [m for m in self.modifiers if not m.tick()]

    def get_modifier_total(self, stat: str) -> int:
        """Soma todos os modificadores ativos para um stat específico."""
        total = 0
        for m in self.modifiers:
            if m.stat == stat or m.stat == "*":
                total += m.delta
        return total

    def increment_stat(self, player_id: int, stat_name: str, amount: int = 1):
        """Incrementa um contador de stat para um jogador."""
        if player_id not in self.player_stats:
            self.player_stats[player_id] = {}
        stats = self.player_stats[player_id]
        stats[stat_name] = stats.get(stat_name, 0) + amount

    @property
    def goals_this_match(self) -> list[MatchEvent]:
        return [e for e in self.all_events if e.event_type == EventType.GOAL]

    @property
    def cards_this_match(self) -> list[MatchEvent]:
        return [e for e in self.all_events if e.event_type == EventType.CARD]
