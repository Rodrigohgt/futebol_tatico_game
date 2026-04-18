"""Classe principal do jogo – orquestra todos os sistemas.

Responsabilidades:
- Coordenar input, update e render por frame
- Delegar passe ao PassController
- Delegar decisões de IA ao AIController
- Emitir eventos via EventBus para desacoplamento

NÃO deve acessar banco de dados diretamente.
"""

import pygame

from config import settings
from utils.coordinates import CoordinateSystem
from utils.event_bus import EventBus
from entities.team import Team, KICKOFF_FORMATION_433, DEFEND_KICKOFF_FORMATION_433
from entities.ball import Ball
from core.turn_system import TurnSystem
from core.pass_controller import PassController
from systems.input_handler import InputHandler
from systems.selection import SelectionSystem
from systems.rival_ai import RivalAI
from systems.ai_controller import AIController
from systems.goalkeeper_ai import GoalkeeperAI
from rendering.field_renderer import FieldRenderer
from rendering.ui_renderer import UIRenderer
from rendering.popup import PlayerPopup


class Game:
    """Loop principal e coordenação de subsistemas."""

    def __init__(self, surface: pygame.Surface | None = None):
        self._standalone = surface is None
        if self._standalone:
            pygame.init()
            self.screen = pygame.display.set_mode(
                (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
            )
            pygame.display.set_caption(settings.WINDOW_TITLE)
        else:
            self.screen = surface
        self.clock = pygame.time.Clock()
        self.running = True

        # Event bus — comunicação desacoplada entre sistemas
        self.event_bus = EventBus()

        # Sistemas
        self.coords = CoordinateSystem()
        self.field = FieldRenderer(self.coords)
        self.ui = UIRenderer()
        self.popup = PlayerPopup()
        self.turn = TurnSystem(event_bus=self.event_bus)
        self.selection = SelectionSystem()
        self.input = InputHandler()
        self.rival_ai = RivalAI(self.coords)
        self.ai_ctrl = AIController(self.rival_ai, self.coords)
        self.rival_gk_ai = GoalkeeperAI(self.coords, side="right")

        # Controlador de passe
        self.passer = PassController(event_bus=self.event_bus)

        # Entidades
        self.home_team = Team(
            name="Time A",
            color=settings.HOME_TEAM_COLOR,
            coord_system=self.coords,
            formation=KICKOFF_FORMATION_433,
            side="left",
        )
        self.rival_team = Team(
            name="Time B",
            color=settings.RIVAL_TEAM_COLOR,
            coord_system=self.coords,
            formation=DEFEND_KICKOFF_FORMATION_433,
            side="right",
        )

        # Bola — inicia com o ST (índice 9 na formação)
        center = self.coords.field_center_px()
        self.ball = Ball(center[0], center[1], self.coords)
        kickoff_player = self.home_team.players[9]
        self.ball.give_to(kickoff_player)

        self._started = False

    # ── Propriedades de compatibilidade ──

    @property
    def pass_mode(self) -> bool:
        return self.passer.pass_mode

    @pass_mode.setter
    def pass_mode(self, value: bool):
        self.passer.pass_mode = value

    @property
    def pass_charging(self) -> bool:
        return self.passer.pass_charging

    @property
    def power_bar(self):
        return self.passer.power_bar

    def run(self):
        """Loop principal — usado apenas no modo standalone."""
        while self.running:
            self._process_input()
            self._update()
            self._render()
            self.clock.tick(settings.FPS)

        pygame.quit()

    # ── Input ──

    def _process_input(self, events: list | None = None):
        ev = self.input.process(events)

        if ev.quit:
            self.running = False
            return

        # ESC: cancela pass mode ou sai do jogo
        if ev.key_escape:
            if self.passer.pass_mode:
                self.passer.cancel()
            else:
                self.running = False
            return

        all_players = self.home_team.players + self.rival_team.players
        self.ui.update(ev.mouse_pos)
        self.popup.update(ev.mouse_pos, all_players)

        self.ui.btn_pass_ball.active = self.passer.can_pass(
            self.ball, self.home_team.players
        )

        # ── Clique esquerdo: seleção de jogador ──
        if ev.left_click is not None:
            if ev.left_click[1] < self.ui.hud_rect.top:
                self.selection.select_at(
                    ev.left_click, self.home_team.players
                )

        # ── Modo de passe com barra de força ──
        if self.passer.pass_mode:
            self._handle_pass_mode(ev)
            return

        # ── Clique direito: movimento / HUD ──
        if ev.right_click is not None:
            self._handle_click(ev.right_click)

    def _handle_pass_mode(self, ev):
        """Gerencia o modo de passe (botão direito).

        - Clique direito em companheiro → passe instantâneo direcionado
        - Clique direito no campo → passe com velocidade auto-calculada
        - Segurar direito → power bar carrega → soltar executa com força manual
        """

        # Clique direito no HUD cancela
        if ev.right_click is not None:
            if ev.right_click[1] >= self.ui.hud_rect.top:
                self.passer.cancel()
                return

        # Botão direito pressionado no campo
        if ev.right_press is not None and ev.right_press[1] < self.ui.hud_rect.top:
            # Clique em companheiro → passe instantâneo para o destino dele
            teammate = self.passer.teammate_at(
                ev.right_press, self.ball, self.home_team.players
            )
            if teammate is not None:
                target = (teammate.target.x, teammate.target.y)
                power = self.passer.auto_power(self.ball, target)
                self._do_pass(target, power)
                self.passer.pass_mode = False
                self.passer.pass_charging = False
                return

            # Inicia carregamento (pode virar clique rápido no release)
            if not self.passer.pass_charging:
                self.passer.start_charge()

        # Botão direito solto → executa o passe
        if ev.right_release is not None and self.passer.pass_charging:
            raw_power = self.passer.stop_charge()
            target = ev.right_release
            if target[1] < self.ui.hud_rect.top:
                if raw_power < 0.05:
                    power = self.passer.auto_power(self.ball, target)
                else:
                    power = raw_power
                self._do_pass(target, power)
            self.passer.pass_mode = False
            return

    def _do_pass(self, target, power: float):
        """Executa o passe e pula o turno automaticamente."""
        self.passer.execute(
            self.ball, target, power, self.coords
        )
        self._started = True
        self._trigger_rival_reaction()
        # Passe encerra o turno
        self._pass_turn()

    def _handle_click(self, click_pos):
        # ── Botões do HUD ──
        if self.ui.btn_end_turn.is_clicked(click_pos):
            self._pass_turn()
            return

        if self.ui.btn_finish.is_clicked(click_pos):
            self._action_finish()
            return

        if self.ui.btn_reset.is_clicked(click_pos):
            self._reset_game()
            return

        if self.ui.btn_pass_ball.is_clicked(click_pos):
            if self.passer.can_pass(self.ball, self.home_team.players):
                self.passer.activate()
            return

        # ── Clique no campo: move o jogador selecionado ──
        if click_pos[1] < self.ui.hud_rect.top:
            moved = self.selection.move_to(click_pos)
            if moved:
                self._started = True
                self._trigger_rival_reaction()
                self._check_auto_pass()

    # ── Update ──

    def _update(self):
        self.home_team.update()
        self.rival_team.update()
        self.ball.update()
        self.passer.power_bar.update()

        # GK rival se posiciona automaticamente (só após primeira ação)
        if self._started:
            rival_gk = self.rival_team.players[0]
            if GoalkeeperAI.is_goalkeeper(rival_gk):
                self.rival_gk_ai.update_position(rival_gk, self.ball.pos)

        # Pickup automático
        if not self.ball.is_held():
            all_players = self.home_team.players + self.rival_team.players
            self.ball.check_pickup(all_players)

    # ── Render ──

    def _render(self):
        self.field.draw(self.screen)
        self.rival_team.draw(self.screen)
        self.home_team.draw(self.screen)
        self.ball.draw(self.screen)

        # Preview de passe (com feedback de força quando carregando)
        if self.passer.pass_mode and self.passer.can_pass(
            self.ball, self.home_team.players
        ):
            mouse_pos = pygame.mouse.get_pos()
            current_power = (self.passer.power_bar.power
                             if self.passer.pass_charging else 0.0)
            self.ball.draw_pass_preview(self.screen, mouse_pos, current_power)

        moved = self.turn.moved_count(self.home_team)
        total = self.turn.total_players(self.home_team)
        strategy_name = self.rival_ai.strategy.name
        self.ui.draw(self.screen, self.turn.current_turn, moved, total, strategy_name)

        # Barra de força
        self.passer.power_bar.draw(self.screen)

        self.popup.draw(self.screen, pygame.mouse.get_pos())

        if self._standalone:
            pygame.display.flip()

    # ── Turno ──

    def _pass_turn(self):
        self.selection.reset()
        self.passer.reset_turn()
        self._started = True

        # Reset rival ANTES da fase da IA para que os targets persistam
        self.rival_team.reset_turn()
        self.ai_ctrl.reset_turn()

        # Fase de decisão completa da IA rival
        self.ai_ctrl.execute_turn_phase(
            ball=self.ball,
            human_players=self.home_team.players,
            rival_players=self.rival_team.players,
        )

        # Avança o turno do humano
        self.turn.pass_turn(self.home_team)

        # Emite evento de turno
        self.event_bus.emit("turn_passed", {"turn": self.turn.current_turn})

    def _check_auto_pass(self):
        """Pula turno quando todos os jogadores esgotaram seu movimento."""
        if self.home_team.all_moved():
            self._pass_turn()

    def _trigger_rival_reaction(self):
        self.ai_ctrl.react_to_move(
            ball=self.ball,
            human_players=self.home_team.players,
            rival_players=self.rival_team.players,
        )

    def _reset_game(self):
        """Reinicia a partida ao estado inicial."""
        # Reset times
        self.home_team = Team(
            name="Time A",
            color=settings.HOME_TEAM_COLOR,
            coord_system=self.coords,
            formation=KICKOFF_FORMATION_433,
            side="left",
        )
        self.rival_team = Team(
            name="Time B",
            color=settings.RIVAL_TEAM_COLOR,
            coord_system=self.coords,
            formation=DEFEND_KICKOFF_FORMATION_433,
            side="right",
        )

        # Reset bola
        center = self.coords.field_center_px()
        self.ball = Ball(center[0], center[1], self.coords)
        kickoff_player = self.home_team.players[9]
        self.ball.give_to(kickoff_player)

        # Reset sistemas
        self.turn = TurnSystem(event_bus=self.event_bus)
        self.selection.reset()
        self.rival_ai = RivalAI(self.coords)
        self.ai_ctrl = AIController(self.rival_ai, self.coords)

        # Reset controladores
        self.passer.reset_turn()
        self._started = False

        self.event_bus.emit("game_reset", {})

    def _action_finish(self):
        self.event_bus.emit("match_finish_requested", {})
