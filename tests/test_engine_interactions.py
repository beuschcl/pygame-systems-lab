from pygame_systems_lab.engine.agent import AgentState, AgentTaskState
from pygame_systems_lab.engine.geometry import Vec2
from pygame_systems_lab.engine.interactions import (
    InteractionKind,
    InteractionTarget,
    can_dropoff,
    claim_target,
    dropoff_item,
    is_within_interaction_range,
    pickup_target,
)


def make_agent(
    *,
    agent_id: int = 1,
    position: Vec2 | None = None,
    carried_item_id: int | None = None,
) -> AgentState:
    if position is None:
        position = Vec2(0.0, 0.0)

    return AgentState(
        id=agent_id,
        name=f"Agent {agent_id}",
        position=position,
        facing=Vec2(1.0, 0.0),
        speed=20.0,
        task_state=AgentTaskState.WAITING,
        carried_item_id=carried_item_id,
    )


def make_target(
    *,
    target_id: int = 10,
    position: Vec2 | None = None,
    available: bool = True,
    claimed_by_id: int | None = None,
) -> InteractionTarget:
    if position is None:
        position = Vec2(3.0, 4.0)

    return InteractionTarget(
        id=target_id,
        kind="sample",
        position=position,
        radius=5.0,
        available=available,
        claimed_by_id=claimed_by_id,
    )


def test_interaction_range_uses_distance_check() -> None:
    assert is_within_interaction_range(Vec2(0.0, 0.0), Vec2(3.0, 4.0), 5.0) is True
    assert is_within_interaction_range(Vec2(0.0, 0.0), Vec2(3.0, 4.0), 4.9) is False


def test_claim_succeeds_for_available_unclaimed_target() -> None:
    agent = make_agent(agent_id=7)
    target = make_target(claimed_by_id=None, available=True)

    updated_target, result = claim_target(agent, target)

    assert updated_target.claimed_by_id == 7
    assert result.succeeded is True
    assert result.kind is InteractionKind.CLAIM
    assert result.agent_id == 7
    assert result.target_id == target.id


def test_claim_fails_when_other_agent_already_claimed_target() -> None:
    agent = make_agent(agent_id=7)
    target = make_target(claimed_by_id=9, available=True)

    updated_target, result = claim_target(agent, target)

    assert updated_target == target
    assert result.succeeded is False
    assert result.kind is InteractionKind.CLAIM
    assert result.agent_id == 7
    assert result.target_id == target.id


def test_pickup_succeeds_when_available_in_range_and_uncarried() -> None:
    agent = make_agent(agent_id=5, position=Vec2(0.0, 0.0), carried_item_id=None)
    target = make_target(position=Vec2(3.0, 4.0), available=True, claimed_by_id=5)

    updated_agent, updated_target, result = pickup_target(agent, target, interaction_radius=5.0)

    assert updated_agent.carried_item_id == target.id
    assert updated_target.available is False
    assert result.succeeded is True
    assert result.kind is InteractionKind.PICKUP
    assert result.agent_id == 5
    assert result.target_id == target.id


def test_pickup_fails_when_out_of_range() -> None:
    agent = make_agent(agent_id=5, position=Vec2(0.0, 0.0), carried_item_id=None)
    target = make_target(position=Vec2(10.0, 0.0), available=True)

    updated_agent, updated_target, result = pickup_target(agent, target, interaction_radius=5.0)

    assert updated_agent == agent
    assert updated_target == target
    assert result.succeeded is False
    assert result.kind is InteractionKind.PICKUP


def test_pickup_fails_when_claimed_by_other_agent() -> None:
    agent = make_agent(agent_id=5, position=Vec2(0.0, 0.0), carried_item_id=None)
    target = make_target(position=Vec2(3.0, 4.0), available=True, claimed_by_id=6)

    updated_agent, updated_target, result = pickup_target(agent, target, interaction_radius=5.0)

    assert updated_agent == agent
    assert updated_target == target
    assert result.succeeded is False
    assert result.kind is InteractionKind.PICKUP


def test_dropoff_succeeds_when_carrying_and_in_range() -> None:
    agent = make_agent(agent_id=3, position=Vec2(3.0, 4.0), carried_item_id=88)

    updated_agent, result = dropoff_item(agent, base_position=Vec2(0.0, 0.0), base_radius=5.0)

    assert can_dropoff(agent, base_position=Vec2(0.0, 0.0), base_radius=5.0) is True
    assert updated_agent.carried_item_id is None
    assert result.succeeded is True
    assert result.kind is InteractionKind.DROPOFF
    assert result.agent_id == 3
    assert result.target_id == 88


def test_dropoff_fails_when_not_carrying() -> None:
    agent = make_agent(agent_id=3, position=Vec2(0.0, 0.0), carried_item_id=None)

    updated_agent, result = dropoff_item(agent, base_position=Vec2(0.0, 0.0), base_radius=5.0)

    assert updated_agent == agent
    assert result.succeeded is False
    assert result.kind is InteractionKind.DROPOFF
    assert result.target_id is None


def test_dropoff_fails_when_out_of_range() -> None:
    agent = make_agent(agent_id=3, position=Vec2(10.0, 0.0), carried_item_id=42)

    updated_agent, result = dropoff_item(agent, base_position=Vec2(0.0, 0.0), base_radius=5.0)

    assert updated_agent == agent
    assert result.succeeded is False
    assert result.kind is InteractionKind.DROPOFF
    assert result.target_id == 42
