from dataclasses import dataclass, replace

from .agent import AgentState
from .geometry import Vec2
from .interactions import (
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
    intent = plan_agent_intent(
        agent=agent,
        available_targets=convert_interaction_targets_to_task_targets(targets),
        base_position=base_position,
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
    updated_targets = list(targets)
    interaction_result: InteractionResult | None = None

    if updated_agent.carried_item_id is not None:
        updated_agent, interaction_result = dropoff_item(
            agent=updated_agent,
            base_position=base_position,
            base_radius=settings.agent.base_interaction_radius,
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
