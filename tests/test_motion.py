from pygame_systems_lab.labs.motion import (
    InputState,
    MotionConfig,
    MotionState,
    Vec2,
    distance_between_points,
    make_initial_state,
    point_is_inside_circle,
    speed_from_velocity,
    update_motion,
    update_motion_with_acceleration,
)


def test_update_motion_applies_acceleration() -> None:
    config = MotionConfig()
    start = make_initial_state(config)

    updated = update_motion(start, InputState(right=True), 0.5, config)

    assert updated.acceleration == Vec2(config.acceleration, 0.0)
    assert updated.velocity.x == config.acceleration * 0.5
    assert updated.position.x > start.position.x


def test_update_motion_applies_friction_without_input() -> None:
    config = MotionConfig(friction=2.0)
    start = MotionState(
        position=Vec2(100.0, 100.0),
        velocity=Vec2(50.0, 0.0),
        acceleration=Vec2(0.0, 0.0),
    )

    updated = update_motion(start, InputState(), 0.5, config)

    assert updated.acceleration == Vec2(0.0, 0.0)
    assert updated.velocity.x == 0.0


def test_update_motion_bounces_off_edges() -> None:
    config = MotionConfig(size=(200, 200), radius=20, friction=0.0)
    start = MotionState(
        position=Vec2(175.0, 100.0),
        velocity=Vec2(100.0, 0.0),
        acceleration=Vec2(0.0, 0.0),
    )

    updated = update_motion(start, InputState(), 0.5, config)

    assert updated.position.x == 180.0
    assert updated.velocity.x < 0.0


def test_make_initial_state_starts_in_the_center() -> None:
    config = MotionConfig(size=(640, 480))

    state = make_initial_state(config)

    assert state.position == Vec2(320.0, 240.0)
    assert state.velocity == Vec2(0.0, 0.0)


def test_distance_between_points_uses_pythagorean_distance() -> None:
    assert distance_between_points(Vec2(0.0, 0.0), Vec2(3.0, 4.0)) == 5.0


def test_point_is_inside_circle_checks_hit_testing() -> None:
    center = Vec2(100.0, 100.0)

    assert point_is_inside_circle(Vec2(110.0, 100.0), center, 10.0) is True
    assert point_is_inside_circle(Vec2(111.0, 100.0), center, 10.0) is False


def test_speed_from_velocity_returns_magnitude() -> None:
    assert speed_from_velocity(Vec2(6.0, 8.0)) == 10.0


def test_update_motion_with_acceleration_updates_state() -> None:
    config = MotionConfig(friction=0.0)
    start = make_initial_state(config)

    updated = update_motion_with_acceleration(
        start,
        Vec2(20.0, 0.0),
        0.5,
        config,
    )

    assert updated.acceleration == Vec2(20.0, 0.0)
    assert updated.velocity == Vec2(10.0, 0.0)
    assert updated.position.x == start.position.x + 5.0
