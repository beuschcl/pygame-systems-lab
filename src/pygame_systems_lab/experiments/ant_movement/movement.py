from __future__ import annotations

import math
import random as random_module
from dataclasses import dataclass, replace

from .state import ExperimentAgentState


@dataclass(frozen=True)
class AntMovementSettings:
    world_width: float = 800.0
    world_height: float = 600.0
    boundary_padding: float = 20.0
    turn_speed: float = 12.0
    detection_radius: float = 130.0
    interaction_radius: float = 18.0
    base_interaction_radius: float = 36.0


@dataclass(frozen=True)
class ExperimentAgent:
    id: int
    x: float
    y: float
    speed: float
    heading: float
    state: ExperimentAgentState = ExperimentAgentState.WANDERING
    target_id: int | None = None
    carried_item_id: int | None = None


@dataclass(frozen=True)
class ExperimentTarget:
    id: int
    x: float
    y: float
    radius: float = 8.0
    available: bool = True
    discovered: bool = False


@dataclass(frozen=True)
class BaseState:
    x: float
    y: float
    radius: float = 28.0


@dataclass(frozen=True)
class MovementStep:
    x: float
    y: float
    heading: float
    reached_target: bool


@dataclass(frozen=True)
class ExperimentSnapshot:
    agents: tuple[ExperimentAgent, ...]
    targets: tuple[ExperimentTarget, ...]
    base: BaseState
    collected_count: int = 0


def distance_between(
    first_x: float,
    first_y: float,
    second_x: float,
    second_y: float,
) -> float:
    return math.hypot(second_x - first_x, second_y - first_y)


def move_toward(
    current_x: float,
    current_y: float,
    target_x: float,
    target_y: float,
    speed: float,
    current_heading: float,
) -> MovementStep:
    """Move directly toward a target using the AntProtptype movement shape.

    This intentionally mirrors the important part of Ant.move_toward:
    calculate the target vector, move by min(speed, distance), and update
    heading from atan2. There is no acceleration and no overshoot.
    """
    x_distance = target_x - current_x
    y_distance = target_y - current_y
    distance = math.hypot(x_distance, y_distance)

    if distance == 0:
        return MovementStep(
            x=current_x,
            y=current_y,
            heading=current_heading % 360,
            reached_target=True,
        )

    movement_distance = min(speed, distance)
    next_x = current_x + x_distance / distance * movement_distance
    next_y = current_y + y_distance / distance * movement_distance
    next_heading = math.degrees(math.atan2(y_distance, x_distance)) % 360

    return MovementStep(
        x=next_x,
        y=next_y,
        heading=next_heading,
        reached_target=movement_distance == distance,
    )


def contain_position(
    x: float,
    y: float,
    heading: float,
    settings: AntMovementSettings,
) -> MovementStep:
    padding = settings.boundary_padding
    hit_horizontal_boundary = not (padding <= x <= settings.world_width - padding)
    hit_vertical_boundary = not (padding <= y <= settings.world_height - padding)

    contained_x = min(max(x, padding), settings.world_width - padding)
    contained_y = min(max(y, padding), settings.world_height - padding)
    contained_heading = heading

    if hit_horizontal_boundary:
        contained_heading = 180 - contained_heading
    if hit_vertical_boundary:
        contained_heading = -contained_heading

    return MovementStep(
        x=contained_x,
        y=contained_y,
        heading=contained_heading % 360,
        reached_target=False,
    )


def wander(
    agent: ExperimentAgent,
    rng: random_module.Random,
    settings: AntMovementSettings,
) -> ExperimentAgent:
    heading_radians = math.radians(agent.heading)
    next_x = agent.x + math.cos(heading_radians) * agent.speed
    next_y = agent.y + math.sin(heading_radians) * agent.speed
    next_heading = agent.heading + rng.uniform(-settings.turn_speed, settings.turn_speed)
    contained = contain_position(next_x, next_y, next_heading, settings)

    return replace(
        agent,
        x=contained.x,
        y=contained.y,
        heading=contained.heading,
    )


def discover_targets_for_agent(
    agent: ExperimentAgent,
    targets: tuple[ExperimentTarget, ...],
    settings: AntMovementSettings,
) -> tuple[ExperimentTarget, ...]:
    updated_targets: list[ExperimentTarget] = []
    for target in targets:
        if not target.available:
            updated_targets.append(target)
            continue

        is_discoverable = (
            distance_between(agent.x, agent.y, target.x, target.y)
            <= settings.detection_radius
        )
        updated_targets.append(
            replace(target, discovered=True) if is_discoverable else target
        )

    return tuple(updated_targets)


def choose_nearest_discovered_target(
    agent: ExperimentAgent,
    targets: tuple[ExperimentTarget, ...],
) -> ExperimentTarget | None:
    candidates = tuple(
        target
        for target in targets
        if target.available and target.discovered
    )
    if not candidates:
        return None

    return min(
        candidates,
        key=lambda target: (
            distance_between(agent.x, agent.y, target.x, target.y),
            target.id,
        ),
    )


def target_by_id(
    targets: tuple[ExperimentTarget, ...],
    target_id: int | None,
) -> ExperimentTarget | None:
    if target_id is None:
        return None

    return next((target for target in targets if target.id == target_id), None)


def replace_target(
    targets: tuple[ExperimentTarget, ...],
    replacement: ExperimentTarget,
) -> tuple[ExperimentTarget, ...]:
    return tuple(
        replacement if target.id == replacement.id else target
        for target in targets
    )


def _move_agent_toward_target(
    agent: ExperimentAgent,
    target: ExperimentTarget,
    settings: AntMovementSettings,
) -> ExperimentAgent:
    movement = move_toward(
        current_x=agent.x,
        current_y=agent.y,
        target_x=target.x,
        target_y=target.y,
        speed=agent.speed,
        current_heading=agent.heading,
    )
    contained = contain_position(movement.x, movement.y, movement.heading, settings)
    return replace(agent, x=contained.x, y=contained.y, heading=contained.heading)


def _move_agent_toward_base(
    agent: ExperimentAgent,
    base: BaseState,
    settings: AntMovementSettings,
) -> ExperimentAgent:
    movement = move_toward(
        current_x=agent.x,
        current_y=agent.y,
        target_x=base.x,
        target_y=base.y,
        speed=agent.speed,
        current_heading=agent.heading,
    )
    contained = contain_position(movement.x, movement.y, movement.heading, settings)
    return replace(agent, x=contained.x, y=contained.y, heading=contained.heading)


def _can_pick_up(
    agent: ExperimentAgent,
    target: ExperimentTarget,
    settings: AntMovementSettings,
) -> bool:
    if agent.carried_item_id is not None:
        return False
    if not target.available:
        return False
    return (
        distance_between(agent.x, agent.y, target.x, target.y)
        <= settings.interaction_radius + target.radius
    )


def _can_drop_off(
    agent: ExperimentAgent,
    base: BaseState,
    settings: AntMovementSettings,
) -> bool:
    if agent.carried_item_id is None:
        return False
    return (
        distance_between(agent.x, agent.y, base.x, base.y)
        <= settings.base_interaction_radius + base.radius
    )


def step_agent(
    agent: ExperimentAgent,
    targets: tuple[ExperimentTarget, ...],
    base: BaseState,
    rng: random_module.Random,
    settings: AntMovementSettings,
) -> tuple[ExperimentAgent, tuple[ExperimentTarget, ...], int]:
    """Step one agent through the ant-style loop.

    The order stays intentionally close to the ant project: sense/discover,
    assign a target, move, then collect or deposit.
    """
    collected_delta = 0
    updated_targets = discover_targets_for_agent(agent, targets, settings)
    updated_agent = agent

    if updated_agent.carried_item_id is not None:
        updated_agent = replace(
            updated_agent,
            state=ExperimentAgentState.CARRYING_RESOURCE,
            target_id=None,
        )
        updated_agent = _move_agent_toward_base(updated_agent, base, settings)
        if _can_drop_off(updated_agent, base, settings):
            updated_agent = replace(
                updated_agent,
                carried_item_id=None,
                state=ExperimentAgentState.WANDERING,
                target_id=None,
            )
            collected_delta = 1
        return updated_agent, updated_targets, collected_delta

    selected_target = target_by_id(updated_targets, updated_agent.target_id)
    if selected_target is None or not selected_target.available:
        selected_target = choose_nearest_discovered_target(updated_agent, updated_targets)

    if selected_target is None:
        updated_agent = wander(updated_agent, rng, settings)
        updated_agent = replace(
            updated_agent,
            state=ExperimentAgentState.WANDERING,
            target_id=None,
        )
        return updated_agent, updated_targets, collected_delta

    updated_agent = replace(
        updated_agent,
        state=ExperimentAgentState.SEEKING_RESOURCE,
        target_id=selected_target.id,
    )
    updated_agent = _move_agent_toward_target(updated_agent, selected_target, settings)
    refreshed_target = target_by_id(updated_targets, selected_target.id)

    if refreshed_target is not None and _can_pick_up(
        updated_agent,
        refreshed_target,
        settings,
    ):
        updated_agent = replace(
            updated_agent,
            carried_item_id=refreshed_target.id,
            state=ExperimentAgentState.CARRYING_RESOURCE,
            target_id=None,
        )
        updated_targets = replace_target(
            updated_targets,
            replace(refreshed_target, available=False),
        )

    return updated_agent, updated_targets, collected_delta


def step_snapshot(
    snapshot: ExperimentSnapshot,
    rng: random_module.Random,
    settings: AntMovementSettings,
) -> ExperimentSnapshot:
    agents: list[ExperimentAgent] = []
    targets = snapshot.targets
    collected_count = snapshot.collected_count

    for agent in sorted(snapshot.agents, key=lambda item: item.id):
        updated_agent, targets, collected_delta = step_agent(
            agent=agent,
            targets=targets,
            base=snapshot.base,
            rng=rng,
            settings=settings,
        )
        agents.append(updated_agent)
        collected_count += collected_delta

    return ExperimentSnapshot(
        agents=tuple(agents),
        targets=targets,
        base=snapshot.base,
        collected_count=collected_count,
    )
