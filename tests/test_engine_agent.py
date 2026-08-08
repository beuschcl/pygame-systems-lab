from pygame_systems_lab.engine.agent import AgentState, AgentTaskState
from pygame_systems_lab.engine.geometry import Vec2


def make_agent(
    task_state: AgentTaskState,
    *,
    target_position: Vec2 | None = None,
    carried_item_id: int | None = None,
) -> AgentState:
    return AgentState(
        id=7,
        name="Worker 7",
        position=Vec2(10.0, 15.0),
        facing=Vec2(1.0, 0.0),
        speed=24.0,
        task_state=task_state,
        target_position=target_position,
        carried_item_id=carried_item_id,
    )


def test_agent_state_can_represent_waiting() -> None:
    agent = make_agent(AgentTaskState.WAITING)

    assert agent.task_state is AgentTaskState.WAITING
    assert agent.target_position is None
    assert agent.carried_item_id is None


def test_agent_state_can_represent_seeking_target() -> None:
    target = Vec2(80.0, 120.0)

    agent = make_agent(AgentTaskState.SEEKING_TARGET, target_position=target)

    assert agent.task_state is AgentTaskState.SEEKING_TARGET
    assert agent.target_position == target
    assert agent.carried_item_id is None


def test_agent_state_can_represent_carrying_item() -> None:
    agent = make_agent(AgentTaskState.CARRYING_ITEM, carried_item_id=42)

    assert agent.task_state is AgentTaskState.CARRYING_ITEM
    assert agent.carried_item_id == 42


def test_agent_state_can_represent_returning_to_base() -> None:
    base_position = Vec2(5.0, 5.0)

    agent = make_agent(
        AgentTaskState.RETURNING_TO_BASE,
        target_position=base_position,
        carried_item_id=42,
    )

    assert agent.task_state is AgentTaskState.RETURNING_TO_BASE
    assert agent.target_position == base_position
    assert agent.carried_item_id == 42
