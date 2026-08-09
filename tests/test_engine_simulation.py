from pygame_systems_lab.engine.agent import AgentState, AgentTaskState
from pygame_systems_lab.engine.geometry import Vec2
from pygame_systems_lab.engine.interactions import InteractionKind, InteractionTarget
from pygame_systems_lab.engine.settings import (
    AgentSettings,
    EngineSettings,
    MovementSettings,
    WorldSettings,
)
from pygame_systems_lab.engine.simulation import (
    SimulationSnapshot,
    convert_interaction_targets_to_task_targets,
    step_agent,
    step_simulation,
)


def make_settings() -> EngineSettings:
    return EngineSettings(
        movement=MovementSettings(
            max_speed=10.0,
            arrival_radius=0.5,
            default_dt=1.0,
        ),
        agent=AgentSettings(
            radius=5.0,
            interaction_radius=2.0,
            base_interaction_radius=2.0,
        ),
        world=WorldSettings(width=500, height=300),
    )


def make_agent(
    agent_id: int,
    *,
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
    target_id: int,
    *,
    position: Vec2,
    available: bool = True,
    claimed_by_id: int | None = None,
) -> InteractionTarget:
    return InteractionTarget(
        id=target_id,
        kind="sample",
        position=position,
        radius=1.0,
        available=available,
        claimed_by_id=claimed_by_id,
    )


def test_interaction_targets_convert_to_task_targets() -> None:
    targets = (
        make_target(3, position=Vec2(10.0, 10.0), available=True),
        make_target(4, position=Vec2(15.0, 20.0), available=False),
    )

    converted = convert_interaction_targets_to_task_targets(targets)

    assert [target.id for target in converted] == [3, 4]
    assert [target.kind for target in converted] == ["sample", "sample"]
    assert [target.position for target in converted] == [Vec2(10.0, 10.0), Vec2(15.0, 20.0)]
    assert [target.available for target in converted] == [True, False]


def test_empty_agent_moves_toward_nearest_available_target() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(0.0, 0.0))
    targets = (
        make_target(9, position=Vec2(20.0, 0.0), available=True),
        make_target(5, position=Vec2(8.0, 0.0), available=True),
    )

    result, _ = step_agent(agent, targets, Vec2(100.0, 0.0), settings, dt=0.5)

    assert result.intent.target_id == 5
    assert result.intent.should_move is True
    assert result.agent.position == Vec2(5.0, 0.0)
    assert result.agent.carried_item_id is None


def test_empty_agent_picks_up_target_when_in_range() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(0.0, 0.0))
    targets = (make_target(7, position=Vec2(1.0, 0.0), available=True),)

    result, updated_targets = step_agent(agent, targets, Vec2(50.0, 0.0), settings, dt=1.0)

    assert result.agent.carried_item_id == 7
    assert result.interaction is not None
    assert result.interaction.succeeded is True
    assert result.interaction.kind is InteractionKind.PICKUP
    assert updated_targets[0].available is False


def test_carrying_agent_moves_toward_base() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(20.0, 0.0), carried_item_id=12)

    result, _ = step_agent(agent, (), Vec2(0.0, 0.0), settings, dt=0.5)

    assert result.intent.task_state is AgentTaskState.RETURNING_TO_BASE
    assert result.agent.position == Vec2(15.0, 0.0)
    assert result.agent.carried_item_id == 12
    assert result.interaction is not None
    assert result.interaction.succeeded is False
    assert result.interaction.kind is InteractionKind.DROPOFF


def test_carrying_agent_drops_off_item_when_in_base_range() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(1.0, 0.0), carried_item_id=55)

    result, _ = step_agent(agent, (), Vec2(0.0, 0.0), settings, dt=1.0)

    assert result.agent.carried_item_id is None
    assert result.interaction is not None
    assert result.interaction.succeeded is True
    assert result.interaction.kind is InteractionKind.DROPOFF
    assert result.interaction.target_id == 55


def test_two_agents_cannot_both_pick_up_same_target_in_one_step() -> None:
    settings = make_settings()
    snapshot = SimulationSnapshot(
        agents=(
            make_agent(1, position=Vec2(0.0, 0.0)),
            make_agent(2, position=Vec2(0.0, 0.0)),
        ),
        targets=(make_target(9, position=Vec2(1.0, 0.0), available=True),),
        base_position=Vec2(100.0, 0.0),
    )

    result = step_simulation(snapshot, settings, dt=1.0)

    carrying_agents = [agent for agent in result.snapshot.agents if agent.carried_item_id == 9]
    assert len(carrying_agents) == 1
    assert result.snapshot.targets[0].available is False


def test_agent_waits_when_no_targets_are_available() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(3.0, 4.0))
    unavailable_targets = (make_target(9, position=Vec2(5.0, 5.0), available=False),)

    result, _ = step_agent(agent, unavailable_targets, Vec2(100.0, 100.0), settings, dt=1.0)

    assert result.intent.task_state is AgentTaskState.WAITING
    assert result.intent.should_move is False
    assert result.agent.position == Vec2(3.0, 4.0)
    assert result.interaction is None


def test_step_simulation_processes_agents_deterministically_by_id() -> None:
    settings = make_settings()
    snapshot = SimulationSnapshot(
        agents=(
            make_agent(2, position=Vec2(0.0, 0.0)),
            make_agent(1, position=Vec2(0.0, 0.0)),
        ),
        targets=(make_target(33, position=Vec2(1.0, 0.0), available=True),),
        base_position=Vec2(100.0, 0.0),
    )

    result = step_simulation(snapshot, settings, dt=1.0)

    assert [agent.id for agent in result.snapshot.agents] == [1, 2]
    assert [agent_result.agent.id for agent_result in result.agent_results] == [1, 2]
    assert result.snapshot.agents[0].carried_item_id == 33
    assert result.snapshot.agents[1].carried_item_id is None
