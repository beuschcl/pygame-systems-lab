from pygame_systems_lab.labs.collision import (
    RectangleObstacle,
    check_circle_against_obstacles,
    circle_intersects_rectangle,
    clamp_point_to_rectangle,
    resolve_circle_position_against_rectangle,
)
from pygame_systems_lab.labs.motion import Vec2


def test_clamp_point_to_rectangle_clamps_each_axis() -> None:
    rectangle = RectangleObstacle("Box", 10.0, 20.0, 30.0, 40.0)

    clamped = clamp_point_to_rectangle(Vec2(100.0, 0.0), rectangle)

    assert clamped == Vec2(40.0, 20.0)


def test_circle_intersects_rectangle_detects_overlap() -> None:
    rectangle = RectangleObstacle("Box", 50.0, 50.0, 40.0, 40.0)

    assert circle_intersects_rectangle(Vec2(45.0, 70.0), 10.0, rectangle) is True
    assert circle_intersects_rectangle(Vec2(10.0, 10.0), 5.0, rectangle) is False


def test_resolve_circle_position_against_rectangle_pushes_outside_x_axis() -> None:
    rectangle = RectangleObstacle("Wall", 100.0, 90.0, 40.0, 60.0)

    result = resolve_circle_position_against_rectangle(
        position=Vec2(95.0, 120.0),
        previous_position=Vec2(70.0, 120.0),
        radius=12.0,
        rectangle=rectangle,
    )

    assert result.collided is True
    assert result.blocked_x is True
    assert result.position == Vec2(88.0, 120.0)


def test_resolve_circle_position_against_rectangle_pushes_outside_y_axis() -> None:
    rectangle = RectangleObstacle("Floor", 100.0, 100.0, 80.0, 40.0)

    result = resolve_circle_position_against_rectangle(
        position=Vec2(130.0, 95.0),
        previous_position=Vec2(130.0, 70.0),
        radius=10.0,
        rectangle=rectangle,
    )

    assert result.collided is True
    assert result.blocked_y is True
    assert result.position == Vec2(130.0, 90.0)


def test_check_circle_against_obstacles_checks_a_list() -> None:
    obstacles = (
        RectangleObstacle("First", 100.0, 100.0, 40.0, 40.0),
        RectangleObstacle("Second", 200.0, 100.0, 40.0, 40.0),
    )

    result = check_circle_against_obstacles(
        position=Vec2(205.0, 120.0),
        previous_position=Vec2(170.0, 120.0),
        velocity=Vec2(35.0, 0.0),
        radius=10.0,
        obstacles=obstacles,
    )

    assert result.collided is True
    assert result.blocked_x is True
    assert result.position == Vec2(190.0, 120.0)
    assert result.velocity == Vec2(0.0, 0.0)


def test_check_circle_against_obstacles_stops_cleanly_on_left_side() -> None:
    rectangle = RectangleObstacle("Wall", 100.0, 100.0, 40.0, 80.0)

    result = check_circle_against_obstacles(
        position=Vec2(95.0, 130.0),
        previous_position=Vec2(70.0, 130.0),
        velocity=Vec2(50.0, 0.0),
        radius=12.0,
        obstacles=[rectangle],
    )

    assert result.position == Vec2(88.0, 130.0)
    assert result.velocity == Vec2(0.0, 0.0)
    assert result.blocked_x is True
    assert result.blocked_y is False


def test_check_circle_against_obstacles_stops_cleanly_on_top_side() -> None:
    rectangle = RectangleObstacle("Ceiling", 100.0, 100.0, 80.0, 40.0)

    result = check_circle_against_obstacles(
        position=Vec2(130.0, 95.0),
        previous_position=Vec2(130.0, 70.0),
        velocity=Vec2(0.0, 60.0),
        radius=10.0,
        obstacles=[rectangle],
    )

    assert result.position == Vec2(130.0, 90.0)
    assert result.velocity == Vec2(0.0, 0.0)
    assert result.blocked_x is False
    assert result.blocked_y is True


def test_check_circle_against_obstacles_slides_past_a_corner() -> None:
    rectangle = RectangleObstacle("Corner", 100.0, 100.0, 50.0, 50.0)

    result = check_circle_against_obstacles(
        position=Vec2(93.0, 93.0),
        previous_position=Vec2(70.0, 85.0),
        velocity=Vec2(50.0, 20.0),
        radius=10.0,
        obstacles=[rectangle],
    )

    assert result.collided is True
    assert result.position.x < 93.0
    assert result.position.y < 93.0
    assert result.velocity.x > 0.0
    assert result.velocity.y < 20.0


def test_center_inside_rectangle_resolves_out_cleanly() -> None:
    rectangle = RectangleObstacle("Box", 100.0, 100.0, 80.0, 40.0)

    result = resolve_circle_position_against_rectangle(
        position=Vec2(120.0, 120.0),
        previous_position=Vec2(90.0, 120.0),
        radius=10.0,
        rectangle=rectangle,
    )

    assert result.collided is True
    assert result.position == Vec2(90.0, 120.0)
    assert result.blocked_x is True
    assert result.blocked_y is False


def test_no_collision_leaves_position_and_velocity_unchanged() -> None:
    rectangle = RectangleObstacle("Box", 100.0, 100.0, 40.0, 40.0)
    start_position = Vec2(40.0, 40.0)
    start_velocity = Vec2(12.0, -3.0)

    result = check_circle_against_obstacles(
        position=start_position,
        previous_position=Vec2(30.0, 43.0),
        velocity=start_velocity,
        radius=8.0,
        obstacles=[rectangle],
    )

    assert result.collided is False
    assert result.position == start_position
    assert result.velocity == start_velocity
