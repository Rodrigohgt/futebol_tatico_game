"""Processamento centralizado de eventos de entrada."""

import pygame


class InputEvent:
    """Resultado processado de um frame de input."""

    def __init__(self):
        self.quit = False
        self.key_escape = False
        self.left_click: tuple[int, int] | None = None
        self.left_press: tuple[int, int] | None = None   # botão pressionado
        self.left_release: tuple[int, int] | None = None  # botão solto
        self.right_click: tuple[int, int] | None = None   # botão direito
        self.right_press: tuple[int, int] | None = None    # direito pressionado
        self.right_release: tuple[int, int] | None = None  # direito solto
        self.mouse_pos: tuple[int, int] = (0, 0)
        self.left_held: bool = False
        self.right_held: bool = False


class InputHandler:
    """Converte eventos brutos do Pygame em dados estruturados."""

    @staticmethod
    def process(events: list | None = None) -> InputEvent:
        """Processa eventos pygame.

        Se *events* for fornecido, usa essa lista (modo ScreenManager).
        Caso contrário, consome a fila diretamente (modo standalone).
        """
        result = InputEvent()
        result.mouse_pos = pygame.mouse.get_pos()
        result.left_held = pygame.mouse.get_pressed()[0]

        if events is None:
            events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                result.quit = True

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                result.key_escape = True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                result.left_click = event.pos
                result.left_press = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                result.left_release = event.pos

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                result.right_click = event.pos
                result.right_press = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                result.right_release = event.pos

        result.right_held = pygame.mouse.get_pressed()[2]
        return result
