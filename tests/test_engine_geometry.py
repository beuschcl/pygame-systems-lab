from math import isclose

from pygame_systems_lab.engine.geometry import Vec2


def test_vec2_supports_addition_subtraction_and_scalar_multiplication() -> None:
    start = Vec2(1.5, -2.0)
    offset = Vec2(2.5, 4.0)

    assert start + offset == Vec2(4.0, 2.0)
    assert start - offset == Vec2(-1.0, -6.0)
    assert start * 2.0 == Vec2(3.0, -4.0)
    assert 2.0 * start == Vec2(3.0, -4.0)


def test_vec2_length_and_distance_use_euclidean_geometry() -> None:
    vector = Vec2(3.0, 4.0)

    assert vector.length() == 5.0
    assert Vec2(0.0, 0.0).distance_to(vector) == 5.0


def test_vec2_normalized_returns_unit_vector() -> None:
    normalized = Vec2(3.0, 4.0).normalized()

    assert isclose(normalized.x, 0.6)
    assert isclose(normalized.y, 0.8)
    assert isclose(normalized.length(), 1.0)


def test_vec2_normalized_returns_zero_vector_for_zero_length() -> None:
    assert Vec2(0.0, 0.0).normalized() == Vec2(0.0, 0.0)


def test_move_toward_snaps_to_target_when_close_enough() -> None:
    start = Vec2(1.0, 1.0)
    target = Vec2(4.0, 5.0)

    assert start.move_toward(target, 5.0) == target


def test_move_toward_does_not_overshoot_target() -> None:
    start = Vec2(0.0, 0.0)
    target = Vec2(10.0, 0.0)

    moved = start.move_toward(target, 3.0)

    assert moved == Vec2(3.0, 0.0)
    assert moved.distance_to(target) == 7.0
