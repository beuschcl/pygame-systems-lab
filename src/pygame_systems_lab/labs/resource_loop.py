from dataclasses import dataclass
from random import Random

from .collision import RectangleObstacle
from .motion import MotionConfig, Vec2
from .multi_agent import (
    AgentState,
    assign_safe_random_target,
    update_one_agent_toward_target,
)
from .steering import SteeringConfig, distance_to_target


@dataclass(frozen=True)
class ResourceNode:
    id: int
    position: Vec2
    available: bool = True


@dataclass(frozen=True)
class ResourceLoopResult:
    agents: list[AgentState]
    resources: list[ResourceNode]
    collected_increment: int


def create_initial_resources(
    resource_count: int,
    world_size: tuple[int, int],
    circle_radius: float,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    steering_config: SteeringConfig,
    random_source: Random,
) -> list[ResourceNode]:
    resources: list[ResourceNode] = []
    for index in range(resource_count):
        safe_position = assign_safe_random_target(
            position=Vec2(world_size[0] / 2.0, world_size[1] / 2.0),
            world_size=world_size,
            circle_radius=circle_radius,
            obstacles=obstacles,
            steering_config=steering_config,
            random_source=random_source,
        )
        resources.append(ResourceNode(id=index + 1, position=safe_position, available=True))
    return resources


def choose_nearest_available_resource(
    position: Vec2,
    resources: list[ResourceNode] | tuple[ResourceNode, ...],
) -> ResourceNode | None:
    available_resources = [resource for resource in resources if resource.available]
    if not available_resources:
        return None
    return min(
        available_resources,
        key=lambda resource: distance_to_target(position, resource.position),
    )


def detect_resource_pickup(
    position: Vec2,
    resources: list[ResourceNode] | tuple[ResourceNode, ...],
    pickup_radius: float,
) -> ResourceNode | None:
    nearest = choose_nearest_available_resource(position, resources)
    if nearest is None:
        return None
    if distance_to_target(position, nearest.position) <= pickup_radius:
        return nearest
    return None


def detect_base_dropoff(
    position: Vec2,
    base_position: Vec2,
    base_radius: float,
) -> bool:
    return distance_to_target(position, base_position) <= base_radius


def mark_resource_collected(
    resources: list[ResourceNode] | tuple[ResourceNode, ...],
    resource_id: int,
) -> list[ResourceNode]:
    updated: list[ResourceNode] = []
    for resource in resources:
        if resource.id == resource_id:
            updated.append(
                ResourceNode(
                    id=resource.id,
                    position=resource.position,
                    available=False,
                )
            )
        else:
            updated.append(resource)
    return updated


def update_one_agent_task(
    agent: AgentState,
    resources: list[ResourceNode] | tuple[ResourceNode, ...],
    base_position: Vec2,
    base_radius: float,
    pickup_radius: float,
) -> tuple[AgentState, list[ResourceNode], int]:
    updated_resources = list(resources)
    collected_increment = 0
    current_agent = agent

    if current_agent.carried_resource_id is not None:
        if detect_base_dropoff(current_agent.position, base_position, base_radius):
            collected_increment = 1
            current_agent = AgentState(
                id=current_agent.id,
                name=current_agent.name,
                position=current_agent.position,
                velocity=current_agent.velocity,
                acceleration=current_agent.acceleration,
                color=current_agent.color,
                target_position=current_agent.target_position,
                active_detour=current_agent.active_detour,
                task_state="seeking_resource",
                carried_resource_id=None,
            )
        else:
            return (
                AgentState(
                    id=current_agent.id,
                    name=current_agent.name,
                    position=current_agent.position,
                    velocity=current_agent.velocity,
                    acceleration=current_agent.acceleration,
                    color=current_agent.color,
                    target_position=base_position,
                    active_detour=current_agent.active_detour,
                    task_state="returning_to_base",
                    carried_resource_id=current_agent.carried_resource_id,
                ),
                updated_resources,
                collected_increment,
            )

    picked_resource = detect_resource_pickup(
        current_agent.position,
        updated_resources,
        pickup_radius,
    )
    if picked_resource is not None:
        updated_resources = mark_resource_collected(updated_resources, picked_resource.id)
        return (
            AgentState(
                id=current_agent.id,
                name=current_agent.name,
                position=current_agent.position,
                velocity=current_agent.velocity,
                acceleration=current_agent.acceleration,
                color=current_agent.color,
                target_position=base_position,
                active_detour=current_agent.active_detour,
                task_state="returning_to_base",
                carried_resource_id=picked_resource.id,
            ),
            updated_resources,
            collected_increment,
        )

    nearest_resource = choose_nearest_available_resource(
        current_agent.position,
        updated_resources,
    )
    if nearest_resource is None:
        return (
            AgentState(
                id=current_agent.id,
                name=current_agent.name,
                position=current_agent.position,
                velocity=current_agent.velocity,
                acceleration=current_agent.acceleration,
                color=current_agent.color,
                target_position=current_agent.position,
                active_detour=current_agent.active_detour,
                task_state="idle",
                carried_resource_id=None,
            ),
            updated_resources,
            collected_increment,
        )

    return (
        AgentState(
            id=current_agent.id,
            name=current_agent.name,
            position=current_agent.position,
            velocity=current_agent.velocity,
            acceleration=current_agent.acceleration,
            color=current_agent.color,
            target_position=nearest_resource.position,
            active_detour=current_agent.active_detour,
            task_state="seeking_resource",
            carried_resource_id=None,
        ),
        updated_resources,
        collected_increment,
    )


def update_resource_loop_for_all_agents(
    agents: list[AgentState] | tuple[AgentState, ...],
    resources: list[ResourceNode] | tuple[ResourceNode, ...],
    dt: float,
    motion_config: MotionConfig,
    steering_config: SteeringConfig,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    base_position: Vec2,
    base_radius: float,
    pickup_radius: float,
    random_source: Random,
) -> ResourceLoopResult:
    updated_agents: list[AgentState] = []
    updated_resources = list(resources)
    total_collected_increment = 0

    for agent in agents:
        moved_agent = update_one_agent_toward_target(
            agent=agent,
            dt=dt,
            motion_config=motion_config,
            steering_config=steering_config,
            obstacles=obstacles,
            random_source=random_source,
        )
        task_agent, updated_resources, collected_increment = update_one_agent_task(
            agent=moved_agent,
            resources=updated_resources,
            base_position=base_position,
            base_radius=base_radius,
            pickup_radius=pickup_radius,
        )
        updated_agents.append(task_agent)
        total_collected_increment += collected_increment

    return ResourceLoopResult(
        agents=updated_agents,
        resources=updated_resources,
        collected_increment=total_collected_increment,
    )
