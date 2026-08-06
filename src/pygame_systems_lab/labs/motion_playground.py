from dataclasses import dataclass, field
from random import Random

import pygame

from .collision import RectangleObstacle
from .history import (
    SignalMarker,
    TrailPoint,
    add_signal_marker,
    add_trail_point,
    age_signal_markers,
    age_trail_points,
    fade_ratio,
    remove_expired_signal_markers,
    remove_expired_trail_points,
)
from .motion import MotionConfig, Vec2, speed_from_velocity
from .multi_agent import AgentState, create_initial_agents, select_agent_by_point
from .resource_loop import (
    ResourceNode,
    create_initial_resources,
    update_one_agent_task,
    update_resource_loop_for_all_agents,
)
from .steering import SteeringConfig, apply_clicked_target, distance_to_target


@dataclass(frozen=True)
class PlaygroundActions:
    running: bool
    paused: bool
    selected_agent_id: int | None
    reset_requested: bool = False
    toggle_trails_requested: bool = False
    clear_trails_requested: bool = False
    drop_signal_requested: bool = False
    toggle_hitboxes_requested: bool = False
    toggle_steering_requested: bool = False
    target_position: Vec2 | None = None
    target_changed: bool = False


def default_obstacles() -> tuple[RectangleObstacle, ...]:
    return (
        RectangleObstacle("Top Block", 300.0, 120.0, 140.0, 36.0),
        RectangleObstacle("Left Block", 150.0, 250.0, 120.0, 36.0),
        RectangleObstacle("Right Block", 520.0, 340.0, 120.0, 36.0),
    )


@dataclass(frozen=True)
class PlaygroundConfig:
    title: str = "Motion Playground - Lab 7: Resource Pickup Loop"
    background_color: tuple[int, int, int] = (20, 24, 36)
    obstacle_color: tuple[int, int, int] = (80, 110, 145)
    signal_color: tuple[int, int, int] = (255, 120, 170)
    text_color: tuple[int, int, int] = (240, 240, 240)
    selection_ring_color: tuple[int, int, int] = (255, 255, 255)
    carrying_ring_color: tuple[int, int, int] = (255, 220, 120)
    hitbox_color: tuple[int, int, int] = (255, 170, 90)
    panel_background_color: tuple[int, int, int] = (34, 40, 56)
    panel_border_color: tuple[int, int, int] = (85, 96, 130)
    base_fill_color: tuple[int, int, int] = (80, 140, 240)
    base_outline_color: tuple[int, int, int] = (170, 210, 255)
    resource_color: tuple[int, int, int] = (120, 255, 140)
    resource_collected_color: tuple[int, int, int] = (70, 90, 70)
    fps: int = 60
    agent_count: int = 5
    resource_count: int = 6
    inspector_width: int = 280
    trail_radius: int = 5
    signal_radius: int = 10
    signal_thickness: int = 2
    resource_radius: int = 8
    base_radius: int = 28
    pickup_radius: float = 18.0
    trail_lifetime: float = 1.6
    signal_lifetime: float = 2.4
    motion: MotionConfig = field(default_factory=MotionConfig)
    steering: SteeringConfig = field(default_factory=SteeringConfig)
    obstacles: tuple[RectangleObstacle, ...] = field(default_factory=default_obstacles)
    base_position: Vec2 = field(default_factory=lambda: Vec2(90.0, 510.0))
    random_seed: int = 7


DEFAULT_CONFIG = PlaygroundConfig()


def mouse_position_to_vec2(position: tuple[int, int]) -> Vec2:
    return Vec2(float(position[0]), float(position[1]))


def get_agent_by_id(
    agents: list[AgentState] | tuple[AgentState, ...],
    agent_id: int | None,
) -> AgentState | None:
    if agent_id is None:
        return None
    for agent in agents:
        if agent.id == agent_id:
            return agent
    return None


def replace_agent(agents: list[AgentState], updated_agent: AgentState) -> list[AgentState]:
    return [updated_agent if agent.id == updated_agent.id else agent for agent in agents]


def handle_events(
    paused: bool,
    agents: list[AgentState] | tuple[AgentState, ...],
    selected_agent_id: int | None,
    radius: int,
) -> PlaygroundActions:
    running = True
    reset_requested = False
    toggle_trails_requested = False
    clear_trails_requested = False
    drop_signal_requested = False
    toggle_hitboxes_requested = False
    toggle_steering_requested = False
    target_position = None
    target_changed = False

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
            elif event.key == pygame.K_t:
                toggle_trails_requested = True
            elif event.key == pygame.K_c:
                clear_trails_requested = True
            elif event.key == pygame.K_s:
                drop_signal_requested = True
            elif event.key == pygame.K_h:
                toggle_hitboxes_requested = True
            elif event.key == pygame.K_a:
                toggle_steering_requested = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click_position = mouse_position_to_vec2(event.pos)
            clicked_agent = select_agent_by_point(agents, click_position, radius)
            if clicked_agent is not None:
                selected_agent_id = clicked_agent.id
            elif selected_agent_id is not None:
                target_position = click_position
                target_changed = True

    return PlaygroundActions(
        running=running,
        paused=paused,
        selected_agent_id=selected_agent_id,
        reset_requested=reset_requested,
        toggle_trails_requested=toggle_trails_requested,
        clear_trails_requested=clear_trails_requested,
        drop_signal_requested=drop_signal_requested,
        toggle_hitboxes_requested=toggle_hitboxes_requested,
        toggle_steering_requested=toggle_steering_requested,
        target_position=target_position,
        target_changed=target_changed,
    )


def format_target(target_position: Vec2) -> str:
    return f"({target_position.x:.1f}, {target_position.y:.1f})"


def count_available_resources(resources: list[ResourceNode] | tuple[ResourceNode, ...]) -> int:
    return sum(1 for resource in resources if resource.available)


def count_carried_resources(agents: list[AgentState] | tuple[AgentState, ...]) -> int:
    return sum(1 for agent in agents if agent.carried_resource_id is not None)


def draw_debug_overlay(
    screen: pygame.Surface,
    font: pygame.font.Font,
    fps: float,
    paused: bool,
    trails_enabled: bool,
    total_trail_count: int,
    show_hitboxes: bool,
    steering_enabled: bool,
    agents: list[AgentState] | tuple[AgentState, ...],
    resources: list[ResourceNode] | tuple[ResourceNode, ...],
    collected_resource_count: int,
    selected_agent: AgentState | None,
    text_color: tuple[int, int, int],
) -> None:
    selected_text = "None"
    if selected_agent is not None:
        selected_text = f"{selected_agent.id} / {selected_agent.name}"

    lines = [
        f"FPS: {fps:.1f}",
        f"Paused: {paused}",
        f"Steering: {steering_enabled}",
        f"Agent Count: {len(agents)}",
        f"Selected: {selected_text}",
        f"Available Resources: {count_available_resources(resources)}",
        f"Carried Resources: {count_carried_resources(agents)}",
        f"Collected Count: {collected_resource_count}",
        f"Trails: {trails_enabled} ({total_trail_count})",
        f"Hitboxes: {show_hitboxes}",
    ]

    y = 10
    for line in lines:
        surface = font.render(line, True, text_color)
        screen.blit(surface, (10, y))
        y += 22


def draw_obstacles(
    screen: pygame.Surface,
    obstacles: tuple[RectangleObstacle, ...],
    color: tuple[int, int, int],
) -> None:
    for obstacle in obstacles:
        pygame.draw.rect(
            screen,
            color,
            pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height),
            border_radius=6,
        )


def draw_base(
    screen: pygame.Surface,
    font: pygame.font.Font,
    position: Vec2,
    radius: int,
    fill_color: tuple[int, int, int],
    outline_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> None:
    center = (round(position.x), round(position.y))
    pygame.draw.circle(screen, fill_color, center, radius)
    pygame.draw.circle(screen, outline_color, center, radius, 3)
    label = font.render("BASE", True, text_color)
    screen.blit(label, (center[0] - 24, center[1] - 10))


def draw_resources(
    screen: pygame.Surface,
    resources: list[ResourceNode] | tuple[ResourceNode, ...],
    available_color: tuple[int, int, int],
    collected_color: tuple[int, int, int],
    radius: int,
) -> None:
    for resource in resources:
        center = (round(resource.position.x), round(resource.position.y))
        color = available_color if resource.available else collected_color
        pygame.draw.circle(screen, color, center, radius)
        pygame.draw.circle(screen, (25, 30, 40), center, radius, 2)
        if not resource.available:
            pygame.draw.line(
                screen,
                (25, 30, 40),
                (center[0] - radius, center[1] - radius),
                (center[0] + radius, center[1] + radius),
                2,
            )
            pygame.draw.line(
                screen,
                (25, 30, 40),
                (center[0] - radius, center[1] + radius),
                (center[0] + radius, center[1] - radius),
                2,
            )


def draw_hitboxes(
    screen: pygame.Surface,
    agents: list[AgentState] | tuple[AgentState, ...],
    obstacles: tuple[RectangleObstacle, ...],
    radius: int,
    color: tuple[int, int, int],
) -> None:
    for obstacle in obstacles:
        pygame.draw.rect(
            screen,
            color,
            pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height),
            2,
            border_radius=6,
        )

    for agent in agents:
        pygame.draw.circle(
            screen,
            color,
            (round(agent.position.x), round(agent.position.y)),
            radius,
            2,
        )


def color_with_fade(
    color: tuple[int, int, int],
    age: float,
    lifetime: float,
) -> tuple[int, int, int, int]:
    return (*color, round(255 * fade_ratio(age, lifetime)))


def draw_trail_points(
    screen: pygame.Surface,
    trails_by_agent: dict[int, list[TrailPoint]],
    agents: list[AgentState] | tuple[AgentState, ...],
    trail_radius: int,
    fallback_color: tuple[int, int, int],
) -> None:
    color_by_agent = {agent.id: agent.color for agent in agents}
    for agent_id, trail_points in trails_by_agent.items():
        color = color_by_agent.get(agent_id, fallback_color)
        for point in trail_points:
            pygame.draw.circle(
                screen,
                color_with_fade(color, point.age, point.lifetime),
                (round(point.position.x), round(point.position.y)),
                trail_radius,
            )


def draw_signal_markers(
    screen: pygame.Surface,
    signal_markers: list[SignalMarker],
    config: PlaygroundConfig,
) -> None:
    for marker in signal_markers:
        center = (round(marker.position.x), round(marker.position.y))
        color = color_with_fade(config.signal_color, marker.age, marker.lifetime)
        pygame.draw.circle(
            screen,
            color,
            center,
            config.signal_radius,
            config.signal_thickness,
        )
        pygame.draw.line(
            screen,
            color,
            (center[0] - config.signal_radius, center[1]),
            (center[0] + config.signal_radius, center[1]),
            config.signal_thickness,
        )
        pygame.draw.line(
            screen,
            color,
            (center[0], center[1] - config.signal_radius),
            (center[0], center[1] + config.signal_radius),
            config.signal_thickness,
        )


def draw_selection_ring(
    screen: pygame.Surface,
    agent: AgentState,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    pygame.draw.circle(
        screen,
        color,
        (round(agent.position.x), round(agent.position.y)),
        radius + 5,
        2,
    )


def draw_agent_body(
    screen: pygame.Surface,
    agent: AgentState,
    radius: int,
    carrying_ring_color: tuple[int, int, int],
) -> None:
    center = (round(agent.position.x), round(agent.position.y))
    pygame.draw.circle(
        screen,
        agent.color,
        center,
        radius,
    )
    if agent.carried_resource_id is not None:
        pygame.draw.circle(
            screen,
            carrying_ring_color,
            center,
            radius - 5,
            3,
        )


def draw_inspector_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    selected_agent: AgentState,
    config: PlaygroundConfig,
) -> None:
    panel_width = config.inspector_width
    window_width, window_height = screen.get_size()
    panel_rect = pygame.Rect(window_width - panel_width, 0, panel_width, window_height)

    pygame.draw.rect(screen, config.panel_background_color, panel_rect)
    pygame.draw.rect(screen, config.panel_border_color, panel_rect, 2)

    carrying_text = "None"
    if selected_agent.carried_resource_id is not None:
        carrying_text = str(selected_agent.carried_resource_id)

    lines = [
        "Inspector",
        f"ID: {selected_agent.id}",
        f"Name: {selected_agent.name}",
        f"Task: {selected_agent.task_state}",
        f"Carrying: {carrying_text}",
        f"Position: ({selected_agent.position.x:.1f}, {selected_agent.position.y:.1f})",
        f"Velocity: ({selected_agent.velocity.x:.1f}, {selected_agent.velocity.y:.1f})",
        f"Acceleration: ({selected_agent.acceleration.x:.1f}, {selected_agent.acceleration.y:.1f})",
        f"Speed: {speed_from_velocity(selected_agent.velocity):.1f}",
        f"Target: {format_target(selected_agent.target_position)}",
        f"Target Dist: {distance_to_target(selected_agent.position, selected_agent.target_position):.1f}",
    ]

    y = 16
    for line in lines:
        surface = font.render(line, True, config.text_color)
        screen.blit(surface, (panel_rect.x + 12, y))
        y += 24


def total_trail_count(trails_by_agent: dict[int, list[TrailPoint]]) -> int:
    return sum(len(points) for points in trails_by_agent.values())


def age_and_prune_trails(
    trails_by_agent: dict[int, list[TrailPoint]],
    dt: float,
) -> dict[int, list[TrailPoint]]:
    return {
        agent_id: remove_expired_trail_points(age_trail_points(points, dt))
        for agent_id, points in trails_by_agent.items()
    }


def draw_scene(
    screen: pygame.Surface,
    font: pygame.font.Font,
    agents: list[AgentState],
    resources: list[ResourceNode],
    fps: float,
    paused: bool,
    selected_agent_id: int | None,
    trails_enabled: bool,
    trails_by_agent: dict[int, list[TrailPoint]],
    signal_markers: list[SignalMarker],
    show_hitboxes: bool,
    steering_enabled: bool,
    collected_resource_count: int,
    config: PlaygroundConfig,
) -> None:
    screen.fill(config.background_color)
    draw_trail_points(
        screen=screen,
        trails_by_agent=trails_by_agent,
        agents=agents,
        trail_radius=config.trail_radius,
        fallback_color=config.text_color,
    )
    draw_signal_markers(screen, signal_markers, config)
    draw_obstacles(screen, config.obstacles, config.obstacle_color)
    draw_base(
        screen=screen,
        font=font,
        position=config.base_position,
        radius=config.base_radius,
        fill_color=config.base_fill_color,
        outline_color=config.base_outline_color,
        text_color=config.text_color,
    )
    draw_resources(
        screen=screen,
        resources=resources,
        available_color=config.resource_color,
        collected_color=config.resource_collected_color,
        radius=config.resource_radius,
    )

    selected_agent = get_agent_by_id(agents, selected_agent_id)

    if show_hitboxes:
        draw_hitboxes(
            screen=screen,
            agents=agents,
            obstacles=config.obstacles,
            radius=config.motion.radius,
            color=config.hitbox_color,
        )

    for agent in agents:
        draw_agent_body(
            screen=screen,
            agent=agent,
            radius=config.motion.radius,
            carrying_ring_color=config.carrying_ring_color,
        )
        if selected_agent is not None and agent.id == selected_agent.id:
            draw_selection_ring(
                screen=screen,
                agent=agent,
                radius=config.motion.radius,
                color=config.selection_ring_color,
            )

    draw_debug_overlay(
        screen=screen,
        font=font,
        fps=fps,
        paused=paused,
        trails_enabled=trails_enabled,
        total_trail_count=total_trail_count(trails_by_agent),
        show_hitboxes=show_hitboxes,
        steering_enabled=steering_enabled,
        agents=agents,
        resources=resources,
        collected_resource_count=collected_resource_count,
        selected_agent=selected_agent,
        text_color=config.text_color,
    )
    if selected_agent is not None:
        draw_inspector_panel(
            screen=screen,
            font=font,
            selected_agent=selected_agent,
            config=config,
        )
    pygame.display.flip()


def initialize_agent_tasks(
    agents: list[AgentState],
    resources: list[ResourceNode],
    base_position: Vec2,
    base_radius: float,
    pickup_radius: float,
) -> tuple[list[AgentState], list[ResourceNode]]:
    updated_agents: list[AgentState] = []
    updated_resources = list(resources)
    for agent in agents:
        task_agent, updated_resources, _ = update_one_agent_task(
            agent=agent,
            resources=updated_resources,
            base_position=base_position,
            base_radius=base_radius,
            pickup_radius=pickup_radius,
        )
        updated_agents.append(task_agent)
    return updated_agents, updated_resources


def run(config: PlaygroundConfig = DEFAULT_CONFIG) -> None:
    pygame.init()
    pygame.display.set_caption(config.title)
    screen = pygame.display.set_mode(config.motion.size, pygame.SRCALPHA)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    random_source = Random(config.random_seed)

    agents = create_initial_agents(
        agent_count=config.agent_count,
        world_size=config.motion.size,
        circle_radius=config.motion.radius,
        obstacles=config.obstacles,
        steering_config=config.steering,
        random_source=random_source,
    )
    resources = create_initial_resources(
        resource_count=config.resource_count,
        world_size=config.motion.size,
        circle_radius=config.motion.radius,
        obstacles=config.obstacles,
        steering_config=config.steering,
        random_source=random_source,
    )
    agents, resources = initialize_agent_tasks(
        agents=agents,
        resources=resources,
        base_position=config.base_position,
        base_radius=config.base_radius,
        pickup_radius=config.pickup_radius,
    )

    trails_by_agent: dict[int, list[TrailPoint]] = {agent.id: [] for agent in agents}
    signal_markers: list[SignalMarker] = []
    collected_resource_count = 0
    paused = False
    running = True
    selected_agent_id: int | None = None
    steering_enabled = True
    trails_enabled = True
    show_hitboxes = False

    try:
        while running:
            dt = clock.tick(config.fps) / 1000.0
            actions = handle_events(
                paused=paused,
                agents=agents,
                selected_agent_id=selected_agent_id,
                radius=config.motion.radius,
            )
            running = actions.running
            paused = actions.paused
            selected_agent_id = actions.selected_agent_id

            if actions.toggle_trails_requested:
                trails_enabled = not trails_enabled

            if actions.clear_trails_requested:
                trails_by_agent = {agent.id: [] for agent in agents}

            if actions.drop_signal_requested and agents:
                selected_agent = get_agent_by_id(agents, selected_agent_id)
                marker_source = selected_agent if selected_agent is not None else agents[0]
                signal_markers = add_signal_marker(
                    signal_markers,
                    marker_source.position,
                    config.signal_lifetime,
                )

            if actions.toggle_hitboxes_requested:
                show_hitboxes = not show_hitboxes

            if actions.toggle_steering_requested:
                steering_enabled = not steering_enabled

            if (
                actions.target_changed
                and actions.target_position is not None
                and selected_agent_id is not None
            ):
                selected_agent = get_agent_by_id(agents, selected_agent_id)
                if selected_agent is not None:
                    safe_target, _ = apply_clicked_target(
                        clicked_target=actions.target_position,
                        obstacles=config.obstacles,
                        config=config.steering,
                        circle_radius=config.motion.radius,
                        active_detour=selected_agent.active_detour,
                    )
                    agents = replace_agent(
                        agents=agents,
                        updated_agent=AgentState(
                            id=selected_agent.id,
                            name=selected_agent.name,
                            position=selected_agent.position,
                            velocity=selected_agent.velocity,
                            acceleration=selected_agent.acceleration,
                            color=selected_agent.color,
                            target_position=safe_target,
                            active_detour=None,
                            task_state=selected_agent.task_state,
                            carried_resource_id=selected_agent.carried_resource_id,
                        ),
                    )

            if actions.reset_requested:
                agents = create_initial_agents(
                    agent_count=config.agent_count,
                    world_size=config.motion.size,
                    circle_radius=config.motion.radius,
                    obstacles=config.obstacles,
                    steering_config=config.steering,
                    random_source=random_source,
                )
                resources = create_initial_resources(
                    resource_count=config.resource_count,
                    world_size=config.motion.size,
                    circle_radius=config.motion.radius,
                    obstacles=config.obstacles,
                    steering_config=config.steering,
                    random_source=random_source,
                )
                agents, resources = initialize_agent_tasks(
                    agents=agents,
                    resources=resources,
                    base_position=config.base_position,
                    base_radius=config.base_radius,
                    pickup_radius=config.pickup_radius,
                )
                trails_by_agent = {agent.id: [] for agent in agents}
                collected_resource_count = 0
                selected_agent_id = None

            if running and not paused and steering_enabled:
                update_result = update_resource_loop_for_all_agents(
                    agents=agents,
                    resources=resources,
                    dt=dt,
                    motion_config=config.motion,
                    steering_config=config.steering,
                    obstacles=config.obstacles,
                    base_position=config.base_position,
                    base_radius=config.base_radius,
                    pickup_radius=config.pickup_radius,
                    random_source=random_source,
                )
                agents = update_result.agents
                resources = update_result.resources
                collected_resource_count += update_result.collected_increment

                for agent in agents:
                    trails_by_agent.setdefault(agent.id, [])
                    if trails_enabled:
                        trails_by_agent[agent.id] = add_trail_point(
                            trails_by_agent[agent.id],
                            agent.position,
                            config.trail_lifetime,
                        )

            trails_by_agent = age_and_prune_trails(trails_by_agent, dt)
            signal_markers = remove_expired_signal_markers(
                age_signal_markers(signal_markers, dt)
            )

            draw_scene(
                screen=screen,
                font=font,
                agents=agents,
                resources=resources,
                fps=clock.get_fps(),
                paused=paused,
                selected_agent_id=selected_agent_id,
                trails_enabled=trails_enabled,
                trails_by_agent=trails_by_agent,
                signal_markers=signal_markers,
                show_hitboxes=show_hitboxes,
                steering_enabled=steering_enabled,
                collected_resource_count=collected_resource_count,
                config=config,
            )
    finally:
        pygame.quit()


def main() -> None:
    run()
