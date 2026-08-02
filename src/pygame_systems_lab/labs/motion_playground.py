from dataclasses import dataclass, field

import pygame

from .motion import (
    InputState,
    MotionConfig,
    MotionState,
    make_initial_state,
    update_motion,
)


@dataclass(frozen=True)
class PlaygroundConfig:
    title: str = "Motion Playground"
    background_color: tuple[int, int, int] = (20, 24, 36)
    circle_color: tuple[int, int, int] = (110, 200, 255)
    vector_color: tuple[int, int, int] = (255, 220, 120)
    text_color: tuple[int, int, int] = (240, 240, 240)
    fps: int = 60
    vector_scale: float = 0.15
    motion: MotionConfig = field(default_factory=MotionConfig)


DEFAULT_CONFIG = PlaygroundConfig()


def read_input() -> InputState:
    keys = pygame.key.get_pressed()
    return InputState(
        left=bool(keys[pygame.K_LEFT]),
        right=bool(keys[pygame.K_RIGHT]),
        up=bool(keys[pygame.K_UP]),
        down=bool(keys[pygame.K_DOWN]),
    )


def handle_events(paused: bool) -> tuple[bool, bool, bool]:
    running = True
    reset_requested = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                reset_requested = True
            elif event.key == pygame.K_SPACE:
                paused = not paused

    return running, paused, reset_requested


def draw_debug_overlay(
    screen: pygame.Surface,
    font: pygame.font.Font,
    state: MotionState,
    fps: float,
    paused: bool,
    text_color: tuple[int, int, int],
) -> None:
    lines = [
        f"Position: ({state.position.x:.1f}, {state.position.y:.1f})",
        f"Velocity: ({state.velocity.x:.1f}, {state.velocity.y:.1f})",
        f"Acceleration: ({state.acceleration.x:.1f}, {state.acceleration.y:.1f})",
        f"FPS: {fps:.1f}",
        f"Paused: {paused}",
    ]

    y = 10
    for line in lines:
        surface = font.render(line, True, text_color)
        screen.blit(surface, (10, y))
        y += 22


def draw_velocity_vector(
    screen: pygame.Surface,
    state: MotionState,
    scale: float,
    color: tuple[int, int, int],
) -> None:
    start = (round(state.position.x), round(state.position.y))
    end = (
        round(state.position.x + state.velocity.x * scale),
        round(state.position.y + state.velocity.y * scale),
    )
    pygame.draw.line(screen, color, start, end, 3)


def draw_scene(
    screen: pygame.Surface,
    font: pygame.font.Font,
    state: MotionState,
    fps: float,
    paused: bool,
    config: PlaygroundConfig,
) -> None:
    screen.fill(config.background_color)
    draw_velocity_vector(screen, state, config.vector_scale, config.vector_color)
    pygame.draw.circle(
        screen,
        config.circle_color,
        (round(state.position.x), round(state.position.y)),
        config.motion.radius,
    )
    draw_debug_overlay(screen, font, state, fps, paused, config.text_color)
    pygame.display.flip()


def run(config: PlaygroundConfig = DEFAULT_CONFIG) -> None:
    pygame.init()
    pygame.display.set_caption(config.title)
    screen = pygame.display.set_mode(config.motion.size)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    state = make_initial_state(config.motion)
    paused = False
    running = True

    try:
        while running:
            dt = clock.tick(config.fps) / 1000.0
            running, paused, reset_requested = handle_events(paused)

            if reset_requested:
                state = make_initial_state(config.motion)

            if running and not paused:
                state = update_motion(state, read_input(), dt, config.motion)

            draw_scene(screen, font, state, clock.get_fps(), paused, config)
    finally:
        pygame.quit()


def main() -> None:
    run()
