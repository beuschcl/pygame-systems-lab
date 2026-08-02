from dataclasses import dataclass, field

import pygame

from .motion import (
    InputState,
    MotionConfig,
    MotionState,
    Vec2,
    make_initial_state,
    point_is_inside_circle,
    speed_from_velocity,
    update_motion,
)


@dataclass(frozen=True)
class PlaygroundConfig:
    object_name: str = "Motion Circle"
    title: str = "Motion Playground"
    background_color: tuple[int, int, int] = (20, 24, 36)
    circle_color: tuple[int, int, int] = (110, 200, 255)
    vector_color: tuple[int, int, int] = (255, 220, 120)
    text_color: tuple[int, int, int] = (240, 240, 240)
    selection_ring_color: tuple[int, int, int] = (255, 255, 255)
    panel_background_color: tuple[int, int, int] = (34, 40, 56)
    panel_border_color: tuple[int, int, int] = (85, 96, 130)
    fps: int = 60
    inspector_width: int = 220
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


def mouse_position_to_vec2(position: tuple[int, int]) -> Vec2:
    return Vec2(float(position[0]), float(position[1]))


def handle_events(
    paused: bool,
    state: MotionState,
    selected: bool,
    radius: int,
) -> tuple[bool, bool, bool, bool]:
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
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click_position = mouse_position_to_vec2(event.pos)
            selected = point_is_inside_circle(click_position, state.position, radius)

    return running, paused, reset_requested, selected


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


def draw_selection_ring(
    screen: pygame.Surface,
    state: MotionState,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    pygame.draw.circle(
        screen,
        color,
        (round(state.position.x), round(state.position.y)),
        radius + 6,
        3,
    )


def draw_inspector_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    state: MotionState,
    paused: bool,
    config: PlaygroundConfig,
) -> None:
    panel_width = config.inspector_width
    window_width, window_height = screen.get_size()
    panel_rect = pygame.Rect(window_width - panel_width, 0, panel_width, window_height)

    pygame.draw.rect(screen, config.panel_background_color, panel_rect)
    pygame.draw.rect(screen, config.panel_border_color, panel_rect, 2)

    lines = [
        "Inspector",
        f"Name: {config.object_name}",
        f"Position: ({state.position.x:.1f}, {state.position.y:.1f})",
        f"Velocity: ({state.velocity.x:.1f}, {state.velocity.y:.1f})",
        f"Acceleration: ({state.acceleration.x:.1f}, {state.acceleration.y:.1f})",
        f"Speed: {speed_from_velocity(state.velocity):.1f}",
        f"Radius: {config.motion.radius}",
        f"Paused: {paused}",
    ]

    y = 16
    for line in lines:
        surface = font.render(line, True, config.text_color)
        screen.blit(surface, (panel_rect.x + 12, y))
        y += 24


def draw_scene(
    screen: pygame.Surface,
    font: pygame.font.Font,
    state: MotionState,
    fps: float,
    paused: bool,
    selected: bool,
    config: PlaygroundConfig,
) -> None:
    screen.fill(config.background_color)
    draw_velocity_vector(screen, state, config.vector_scale, config.vector_color)
    if selected:
        draw_selection_ring(
            screen,
            state,
            config.motion.radius,
            config.selection_ring_color,
        )
    pygame.draw.circle(
        screen,
        config.circle_color,
        (round(state.position.x), round(state.position.y)),
        config.motion.radius,
    )
    draw_debug_overlay(screen, font, state, fps, paused, config.text_color)
    if selected:
        draw_inspector_panel(screen, font, state, paused, config)
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
    selected = False

    try:
        while running:
            dt = clock.tick(config.fps) / 1000.0
            running, paused, reset_requested, selected = handle_events(
                paused,
                state,
                selected,
                config.motion.radius,
            )

            if reset_requested:
                state = make_initial_state(config.motion)
                selected = False

            if running and not paused:
                state = update_motion(state, read_input(), dt, config.motion)

            draw_scene(screen, font, state, clock.get_fps(), paused, selected, config)
    finally:
        pygame.quit()


def main() -> None:
    run()
