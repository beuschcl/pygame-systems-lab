from random import Random

from pygame_systems_lab.experiments.ant_movement import (
    AntMovementSettings,
    BaseState,
    ExperimentAgent,
    ExperimentAgentState,
    ExperimentSnapshot,
    ExperimentTarget,
    contain_position,
    discover_targets_for_agent,
    move_toward,
    step_snapshot,
    wander,
)


def test_move_toward_does_not_overshoot() -> None:
    movement = move_toward(
        current_x=0.0,
        current_y=0.0,
        target_x=3.0,
        target_y=4.0,
        speed=10.0,
        current_heading=90.0,
    )

    assert movement.x == 3.0
    assert movement.y == 4.0
    assert movement.reached_target is True


def test_move_toward_updates_heading() -> None:
    movement = move_toward(
        current_x=0.0,
        current_y=0.0,
        target_x=10.0,
        target_y=0.0,
        speed=2.0,
        current_heading=90.0,
    )

    assert movement.x == 2.0
    assert movement.y == 0.0
    assert movement.heading == 0.0
    assert movement.reached_target is False


def test_contain_position_reflects_boundary_heading() -> None:
    settings = AntMovementSettings(world_width=100.0, world_height=100.0)

    contained = contain_position(
        x=95.0,
        y=50.0,
        heading=0.0,
        settings=settings,
    )

    assert contained.x == 80.0
    assert contained.y == 50.0
    assert contained.heading == 180.0


def test_wander_moves_using_heading_and_turns() -> None:
    settings = AntMovementSettings(turn_speed=0.0)
    agent = ExperimentAgent(
        id=1,
        x=100.0,
        y=100.0,
        speed=5.0,
        heading=0.0,
    )

    updated = wander(agent, Random(1), settings)

    assert updated.x == 105.0
    assert updated.y == 100.0
    assert updated.heading == 0.0
    assert updated.state == ExperimentAgentState.WANDERING


def test_discover_targets_marks_nearby_available_targets() -> None:
    settings = AntMovementSettings(detection_radius=50.0)
    agent = ExperimentAgent(
        id=1,
        x=100.0,
        y=100.0,
        speed=5.0,
        heading=0.0,
    )
    targets = (
        ExperimentTarget(id=1, x=125.0, y=100.0),
        ExperimentTarget(id=2, x=300.0, y=100.0),
    )

    discovered = discover_targets_for_agent(agent, targets, settings)

    assert discovered[0].discovered is True
    assert discovered[1].discovered is False


def test_wandering_agent_seeks_discovered_resource() -> None:
    settings = AntMovementSettings(detection_radius=75.0)
    snapshot = ExperimentSnapshot(
        agents=(
            ExperimentAgent(
                id=1,
                x=100.0,
                y=100.0,
                speed=5.0,
                heading=0.0,
            ),
        ),
        targets=(ExperimentTarget(id=1, x=150.0, y=100.0),),
        base=BaseState(x=50.0, y=50.0),
    )

    updated = step_snapshot(snapshot, Random(1), settings)
    agent = updated.agents[0]

    assert agent.state == ExperimentAgentState.SEEKING_RESOURCE
    assert agent.target_id == 1
    assert agent.x > 100.0
    assert updated.targets[0].discovered is True


def test_agent_picks_up_resource_when_close_enough() -> None:
    settings = AntMovementSettings(
        detection_radius=75.0,
        interaction_radius=12.0,
    )
    snapshot = ExperimentSnapshot(
        agents=(
            ExperimentAgent(
                id=1,
                x=100.0,
                y=100.0,
                speed=5.0,
                heading=0.0,
            ),
        ),
        targets=(ExperimentTarget(id=1, x=105.0, y=100.0, radius=4.0),),
        base=BaseState(x=50.0, y=50.0),
    )

    updated = step_snapshot(snapshot, Random(1), settings)
    agent = updated.agents[0]

    assert agent.state == ExperimentAgentState.CARRYING_RESOURCE
    assert agent.carried_item_id == 1
    assert updated.targets[0].available is False


def test_carrying_agent_moves_toward_base() -> None:
    settings = AntMovementSettings(base_interaction_radius=1.0)
    snapshot = ExperimentSnapshot(
        agents=(
            ExperimentAgent(
                id=1,
                x=100.0,
                y=100.0,
                speed=10.0,
                heading=0.0,
                state=ExperimentAgentState.CARRYING_RESOURCE,
                carried_item_id=7,
            ),
        ),
        targets=(),
        base=BaseState(x=50.0, y=100.0, radius=1.0),
    )

    updated = step_snapshot(snapshot, Random(1), settings)
    agent = updated.agents[0]

    assert agent.state == ExperimentAgentState.CARRYING_RESOURCE
    assert agent.carried_item_id == 7
    assert agent.x < 100.0
    assert agent.heading == 180.0


def test_carrying_agent_drops_off_at_base() -> None:
    settings = AntMovementSettings(base_interaction_radius=15.0)
    snapshot = ExperimentSnapshot(
        agents=(
            ExperimentAgent(
                id=1,
                x=55.0,
                y=50.0,
                speed=10.0,
                heading=180.0,
                state=ExperimentAgentState.CARRYING_RESOURCE,
                carried_item_id=7,
            ),
        ),
        targets=(),
        base=BaseState(x=50.0, y=50.0, radius=5.0),
    )

    updated = step_snapshot(snapshot, Random(1), settings)
    agent = updated.agents[0]

    assert agent.state == ExperimentAgentState.WANDERING
    assert agent.carried_item_id is None
    assert updated.collected_count == 1


def test_full_loop_from_discovery_to_dropoff() -> None:
    settings = AntMovementSettings(
        detection_radius=100.0,
        interaction_radius=10.0,
        base_interaction_radius=10.0,
    )
    snapshot = ExperimentSnapshot(
        agents=(
            ExperimentAgent(
                id=1,
                x=100.0,
                y=100.0,
                speed=50.0,
                heading=0.0,
            ),
        ),
        targets=(ExperimentTarget(id=1, x=150.0, y=100.0, radius=5.0),),
        base=BaseState(x=100.0, y=100.0, radius=8.0),
    )
    rng = Random(1)

    after_pickup = step_snapshot(snapshot, rng, settings)
    after_dropoff = step_snapshot(after_pickup, rng, settings)

    assert after_pickup.agents[0].state == ExperimentAgentState.CARRYING_RESOURCE
    assert after_dropoff.agents[0].state == ExperimentAgentState.WANDERING
    assert after_dropoff.agents[0].carried_item_id is None
    assert after_dropoff.collected_count == 1
