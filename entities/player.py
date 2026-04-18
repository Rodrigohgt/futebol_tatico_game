"""Entidade do jogador de futebol.

Responsabilidades:
- Posição / movimentação / colisão em campo (game layer)
- Renderização visual (delegada a PlayerRenderer)
- Dados de identidade e atributos (delegados a PlayerInfo / PlayerStats)

PlayerInfo e PlayerStats são re-exportados aqui para compatibilidade,
mas a definição canônica está em dataclasses locais simples enquanto
o domain layer (domain.player) guarda o modelo de persistência.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from config import settings
from utils.helpers import clamp


# ── Dados leves de gameplay (in-memory, sem persistência) ──

@dataclass
class PlayerStats:
    """Atributos do jogador (0-100) usados em campo."""
    finishing: int = 50
    passing: int = 50
    stamina: int = 50
    pace: int = 50
    dribbling: int = 50
    defending: int = 50
    heading: int = 50
    composure: int = 50
    positioning: int = 50
    vision: int = 50

    @classmethod
    def random(cls) -> PlayerStats:
        return cls(
            finishing=random.randint(40, 95),
            passing=random.randint(40, 95),
            stamina=random.randint(45, 99),
            pace=random.randint(40, 95),
            dribbling=random.randint(40, 90),
            defending=random.randint(30, 90),
            heading=random.randint(30, 85),
            composure=random.randint(40, 90),
            positioning=random.randint(35, 90),
            vision=random.randint(35, 90),
        )

    @property
    def overall(self) -> int:
        vals = [self.finishing, self.passing, self.stamina, self.pace,
                self.dribbling, self.defending, self.heading,
                self.composure, self.positioning, self.vision]
        return sum(vals) // len(vals)


@dataclass
class PlayerInfo:
    """Dados de identidade do jogador."""
    name: str = "Jogador"
    age: int = 25
    number: int = 1
    position: str = "CM"
    status: str = "Titular"


# ── Entidade de campo ──

class Player:
    """Entidade jogável representando um atleta em campo."""

    def __init__(
        self,
        info: PlayerInfo,
        stats: PlayerStats,
        start_x: float,
        start_y: float,
        color: tuple[int, int, int] = (200, 50, 50),
        coord_system=None,
        facing: tuple[float, float] = (1.0, 0.0),
    ):
        self.info = info
        self.stats = stats
        self.color = color
        self.coord_system = coord_system

        self.pos = pygame.Vector2(start_x, start_y)
        self.target = self.pos.copy()
        self.radius = settings.PLAYER_RADIUS

        self.selected = False

        # Movimento em metros (estilo D&D) — 1 ação por turno
        self.max_move_meters = round(
            settings.BASE_MOVE_METERS
            + self.stats.pace * settings.PACE_METER_BONUS, 1
        )
        self.move_meters_remaining = self.max_move_meters

        # Orientação espacial — desacoplada do movimento
        self.facing = pygame.Vector2(facing[0], facing[1])
        if self.facing.length() > 0:
            self.facing.normalize_ip()

    @property
    def rect(self) -> pygame.Rect:
        """Rect de colisão centrado na posição."""
        size = self.radius * 2
        return pygame.Rect(
            self.pos.x - self.radius,
            self.pos.y - self.radius,
            size,
            size,
        )

    def contains_point(self, point: tuple[float, float]) -> bool:
        dx = point[0] - self.pos.x
        dy = point[1] - self.pos.y
        return (dx * dx + dy * dy) <= (self.radius + 4) ** 2

    @property
    def has_moved(self) -> bool:
        """Compatibilidade: True se o jogador esgotou seu movimento."""
        return self.move_meters_remaining < settings.MOVE_EXHAUSTED_THRESHOLD

    @has_moved.setter
    def has_moved(self, value: bool):
        """Setter de compatibilidade — esgota ou restaura metros."""
        if value:
            self.move_meters_remaining = 0.0
        else:
            self.move_meters_remaining = self.max_move_meters

    def can_move(self) -> bool:
        """Retorna True se o jogador ainda tem metros disponíveis."""
        return self.move_meters_remaining >= settings.MOVE_EXHAUSTED_THRESHOLD

    @property
    def move_ratio(self) -> float:
        """Fração de movimento restante (0.0–1.0)."""
        if self.max_move_meters <= 0:
            return 0.0
        return clamp(self.move_meters_remaining / self.max_move_meters, 0.0, 1.0)

    def set_target(self, dest: tuple[float, float]):
        if not self.can_move():
            return

        bounds = self.coord_system.field_bounds()
        tx = clamp(dest[0], bounds[0], bounds[2])
        ty = clamp(dest[1], bounds[1], bounds[3])

        direction = pygame.Vector2(tx, ty) - self.pos
        distance_px = direction.length()
        if distance_px <= 0:
            return

        # Atualiza orientação para o destino
        self.facing = direction.normalize()

        # Converter metros disponíveis em pixels
        scale = min(self.coord_system.scale_x, self.coord_system.scale_y)
        available_px = self.move_meters_remaining * scale

        if distance_px > available_px:
            direction.scale_to_length(available_px)
            limited = self.pos + direction
            self.target = pygame.Vector2(limited.x, limited.y)
            moved_px = available_px
        else:
            self.target = pygame.Vector2(tx, ty)
            moved_px = distance_px

        # Consumir metros proporcionais à distância real
        moved_meters = moved_px / scale
        self.move_meters_remaining = max(0.0, self.move_meters_remaining - moved_meters)

    def reposition(self, dest: tuple[float, float]):
        """Move o jogador para uma posição sem consumir a ação de turno.

        Usado pelo GoalkeeperAI para posicionamento contínuo.
        Ignora has_moved e NÃO o marca como True.
        """
        bounds = self.coord_system.field_bounds()
        tx = clamp(dest[0], bounds[0], bounds[2])
        ty = clamp(dest[1], bounds[1], bounds[3])

        direction = pygame.Vector2(tx, ty) - self.pos
        distance = direction.length()
        if distance <= 0:
            return

        self.facing = direction.normalize()

        max_px = self.coord_system.max_move_px
        if distance > max_px:
            direction.scale_to_length(max_px)
            limited = self.pos + direction
            self.target = pygame.Vector2(limited.x, limited.y)
        else:
            self.target = pygame.Vector2(tx, ty)

    def update(self):
        direction = self.target - self.pos
        dist = direction.length()

        if dist > settings.PLAYER_SPEED:
            direction.scale_to_length(settings.PLAYER_SPEED)
            self.pos += direction
        elif dist > 0:
            self.pos = self.target.copy()

        bounds = self.coord_system.field_bounds()
        self.pos.x = clamp(self.pos.x, bounds[0], bounds[2])
        self.pos.y = clamp(self.pos.y, bounds[1], bounds[3])

    def reset_turn(self):
        self.selected = False
        self.move_meters_remaining = self.max_move_meters
        self.target = self.pos.copy()

    def draw(self, surface: pygame.Surface):
        PlayerRenderer.draw(surface, self)


# ── Renderização isolada ──

class PlayerRenderer:
    """Renderização pura — não acessa banco, não muda estado."""

    _font_number: pygame.font.Font | None = None

    @classmethod
    def _ensure_font(cls):
        if cls._font_number is None:
            cls._font_number = pygame.font.SysFont(None, 20, bold=True)

    @classmethod
    def draw(cls, surface: pygame.Surface, player: Player):
        cls._ensure_font()
        cx, cy = int(player.pos.x), int(player.pos.y)
        r = player.radius
        is_sel = player.selected

        # ── Camada 0: marcador de chão (hexágono) quando selecionado ──
        if is_sel:
            cls._draw_ground_hex(surface, cx, cy, r)

        # ── Camada 1: glow pulsante atrás do corpo ──
        if is_sel:
            cls._draw_selection_glow(surface, cx, cy, r)

        # Sombra
        shadow = pygame.Surface((r * 2 + 4, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 50), shadow.get_rect())
        surface.blit(shadow, (cx - r - 2, cy + r - 2))

        # Indicador de esgotou movimento (cinza discreto)
        if player.has_moved and not is_sel:
            pygame.draw.circle(surface, (100, 100, 100, 180), (cx, cy), r + 3, 2)

        # Seta de direção
        cls._draw_direction_arrow(surface, player)

        # ── Corpo principal ──
        pygame.draw.circle(surface, player.color, (cx, cy), r)

        # Borda do corpo
        if is_sel:
            # Borda dourada vibrante quando selecionado
            pygame.draw.circle(surface, (255, 210, 40), (cx, cy), r, 3)
        else:
            border = tuple(max(0, c - 40) for c in player.color)
            pygame.draw.circle(surface, border, (cx, cy), r, 2)

        # Número da camisa
        num_text = cls._font_number.render(str(player.info.number), True, settings.WHITE)
        num_rect = num_text.get_rect(center=(cx, cy))
        surface.blit(num_text, num_rect)

        # ── Camada sobre o corpo: anel externo + chevron ──
        if is_sel:
            cls._draw_selection_ring(surface, cx, cy, r)
            cls._draw_selection_chevron(surface, cx, cy, r)

        # Label de metros restantes (estilo D&D)
        cls._draw_move_label(surface, player, cx, cy, r)

    _font_move: pygame.font.Font | None = None

    @classmethod
    def _ensure_move_font(cls):
        if cls._font_move is None:
            cls._font_move = pygame.font.SysFont(None, 16, bold=True)

    @classmethod
    def _draw_move_label(cls, surface: pygame.Surface, player: Player,
                         cx: int, cy: int, r: int):
        """Texto estilo D&D mostrando metros restantes — ex: '8/8M' em verde."""
        cls._ensure_move_font()

        remaining = player.move_meters_remaining
        maximum = player.max_move_meters
        ratio = player.move_ratio

        label = f"{remaining:.0f}/{maximum:.0f}M"

        # Cor baseada na fração restante
        if ratio >= 1.0:
            color = (80, 220, 100)     # verde — cheio
        elif ratio > 0.0:
            color = (220, 200, 50)     # amarelo — parcial
        else:
            color = (140, 140, 150)    # cinza — esgotado

        txt = cls._font_move.render(label, True, color)
        txt_rect = txt.get_rect(center=(cx, cy + r + 10))

        # Fundo semi-transparente para legibilidade
        pad = 2
        bg = pygame.Surface((txt_rect.width + pad * 2, txt_rect.height + pad),
                            pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 10, 15, 160), bg.get_rect(), border_radius=3)
        surface.blit(bg, (txt_rect.x - pad, txt_rect.y))
        surface.blit(txt, txt_rect)

    @staticmethod
    def _draw_ground_hex(surface: pygame.Surface, cx: int, cy: int, r: int):
        """Hexágono semi-transparente no chão — indicador de zona selecionada."""
        hex_r = r + 12
        pts = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            pts.append((cx + hex_r * math.cos(angle),
                        cy + hex_r * math.sin(angle) * 0.55))
        sz = hex_r * 2 + 4
        hex_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        local = [(p[0] - cx + sz // 2, p[1] - cy + sz // 2) for p in pts]
        pygame.draw.polygon(hex_surf, (255, 220, 50, 35), local)
        pygame.draw.polygon(hex_surf, (255, 220, 50, 90), local, 2)
        surface.blit(hex_surf, (cx - sz // 2, cy - sz // 2))

    @staticmethod
    def _draw_selection_glow(surface: pygame.Surface, cx: int, cy: int, r: int):
        """Halo pulsante por trás do jogador — glow animado."""
        t = pygame.time.get_ticks()
        pulse = 0.55 + 0.45 * math.sin(t * 0.005)
        alpha = int(40 + 55 * pulse)
        glow_r = int(r + 8 + 4 * pulse)
        glow_sz = (glow_r + 4) * 2
        glow_surf = pygame.Surface((glow_sz, glow_sz), pygame.SRCALPHA)
        center = glow_sz // 2
        pygame.draw.circle(glow_surf, (255, 230, 60, alpha), (center, center), glow_r)
        pygame.draw.circle(glow_surf, (255, 200, 40, alpha // 2), (center, center), glow_r + 3)
        surface.blit(glow_surf, (cx - center, cy - center))

    @staticmethod
    def _draw_selection_ring(surface: pygame.Surface, cx: int, cy: int, r: int):
        """Anel externo segmentado com traços animados — estilo tático moderno."""
        t = pygame.time.get_ticks()
        ring_r = r + 4
        seg_count = 8
        seg_gap = 0.12
        rotation = (t * 0.001) % (2 * math.pi)

        ring_sz = (ring_r + 6) * 2
        ring_surf = pygame.Surface((ring_sz, ring_sz), pygame.SRCALPHA)
        rc = ring_sz // 2

        seg_arc = (2 * math.pi / seg_count) - seg_gap
        for i in range(seg_count):
            start_a = rotation + i * (2 * math.pi / seg_count)
            steps = 12
            pts = []
            for s in range(steps + 1):
                a = start_a + seg_arc * s / steps
                pts.append((rc + ring_r * math.cos(a), rc + ring_r * math.sin(a)))
            if len(pts) >= 2:
                pygame.draw.lines(ring_surf, (255, 220, 50, 220), False, pts, 3)

        surface.blit(ring_surf, (cx - rc, cy - rc))

    @staticmethod
    def _draw_selection_chevron(surface: pygame.Surface, cx: int, cy: int, r: int):
        """Chevron (seta ▼) acima do jogador — indica o jogador ativo."""
        t = pygame.time.get_ticks()
        bob = math.sin(t * 0.006) * 2.5
        top_y = cy - r - 16 + bob

        chev_w = 8
        chev_h = 5
        pts = [
            (cx - chev_w, top_y - chev_h),
            (cx, top_y),
            (cx + chev_w, top_y - chev_h),
        ]
        chev_surf = pygame.Surface((chev_w * 2 + 4, chev_h + 6), pygame.SRCALPHA)
        local = [(p[0] - cx + chev_w + 2, p[1] - top_y + chev_h + 2) for p in pts]
        pygame.draw.polygon(chev_surf, (255, 220, 50, 230), local)
        pygame.draw.polygon(chev_surf, (255, 255, 180, 180), local, 1)
        surface.blit(chev_surf, (cx - chev_w - 2, top_y - chev_h - 2))

    @staticmethod
    def _draw_direction_arrow(surface: pygame.Surface, player: Player):
        """Desenha o triângulo indicador de direção à frente do jogador."""
        if player.facing.length_squared() < 0.01:
            return

        f = player.facing
        arrow_dist = settings.DIRECTION_ARROW_DISTANCE
        arrow_len = settings.DIRECTION_ARROW_LENGTH
        half_base = settings.DIRECTION_ARROW_HALF_BASE

        # Ponta da seta (à frente do jogador)
        tip_x = player.pos.x + f.x * arrow_dist
        tip_y = player.pos.y + f.y * arrow_dist

        # Base da seta (perpendicular à direção)
        perp = pygame.Vector2(-f.y, f.x)
        base_center_x = player.pos.x + f.x * (arrow_dist - arrow_len)
        base_center_y = player.pos.y + f.y * (arrow_dist - arrow_len)

        left_x = base_center_x + perp.x * half_base
        left_y = base_center_y + perp.y * half_base
        right_x = base_center_x - perp.x * half_base
        right_y = base_center_y - perp.y * half_base

        points = [
            (tip_x, tip_y),
            (left_x, left_y),
            (right_x, right_y),
        ]

        # Cor da seta: mais clara que a cor do time
        arrow_color = tuple(min(255, c + 80) for c in player.color)

        # Desenha com superfície alpha para transparência
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        pad = 2
        sw = int(max_x - min_x) + pad * 2 + 1
        sh = int(max_y - min_y) + pad * 2 + 1

        if sw < 1 or sh < 1:
            return

        arrow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        local_pts = [(p[0] - min_x + pad, p[1] - min_y + pad) for p in points]

        fill_color = (*arrow_color, settings.DIRECTION_ARROW_ALPHA)
        pygame.draw.polygon(arrow_surf, fill_color, local_pts)

        # Borda sutil
        border_color = (*tuple(max(0, c - 30) for c in arrow_color), settings.DIRECTION_ARROW_ALPHA)
        pygame.draw.polygon(arrow_surf, border_color, local_pts, 1)

        surface.blit(arrow_surf, (min_x - pad, min_y - pad))
