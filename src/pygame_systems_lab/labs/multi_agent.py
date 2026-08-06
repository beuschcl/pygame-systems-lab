from dataclasses import dataclass
from random import Random

from .collision import RectangleObstacle, check_circle_against_obstacles
from .motion import (
    MotionConfig,
    MotionState,
    Vec2,
    point_is_inside_circle,
    update_motion_with_acceleration,
)
from .steering import (
    SteeringConfig,
    choose_active_steering_target,
    desired_velocity_toward_target,
    distance_to_target,
    point_is_outside_all_obstacles,
    resolve_clicked_target_against_obstacles,
    steering_acceleration_toward_velocity,
)


@dataclass(frozen=True)
class AgentState:
    id: int
    name: str
    position: Vec2
    velocity: Vec2
    acceleration: Vec2
    color: tuple[int, int, int]
    target_position: Vec2
    active_detour: Vec2 | None = None
    task_state: str = "seeking_resource"
    carried_resource_id: int | None = None


DEFAULT_AGENT_COLORS = (
    (110, 200, 255),
    (255, 180, 110),
    (170, 255, 140),
    (220, 150, 255),
    (255, 120, 170),
)


def clamp_point_to_world(point: Vec2, world_size: tuple[int, int], radius: float) -> Vec2:
    width, height = world_size
    return Vec2(
        min(max(point.x, radius), width - radius),
        min(max(point.y, radius), height - radius),
    )


def random_world_point(
    random_source: Random,
    world_size: tuple[int, int],
    radius: float,
) -> Vec2:
    width, height = world_size
    return Vec2(
        random_source.uniform(radius, width - radius),
        random_source.uniform(radius, height - radius),
    )


def assign_safe_random_target(
    position: Vec2,
    world_size: tuple[int, int],
    circle_radius: float,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    steering_config: SteeringConfig,
    random_source: Random,
    attempts: int = 32,
) -> Vec2:
    clearance = circle_radius + steering_config.detour_margin
    for _ in range(attempts):
        candidate = random_world_point(random_source, world_size, circle_radius)
        resolved = resolve_clicked_target_against_obstacles(candidate, obstacles, clearance)
        resolved = clamp_point_to_world(resolved, world_size, circle_radius)
        if point_is_outside_all_obstacles(resolved, obstacles, clearance):
            return resolved

    fallback = resolve_clicked_target_against_obstacles(position, obstacles, clearance)
    return clamp_point_to_world(fallback, world_size, circle_radius)


def create_initial_agents(
    agent_count: int,
    world_size: tuple[int, int],
    circle_radius: float,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    steering_config: SteeringConfig,
    random_source: Random,
) -> list[AgentState]:
    agents: list[AgentState] = []
    clearance = circle_radius + steering_config.detour_margin

    for index in range(agent_count):
        position = random_world_point(random_source, world_size, circle_radius)
        if not point_is_outside_all_obstacles(position, obstacles, clearance):
            position = assign_safe_random_target(
                position=position,
                world_size=world_size,
                circle_radius=circle_radius,
                obstacles=obstacles,
                steering_config=steering_config,
                random_source=random_source,
            )

        target = assign_safe_random_target(
            position=position,
            world_size=world_size,
            circle_radius=circle_radius,
            obstacles=obstacles,
            steering_config=steering_config,
            random_source=random_source,
        )
        color = DEFAULT_AGENT_COLORS[index % len(DEFAULT_AGENT_COLORS)]
        agents.append(
            AgentState(
                id=index + 1,
                name=f"Agent {index + 1}",
                position=position,
                velocity=Vec2(0.0, 0.0),
                acceleration=Vec2(0.0, 0.0),
                color=color,
                target_position=target,
            )
        )

    return agents


def select_agent_by_point(
    agents: list[AgentState] | tuple[AgentState, ...],
    click_position: Vec2,
    circle_radius: float,
) -> AgentState | None:
    hit_agents = [
        agent
        for agent in agents
        if point_is_inside_circle(click_position, agent.position, circle_radius)
    ]
    if not hit_agents:
        return None
    return min(
        hit_agents,
        key=lambda agent: distance_to_target(click_position, agent.position),
    )


def update_one_agent_toward_target(
    agent: AgentState,
    dt: float,
    motion_config: MotionConfig,
    steering_config: SteeringConfig,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    random_source: Random,
) -> AgentState:
    target_choice = choose_active_steering_target(
        position=agent.position,
        target=agent.target_position,
        obstacles=obstacles,
        config=steering_config,
        circle_radius=motion_config.radius,
        active_detour=agent.active_detour,
    )
    active_target = target_choice.active_target
    if active_target is None:
        desired_velocity = Vec2(0.0, 0.0)
    else:
        desired_velocity = desired_velocity_toward_target(
            agent.position,
            active_target,
            steering_config,
        )
    steering_acceleration = steering_acceleration_toward_velocity(
        agent.velocity,
        desired_velocity,
        steering_config.max_acceleration,
    )

    updated_motion = update_motion_with_acceleration(
        state=MotionState(
            position=agent.position,
            velocity=agent.velocity,
            acceleration=agent.acceleration,
        ),
        acceleration=steering_acceleration,
        dt=dt,
        config=motion_config,
    )
    collision = check_circle_against_obstacles(
        position=updated_motion.position,
        previous_position=agent.position,
        velocity=updated_motion.velocity,
        radius=motion_config.radius,
        obstacles=obstacles,
    )
    if collision.collided:
        updated_motion = MotionState(
            position=collision.position,
            velocity=collision.velocity,
            acceleration=updated_motion.acceleration,
        )

    target_position = agent.target_position
    active_detour = target_choice.detour_point
    if distance_to_target(updated_motion.position, target_position) <= steering_config.stop_radius:
        target_position = assign_safe_random_target(
            position=updated_motion.position,
            world_size=motion_config.size,
            circle_radius=motion_config.radius,
            obstacles=obstacles,
            steering_config=steering_config,
            random_source=random_source,
        )
        active_detour = None

    return AgentState(
        id=agent.id,
        name=agent.name,
        position=updated_motion.position,
        velocity=updated_motion.velocity,
        acceleration=updated_motion.acceleration,
        color=agent.color,
        target_position=target_position,
        active_detour=active_detour,
        task_state=agent.task_state,
        carried_resource_id=agent.carried_resource_id,
    )


def update_agents(
    agents: list[AgentState] | tuple[AgentState, ...],
    dt: float,
    motion_config: MotionConfig,
    steering_config: SteeringConfig,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    random_source: Random,
) -> list[AgentState]:
    return [
        update_one_agent_toward_target(
            agent=agent,
            dt=dt,
            motion_config=motion_config,
            steering_config=steering_config,
            obstacles=obstacles,
            random_source=random_source,
        )
        for agent in agents
    ]
