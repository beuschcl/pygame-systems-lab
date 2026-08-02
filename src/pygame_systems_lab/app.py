from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class AppConfig:
    title: str = "Pygame Systems Lab"
    size: tuple[int, int] = (800, 600)
    background_color: tuple[int, int, int] = (30, 30, 45)
    fps: int = 60


DEFAULT_CONFIG = AppConfig()


def handle_events() -> bool:
    """Return False when the user asks to close the window."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
    return True


def run(config: AppConfig = DEFAULT_CONFIG) -> None:
    pygame.init()
    pygame.display.set_caption(config.title)
    screen = pygame.display.set_mode(config.size)
    clock = pygame.time.Clock()
    running = True

    try:
        while running:
            running = handle_events()
            screen.fill(config.background_color)
            pygame.display.flip()
            clock.tick(config.fps)
    finally:
        pygame.quit()


def main() -> None:
    run()
