"""Sistema de seleção de jogadores em campo."""

from __future__ import annotations
from entities.player import Player


class SelectionSystem:
    """Gerencia qual jogador está selecionado e executa movimentação."""

    def __init__(self):
        self.selected: Player | None = None

    def select_at(self, mouse_pos: tuple[int, int], players: list[Player]) -> bool:
        """Clique direito — seleciona o jogador sob o cursor.

        Retorna True se um jogador foi selecionado.
        """
        clicked_player = self._player_at(mouse_pos, players)
        if clicked_player is not None:
            self._select(clicked_player)
            return True
        return False

    def move_to(self, mouse_pos: tuple[int, int]) -> bool:
        """Clique direito — move o jogador selecionado para a posição.

        Uma ação por turno: esgota todo o movimento após o deslocamento.
        Retorna True se o movimento foi realizado.
        """
        if self.selected is None or not self.selected.can_move():
            return False

        self.selected.set_target(mouse_pos)
        # Uma ação por turno — esgota metros restantes e desseleciona
        self.selected.move_meters_remaining = 0.0
        self.selected.selected = False
        self.selected = None
        return True

    def deselect(self):
        if self.selected is not None:
            self.selected.selected = False
            self.selected = None

    def reset(self):
        self.deselect()

    def _select(self, player: Player):
        if not player.can_move():
            return
        if self.selected is not None:
            self.selected.selected = False
        self.selected = player
        player.selected = True

    @staticmethod
    def _player_at(pos: tuple, players: list[Player]) -> Player | None:
        for p in players:
            if p.contains_point(pos):
                return p
        return None
