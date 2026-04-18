"""Gerenciamento de time e formações táticas.

Formações são carregadas do data/formations.json via FormationLoader.
As constantes KICKOFF/DEFEND mantêm compatibilidade com código existente
como listas simples derivadas dos JSON.
"""

from __future__ import annotations

from entities.player import Player, PlayerInfo, PlayerStats
from loaders.formation_loader import FormationLoader


def _formation_to_list(key: str) -> list[tuple[str, float, float]]:
    """Converte uma Formation do loader para o formato legado (pos, x, y)."""
    formation = FormationLoader.get(key)
    if formation is None:
        raise ValueError(f"Formação '{key}' não encontrada em formations.json")
    return [(s.position, s.x_meters, s.y_meters) for s in formation.slots]


# Formações carregadas do JSON — compatíveis com código legado
KICKOFF_FORMATION_433 = _formation_to_list("4-3-3_kickoff")
DEFEND_KICKOFF_FORMATION_433 = _formation_to_list("4-3-3")

# Nomes de jogadores por time
DEFAULT_NAMES = [
    ("Silva", 28), ("Santos", 24), ("Oliveira", 30), ("Costa", 26),
    ("Souza", 22), ("Ferreira", 27), ("Almeida", 25), ("Pereira", 29),
    ("Rodrigues", 23), ("Lima", 31), ("Barbosa", 26),
]

RIVAL_NAMES = [
    ("Müller", 27), ("Schneider", 23), ("Weber", 31), ("Fischer", 25),
    ("Wagner", 29), ("Becker", 22), ("Hoffmann", 26), ("Schäfer", 28),
    ("Koch", 24), ("Richter", 30), ("Klein", 27),
]


class Team:
    """Representa um time completo com 11 jogadores."""

    def __init__(
        self,
        name: str,
        color: tuple[int, int, int],
        coord_system,
        formation: list | None = None,
        side: str = "left",
    ):
        self.name = name
        self.color = color
        self.coord_system = coord_system
        self.side = side
        self.players: list[Player] = []

        formation = formation or KICKOFF_FORMATION_433
        self._create_players(formation)

    def _create_players(self, formation: list):
        from config import field_specs

        names = RIVAL_NAMES if self.side == "right" else DEFAULT_NAMES

        for i, (pos_name, mx, my) in enumerate(formation):
            # Espelha posição X para o time da direita
            if self.side == "right":
                mx = field_specs.FIELD_LENGTH - mx

            px = self.coord_system.m2px_x(mx)
            py = self.coord_system.m2px_y(my)

            name, age = names[i]
            info = PlayerInfo(
                name=name,
                age=age,
                number=i + 1 if i > 0 else 1,
                position=pos_name,
                status="Titular",
            )
            if i == 0:
                info.number = 1

            stats = PlayerStats.random()
            initial_facing = (-1.0, 0.0) if self.side == "right" else (1.0, 0.0)
            player = Player(
                info=info,
                stats=stats,
                start_x=px,
                start_y=py,
                color=self.color,
                coord_system=self.coord_system,
                facing=initial_facing,
            )
            self.players.append(player)

    def update(self):
        for p in self.players:
            p.update()

    def reset_turn(self):
        for p in self.players:
            p.reset_turn()

    def all_moved(self) -> bool:
        return all(not p.can_move() for p in self.players)

    def draw(self, surface):
        for p in self.players:
            p.draw(surface)
