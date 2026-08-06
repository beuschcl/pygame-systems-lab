from random import Random

from pygame_systems_lab.labs.collision import RectangleObstacle
from pygame_systems_lab.labs.motion import MotionConfig, Vec2
from pygame_systems_lab.labs.multi_agent import AgentState
from pygame_systems_lab.labs.resource_loop import (
    ResourceNode,
    choose_nearest_available_resource,
    create_initial_resources,
    detect_base_dropoff,
    detect_resource_pickup,
    update_one_agent_task,
    update_resource_loop_for_all_agents,
)
from pygame_systems_lab.labs.steering import SteeringConfig


def test_create_initial_resources_builds_requested_count() -> None:
    random_source = Random(7)
    obstacles = [RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)]
    steering = SteeringConfig(detour_margin=8.0)

    resources = create_initial_resources(
        resource_count=6,
        world_size=(800, 600),
        circle_radius=20.0,
        obstacles=obstacles,
        steering_config=steering,
        random_source=random_source,
    )

    assert len(resources) == 6
    assert [resource.id for resource in resources] == [1, 2, 3, 4, 5, 6]
    assert all(resource.available for resource in resources)


def test_choose_nearest_available_resource_picks_closest_node() -> None:
    resources = [
        ResourceNode(id=1, position=Vec2(200.0, 200.0), available=True),
        ResourceNode(id=2, position=Vec2(120.0, 100.0), available=True),
        ResourceNode(id=3, position=Vec2(400.0, 200.0), available=False),
    ]

    nearest = choose_nearest_available_resource(Vec2(100.0, 100.0), resources)

    assert nearest is not None
    assert nearest.id == 2


def test_detect_resource_pickup_returns_resource_when_in_range() -> None:
    resources = [ResourceNode(id=1, position=Vec2(110.0, 100.0), available=True)]

    picked = detect_resource_pickup(
        position=Vec2(100.0, 100.0),
        resources=resources,
        pickup_radius=12.0,
    )

    assert picked is not None
    assert picked.id == 1


def test_detect_base_dropoff_returns_true_when_inside_base_radius() -> None:
    dropped = detect_base_dropoff(
        position=Vec2(92.0, 508.0),
        base_position=Vec2(90.0, 510.0),
        base_radius=6.0,
    )

    assert dropped is True


def test_update_one_agent_task_marks_pickup_and_sets_returning_task() -> None:
    agent = AgentState(
        id=1,
        name="Agent 1",
        position=Vec2(100.0, 100.0),
        velocity=Vec2(0.0, 0.0),
        acceleration=Vec2(0.0, 0.0),
        color=(255, 0, 0),
        target_position=Vec2(100.0, 100.0),
        task_state="seeking_resource",
    )
    resources = [ResourceNode(id=3, position=Vec2(105.0, 100.0), available=True)]

    updated_agent, updated_resources, collected_increment = update_one_agent_task(
        agent=agent,
        resources=resources,
        base_position=Vec2(90.0, 510.0),
        base_radius=28.0,
        pickup_radius=8.0,
    )

    assert collected_increment == 0
    assert updated_agent.task_state == "returning_to_base"
    assert updated_agent.carried_resource_id == 3
    assert updated_resources[0].available is False


def test_update_one_agent_task_drops_off_and_counts_collection() -> None:
    agent = AgentState(
        id=1,
        name="Agent 1",
        position=Vec2(90.0, 510.0),
        velocity=Vec2(0.0, 0.0),
        acceleration=Vec2(0.0, 0.0),
        color=(255, 0, 0),
        target_position=Vec2(90.0, 510.0),
        task_state="returning_to_base",
        carried_resource_id=2,
    )
    resources = [ResourceNode(id=4, position=Vec2(300.0, 300.0), available=True)]

    updated_agent, updated_resources, collected_increment = update_one_agent_task(
        agent=agent,
        resources=resources,
        base_position=Vec2(90.0, 510.0),
        base_radius=28.0,
        pickup_radius=8.0,
    )

    assert collected_increment == 1
    assert updated_agent.carried_resource_id is None
    assert updated_agent.task_state == "seeking_resource"
    assert updated_agent.target_position == updated_resources[0].position


def test_update_resource_loop_for_all_agents_updates_collected_count() -> None:
    random_source = Random(17)
    agents = [
        AgentState(
            id=1,
            name="Agent 1",
            position=Vec2(100.0, 100.0),
            velocity=Vec2(0.0, 0.0),
            acceleration=Vec2(0.0, 0.0),
            color=(255, 0, 0),
            target_position=Vec2(100.0, 100.0),
            task_state="seeking_resource",
        ),
        AgentState(
            id=2,
            name="Agent 2",
            position=Vec2(90.0, 510.0),
            velocity=Vec2(0.0, 0.0),
            acceleration=Vec2(0.0, 0.0),
            color=(0, 255, 0),
            target_position=Vec2(90.0, 510.0),
            task_state="returning_to_base",
            carried_resource_id=9,
        ),
    ]
    resources = [
        ResourceNode(id=1, position=Vec2(102.0, 100.0), available=True),
        ResourceNode(id=2, position=Vec2(280.0, 100.0), available=True),
    ]

    result = update_resource_loop_for_all_agents(
        agents=agents,
        resources=resources,
        dt=0.0,
        motion_config=MotionConfig(size=(800, 600), radius=20, friction=0.0),
        steering_config=SteeringConfig(),
        obstacles=[],
        base_position=Vec2(90.0, 510.0),
        base_radius=28.0,
        pickup_radius=8.0,
        random_source=random_source,
    )

    assert result.collected_increment == 1
    assert any(agent.carried_resource_id == 1 for agent in result.agents)
    assert any(agent.carried_resource_id is None for agent in result.agents)
