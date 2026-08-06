from pygame_systems_lab.labs.collision import RectangleObstacle
from pygame_systems_lab.labs.motion import Vec2
from pygame_systems_lab.labs.steering import (
    SteeringConfig,
    apply_clicked_target,
    arrival_speed,
    choose_active_steering_target,
    choose_detour_point_around_rectangle,
    desired_velocity_toward_target,
    direction_to_target,
    distance_to_target,
    expand_rectangle,
    find_blocking_obstacle_on_path,
    line_segment_intersects_rectangle,
    point_is_inside_expanded_obstacle,
    point_is_outside_all_obstacles,
    resolve_clicked_target_against_obstacles,
    snap_point_out_of_expanded_obstacle,
    steering_acceleration_toward_velocity,
)


def test_direction_to_target_returns_unit_direction() -> None:
    direction = direction_to_target(Vec2(1.0, 1.0), Vec2(4.0, 5.0))

    assert direction == Vec2(0.6, 0.8)


def test_distance_to_target_returns_distance() -> None:
    assert distance_to_target(Vec2(0.0, 0.0), Vec2(3.0, 4.0)) == 5.0


def test_desired_velocity_toward_target_uses_max_speed_when_far() -> None:
    config = SteeringConfig(max_speed=100.0, slow_radius=50.0, stop_radius=5.0)

    velocity = desired_velocity_toward_target(
        Vec2(0.0, 0.0),
        Vec2(100.0, 0.0),
        config,
    )

    assert velocity == Vec2(100.0, 0.0)


def test_steering_acceleration_toward_velocity_is_clamped() -> None:
    acceleration = steering_acceleration_toward_velocity(
        current_velocity=Vec2(0.0, 0.0),
        desired_velocity=Vec2(30.0, 40.0),
        max_acceleration=10.0,
    )

    assert acceleration == Vec2(6.0, 8.0)


def test_arrival_speed_slows_down_near_target() -> None:
    config = SteeringConfig(max_speed=120.0, slow_radius=60.0, stop_radius=10.0)

    assert arrival_speed(60.0, config) == 120.0
    assert arrival_speed(30.0, config) == 60.0
    assert arrival_speed(10.0, config) == 0.0


def test_desired_velocity_toward_target_stops_inside_stop_radius() -> None:
    config = SteeringConfig(max_speed=120.0, slow_radius=60.0, stop_radius=10.0)

    velocity = desired_velocity_toward_target(
        Vec2(100.0, 100.0),
        Vec2(106.0, 108.0),
        config,
    )

    assert velocity == Vec2(0.0, 0.0)


def test_line_segment_intersects_rectangle_detects_a_blocked_path() -> None:
    obstacle = RectangleObstacle("Block", 100.0, 80.0, 60.0, 60.0)

    assert (
        line_segment_intersects_rectangle(
            Vec2(20.0, 110.0),
            Vec2(220.0, 110.0),
            obstacle,
        )
        is True
    )


def test_clear_line_to_target_uses_the_real_target() -> None:
    config = SteeringConfig()
    target = Vec2(220.0, 40.0)
    obstacles = [RectangleObstacle("Block", 100.0, 120.0, 60.0, 60.0)]

    choice = choose_active_steering_target(
        position=Vec2(20.0, 20.0),
        target=target,
        obstacles=obstacles,
        config=config,
        circle_radius=20.0,
    )

    assert choice.active_target == target
    assert choice.detour_active is False


def test_blocked_line_chooses_a_detour_target() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 100.0, 80.0, 120.0, 40.0)

    choice = choose_active_steering_target(
        position=Vec2(20.0, 110.0),
        target=Vec2(220.0, 110.0),
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )

    assert choice.detour_active is True
    assert choice.active_target == choice.detour_point


def test_detour_target_is_outside_the_blocking_rectangle() -> None:
    obstacle = RectangleObstacle("Block", 100.0, 80.0, 120.0, 40.0)
    clearance = 28.0

    detour = choose_detour_point_around_rectangle(
        start=Vec2(20.0, 110.0),
        target=Vec2(260.0, 110.0),
        rectangle=obstacle,
        obstacles=[obstacle],
        clearance=clearance,
    )

    assert detour is not None
    assert point_is_outside_all_obstacles(detour, [obstacle], clearance) is True


def test_find_blocking_obstacle_returns_first_hit_on_path() -> None:
    obstacles = [
        RectangleObstacle("Near", 100.0, 80.0, 60.0, 60.0),
        RectangleObstacle("Far", 180.0, 80.0, 60.0, 60.0),
    ]

    blocking = find_blocking_obstacle_on_path(
        start=Vec2(20.0, 110.0),
        target=Vec2(320.0, 110.0),
        obstacles=obstacles,
        clearance=28.0,
    )

    assert blocking == obstacles[0]


def test_real_target_is_used_again_when_path_clears() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 100.0, 80.0, 60.0, 60.0)
    blocked_target = Vec2(220.0, 110.0)
    clear_target = Vec2(220.0, 20.0)

    blocked_choice = choose_active_steering_target(
        position=Vec2(20.0, 110.0),
        target=blocked_target,
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )
    clear_choice = choose_active_steering_target(
        position=Vec2(20.0, -100.0),
        target=clear_target,
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )

    assert blocked_choice.detour_active is True
    assert clear_choice.active_target == clear_target
    assert clear_choice.detour_active is False


def test_target_near_upper_left_corner_chooses_reachable_detour() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)

    choice = choose_active_steering_target(
        position=Vec2(40.0, 220.0),
        target=Vec2(92.0, 92.0),
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )

    assert choice.detour_active is True
    assert choice.detour_point is not None
    expanded = expand_rectangle(obstacle, 28.0)
    assert line_segment_intersects_rectangle(
        Vec2(40.0, 220.0),
        choice.detour_point,
        expanded,
    ) is False


def test_target_near_upper_right_corner_chooses_reachable_detour() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)

    choice = choose_active_steering_target(
        position=Vec2(240.0, 220.0),
        target=Vec2(188.0, 92.0),
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )

    assert choice.detour_active is True
    assert choice.detour_point is not None
    expanded = expand_rectangle(obstacle, 28.0)
    assert line_segment_intersects_rectangle(
        Vec2(240.0, 220.0),
        choice.detour_point,
        expanded,
    ) is False


def test_blocked_detour_candidates_are_rejected() -> None:
    blocking = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)
    extra = RectangleObstacle("Extra", 40.0, 40.0, 70.0, 70.0)

    detour = choose_detour_point_around_rectangle(
        start=Vec2(20.0, 220.0),
        target=Vec2(220.0, 120.0),
        rectangle=blocking,
        obstacles=[blocking, extra],
        clearance=28.0,
    )

    assert detour is not None
    blocked_candidate = Vec2(72.0, 72.0)
    assert detour != blocked_candidate


def test_target_directly_above_horizontal_obstacle_chooses_side_detour() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 120.0, 120.0, 180.0, 40.0)

    choice = choose_active_steering_target(
        position=Vec2(210.0, 260.0),
        target=Vec2(210.0, 20.0),
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )

    assert choice.detour_point is not None
    expanded = expand_rectangle(obstacle, 28.0)
    assert choice.detour_point.x < expanded.left or choice.detour_point.x > expanded.right


def test_target_directly_below_horizontal_obstacle_chooses_side_detour() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 120.0, 120.0, 180.0, 40.0)

    choice = choose_active_steering_target(
        position=Vec2(210.0, 20.0),
        target=Vec2(210.0, 260.0),
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )

    assert choice.detour_point is not None
    expanded = expand_rectangle(obstacle, 28.0)
    assert choice.detour_point.x < expanded.left or choice.detour_point.x > expanded.right


def test_active_detour_persists_while_direct_path_is_blocked() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 120.0, 120.0, 180.0, 40.0)
    target = Vec2(210.0, 20.0)
    first_choice = choose_active_steering_target(
        position=Vec2(210.0, 260.0),
        target=target,
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )

    second_choice = choose_active_steering_target(
        position=Vec2(160.0, 250.0),
        target=target,
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
        active_detour=first_choice.detour_point,
    )

    assert first_choice.detour_point is not None
    assert second_choice.detour_point == first_choice.detour_point


def test_active_detour_clears_when_direct_path_becomes_clear() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 120.0, 120.0, 180.0, 40.0)
    target = Vec2(210.0, 20.0)
    detour = Vec2(91.0, 140.0)

    choice = choose_active_steering_target(
        position=Vec2(20.0, 20.0),
        target=target,
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
        active_detour=detour,
    )

    assert choice.active_target == target
    assert choice.detour_active is False


def test_detour_does_not_alternate_every_update() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 120.0, 120.0, 180.0, 40.0)
    target = Vec2(210.0, 20.0)
    first_choice = choose_active_steering_target(
        position=Vec2(210.0, 260.0),
        target=target,
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
    )
    second_choice = choose_active_steering_target(
        position=Vec2(205.0, 250.0),
        target=target,
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
        active_detour=first_choice.detour_point,
    )

    assert first_choice.detour_point is not None
    assert second_choice.detour_point == first_choice.detour_point


def test_clicked_target_outside_obstacles_is_unchanged() -> None:
    obstacle = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)

    resolved = resolve_clicked_target_against_obstacles(
        clicked_target=Vec2(20.0, 20.0),
        obstacles=[obstacle],
        clearance=28.0,
    )

    assert resolved == Vec2(20.0, 20.0)


def test_clicked_target_inside_expanded_obstacle_snaps_outside() -> None:
    obstacle = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)

    resolved = resolve_clicked_target_against_obstacles(
        clicked_target=Vec2(120.0, 120.0),
        obstacles=[obstacle],
        clearance=28.0,
    )

    assert point_is_inside_expanded_obstacle(resolved, obstacle, 28.0) is False


def test_snap_point_out_of_expanded_obstacle_uses_nearest_edge() -> None:
    obstacle = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)

    snapped = snap_point_out_of_expanded_obstacle(
        point=Vec2(125.0, 140.0),
        obstacle=obstacle,
        clearance=28.0,
    )

    assert snapped == Vec2(71.0, 140.0)


def test_clicked_target_near_obstacle_edge_snaps_with_clearance() -> None:
    obstacle = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)

    resolved = resolve_clicked_target_against_obstacles(
        clicked_target=Vec2(95.0, 140.0),
        obstacles=[obstacle],
        clearance=28.0,
    )

    expanded = expand_rectangle(obstacle, 28.0)
    assert resolved.x == expanded.left - 1.0


def test_target_resolution_across_multiple_obstacles() -> None:
    obstacles = [
        RectangleObstacle("First", 100.0, 100.0, 80.0, 80.0),
        RectangleObstacle("Second", 30.0, 100.0, 60.0, 80.0),
    ]

    resolved = resolve_clicked_target_against_obstacles(
        clicked_target=Vec2(95.0, 140.0),
        obstacles=obstacles,
        clearance=28.0,
    )

    assert point_is_outside_all_obstacles(resolved, obstacles, 28.0) is True


def test_active_detour_clears_when_a_new_target_is_set() -> None:
    config = SteeringConfig(detour_margin=8.0)
    obstacle = RectangleObstacle("Block", 100.0, 100.0, 80.0, 80.0)

    safe_target, detour = apply_clicked_target(
        clicked_target=Vec2(120.0, 120.0),
        obstacles=[obstacle],
        config=config,
        circle_radius=20.0,
        active_detour=Vec2(20.0, 220.0),
    )

    assert detour is None
    assert point_is_inside_expanded_obstacle(safe_target, obstacle, 28.0) is False
