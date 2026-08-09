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
    discover_targets_in_range,
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
            detection_radius=6.0,
            wander_step_distance=4.0,
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
    discovered: bool = True,
) -> InteractionTarget:
    return InteractionTarget(
        id=target_id,
        kind="sample",
        position=position,
        radius=1.0,
        available=available,
        claimed_by_id=claimed_by_id,
        discovered=discovered,
    )


def test_interaction_targets_convert_to_task_targets() -> None:
    targets = (
        make_target(3, position=Vec2(10.0, 10.0), available=True, discovered=True),
        make_target(4, position=Vec2(15.0, 20.0), available=False, discovered=False),
    )

    converted = convert_interaction_targets_to_task_targets(targets)

    assert [target.id for target in converted] == [3, 4]
    assert [target.kind for target in converted] == ["sample", "sample"]
    assert [target.position for target in converted] == [Vec2(10.0, 10.0), Vec2(15.0, 20.0)]
    assert [target.available for target in converted] == [True, False]
    assert [target.discovered for target in converted] == [True, False]


def test_wandering_agent_remains_wandering_when_no_targets_discoverable() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(0.0, 0.0))
    targets = (make_target(9, position=Vec2(30.0, 0.0), discovered=False),)

    result, updated_targets = step_agent(agent, targets, Vec2(100.0, 100.0), settings, dt=1.0)

    assert result.intent.task_state is AgentTaskState.WANDERING
    assert result.intent.target_id is None
    assert result.agent.position != Vec2(0.0, 0.0)
    assert updated_targets[0].discovered is False


def test_wandering_agent_discovers_a_nearby_target() -> None:
    discovered = discover_targets_in_range(
        position=Vec2(0.0, 0.0),
        targets=(make_target(9, position=Vec2(4.0, 0.0), discovered=False),),
        detection_radius=6.0,
    )

    assert discovered[0].discovered is True


def test_discovered_target_causes_agent_to_seek_target() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(0.0, 0.0))
    targets = (make_target(5, position=Vec2(4.0, 0.0), discovered=False),)

    result, updated_targets = step_agent(agent, targets, Vec2(90.0, 90.0), settings, dt=0.1)

    assert updated_targets[0].discovered is True
    assert result.intent.task_state is AgentTaskState.SEEKING_TARGET
    assert result.intent.target_id == 5


def test_agent_picks_up_target_when_in_range() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(0.0, 0.0))
    targets = (make_target(7, position=Vec2(1.0, 0.0), discovered=True),)

    result, updated_targets = step_agent(agent, targets, Vec2(50.0, 0.0), settings, dt=1.0)

    assert result.agent.carried_item_id == 7
    assert result.interaction is not None
    assert result.interaction.succeeded is True
    assert result.interaction.kind is InteractionKind.PICKUP
    assert updated_targets[0].available is False


def test_carrying_agent_returns_to_base() -> None:
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
    targets = (make_target(8, position=Vec2(10.0, 0.0), discovered=True),)

    result, _ = step_agent(agent, targets, Vec2(0.0, 0.0), settings, dt=1.0)

    assert result.agent.carried_item_id is None
    assert result.interaction is not None
    assert result.interaction.succeeded is True
    assert result.interaction.kind is InteractionKind.DROPOFF
    assert result.interaction.target_id == 55
    assert result.agent.task_state in (AgentTaskState.WANDERING, AgentTaskState.SEEKING_TARGET)


def test_movement_uses_non_overshooting_engine_movement() -> None:
    settings = make_settings()
    agent = make_agent(1, position=Vec2(0.0, 0.0))
    targets = (make_target(4, position=Vec2(3.0, 4.0), discovered=True),)

    result, _ = step_agent(agent, targets, Vec2(100.0, 0.0), settings, dt=10.0)

    assert result.agent.position == Vec2(3.0, 4.0)
    assert result.movement.reached_target is True


def test_two_agents_cannot_both_pick_up_same_target_in_one_step() -> None:
    settings = make_settings()
    snapshot = SimulationSnapshot(
        agents=(
            make_agent(1, position=Vec2(0.0, 0.0)),
            make_agent(2, position=Vec2(0.0, 0.0)),
        ),
        targets=(make_target(9, position=Vec2(1.0, 0.0), discovered=True),),
        base_position=Vec2(100.0, 0.0),
    )

    result = step_simulation(snapshot, settings, dt=1.0)

    carrying_agents = [agent for agent in result.snapshot.agents if agent.carried_item_id == 9]
    assert len(carrying_agents) == 1
    assert result.snapshot.targets[0].available is False


def test_step_simulation_processes_agents_deterministically_by_id() -> None:
    settings = make_settings()
    snapshot = SimulationSnapshot(
        agents=(
            make_agent(2, position=Vec2(0.0, 0.0)),
            make_agent(1, position=Vec2(0.0, 0.0)),
        ),
        targets=(make_target(33, position=Vec2(1.0, 0.0), discovered=True),),
        base_position=Vec2(100.0, 0.0),
    )

    result = step_simulation(snapshot, settings, dt=1.0)

    assert [agent.id for agent in result.snapshot.agents] == [1, 2]
    assert [agent_result.agent.id for agent_result in result.agent_results] == [1, 2]
    assert result.snapshot.agents[0].carried_item_id == 33
    assert result.snapshot.agents[1].carried_item_id is None


def test_full_loop_from_wandering_to_pickup_to_dropoff() -> None:
    settings = make_settings()
    snapshot = SimulationSnapshot(
        agents=(make_agent(1, position=Vec2(0.0, 0.0)),),
        targets=(make_target(41, position=Vec2(6.0, 0.0), discovered=False),),
        base_position=Vec2(0.0, 0.0),
    )

    step_one = step_simulation(snapshot, settings, dt=0.1)
    step_two = step_simulation(step_one.snapshot, settings, dt=0.5)
    step_three = step_simulation(step_two.snapshot, settings, dt=0.5)

    assert step_one.snapshot.targets[0].discovered is True
    assert step_two.snapshot.agents[0].carried_item_id == 41
    assert step_three.snapshot.agents[0].carried_item_id is None


def test_behavior_uses_tuning_values_from_engine_settings() -> None:
    settings = EngineSettings(
        movement=MovementSettings(max_speed=2.0, arrival_radius=0.25, default_dt=1.0),
        agent=AgentSettings(
            radius=5.0,
            interaction_radius=0.5,
            base_interaction_radius=0.5,
            detection_radius=1.5,
            wander_step_distance=1.25,
        ),
        world=WorldSettings(width=40, height=30),
    )
    agent = make_agent(1, position=Vec2(0.0, 0.0))
    targets = (make_target(1, position=Vec2(2.0, 0.0), discovered=False),)

    result, updated_targets = step_agent(agent, targets, Vec2(0.0, 0.0), settings, dt=1.0)

    assert updated_targets[0].discovered is False
    assert result.intent.task_state is AgentTaskState.WANDERING
    assert result.agent.position != Vec2(0.0, 0.0)
