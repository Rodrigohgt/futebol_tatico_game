"""Componentes de UI reutilizáveis para telas do jogo.

Módulo de componentes desacoplados que podem ser compostos em qualquer tela.
Cada componente gerencia seu próprio estado, renderização e interação.
"""

from __future__ import annotations

import math
from typing import Callable

import pygame


# ═══════════════════════════════════════════════════════════
#  CORES — paleta base para UI premium
# ═══════════════════════════════════════════════════════════

class UIColors:
    """Paleta centralizada para componentes de UI."""

    BG_DARK = (14, 17, 23)
    BG_PANEL = (22, 26, 35)
    BG_CARD = (30, 35, 48)
    BG_CARD_HOVER = (38, 44, 60)
    BG_CARD_SELECTED = (35, 45, 70)

    BORDER_SUBTLE = (50, 58, 75)
    BORDER_HIGHLIGHT = (100, 160, 255)
    BORDER_SELECTED = (120, 180, 255)

    TEXT_PRIMARY = (230, 235, 245)
    TEXT_SECONDARY = (150, 158, 175)
    TEXT_MUTED = (90, 98, 115)
    TEXT_ACCENT = (100, 170, 255)

    BUTTON_PRIMARY = (55, 120, 220)
    BUTTON_PRIMARY_HOVER = (70, 140, 245)
    BUTTON_PRIMARY_TEXT = (255, 255, 255)

    BUTTON_DISABLED_BG = (40, 44, 55)
    BUTTON_DISABLED_TEXT = (80, 85, 100)
    BUTTON_DISABLED_BORDER = (50, 55, 68)

    BUTTON_SECONDARY = (45, 50, 65)
    BUTTON_SECONDARY_HOVER = (55, 62, 80)
    BUTTON_SECONDARY_TEXT = (200, 205, 218)

    DIVIDER = (45, 52, 68)

    GLOW_BLUE = (80, 150, 255, 40)
    GLOW_RED = (255, 80, 80, 30)

    OVERLAY_BG = (0, 0, 0, 160)

    BUTTON_DANGER = (170, 45, 50)
    BUTTON_DANGER_HOVER = (200, 60, 65)


# ═══════════════════════════════════════════════════════════
#  BUTTON — botão reutilizável com estados
# ═══════════════════════════════════════════════════════════

class UIButton:
    """Botão com suporte a hover, disabled e callback."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        *,
        font: pygame.font.Font | None = None,
        on_click: Callable[[], None] | None = None,
        color_bg: tuple = UIColors.BUTTON_PRIMARY,
        color_hover: tuple = UIColors.BUTTON_PRIMARY_HOVER,
        color_text: tuple = UIColors.BUTTON_PRIMARY_TEXT,
        color_border: tuple | None = None,
        border_radius: int = 8,
        enabled: bool = True,
    ):
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.font = font
        self.color_bg = color_bg
        self.color_hover = color_hover
        self.color_text = color_text
        self.color_border = color_border
        self.border_radius = border_radius
        self.enabled = enabled
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Retorna True se o botão foi clicado."""
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True

        return False

    def render(self, surface: pygame.Surface):
        if self.font is None:
            self.font = pygame.font.SysFont(None, 28, bold=True)

        if not self.enabled:
            bg = UIColors.BUTTON_DISABLED_BG
            text_color = UIColors.BUTTON_DISABLED_TEXT
            border_color = UIColors.BUTTON_DISABLED_BORDER
        elif self._hovered:
            bg = self.color_hover
            text_color = self.color_text
            border_color = self.color_border or self.color_hover
        else:
            bg = self.color_bg
            text_color = self.color_text
            border_color = self.color_border

        pygame.draw.rect(surface, bg, self.rect, border_radius=self.border_radius)

        if border_color:
            pygame.draw.rect(
                surface, border_color, self.rect,
                width=2, border_radius=self.border_radius,
            )

        text_surf = self.font.render(self.label, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


# ═══════════════════════════════════════════════════════════
#  PANEL — container visual com título opcional
# ═══════════════════════════════════════════════════════════

class UIPanel:
    """Painel visual com fundo, borda e título opcional."""

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        title: str = "",
        bg_color: tuple = UIColors.BG_PANEL,
        border_color: tuple = UIColors.BORDER_SUBTLE,
        border_radius: int = 12,
        title_font: pygame.font.Font | None = None,
    ):
        self.rect = rect
        self.title = title
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_radius = border_radius
        self.title_font = title_font

    @property
    def content_rect(self) -> pygame.Rect:
        """Área interna disponível para conteúdo, abaixo do título."""
        offset = 44 if self.title else 16
        return pygame.Rect(
            self.rect.x + 16,
            self.rect.y + offset,
            self.rect.width - 32,
            self.rect.height - offset - 16,
        )

    def render(self, surface: pygame.Surface):
        if self.title_font is None:
            self.title_font = pygame.font.SysFont(None, 22)

        pygame.draw.rect(
            surface, self.bg_color, self.rect,
            border_radius=self.border_radius,
        )
        pygame.draw.rect(
            surface, self.border_color, self.rect,
            width=1, border_radius=self.border_radius,
        )

        if self.title:
            title_surf = self.title_font.render(
                self.title.upper(), True, UIColors.TEXT_SECONDARY,
            )
            surface.blit(
                title_surf,
                (self.rect.x + 20, self.rect.y + 14),
            )
            line_y = self.rect.y + 38
            pygame.draw.line(
                surface, UIColors.DIVIDER,
                (self.rect.x + 16, line_y),
                (self.rect.x + self.rect.width - 16, line_y),
            )


# ═══════════════════════════════════════════════════════════
#  CLUB EMBLEM — emblema geométrico abstrato
# ═══════════════════════════════════════════════════════════

def draw_club_emblem(
    surface: pygame.Surface,
    center: tuple[int, int],
    size: int,
    primary_color: tuple,
    secondary_color: tuple,
    variant: int = 0,
):
    """Desenha um emblema abstrato geométrico para um clube.

    Cada variant gera uma composição visual distinta.
    """
    cx, cy = center
    r = size // 2

    # Escudo base (hexágono arredondado)
    shield_surf = pygame.Surface((size + 4, size + 4), pygame.SRCALPHA)
    sc = size // 2 + 2

    if variant == 0:
        # Variante Vermelho: escudo com chevron
        _draw_hex_shield(shield_surf, sc, sc, r, primary_color)

        # Chevron central
        pts_chev = [
            (sc - r * 0.5, sc - r * 0.15),
            (sc, sc + r * 0.35),
            (sc + r * 0.5, sc - r * 0.15),
        ]
        pygame.draw.lines(shield_surf, secondary_color, False,
                          [(int(x), int(y)) for x, y in pts_chev], 3)

        # Diamante topo
        dr = r * 0.18
        pts_diamond = [
            (sc, sc - r * 0.45 - dr),
            (sc + dr, sc - r * 0.45),
            (sc, sc - r * 0.45 + dr),
            (sc - dr, sc - r * 0.45),
        ]
        pygame.draw.polygon(shield_surf, secondary_color,
                            [(int(x), int(y)) for x, y in pts_diamond])

        # Linhas laterais decorativas
        pygame.draw.line(shield_surf, (*secondary_color[:3], 100),
                         (int(sc - r * 0.65), int(sc + r * 0.1)),
                         (int(sc - r * 0.35), int(sc + r * 0.45)), 2)
        pygame.draw.line(shield_surf, (*secondary_color[:3], 100),
                         (int(sc + r * 0.65), int(sc + r * 0.1)),
                         (int(sc + r * 0.35), int(sc + r * 0.45)), 2)

    elif variant == 1:
        # Variante Azul: escudo com estrela e faixas
        _draw_hex_shield(shield_surf, sc, sc, r, primary_color)

        # Estrela 6 pontas
        _draw_star(shield_surf, sc, int(sc - r * 0.15), int(r * 0.3), 6,
                   secondary_color)

        # Faixa horizontal
        bar_h = int(r * 0.12)
        bar_y = int(sc + r * 0.3)
        bar_rect = pygame.Rect(int(sc - r * 0.55), bar_y, int(r * 1.1), bar_h)
        pygame.draw.rect(shield_surf, secondary_color, bar_rect,
                         border_radius=2)

        # Três pontos sob a faixa
        for dx in (-0.25, 0, 0.25):
            px = int(sc + r * dx)
            py = int(sc + r * 0.55)
            pygame.draw.circle(shield_surf, secondary_color, (px, py),
                               int(r * 0.05) + 1)

    surface.blit(shield_surf, (cx - sc, cy - sc))


def _draw_hex_shield(
    surface: pygame.Surface, cx: int, cy: int, r: int, color: tuple,
):
    """Desenha um escudo hexagonal arredondado."""
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 90)
        px = cx + r * 0.85 * math.cos(angle)
        py = cy + r * 0.9 * math.sin(angle) + r * 0.05
        points.append((int(px), int(py)))

    pygame.draw.polygon(surface, color, points)

    # Borda com brilho sutil
    lighter = tuple(min(c + 40, 255) for c in color[:3])
    pygame.draw.polygon(surface, lighter, points, 2)


def _draw_star(
    surface: pygame.Surface,
    cx: int, cy: int, r: int, points: int, color: tuple,
):
    """Desenha uma estrela com n pontas."""
    pts = []
    for i in range(points * 2):
        angle = math.radians(360 / (points * 2) * i - 90)
        dist = r if i % 2 == 0 else r * 0.45
        px = cx + dist * math.cos(angle)
        py = cy + dist * math.sin(angle)
        pts.append((int(px), int(py)))
    pygame.draw.polygon(surface, color, pts)


# ═══════════════════════════════════════════════════════════
#  CLUB CARD — card de seleção de clube
# ═══════════════════════════════════════════════════════════

class ClubCard:
    """Card interativo para seleção de clube."""

    def __init__(
        self,
        rect: pygame.Rect,
        club_name: str,
        primary_color: tuple,
        secondary_color: tuple,
        emblem_variant: int = 0,
    ):
        self.rect = rect
        self.club_name = club_name
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.emblem_variant = emblem_variant

        self.selected = False
        self._hovered = False
        self._font_name: pygame.font.Font | None = None
        self._font_sub: pygame.font.Font | None = None

        # Animação de seleção
        self._glow_alpha = 0.0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Retorna True se o card foi clicado."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def update(self, dt: float):
        target = 1.0 if self.selected else 0.0
        speed = 5.0
        if self._glow_alpha < target:
            self._glow_alpha = min(target, self._glow_alpha + speed * dt)
        elif self._glow_alpha > target:
            self._glow_alpha = max(target, self._glow_alpha - speed * dt)

    def render(self, surface: pygame.Surface):
        if self._font_name is None:
            self._font_name = pygame.font.SysFont(None, 30, bold=True)
            self._font_sub = pygame.font.SysFont(None, 20)

        # Fundo do card
        if self.selected:
            bg = UIColors.BG_CARD_SELECTED
        elif self._hovered:
            bg = UIColors.BG_CARD_HOVER
        else:
            bg = UIColors.BG_CARD

        pygame.draw.rect(surface, bg, self.rect, border_radius=12)

        # Borda — destaque quando selecionado
        if self.selected:
            border_color = self.primary_color
            border_w = 2
        elif self._hovered:
            border_color = UIColors.BORDER_SUBTLE
            border_w = 1
        else:
            border_color = UIColors.BORDER_SUBTLE
            border_w = 1

        pygame.draw.rect(
            surface, border_color, self.rect,
            width=border_w, border_radius=12,
        )

        # Glow de seleção
        if self._glow_alpha > 0.01:
            glow_surf = pygame.Surface(
                (self.rect.width + 16, self.rect.height + 16), pygame.SRCALPHA,
            )
            glow_color = (*self.primary_color[:3], int(30 * self._glow_alpha))
            pygame.draw.rect(
                glow_surf, glow_color,
                glow_surf.get_rect(),
                border_radius=16,
            )
            surface.blit(
                glow_surf,
                (self.rect.x - 8, self.rect.y - 8),
            )

        # Emblema
        emblem_cx = self.rect.centerx
        emblem_cy = self.rect.y + self.rect.height // 2 - 16
        emblem_size = min(self.rect.width - 60, 90)
        draw_club_emblem(
            surface, (emblem_cx, emblem_cy), emblem_size,
            self.primary_color, self.secondary_color,
            self.emblem_variant,
        )

        # Nome do clube
        name_surf = self._font_name.render(
            self.club_name, True, UIColors.TEXT_PRIMARY,
        )
        name_rect = name_surf.get_rect(
            centerx=self.rect.centerx,
            bottom=self.rect.bottom - 20,
        )
        surface.blit(name_surf, name_rect)

        # Indicador de seleção
        if self.selected:
            check_surf = self._font_sub.render(
                "✓ Selecionado", True, self.primary_color,
            )
            check_rect = check_surf.get_rect(
                centerx=self.rect.centerx,
                bottom=self.rect.bottom - 4,
            )
            surface.blit(check_surf, check_rect)


# ═══════════════════════════════════════════════════════════
#  REFEREE CARD — card compacto para seleção de árbitro
# ═══════════════════════════════════════════════════════════

# Cores por tier de árbitro
_TIER_COLORS = {
    "FIFA": (255, 215, 0),       # dourado
    "Série A": (160, 190, 220),  # prata-azulado
    "Série B": (140, 140, 150),  # cinza
}

_TIER_COLORS_BG = {
    "FIFA": (50, 45, 20),
    "Série A": (30, 38, 50),
    "Série B": (35, 35, 40),
}


class RefereeCard:
    """Card compacto para seleção de árbitro na tela pré-partida."""

    def __init__(
        self,
        rect: pygame.Rect,
        referee,
        *,
        is_random: bool = False,
    ):
        self.rect = rect
        self.referee = referee  # Referee | None (None se is_random)
        self.is_random = is_random

        self.selected = False
        self._hovered = False
        self._glow_alpha = 0.0

        # Fontes lazy
        self._font_name: pygame.font.Font | None = None
        self._font_tier: pygame.font.Font | None = None
        self._font_stat: pygame.font.Font | None = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Retorna True se o card foi clicado."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def update(self, dt: float):
        target = 1.0 if self.selected else 0.0
        speed = 5.0
        if self._glow_alpha < target:
            self._glow_alpha = min(target, self._glow_alpha + speed * dt)
        elif self._glow_alpha > target:
            self._glow_alpha = max(target, self._glow_alpha - speed * dt)

    def render(self, surface: pygame.Surface):
        if self._font_name is None:
            self._font_name = pygame.font.SysFont(None, 19, bold=True)
            self._font_tier = pygame.font.SysFont(None, 16, bold=True)
            self._font_stat = pygame.font.SysFont(None, 15)

        # ── Fundo ──
        if self.selected:
            bg = UIColors.BG_CARD_SELECTED
        elif self._hovered:
            bg = UIColors.BG_CARD_HOVER
        else:
            bg = UIColors.BG_CARD

        pygame.draw.rect(surface, bg, self.rect, border_radius=10)

        # ── Borda ──
        if self.selected and self.referee:
            tier = self.referee.stats.tier_label
            border_color = _TIER_COLORS.get(tier, UIColors.BORDER_SUBTLE)
            border_w = 2
        elif self.selected:
            border_color = UIColors.BORDER_HIGHLIGHT
            border_w = 2
        elif self._hovered:
            border_color = UIColors.BORDER_SUBTLE
            border_w = 1
        else:
            border_color = UIColors.BORDER_SUBTLE
            border_w = 1

        pygame.draw.rect(
            surface, border_color, self.rect,
            width=border_w, border_radius=10,
        )

        # ── Glow de seleção ──
        if self._glow_alpha > 0.01:
            glow_surf = pygame.Surface(
                (self.rect.width + 12, self.rect.height + 12), pygame.SRCALPHA,
            )
            if self.referee:
                tier = self.referee.stats.tier_label
                glow_base = _TIER_COLORS.get(tier, (100, 160, 255))
            else:
                glow_base = (100, 160, 255)
            glow_color = (*glow_base[:3], int(25 * self._glow_alpha))
            pygame.draw.rect(
                glow_surf, glow_color, glow_surf.get_rect(), border_radius=14,
            )
            surface.blit(glow_surf, (self.rect.x - 6, self.rect.y - 6))

        if self.is_random:
            self._render_random(surface)
        else:
            self._render_referee(surface)

    def _render_random(self, surface: pygame.Surface):
        """Renderiza o card de opção aleatória."""
        cx, cy = self.rect.centerx, self.rect.centery

        # Ícone de dados (?)
        icon_font = pygame.font.SysFont(None, 36, bold=True)
        icon = icon_font.render("?", True, UIColors.TEXT_ACCENT)
        icon_rect = icon.get_rect(centerx=cx, centery=cy - 12)
        surface.blit(icon, icon_rect)

        # Label
        label = self._font_name.render("Aleatório", True, UIColors.TEXT_SECONDARY)
        label_rect = label.get_rect(centerx=cx, centery=cy + 16)
        surface.blit(label, label_rect)

        # Indicador de seleção
        if self.selected:
            sel = self._font_stat.render(
                "Selecionado", True, UIColors.TEXT_ACCENT,
            )
            sel_rect = sel.get_rect(centerx=cx, bottom=self.rect.bottom - 4)
            surface.blit(sel, sel_rect)

    def _render_referee(self, surface: pygame.Surface):
        """Renderiza o card com dados do árbitro."""
        ref = self.referee
        if ref is None:
            return

        stats = ref.stats
        tier = stats.tier_label
        tier_color = _TIER_COLORS.get(tier, UIColors.TEXT_SECONDARY)
        tier_bg = _TIER_COLORS_BG.get(tier, UIColors.BG_CARD)

        x, y, w, h = self.rect.x, self.rect.y, self.rect.width, self.rect.height

        # Badge de tier (topo do card)
        badge_h = 20
        badge_rect = pygame.Rect(x + 1, y + 1, w - 2, badge_h)
        badge_surf = pygame.Surface((w - 2, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(
            badge_surf, (*tier_bg, 200),
            (0, 0, w - 2, badge_h),
            border_top_left_radius=9, border_top_right_radius=9,
        )
        surface.blit(badge_surf, badge_rect.topleft)

        tier_surf = self._font_tier.render(tier, True, tier_color)
        tier_rect = tier_surf.get_rect(centerx=x + w // 2, centery=y + badge_h // 2 + 1)
        surface.blit(tier_surf, tier_rect)

        # Nome do árbitro
        name_surf = self._font_name.render(ref.name, True, UIColors.TEXT_PRIMARY)
        # Truncar se muito largo
        if name_surf.get_width() > w - 12:
            # Tenta com nome mais curto
            parts = ref.name.split()
            short = parts[0][0] + ". " + parts[-1] if len(parts) > 1 else ref.name[:12]
            name_surf = self._font_name.render(short, True, UIColors.TEXT_PRIMARY)
        name_rect = name_surf.get_rect(centerx=x + w // 2, top=y + badge_h + 6)
        surface.blit(name_surf, name_rect)

        # Linha divisória
        div_y = y + badge_h + 28
        pygame.draw.line(
            surface, UIColors.DIVIDER,
            (x + 10, div_y), (x + w - 10, div_y),
        )

        # Stats compactos
        stat_y = div_y + 5
        stat_pairs = [
            ("RIG", stats.strictness),
            ("PRE", stats.accuracy),
            ("CAR", stats.card_tendency),
        ]

        for label, value in stat_pairs:
            self._draw_stat_bar(surface, x + 8, stat_y, w - 16, label, value)
            stat_y += 17

        # Indicador de seleção
        if self.selected:
            sel = self._font_stat.render(
                "Selecionado", True, tier_color,
            )
            sel_rect = sel.get_rect(centerx=x + w // 2, bottom=y + h - 3)
            surface.blit(sel, sel_rect)

    def _draw_stat_bar(self, surface, x, y, max_w, label, value):
        """Desenha um stat com mini barra de progresso."""
        # Label
        lbl = self._font_stat.render(label, True, UIColors.TEXT_MUTED)
        surface.blit(lbl, (x, y))

        # Valor
        val_color = UIColors.TEXT_PRIMARY if value >= 60 else UIColors.TEXT_SECONDARY
        val_surf = self._font_stat.render(str(value), True, val_color)
        surface.blit(val_surf, (x + max_w - val_surf.get_width(), y))

        # Barra
        bar_x = x + 30
        bar_w = max_w - 55
        bar_h = 4
        bar_y = y + 8

        # Fundo
        pygame.draw.rect(
            surface, (40, 44, 55),
            (bar_x, bar_y, bar_w, bar_h), border_radius=2,
        )
        # Preenchimento
        fill_w = int(bar_w * value / 100)
        if value >= 70:
            fill_color = (80, 200, 120)
        elif value >= 45:
            fill_color = (200, 180, 60)
        else:
            fill_color = (200, 80, 60)

        if fill_w > 0:
            pygame.draw.rect(
                surface, fill_color,
                (bar_x, bar_y, fill_w, bar_h), border_radius=2,
            )


# ═══════════════════════════════════════════════════════════
#  PAUSE OVERLAY — menu de pausa modal
# ═══════════════════════════════════════════════════════════

class PauseOverlay:
    """Overlay modal de pausa com opções de voltar ao menu ou sair do jogo.

    Renderiza por cima de qualquer tela com fundo semi-transparente.
    Consome todos os eventos enquanto ativo para não vazar para a tela abaixo.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        *,
        on_resume: Callable[[], None] | None = None,
        on_main_menu: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ):
        self.visible = False
        self._sw = screen_width
        self._sh = screen_height

        self._on_resume = on_resume
        self._on_main_menu = on_main_menu
        self._on_quit = on_quit

        # Fontes
        self._font_title: pygame.font.Font | None = None
        self._font_hint: pygame.font.Font | None = None
        self._font_btn: pygame.font.Font | None = None

        # Botões (construídos no primeiro render)
        self._buttons: list[UIButton] = []
        self._built = False

    def _build(self):
        """Constrói layout dos botões centralizados."""
        self._font_title = pygame.font.SysFont(None, 40, bold=True)
        self._font_hint = pygame.font.SysFont(None, 18)
        self._font_btn = pygame.font.SysFont(None, 26, bold=True)

        btn_w = 260
        btn_h = 46
        gap = 14
        total_buttons = 3
        total_h = total_buttons * btn_h + (total_buttons - 1) * gap
        start_y = self._sh // 2 - total_h // 2 + 20
        cx = self._sw // 2

        self._buttons = [
            UIButton(
                pygame.Rect(cx - btn_w // 2, start_y, btn_w, btn_h),
                "Continuar Partida",
                font=self._font_btn,
                on_click=self._resume,
                color_bg=UIColors.BUTTON_PRIMARY,
                color_hover=UIColors.BUTTON_PRIMARY_HOVER,
                color_text=UIColors.BUTTON_PRIMARY_TEXT,
                border_radius=8,
            ),
            UIButton(
                pygame.Rect(cx - btn_w // 2, start_y + btn_h + gap, btn_w, btn_h),
                "Voltar ao Menu",
                font=self._font_btn,
                on_click=self._main_menu,
                color_bg=UIColors.BUTTON_SECONDARY,
                color_hover=UIColors.BUTTON_SECONDARY_HOVER,
                color_text=UIColors.BUTTON_SECONDARY_TEXT,
                color_border=UIColors.BORDER_SUBTLE,
                border_radius=8,
            ),
            UIButton(
                pygame.Rect(cx - btn_w // 2, start_y + 2 * (btn_h + gap), btn_w, btn_h),
                "Fechar Jogo",
                font=self._font_btn,
                on_click=self._quit,
                color_bg=UIColors.BUTTON_DANGER,
                color_hover=UIColors.BUTTON_DANGER_HOVER,
                color_text=UIColors.BUTTON_PRIMARY_TEXT,
                border_radius=8,
            ),
        ]
        self._built = True

    def toggle(self):
        """Alterna visibilidade do overlay."""
        self.visible = not self.visible

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Processa evento. Retorna True se o overlay consumiu o evento."""
        if not self.visible:
            return False

        # ESC fecha o overlay (resume)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()
            return True

        for btn in self._buttons:
            btn.handle_event(event)

        # Consume todos os eventos enquanto visível
        return True

    def render(self, surface: pygame.Surface):
        """Renderiza overlay por cima da surface atual."""
        if not self.visible:
            return

        if not self._built:
            self._build()

        # Fundo semi-transparente
        overlay_surf = pygame.Surface(
            (self._sw, self._sh), pygame.SRCALPHA,
        )
        overlay_surf.fill(UIColors.OVERLAY_BG)
        surface.blit(overlay_surf, (0, 0))

        # Painel central
        panel_w = 340
        panel_h = 300
        px = self._sw // 2 - panel_w // 2
        py = self._sh // 2 - panel_h // 2
        panel_rect = pygame.Rect(px, py, panel_w, panel_h)

        pygame.draw.rect(
            surface, UIColors.BG_PANEL, panel_rect, border_radius=14,
        )
        pygame.draw.rect(
            surface, UIColors.BORDER_SUBTLE, panel_rect,
            width=1, border_radius=14,
        )

        # Título
        title_surf = self._font_title.render(
            "Jogo Pausado", True, UIColors.TEXT_PRIMARY,
        )
        title_rect = title_surf.get_rect(
            centerx=self._sw // 2, top=py + 24,
        )
        surface.blit(title_surf, title_rect)

        # Linha divisória
        div_y = py + 66
        pygame.draw.line(
            surface, UIColors.DIVIDER,
            (px + 20, div_y), (px + panel_w - 20, div_y),
        )

        # Botões
        for btn in self._buttons:
            btn.render(surface)

        # Hint
        hint_surf = self._font_hint.render(
            "ESC para continuar", True, UIColors.TEXT_MUTED,
        )
        hint_rect = hint_surf.get_rect(
            centerx=self._sw // 2, bottom=py + panel_h - 12,
        )
        surface.blit(hint_surf, hint_rect)

    # ── Callbacks internos ──

    def _resume(self):
        self.hide()
        if self._on_resume:
            self._on_resume()

    def _main_menu(self):
        self.hide()
        if self._on_main_menu:
            self._on_main_menu()

    def _quit(self):
        self.hide()
        if self._on_quit:
            self._on_quit()
