from dataclasses import dataclass

from .agent import AgentState, AgentTaskState
from .geometry import Vec2


@dataclass(frozen=True)
class TaskTarget:
    id: int
    kind: str
    position: Vec2
    available: bool = True


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
    available_targets = [target for target in targets if target.available]
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
) -> AgentIntent:
    selected_target = choose_nearest_available_target(agent.position, available_targets)
    if selected_target is None:
        return AgentIntent(
            task_state=AgentTaskState.WAITING,
            target_position=None,
            target_id=None,
            should_move=False,
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
) -> AgentIntent:
    if agent.carried_item_id is not None:
        return plan_carrying_agent_intent(agent, base_position)
    return plan_empty_agent_intent(agent, available_targets)
