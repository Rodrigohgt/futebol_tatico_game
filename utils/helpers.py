"""Funções utilitárias genéricas."""

import pygame


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value, hi))


def draw_rounded_rect(surface: pygame.Surface, color, rect: pygame.Rect,
                      radius: int = 8, border: int = 0):
    pygame.draw.rect(surface, color, rect, border, border_radius=radius)
