"""Ponto de entrada do Football Tactics."""

import sys
import os

# Garante que o diretório do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from config import settings
from screens.screen_manager import ScreenManager
from screens.main_menu_screen import MainMenuScreen
from screens.match_screen import MatchScreen
from screens.pre_match_screen import PreMatchScreen


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
    )
    pygame.display.set_caption(settings.WINDOW_TITLE)
    clock = pygame.time.Clock()

    # Screen manager
    sm = ScreenManager()
    sm.register("main_menu", MainMenuScreen(sm))
    sm.register("pre_match", PreMatchScreen(sm))
    sm.register("match", MatchScreen(sm))
    sm.switch("main_menu")

    running = True
    while running:
        dt = clock.tick(settings.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            sm.handle_event(event)

        if not running:
            break

        sm.update(dt)
        sm.render(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
