from dataclasses import dataclass, replace
from math import cos, sin, tau

from .agent import AgentState
from .geometry import Vec2
from .interactions import (
    InteractionKind,
    InteractionResult,
    InteractionTarget,
    claim_target,
    dropoff_item,
    pickup_target,
)
from .movement import MovementResult, apply_movement_plan, plan_direct_movement
from .settings import EngineSettings
from .tasks import AgentIntent, TaskTarget, plan_agent_intent


@dataclass(frozen=True)
class SimulationSnapshot:
    agents: tuple[AgentState, ...]
    targets: tuple[InteractionTarget, ...]
    base_position: Vec2


@dataclass(frozen=True)
class AgentStepResult:
    agent: AgentState
    intent: AgentIntent
    movement: MovementResult
    interaction: InteractionResult | None = None


@dataclass(frozen=True)
class SimulationStepResult:
    snapshot: SimulationSnapshot
    agent_results: tuple[AgentStepResult, ...]


def convert_interaction_targets_to_task_targets(
    targets: tuple[InteractionTarget, ...],
) -> tuple[TaskTarget, ...]:
    return tuple(
        TaskTarget(
            id=target.id,
            kind=target.kind,
            position=target.position,
            available=target.available,
            discovered=target.discovered,
        )
        for target in targets
    )


def step_agent(
    agent: AgentState,
    targets: tuple[InteractionTarget, ...],
    base_position: Vec2,
    settings: EngineSettings,
    dt: float,
) -> tuple[AgentStepResult, tuple[InteractionTarget, ...]]:
    discovered_targets = discover_targets_in_range(
        position=agent.position,
        targets=targets,
        detection_radius=settings.agent.detection_radius,
    )
    intent = plan_agent_intent(
        agent=agent,
        available_targets=convert_interaction_targets_to_task_targets(discovered_targets),
        base_position=base_position,
        wander_target=choose_wander_target(agent, settings),
    )

    if intent.should_move:
        movement_plan = plan_direct_movement(
            position=agent.position,
            target_position=intent.target_position,
            settings=settings.movement,
        )
        movement = apply_movement_plan(
            position=agent.position,
            facing=agent.facing,
            plan=movement_plan,
            dt=dt,
        )
    else:
        movement = MovementResult(
            position=agent.position,
            facing=agent.facing,
            reached_target=False,
        )

    updated_agent = replace(
        agent,
        position=Vec2(movement.position.x, movement.position.y),
        facing=Vec2(movement.facing.x, movement.facing.y),
        task_state=intent.task_state,
        target_position=intent.target_position,
    )
    updated_targets = list(discovered_targets)
    interaction_result: InteractionResult | None = None

    if updated_agent.carried_item_id is not None:
        updated_agent, interaction_result = dropoff_item(
            agent=updated_agent,
            base_position=base_position,
            base_radius=settings.agent.base_interaction_radius,
        )
        if (
            interaction_result.succeeded
            and interaction_result.kind is InteractionKind.DROPOFF
        ):
            next_intent = plan_agent_intent(
                agent=updated_agent,
                available_targets=convert_interaction_targets_to_task_targets(
                    tuple(updated_targets)
                ),
                base_position=base_position,
                wander_target=choose_wander_target(updated_agent, settings),
            )
            updated_agent = replace(
                updated_agent,
                task_state=next_intent.task_state,
                target_position=next_intent.target_position,
            )
    elif intent.target_id is not None:
        target_index = _target_index_by_id(updated_targets, intent.target_id)
        if target_index is not None:
            claimed_target, _ = claim_target(updated_agent, updated_targets[target_index])
            updated_targets[target_index] = claimed_target
            updated_agent, picked_target, interaction_result = pickup_target(
                agent=updated_agent,
                target=claimed_target,
                interaction_radius=settings.agent.interaction_radius,
            )
            updated_targets[target_index] = picked_target

    return (
        AgentStepResult(
            agent=updated_agent,
            intent=intent,
            movement=movement,
            interaction=interaction_result,
        ),
        tuple(updated_targets),
    )


def step_simulation(
    snapshot: SimulationSnapshot,
    settings: EngineSettings,
    dt: float,
) -> SimulationStepResult:
    ordered_agents = sorted(snapshot.agents, key=lambda item: item.id)
    current_targets = snapshot.targets
    agent_results: list[AgentStepResult] = []
    updated_agents: list[AgentState] = []

    for agent in ordered_agents:
        agent_result, current_targets = step_agent(
            agent=agent,
            targets=current_targets,
            base_position=snapshot.base_position,
            settings=settings,
            dt=dt,
        )
        agent_results.append(agent_result)
        updated_agents.append(agent_result.agent)

    return SimulationStepResult(
        snapshot=SimulationSnapshot(
            agents=tuple(updated_agents),
            targets=current_targets,
            base_position=snapshot.base_position,
        ),
        agent_results=tuple(agent_results),
    )


def _target_index_by_id(targets: list[InteractionTarget], target_id: int) -> int | None:
    for index, target in enumerate(targets):
        if target.id == target_id:
            return index
    return None


def discover_targets_in_range(
    position: Vec2,
    targets: tuple[InteractionTarget, ...],
    detection_radius: float,
) -> tuple[InteractionTarget, ...]:
    updated_targets: list[InteractionTarget] = []
    for target in targets:
        if target.discovered:
            updated_targets.append(target)
            continue

        if position.distance_to(target.position) <= detection_radius:
            updated_targets.append(replace(target, discovered=True))
            continue

        updated_targets.append(target)
    return tuple(updated_targets)


def choose_wander_target(agent: AgentState, settings: EngineSettings) -> Vec2:
    heading_angle = (agent.id * 1.61803398875) % tau
    heading = Vec2(cos(heading_angle), sin(heading_angle))
    candidate = agent.position + (heading * settings.agent.wander_step_distance)
    return Vec2(
        min(max(candidate.x, 0.0), float(settings.world.width)),
        min(max(candidate.y, 0.0), float(settings.world.height)),
    )
