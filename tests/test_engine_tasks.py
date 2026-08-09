from pygame_systems_lab.engine.agent import AgentState, AgentTaskState
from pygame_systems_lab.engine.geometry import Vec2
from pygame_systems_lab.engine.tasks import (
    TaskTarget,
    choose_nearest_available_target,
    plan_agent_intent,
    plan_carrying_agent_intent,
    plan_empty_agent_intent,
)


def make_agent(*, carried_item_id: int | None = None) -> AgentState:
    return AgentState(
        id=1,
        name="Agent 1",
        position=Vec2(0.0, 0.0),
        facing=Vec2(1.0, 0.0),
        speed=20.0,
        task_state=AgentTaskState.WAITING,
        carried_item_id=carried_item_id,
    )


def test_nearest_available_target_is_selected() -> None:
    targets = [
        TaskTarget(id=20, kind="sample", position=Vec2(30.0, 0.0)),
        TaskTarget(id=10, kind="sample", position=Vec2(5.0, 0.0)),
    ]

    selected = choose_nearest_available_target(Vec2(0.0, 0.0), targets)

    assert selected == targets[1]


def test_unavailable_targets_are_ignored() -> None:
    targets = [
        TaskTarget(id=10, kind="sample", position=Vec2(3.0, 0.0), available=False),
        TaskTarget(id=11, kind="sample", position=Vec2(8.0, 0.0), available=True),
    ]

    selected = choose_nearest_available_target(Vec2(0.0, 0.0), targets)

    assert selected == targets[1]


def test_undiscovered_targets_are_ignored() -> None:
    targets = [
        TaskTarget(id=10, kind="sample", position=Vec2(3.0, 0.0), discovered=False),
        TaskTarget(id=11, kind="sample", position=Vec2(8.0, 0.0), discovered=True),
    ]

    selected = choose_nearest_available_target(Vec2(0.0, 0.0), targets)

    assert selected == targets[1]


def test_tie_breaking_uses_target_id() -> None:
    targets = [
        TaskTarget(id=30, kind="sample", position=Vec2(6.0, 8.0)),
        TaskTarget(id=10, kind="sample", position=Vec2(-6.0, -8.0)),
    ]

    selected = choose_nearest_available_target(Vec2(0.0, 0.0), targets)

    assert selected == targets[1]


def test_empty_agent_with_available_target_seeks_target() -> None:
    agent = make_agent()
    target = TaskTarget(id=7, kind="sample", position=Vec2(15.0, 4.0))

    intent = plan_empty_agent_intent(agent, [target])

    assert intent.task_state is AgentTaskState.SEEKING_TARGET
    assert intent.target_position == target.position
    assert intent.target_id == target.id
    assert intent.should_move is True


def test_empty_agent_with_no_available_targets_waits() -> None:
    agent = make_agent()
    unavailable_target = TaskTarget(
        id=7,
        kind="sample",
        position=Vec2(15.0, 4.0),
        available=False,
    )

    intent = plan_empty_agent_intent(
        agent,
        [unavailable_target],
        wander_target=Vec2(6.0, 9.0),
    )

    assert intent.task_state is AgentTaskState.WANDERING
    assert intent.target_position == Vec2(6.0, 9.0)
    assert intent.target_id is None
    assert intent.should_move is True


def test_carrying_agent_returns_to_base() -> None:
    agent = make_agent(carried_item_id=42)
    base_position = Vec2(100.0, 50.0)

    intent = plan_carrying_agent_intent(agent, base_position)

    assert intent.task_state is AgentTaskState.RETURNING_TO_BASE
    assert intent.target_position == base_position
    assert intent.target_id is None
    assert intent.should_move is True


def test_plan_agent_intent_routes_carrying_vs_empty() -> None:
    target = TaskTarget(id=9, kind="sample", position=Vec2(20.0, 10.0))
    base_position = Vec2(2.0, 3.0)

    carrying_intent = plan_agent_intent(
        agent=make_agent(carried_item_id=5),
        available_targets=[target],
        base_position=base_position,
    )
    empty_intent = plan_agent_intent(
        agent=make_agent(carried_item_id=None),
        available_targets=[target],
        base_position=base_position,
    )

    assert carrying_intent.task_state is AgentTaskState.RETURNING_TO_BASE
    assert carrying_intent.target_position == base_position
    assert carrying_intent.target_id is None
    assert carrying_intent.should_move is True

    assert empty_intent.task_state is AgentTaskState.SEEKING_TARGET
    assert empty_intent.target_position == target.position
    assert empty_intent.target_id == target.id
    assert empty_intent.should_move is True
