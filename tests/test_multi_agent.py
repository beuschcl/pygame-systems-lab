from random import Random

from pygame_systems_lab.labs.collision import RectangleObstacle
from pygame_systems_lab.labs.motion import MotionConfig, Vec2
from pygame_systems_lab.labs.multi_agent import (
    AgentState,
    assign_safe_random_target,
    create_initial_agents,
    select_agent_by_point,
    update_agents,
    update_one_agent_toward_target,
)
from pygame_systems_lab.labs.steering import (
    SteeringConfig,
    point_is_inside_expanded_obstacle,
)


def test_create_initial_agents_builds_requested_count_with_targets() -> None:
    obstacles = [RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)]
    steering = SteeringConfig(detour_margin=8.0)
    random_source = Random(7)

    agents = create_initial_agents(
        agent_count=5,
        world_size=(800, 600),
        circle_radius=20.0,
        obstacles=obstacles,
        steering_config=steering,
        random_source=random_source,
    )

    assert len(agents) == 5
    assert [agent.id for agent in agents] == [1, 2, 3, 4, 5]
    assert all(agent.name.startswith("Agent ") for agent in agents)
    assert all(
        not point_is_inside_expanded_obstacle(
            agent.target_position,
            obstacles[0],
            28.0,
        )
        for agent in agents
    )


def test_select_agent_by_point_returns_hit_agent() -> None:
    agents = [
        AgentState(
            id=1,
            name="Agent 1",
            position=Vec2(100.0, 100.0),
            velocity=Vec2(0.0, 0.0),
            acceleration=Vec2(0.0, 0.0),
            color=(255, 0, 0),
            target_position=Vec2(200.0, 100.0),
        ),
        AgentState(
            id=2,
            name="Agent 2",
            position=Vec2(300.0, 100.0),
            velocity=Vec2(0.0, 0.0),
            acceleration=Vec2(0.0, 0.0),
            color=(0, 255, 0),
            target_position=Vec2(350.0, 100.0),
        ),
    ]

    selected = select_agent_by_point(agents, Vec2(104.0, 100.0), 20.0)
    missed = select_agent_by_point(agents, Vec2(220.0, 220.0), 20.0)

    assert selected is not None
    assert selected.id == 1
    assert missed is None


def test_assign_safe_random_target_returns_target_outside_clearance_zone() -> None:
    obstacle = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)
    steering = SteeringConfig(detour_margin=8.0)
    random_source = Random(3)

    target = assign_safe_random_target(
        position=Vec2(130.0, 130.0),
        world_size=(400, 300),
        circle_radius=20.0,
        obstacles=[obstacle],
        steering_config=steering,
        random_source=random_source,
    )

    assert point_is_inside_expanded_obstacle(target, obstacle, 28.0) is False


def test_update_one_agent_toward_target_moves_the_agent() -> None:
    steering = SteeringConfig(max_speed=200.0, max_acceleration=500.0)
    motion = MotionConfig(size=(500, 400), radius=20, friction=0.0)
    random_source = Random(11)
    agent = AgentState(
        id=1,
        name="Agent 1",
        position=Vec2(50.0, 50.0),
        velocity=Vec2(0.0, 0.0),
        acceleration=Vec2(0.0, 0.0),
        color=(120, 200, 255),
        target_position=Vec2(220.0, 50.0),
    )

    updated = update_one_agent_toward_target(
        agent=agent,
        dt=0.1,
        motion_config=motion,
        steering_config=steering,
        obstacles=[],
        random_source=random_source,
    )

    assert updated.position.x > agent.position.x
    assert updated.velocity.x > 0.0


def test_update_one_agent_assigns_new_target_when_current_target_reached() -> None:
    steering = SteeringConfig(stop_radius=10.0, max_speed=150.0, max_acceleration=300.0)
    motion = MotionConfig(size=(500, 400), radius=20, friction=0.0)
    random_source = Random(13)
    agent = AgentState(
        id=1,
        name="Agent 1",
        position=Vec2(180.0, 180.0),
        velocity=Vec2(0.0, 0.0),
        acceleration=Vec2(0.0, 0.0),
        color=(120, 200, 255),
        target_position=Vec2(180.0, 180.0),
    )

    updated = update_one_agent_toward_target(
        agent=agent,
        dt=0.1,
        motion_config=motion,
        steering_config=steering,
        obstacles=[],
        random_source=random_source,
    )

    assert updated.target_position != agent.target_position


def test_update_agents_updates_each_agent() -> None:
    steering = SteeringConfig(max_speed=200.0, max_acceleration=500.0)
    motion = MotionConfig(size=(500, 400), radius=20, friction=0.0)
    random_source = Random(17)
    agents = [
        AgentState(
            id=1,
            name="Agent 1",
            position=Vec2(50.0, 50.0),
            velocity=Vec2(0.0, 0.0),
            acceleration=Vec2(0.0, 0.0),
            color=(255, 0, 0),
            target_position=Vec2(220.0, 50.0),
        ),
        AgentState(
            id=2,
            name="Agent 2",
            position=Vec2(60.0, 90.0),
            velocity=Vec2(0.0, 0.0),
            acceleration=Vec2(0.0, 0.0),
            color=(0, 255, 0),
            target_position=Vec2(200.0, 90.0),
        ),
    ]

    updated = update_agents(
        agents=agents,
        dt=0.1,
        motion_config=motion,
        steering_config=steering,
        obstacles=[],
        random_source=random_source,
    )

    assert len(updated) == 2
    assert updated[0].position.x > agents[0].position.x
    assert updated[1].position.x > agents[1].position.x
