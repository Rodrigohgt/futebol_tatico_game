"""Tela de pré-partida — seleção de clube e configurações antes do jogo.

Tela intermediária entre o menu principal e a partida, projetada como
container expansível de configurações pré-jogo. Estrutura modular baseada
em painéis e seções, permitindo adicionar facilmente novas opções sem
refatoração (estádio, dificuldade, formação, regras, etc.).
"""

from __future__ import annotations

import pygame

from config import settings
from screens.screen_manager import Screen
from entities.referee import Referee, generate_referee
from screens.ui_components import (
    ClubCard,
    RefereeCard,
    UIButton,
    UIColors,
    UIPanel,
)


# ═══════════════════════════════════════════════════════════
#  DADOS DOS CLUBES
# ═══════════════════════════════════════════════════════════

CLUBS = [
    {
        "name": "Clube Vermelho",
        "primary": (190, 45, 55),
        "secondary": (255, 200, 180),
        "variant": 0,
    },
    {
        "name": "Clube Azul",
        "primary": (45, 85, 190),
        "secondary": (180, 210, 255),
        "variant": 1,
    },
]


# ═══════════════════════════════════════════════════════════
#  PRE-MATCH SCREEN
# ═══════════════════════════════════════════════════════════

class PreMatchScreen(Screen):
    """Tela de configuração pré-partida com seleção de clube.

    Arquitetura de layout:
    ┌─────────────────────────────────────────────┐
    │  HEADER — título + breadcrumb               │
    ├─────────────────────────────────────────────┤
    │  PAINEL: Selecione seu Clube                │
    │  ┌───────────┐     ┌───────────┐            │
    │  │ Card Red  │     │ Card Blue │            │
    │  └───────────┘     └───────────┘            │
    ├─────────────────────────────────────────────┤
    │  (espaço reservado para futuros painéis)    │
    ├─────────────────────────────────────────────┤
    │  FOOTER — botão Voltar | botão Iniciar      │
    └─────────────────────────────────────────────┘
    """

    def __init__(self, screen_manager):
        self._sm = screen_manager

        # Estado
        self._selected_club: int | None = None
        self._selected_referee: int | None = None  # índice no _referee_cards

        # Pool de árbitros gerados
        self._referees: list[Referee] = []

        # Fontes (inicializadas em on_enter)
        self._font_header: pygame.font.Font | None = None
        self._font_breadcrumb: pygame.font.Font | None = None
        self._font_section: pygame.font.Font | None = None
        self._font_button: pygame.font.Font | None = None

        # Componentes (construídos em _build_layout)
        self._club_panel: UIPanel | None = None
        self._club_cards: list[ClubCard] = []
        self._referee_panel: UIPanel | None = None
        self._referee_cards: list[RefereeCard] = []
        self._btn_start: UIButton | None = None
        self._btn_back: UIButton | None = None

        self._built = False

    # ───────────────────────────────────────────
    #  Lifecycle
    # ───────────────────────────────────────────

    def on_enter(self, **kwargs):
        self._selected_club = None
        self._selected_referee = None

        # Gera 3 árbitros aleatórios (um de cada tier)
        self._referees = [
            generate_referee(tier="elite"),
            generate_referee(tier="experienced"),
            generate_referee(tier="developing"),
        ]

        if self._font_header is None:
            self._font_header = pygame.font.SysFont(None, 44, bold=True)
            self._font_breadcrumb = pygame.font.SysFont(None, 20)
            self._font_section = pygame.font.SysFont(None, 22)
            self._font_button = pygame.font.SysFont(None, 28, bold=True)

        self._build_layout()

    def on_exit(self):
        self._selected_club = None
        self._selected_referee = None

    # ───────────────────────────────────────────
    #  Layout builder
    # ───────────────────────────────────────────

    def _build_layout(self):
        """Constrói/reconstrói o layout com base nas dimensões da janela."""
        sw, sh = settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT

        # Margens gerais
        mx = 60
        header_h = 80
        footer_h = 70
        content_top = header_h + 10
        content_bottom = sh - footer_h - 10
        available_h = content_bottom - content_top
        panel_gap = 10

        # ── Painel de seleção de clube (60% do espaço) ──
        panel_w = sw - mx * 2
        club_h = min(int(available_h * 0.58), 300)
        self._club_panel = UIPanel(
            pygame.Rect(mx, content_top, panel_w, club_h),
            title="Selecione seu Clube",
            title_font=self._font_section,
        )

        # ── Cards de clube ──
        cr = self._club_panel.content_rect
        card_w = min(200, (cr.width - 40) // 2)
        card_h = min(220, cr.height - 10)
        gap = 40
        total_w = card_w * 2 + gap
        start_x = cr.x + (cr.width - total_w) // 2
        card_y = cr.y + (cr.height - card_h) // 2

        self._club_cards = []
        for i, club in enumerate(CLUBS):
            rect = pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
            card = ClubCard(
                rect,
                club["name"],
                club["primary"],
                club["secondary"],
                club["variant"],
            )
            self._club_cards.append(card)

        # ── Painel de seleção de árbitro (resto do espaço) ──
        ref_top = content_top + club_h + panel_gap
        ref_h = content_bottom - ref_top
        self._referee_panel = UIPanel(
            pygame.Rect(mx, ref_top, panel_w, ref_h),
            title="Selecione o Árbitro",
            title_font=self._font_section,
        )

        # ── Cards de árbitro ──
        rr = self._referee_panel.content_rect
        num_cards = len(self._referees) + 1  # +1 para "Aleatório"
        ref_card_w = min(140, (rr.width - (num_cards - 1) * 12) // num_cards)
        ref_card_h = min(130, rr.height - 8)
        ref_gap = 12
        total_ref_w = ref_card_w * num_cards + ref_gap * (num_cards - 1)
        ref_start_x = rr.x + (rr.width - total_ref_w) // 2
        ref_card_y = rr.y + (rr.height - ref_card_h) // 2

        self._referee_cards = []
        for i, ref in enumerate(self._referees):
            rect = pygame.Rect(
                ref_start_x + i * (ref_card_w + ref_gap),
                ref_card_y, ref_card_w, ref_card_h,
            )
            self._referee_cards.append(RefereeCard(rect, ref))

        # Card "Aleatório"
        random_rect = pygame.Rect(
            ref_start_x + len(self._referees) * (ref_card_w + ref_gap),
            ref_card_y, ref_card_w, ref_card_h,
        )
        self._referee_cards.append(
            RefereeCard(random_rect, None, is_random=True)
        )

        # ── Botões do footer ──
        btn_w = 180
        btn_h = 44
        btn_y = sh - footer_h + (footer_h - btn_h) // 2

        self._btn_back = UIButton(
            pygame.Rect(mx, btn_y, btn_w, btn_h),
            "← Voltar",
            font=self._font_button,
            on_click=self._on_back,
            color_bg=UIColors.BUTTON_SECONDARY,
            color_hover=UIColors.BUTTON_SECONDARY_HOVER,
            color_text=UIColors.BUTTON_SECONDARY_TEXT,
            color_border=UIColors.BORDER_SUBTLE,
        )

        self._btn_start = UIButton(
            pygame.Rect(sw - mx - btn_w, btn_y, btn_w, btn_h),
            "Iniciar Partida",
            font=self._font_button,
            on_click=self._on_start,
            enabled=False,
        )

        self._built = True

        # Pré-seleciona "Aleatório" por padrão (após botões criados)
        self._select_referee(len(self._referee_cards) - 1)

    # ───────────────────────────────────────────
    #  Events
    # ───────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if not self._built:
            return

        # Teclas de atalho
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return
            if event.key == pygame.K_RETURN and self._selected_club is not None:
                self._on_start()
                return
            if event.key == pygame.K_1:
                self._select_club(0)
                return
            if event.key == pygame.K_2:
                self._select_club(1)
                return
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                if self._selected_club is None:
                    self._select_club(0)
                else:
                    self._select_club(1 - self._selected_club)
                return

        # Botões
        self._btn_back.handle_event(event)
        self._btn_start.handle_event(event)

        # Cards de clube
        for i, card in enumerate(self._club_cards):
            if card.handle_event(event):
                self._select_club(i)

        # Cards de árbitro
        for i, card in enumerate(self._referee_cards):
            if card.handle_event(event):
                self._select_referee(i)

    def _select_club(self, index: int):
        """Atualiza a seleção de clube."""
        self._selected_club = index
        for i, card in enumerate(self._club_cards):
            card.selected = (i == index)
        self._update_start_button()

    def _select_referee(self, index: int):
        """Atualiza a seleção de árbitro."""
        self._selected_referee = index
        for i, card in enumerate(self._referee_cards):
            card.selected = (i == index)
        self._update_start_button()

    def _update_start_button(self):
        """Habilita botão Iniciar quando clube e árbitro estão selecionados."""
        self._btn_start.enabled = (
            self._selected_club is not None
            and self._selected_referee is not None
        )

    # ───────────────────────────────────────────
    #  Actions
    # ───────────────────────────────────────────

    def _on_back(self):
        self._sm.switch("main_menu")

    def _on_start(self):
        if self._selected_club is None or self._selected_referee is None:
            return
        club = CLUBS[self._selected_club]

        # Resolve árbitro selecionado
        card = self._referee_cards[self._selected_referee]
        if card.is_random:
            referee = generate_referee()
        else:
            referee = card.referee

        self._sm.switch("match", selected_club=club, referee=referee)

    # ───────────────────────────────────────────
    #  Update
    # ───────────────────────────────────────────

    def update(self, dt: float):
        if not self._built:
            return
        for card in self._club_cards:
            card.update(dt)
        for card in self._referee_cards:
            card.update(dt)

    # ───────────────────────────────────────────
    #  Render
    # ───────────────────────────────────────────

    def render(self, surface: pygame.Surface):
        if not self._built:
            return

        sw, sh = settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT

        # ── Fundo ──
        surface.fill(UIColors.BG_DARK)

        # Gradiente sutil vertical
        for y in range(sh):
            t = y / sh
            r = int(UIColors.BG_DARK[0] + 6 * t)
            g = int(UIColors.BG_DARK[1] + 4 * t)
            b = int(UIColors.BG_DARK[2] + 10 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (sw, y))

        # ── Header ──
        self._render_header(surface, sw)

        # ── Linha divisória header ──
        pygame.draw.line(
            surface, UIColors.DIVIDER,
            (40, 76), (sw - 40, 76),
        )

        # ── Painel de seleção de clube ──
        self._club_panel.render(surface)
        for card in self._club_cards:
            card.render(surface)

        # ── VS indicator ──
        if len(self._club_cards) == 2:
            mid_x = (self._club_cards[0].rect.right
                     + self._club_cards[1].rect.left) // 2
            mid_y = self._club_cards[0].rect.centery
            vs_font = pygame.font.SysFont(None, 32, bold=True)
            vs_surf = vs_font.render("VS", True, UIColors.TEXT_MUTED)
            vs_rect = vs_surf.get_rect(center=(mid_x, mid_y))
            surface.blit(vs_surf, vs_rect)

        # ── Painel de seleção de árbitro ──
        self._referee_panel.render(surface)
        for card in self._referee_cards:
            card.render(surface)

        # ── Linha divisória footer ──
        footer_line_y = sh - 74
        pygame.draw.line(
            surface, UIColors.DIVIDER,
            (40, footer_line_y), (sw - 40, footer_line_y),
        )

        # ── Botões footer ──
        self._btn_back.render(surface)
        self._btn_start.render(surface)

        # ── Dica de teclado ──
        hint_font = pygame.font.SysFont(None, 18)
        hint = hint_font.render(
            "ESC voltar  •  ←→ ou 1/2 selecionar  •  ENTER confirmar",
            True, UIColors.TEXT_MUTED,
        )
        surface.blit(hint, (sw // 2 - hint.get_width() // 2, sh - 18))

    def _render_header(self, surface: pygame.Surface, sw: int):
        """Renderiza o header com título e breadcrumb."""
        # Breadcrumb
        bc = self._font_breadcrumb.render(
            "Menu  ›  Pré-Partida", True, UIColors.TEXT_MUTED,
        )
        surface.blit(bc, (60, 14))

        # Título
        title = self._font_header.render(
            "Configuração da Partida", True, UIColors.TEXT_PRIMARY,
        )
        surface.blit(title, (60, 34))
