from pygame_systems_lab.labs.motion import (
    InputState,
    MotionConfig,
    MotionState,
    Vec2,
    make_initial_state,
    update_motion,
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
