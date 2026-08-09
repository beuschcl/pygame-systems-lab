from dataclasses import dataclass

from .agent import AgentState, AgentTaskState
from .geometry import Vec2


@dataclass(frozen=True)
class TaskTarget:
    id: int
    kind: str
    position: Vec2
    available: bool = True
    discovered: bool = True


@dataclass(frozen=True)
class AgentIntent:
    task_state: AgentTaskState
    target_position: Vec2 | None
    target_id: int | None = None
    should_move: bool = True


def choose_nearest_available_target(
    position: Vec2,
    targets: list[TaskTarget] | tuple[TaskTarget, ...],
) -> TaskTarget | None:
    available_targets = [
        target for target in targets if target.available and target.discovered
    ]
    if not available_targets:
        return None

    ranked_targets = sorted(
        available_targets,
        key=lambda target: (position.distance_to(target.position), target.id),
    )
    return ranked_targets[0]


def plan_empty_agent_intent(
    agent: AgentState,
    available_targets: list[TaskTarget] | tuple[TaskTarget, ...],
    wander_target: Vec2 | None = None,
) -> AgentIntent:
    selected_target = choose_nearest_available_target(agent.position, available_targets)
    if selected_target is None:
        if wander_target is None:
            wander_target = agent.position
        return AgentIntent(
            task_state=AgentTaskState.WANDERING,
            target_position=wander_target,
            target_id=None,
            should_move=True,
        )

    return AgentIntent(
        task_state=AgentTaskState.SEEKING_TARGET,
        target_position=selected_target.position,
        target_id=selected_target.id,
        should_move=True,
    )


def plan_carrying_agent_intent(agent: AgentState, base_position: Vec2) -> AgentIntent:
    return AgentIntent(
        task_state=AgentTaskState.RETURNING_TO_BASE,
        target_position=base_position,
        target_id=None,
        should_move=True,
    )


def plan_agent_intent(
    agent: AgentState,
    available_targets: list[TaskTarget] | tuple[TaskTarget, ...],
    base_position: Vec2,
    wander_target: Vec2 | None = None,
) -> AgentIntent:
    if agent.carried_item_id is not None:
        return plan_carrying_agent_intent(agent, base_position)
    return plan_empty_agent_intent(agent, available_targets, wander_target=wander_target)
