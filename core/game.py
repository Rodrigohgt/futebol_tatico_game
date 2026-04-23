"""Classe principal do jogo – orquestra todos os sistemas.

Responsabilidades:
- Coordenar input, update e render por frame
- Delegar passe ao PassController
- Delegar decisões de IA ao AIController
- Emitir eventos via EventBus para desacoplamento

NÃO deve acessar banco de dados diretamente.
"""

import math
import random

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
from entities.referee import Referee, generate_referee
from rendering.field_renderer import FieldRenderer
from rendering.ui_renderer import UIRenderer
from rendering.popup import PlayerPopup


class Game:
    """Loop principal e coordenação de subsistemas."""

    def __init__(self, surface: pygame.Surface | None = None,
                 referee: Referee | None = None):
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

        # Árbitro da partida
        self.referee: Referee = referee if referee is not None else generate_referee(
            tier=settings.REFEREE_DEFAULT_TIER)
        self._foul_stop_timer = 0  # frames de pausa após falta/cartão

        # ── P1: Interceptação — tracking por passe ──
        self._intercept_cooldowns: dict[int, int] = {}  # player_id → frames restantes

        # ── P3: Tackle — cooldown para não repetir todo frame ──
        self._tackle_cooldown = 60  # cooldown inicial para não triggerar no spawn

        # ── P4: Contra-ataque — budget imediato ──
        self._counter_attack_budget = 0

        # ── P2: IA Animada — ações step-by-step com delay ──
        self._ai_phase_active = False
        self._ai_phase_budget = 0
        self._ai_phase_last_tick = 0  # timestamp absoluto (pygame.time.get_ticks)
        self._ai_fast_forward = False

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
            if self._ai_phase_active:
                self._ai_fast_forward = True
                return
            if self.passer.pass_mode:
                self.passer.cancel()
            else:
                self.running = False
            return

        # Bloqueia input do jogador durante fase da IA (P2)
        if self._ai_phase_active:
            # Permite apenas fast-forward com Space
            if ev.key_space:
                self._ai_fast_forward = not self._ai_fast_forward
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
        """Executa o passe com checagem de campo de visão (FOV).

        - Alvo dentro do FOV → passe instantâneo, turno encerra normalmente.
        - Alvo fora do FOV  → jogador apenas gira para encarar o alvo,
          consumindo a ação. O passe deve ser tentado no turno seguinte.
        """
        if not self.ball.is_held() or self.ball.owner is None:
            return

        passer = self.ball.owner

        if passer.is_within_fov(target):
            # ── Dentro do FOV: passe direto ──
            self._intercept_cooldowns.clear()
            self.passer.execute(
                self.ball, target, power, self.coords
            )
            self._started = True
            self._trigger_rival_reaction()
            self.event_bus.emit("pass_in_fov", {
                "passer": passer,
                "target": target,
                "fov": passer.calc_fov(),
            })
            self._pass_turn()
        else:
            # ── Fora do FOV: rotação consome a ação ──
            passer.rotate_towards(target)
            passer.has_moved = True  # consome a ação do jogador
            self._started = True
            self.event_bus.emit("pass_rotate_needed", {
                "passer": passer,
                "target": target,
                "fov": passer.calc_fov(),
            })
            self.passer.cancel()
            self._check_auto_pass()

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

        # P2: Fase animada da IA — processa fila com delay
        if self._ai_phase_active:
            self._update_ai_phase()

        # Pausa após falta marcada pelo árbitro
        if self._foul_stop_timer > 0:
            self._foul_stop_timer -= 1
            return  # Congela o jogo brevemente

        # P1: Interceptação — rivais podem cortar passes em trânsito
        if self.ball.is_moving():
            self._check_interception()

        # P3: Tackle — disputa quando rival chega perto do portador
        if self._tackle_cooldown > 0:
            self._tackle_cooldown -= 1
        if self.ball.is_held() and self._tackle_cooldown <= 0:
            self._check_tackle()

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
            # Desenha cone de FOV do passador
            if self.ball.owner is not None:
                self._draw_fov_cone(self.ball.owner)

            mouse_pos = pygame.mouse.get_pos()
            current_power = (self.passer.power_bar.power
                             if self.passer.pass_charging else 0.0)
            self.ball.draw_pass_preview(self.screen, mouse_pos, current_power)

        moved = self.turn.moved_count(self.home_team)
        total = self.turn.total_players(self.home_team)
        strategy_name = self.rival_ai.strategy.name
        self.ui.draw(self.screen, self.turn.current_turn, moved, total,
                     strategy_name, referee=self.referee)

        # Barra de força
        self.passer.power_bar.draw(self.screen)

        self.popup.draw(self.screen, pygame.mouse.get_pos())

        if self._standalone:
            pygame.display.flip()

    def _draw_fov_cone(self, player):
        """Desenha o cone de visão do passador (semi-transparente)."""
        if player.facing.length_squared() < 0.01:
            return

        fov_half = player.fov_half_rad
        facing_angle = math.atan2(player.facing.y, player.facing.x)
        cone_radius = 120  # alcance visual do cone em pixels

        # Gera pontos do arco
        steps = 20
        points = [(int(player.pos.x), int(player.pos.y))]
        for i in range(steps + 1):
            a = facing_angle - fov_half + (2 * fov_half) * i / steps
            px = player.pos.x + cone_radius * math.cos(a)
            py = player.pos.y + cone_radius * math.sin(a)
            points.append((int(px), int(py)))

        # Superfície alpha para o cone
        min_x = min(p[0] for p in points) - 2
        min_y = min(p[1] for p in points) - 2
        max_x = max(p[0] for p in points) + 2
        max_y = max(p[1] for p in points) + 2
        sw = max(1, max_x - min_x)
        sh = max(1, max_y - min_y)

        cone_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        local_pts = [(p[0] - min_x, p[1] - min_y) for p in points]

        if len(local_pts) >= 3:
            pygame.draw.polygon(cone_surf, (100, 200, 255, 30), local_pts)
            pygame.draw.polygon(cone_surf, (100, 200, 255, 80), local_pts, 1)

        self.screen.blit(cone_surf, (min_x, min_y))

    # ── Turno ──

    def _pass_turn(self):
        self.selection.reset()
        self.passer.reset_turn()
        self._started = True

        # Reset rival ANTES da fase da IA para que os targets persistam
        self.rival_team.reset_turn()
        self.ai_ctrl.reset_turn()

        # P2: Calcula budget e inicia fase animada
        self._ai_phase_budget = self.ai_ctrl.calc_turn_budget(
            ball=self.ball,
            human_players=self.home_team.players,
            rival_players=self.rival_team.players,
        )
        self._ai_phase_active = True
        self._ai_phase_last_tick = pygame.time.get_ticks()
        self._ai_fast_forward = False

        # Se não há budget, finaliza imediatamente
        if self._ai_phase_budget <= 0:
            self._finish_ai_phase()

    def _update_ai_phase(self):
        """Processa uma ação da IA por intervalo de tempo (P2)."""
        now = pygame.time.get_ticks()
        delay = (settings.AI_FAST_FORWARD_DELAY_MS if self._ai_fast_forward
                 else settings.AI_ACTION_DELAY_MS)

        if now - self._ai_phase_last_tick < delay:
            return

        self._ai_phase_last_tick = now

        if self._ai_phase_budget <= 0:
            self._finish_ai_phase()
            return

        # Executa uma única ação da IA
        result = self.ai_ctrl.execute_single_action(
            ball=self.ball,
            human_players=self.home_team.players,
            rival_players=self.rival_team.players,
        )
        self._ai_phase_budget -= 1

        if result is not None:
            self.event_bus.emit("ai_action", {
                "player": result,
                "target": (result.target.x, result.target.y),
                "remaining": self._ai_phase_budget,
            })
        elif self._ai_phase_budget > 0:
            # Nenhum jogador disponível — encerra cedo
            self._ai_phase_budget = 0

        if self._ai_phase_budget <= 0:
            self._finish_ai_phase()

    def _finish_ai_phase(self):
        """Finaliza a fase da IA e devolve controle ao humano."""
        self._ai_phase_active = False
        self._ai_phase_budget = 0
        self._ai_fast_forward = False

        # Avança o turno do humano
        self.turn.pass_turn(self.home_team)

        # Emite evento de turno
        self.event_bus.emit("turn_passed", {"turn": self.turn.current_turn})

    def _check_auto_pass(self):
        """Pula turno quando todos os jogadores esgotaram seu movimento."""
        if self.home_team.all_moved():
            self._pass_turn()

    def _trigger_rival_reaction(self):
        """P5: Reações contextuais — mais rivais reagem em zona perigosa."""
        reactions = self._calc_pressing_reactions()
        for _ in range(reactions):
            self.ai_ctrl.react_to_move(
                ball=self.ball,
                human_players=self.home_team.players,
                rival_players=self.rival_team.players,
            )

    def _calc_pressing_reactions(self) -> int:
        """Calcula quantos rivais reagem baseado na posição da bola."""
        if not self.ball.is_held() or self.ball.owner is None:
            return 1

        carrier = self.ball.owner
        if carrier not in self.home_team.players:
            return 1

        # Limites do campo
        field_right = self.coords.origin_x + self.coords.field_px_w
        field_w = self.coords.field_px_w

        # Zona da grande área rival (últimos ~16% do campo)
        box_threshold = field_right - field_w * 0.16
        if carrier.pos.x >= box_threshold:
            return settings.PRESSING_BOX_REACTIONS

        # Meio-campo rival (últimos ~50%)
        half_threshold = self.coords.origin_x + field_w * 0.5
        if carrier.pos.x >= half_threshold:
            return settings.PRESSING_HALF_ADVANCE_REACTIONS

        return 1

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
        self._intercept_cooldowns.clear()
        self._tackle_cooldown = 0
        self._counter_attack_budget = 0
        self._ai_phase_active = False
        self._ai_phase_budget = 0
        self._ai_phase_last_tick = 0
        self._ai_fast_forward = False
        self.referee = generate_referee(tier=settings.REFEREE_DEFAULT_TIER)
        self._foul_stop_timer = 0

        self.event_bus.emit("game_reset", {})

    def _action_finish(self):
        self.event_bus.emit("match_finish_requested", {})

    # ── P1: Interceptação de passes ──

    def _check_interception(self):
        """Verifica se algum rival intercepta a bola em trânsito."""
        for p in self.rival_team.players:
            pid = id(p)

            # Cooldown ativo — pular
            if self._intercept_cooldowns.get(pid, 0) > 0:
                self._intercept_cooldowns[pid] -= 1
                continue

            dist = p.pos.distance_to(self.ball.pos)
            if dist > settings.INTERCEPT_RADIUS:
                continue

            # Calcula chance baseada em defending
            chance = settings.INTERCEPT_BASE_CHANCE + (
                p.stats.defending * settings.INTERCEPT_DEFENDING_BONUS
            )
            chance = min(chance, settings.INTERCEPT_MAX_CHANCE)

            if random.random() < chance:
                # Interceptação bem-sucedida!
                self.ball.give_to(p)
                self.event_bus.emit("pass_intercepted", {
                    "interceptor": p,
                    "position": (p.pos.x, p.pos.y),
                })
                self._intercept_cooldowns.clear()
                # P4: Contra-ataque
                self._trigger_counter_attack()
                return
            else:
                # Falhou — entra em cooldown
                self._intercept_cooldowns[pid] = settings.INTERCEPT_COOLDOWN_FRAMES

    # ── P3: Tackle / Disputa de bola ──

    def _check_tackle(self):
        """Verifica se algum rival pode disputar bola com o portador."""
        if not self.ball.is_held() or self.ball.owner is None:
            return

        carrier = self.ball.owner
        # Só disputa se o portador é do time humano
        if carrier not in self.home_team.players:
            return

        for p in self.rival_team.players:
            if p.info.position == "GK":
                continue

            dist = p.pos.distance_to(carrier.pos)
            if dist > settings.TACKLE_RADIUS:
                continue

            # Calcula chance: defending do rival - dribbling do portador
            chance = (
                settings.TACKLE_BASE_CHANCE
                + p.stats.defending * settings.TACKLE_DEFENDING_BONUS
                - carrier.stats.dribbling * settings.TACKLE_DRIBBLING_PENALTY
            )
            chance = max(0.10, min(chance, settings.TACKLE_MAX_CHANCE))

            self.event_bus.emit("tackle_attempted", {
                "tackler": p,
                "carrier": carrier,
                "chance": chance,
            })

            if random.random() < chance:
                # Tackle bem-sucedido — bola solta
                self.ball.release()
                # Bola se afasta levemente do portador na direção do tackle
                direction = carrier.pos - p.pos
                if direction.length() > 0:
                    direction.normalize_ip()
                    self.ball.pos = carrier.pos + direction * 15

                self.event_bus.emit("ball_won", {
                    "tackler": p,
                    "carrier": carrier,
                })
                self._tackle_cooldown = 30  # ~0.5s de cooldown
                # P4: Contra-ataque
                self._trigger_counter_attack()
                return
            else:
                # Tackle falhou — árbitro avalia falta
                self._referee_judge_foul(fouler=p, victim=carrier)
                self._tackle_cooldown = 45  # ~0.75s cooldown após falha
                return

    # ── P4: Contra-ataque ──

    def _trigger_counter_attack(self):
        """Dá ações imediatas à IA após recuperar a bola."""
        budget = settings.COUNTER_ATTACK_BUDGET
        for _ in range(budget):
            self.ai_ctrl.react_to_move(
                ball=self.ball,
                human_players=self.home_team.players,
                rival_players=self.rival_team.players,
            )
        self.event_bus.emit("counter_attack", {"budget": budget})

    # ── Árbitro — avaliação de falta e cartão ──

    def _referee_judge_foul(self, fouler, victim):
        """O árbitro decide se marca falta e qual punição aplicar.

        A decisão é influenciada por:
        - strictness → chance de marcar falta
        - accuracy → chance de errar (deixar passar ou marcar fantasma)
        - card_tendency → chance de cartão
        - consistency → variação ao longo da partida
        - composure → efeito de pressão no julgamento
        """
        ref = self.referee
        stats = ref.stats

        # 1) A falta realmente aconteceu? (base de settings)
        base_foul_chance = settings.TACKLE_FOUL_CHANCE

        # 2) Modificador de rigor do árbitro
        foul_chance = base_foul_chance * stats.foul_chance_modifier()

        # 3) Consistência: árbitros inconsistentes variam decisões
        consistency_noise = random.uniform(
            -0.05 * (100 - stats.consistency) / 100,
            0.05 * (100 - stats.consistency) / 100,
        )
        foul_chance += consistency_noise
        foul_chance = max(0.02, min(0.95, foul_chance))

        # 4) O árbitro decide: falta ou não?
        is_foul = random.random() < foul_chance

        # 5) Chance de erro — missed call ou phantom foul
        if is_foul and random.random() < stats.missed_call_chance():
            # Árbitro erra: falta aconteceu mas ele deixou seguir
            self.event_bus.emit("referee_missed_call", {
                "fouler": fouler,
                "victim": victim,
                "referee": ref.name,
            })
            return
        if not is_foul and random.random() < stats.phantom_foul_chance():
            # Árbitro erra: marca falta que não houve
            is_foul = True
            self.event_bus.emit("referee_phantom_foul", {
                "fouler": fouler,
                "victim": victim,
                "referee": ref.name,
            })

        if not is_foul:
            return

        # ── Falta confirmada ──
        ref.record_foul()
        self._foul_stop_timer = settings.REFEREE_FOUL_STOP_FRAMES

        self.event_bus.emit("foul_committed", {
            "fouler": fouler,
            "victim": victim,
            "referee": ref.name,
            "fouls_total": ref.fouls_called,
        })

        # 6) Avaliar cartão
        self._referee_judge_card(fouler)

    def _referee_judge_card(self, fouler):
        """Decide se o árbitro mostra cartão ao jogador."""
        ref = self.referee
        stats = ref.stats

        # Chance base de cartão (regra do jogo)
        base_card_chance = 0.12  # ~12% base

        # Modificador de tendência do árbitro
        card_chance = base_card_chance * stats.card_chance_modifier()

        # Reincidência: mais amarelos = mais chance de cartão
        player_id = id(fouler)
        prev_yellows = ref.player_yellow_count(player_id)
        if prev_yellows > 0:
            card_chance += 0.15 * prev_yellows

        card_chance = max(0.02, min(0.90, card_chance))

        if random.random() >= card_chance:
            return  # Sem cartão

        # Determinar tipo de cartão
        card_type = "yellow"

        # Segundo amarelo → vermelho
        if prev_yellows >= settings.REFEREE_YELLOW_TO_RED - 1:
            card_type = "second_yellow"
        # Chance rara de vermelho direto (infração muito grave)
        elif random.random() < 0.03 * stats.card_chance_modifier():
            card_type = "red"

        ref.record_card(player_id, card_type)
        self._foul_stop_timer = settings.REFEREE_CARD_STOP_FRAMES

        self.event_bus.emit("card_shown", {
            "player": fouler,
            "card_type": card_type,
            "referee": ref.name,
            "total_cards": ref.cards_given,
        })
