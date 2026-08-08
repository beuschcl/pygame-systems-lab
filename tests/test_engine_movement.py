from math import isclose

from pygame_systems_lab.engine.movement import (
    MovementPlan,
    apply_movement_plan,
    plan_direct_movement,
)
from pygame_systems_lab.engine.settings import MovementSettings
from pygame_systems_lab.labs.motion import Vec2


def test_direct_movement_moves_toward_target() -> None:
    settings = MovementSettings(max_speed=10.0, arrival_radius=1.0, default_dt=0.5)

    plan = plan_direct_movement(
        position=Vec2(0.0, 0.0),
        target_position=Vec2(20.0, 0.0),
        settings=settings,
    )
    result = apply_movement_plan(
        position=Vec2(0.0, 0.0),
        facing=Vec2(0.0, 1.0),
        plan=plan,
        dt=settings.default_dt,
    )

    assert result.position == Vec2(5.0, 0.0)
    assert result.facing == Vec2(1.0, 0.0)
    assert result.reached_target is False


def test_movement_does_not_overshoot_target() -> None:
    plan = MovementPlan(
        target_position=Vec2(3.0, 4.0),
        speed=20.0,
        arrival_radius=0.5,
    )

    result = apply_movement_plan(
        position=Vec2(0.0, 0.0),
        facing=Vec2(0.0, 1.0),
        plan=plan,
        dt=1.0,
    )

    assert result.position == Vec2(3.0, 4.0)
    assert isclose(result.facing.x, 0.6)
    assert isclose(result.facing.y, 0.8)
    assert result.reached_target is True


def test_reaching_within_arrival_radius_snaps_to_target() -> None:
    plan = MovementPlan(
        target_position=Vec2(10.0, 12.0),
        speed=50.0,
        arrival_radius=3.0,
    )

    result = apply_movement_plan(
        position=Vec2(8.0, 10.0),
        facing=Vec2(-1.0, 0.0),
        plan=plan,
        dt=0.1,
    )

    assert result.position == Vec2(10.0, 12.0)
    assert isclose(result.facing.x, 0.70710678118)
    assert isclose(result.facing.y, 0.70710678118)
    assert result.reached_target is True


def test_none_target_keeps_position_unchanged() -> None:
    settings = MovementSettings(max_speed=10.0, arrival_radius=1.0, default_dt=0.5)

    plan = plan_direct_movement(
        position=Vec2(4.0, 6.0),
        target_position=None,
        settings=settings,
    )
    result = apply_movement_plan(
        position=Vec2(4.0, 6.0),
        facing=Vec2(1.0, 0.0),
        plan=plan,
        dt=settings.default_dt,
    )

    assert result.position == Vec2(4.0, 6.0)
    assert result.facing == Vec2(1.0, 0.0)
    assert result.reached_target is False


def test_facing_updates_only_when_movement_occurs() -> None:
    plan = MovementPlan(
        target_position=Vec2(10.0, 0.0),
        speed=0.0,
        arrival_radius=0.5,
    )

    result = apply_movement_plan(
        position=Vec2(0.0, 0.0),
        facing=Vec2(0.0, 1.0),
        plan=plan,
        dt=1.0,
    )

    assert result.position == Vec2(0.0, 0.0)
    assert result.facing == Vec2(0.0, 1.0)
    assert result.reached_target is False
