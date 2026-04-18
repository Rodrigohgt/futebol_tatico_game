"""Conversão entre coordenadas reais (metros) e coordenadas de tela (pixels).

Centraliza toda a lógica de escala em um único lugar. Qualquer módulo que
precise posicionar elementos no campo deve usar esta classe.
"""

from config import settings, field_specs


class CoordinateSystem:
    """Converte metros do campo FIFA em pixels da tela."""

    def __init__(self):
        playable_height = settings.WINDOW_HEIGHT - settings.HUD_BOTTOM_HEIGHT
        self.field_px_w = settings.WINDOW_WIDTH - 2 * settings.MARGIN_X
        self.field_px_h = playable_height - 2 * settings.MARGIN_Y
        self.origin_x = settings.MARGIN_X
        self.origin_y = settings.MARGIN_Y

        self.scale_x = self.field_px_w / field_specs.FIELD_LENGTH
        self.scale_y = self.field_px_h / field_specs.FIELD_WIDTH

        self.max_move_px = min(self.scale_x, self.scale_y) * settings.MAX_MOVE_METERS

    def m2px_x(self, meters: float) -> float:
        return self.origin_x + meters * self.scale_x

    def m2px_y(self, meters: float) -> float:
        return self.origin_y + meters * self.scale_y

    def m2px_w(self, meters: float) -> float:
        return meters * self.scale_x

    def m2px_h(self, meters: float) -> float:
        return meters * self.scale_y

    def field_bounds(self) -> tuple[float, float, float, float]:
        """Retorna (min_x, min_y, max_x, max_y) da área jogável em pixels."""
        pad = settings.PLAYER_BOUNDARY_PADDING
        return (
            self.origin_x + pad,
            self.origin_y + pad,
            self.origin_x + self.field_px_w - pad,
            self.origin_y + self.field_px_h - pad,
        )

    def field_center_px(self) -> tuple[float, float]:
        return (
            self.origin_x + self.field_px_w / 2,
            self.origin_y + self.field_px_h / 2,
        )
