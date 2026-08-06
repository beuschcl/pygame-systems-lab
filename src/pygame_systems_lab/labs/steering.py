from dataclasses import dataclass

from .collision import RectangleObstacle
from .motion import Vec2


@dataclass(frozen=True)
class SteeringConfig:
    max_speed: float = 320.0
    max_acceleration: float = 900.0
    slow_radius: float = 140.0
    stop_radius: float = 10.0
    detour_margin: float = 8.0


@dataclass(frozen=True)
class SteeringTargetChoice:
    active_target: Vec2 | None
    detour_point: Vec2 | None = None
    blocking_obstacle: RectangleObstacle | None = None

    @property
    def detour_active(self) -> bool:
        return self.detour_point is not None


def vector_length(vector: Vec2) -> float:
    return ((vector.x * vector.x) + (vector.y * vector.y)) ** 0.5


def direction_to_target(start: Vec2, target: Vec2) -> Vec2:
    offset = target - start
    length = vector_length(offset)
    if length == 0.0:
        return Vec2(0.0, 0.0)
    return Vec2(offset.x / length, offset.y / length)


def distance_to_target(start: Vec2, target: Vec2) -> float:
    return vector_length(target - start)


def arrival_speed(distance: float, config: SteeringConfig) -> float:
    if distance <= config.stop_radius:
        return 0.0
    if distance >= config.slow_radius:
        return config.max_speed
    return config.max_speed * (distance / config.slow_radius)


def desired_velocity_toward_target(
    position: Vec2,
    target: Vec2,
    config: SteeringConfig,
) -> Vec2:
    direction = direction_to_target(position, target)
    speed = arrival_speed(distance_to_target(position, target), config)
    return direction * speed


def steering_acceleration_toward_velocity(
    current_velocity: Vec2,
    desired_velocity: Vec2,
    max_acceleration: float,
) -> Vec2:
    delta_velocity = desired_velocity - current_velocity
    delta_speed = vector_length(delta_velocity)
    if delta_speed == 0.0:
        return Vec2(0.0, 0.0)
    if delta_speed <= max_acceleration:
        return delta_velocity

    scale = max_acceleration / delta_speed
    return Vec2(delta_velocity.x * scale, delta_velocity.y * scale)


def _point_on_segment(point: Vec2, start: Vec2, end: Vec2) -> bool:
    cross = ((point.y - start.y) * (end.x - start.x)) - (
        (point.x - start.x) * (end.y - start.y)
    )
    if abs(cross) > 0.0001:
        return False

    return (
        min(start.x, end.x) - 0.0001 <= point.x <= max(start.x, end.x) + 0.0001
        and min(start.y, end.y) - 0.0001 <= point.y <= max(start.y, end.y) + 0.0001
    )


def _orientation(start: Vec2, middle: Vec2, end: Vec2) -> float:
    return ((middle.y - start.y) * (end.x - middle.x)) - (
        (middle.x - start.x) * (end.y - middle.y)
    )


def _segments_intersect(first_start: Vec2, first_end: Vec2, second_start: Vec2, second_end: Vec2) -> bool:
    first = _orientation(first_start, first_end, second_start)
    second = _orientation(first_start, first_end, second_end)
    third = _orientation(second_start, second_end, first_start)
    fourth = _orientation(second_start, second_end, first_end)

    if (first > 0.0 and second < 0.0 or first < 0.0 and second > 0.0) and (
        third > 0.0 and fourth < 0.0 or third < 0.0 and fourth > 0.0
    ):
        return True

    if first == 0.0 and _point_on_segment(second_start, first_start, first_end):
        return True
    if second == 0.0 and _point_on_segment(second_end, first_start, first_end):
        return True
    if third == 0.0 and _point_on_segment(first_start, second_start, second_end):
        return True
    return fourth == 0.0 and _point_on_segment(first_end, second_start, second_end)


def _segment_rectangle_hit_time(
    start: Vec2,
    end: Vec2,
    rectangle: RectangleObstacle,
) -> float | None:
    if point_is_inside_rectangle(start, rectangle):
        return 0.0

    edges = [
        (Vec2(rectangle.left, rectangle.top), Vec2(rectangle.right, rectangle.top)),
        (Vec2(rectangle.right, rectangle.top), Vec2(rectangle.right, rectangle.bottom)),
        (Vec2(rectangle.right, rectangle.bottom), Vec2(rectangle.left, rectangle.bottom)),
        (Vec2(rectangle.left, rectangle.bottom), Vec2(rectangle.left, rectangle.top)),
    ]

    hit_time = None
    segment_length = distance_to_target(start, end)
    if segment_length == 0.0:
        return None

    for edge_start, edge_end in edges:
        if _segments_intersect(start, end, edge_start, edge_end):
            distance_from_start = distance_to_target(start, edge_start)
            current_hit_time = distance_from_start / segment_length
            if hit_time is None or current_hit_time < hit_time:
                hit_time = current_hit_time

    return hit_time


def line_segment_intersects_rectangle(
    start: Vec2,
    end: Vec2,
    rectangle: RectangleObstacle,
) -> bool:
    return _segment_rectangle_hit_time(start, end, rectangle) is not None


def expand_rectangle(rectangle: RectangleObstacle, padding: float) -> RectangleObstacle:
    return RectangleObstacle(
        name=rectangle.name,
        x=rectangle.x - padding,
        y=rectangle.y - padding,
        width=rectangle.width + (padding * 2.0),
        height=rectangle.height + (padding * 2.0),
    )


def point_is_inside_rectangle(point: Vec2, rectangle: RectangleObstacle) -> bool:
    return (
        rectangle.left <= point.x <= rectangle.right
        and rectangle.top <= point.y <= rectangle.bottom
    )


def point_is_inside_expanded_obstacle(
    point: Vec2,
    obstacle: RectangleObstacle,
    clearance: float,
) -> bool:
    return point_is_inside_rectangle(point, expand_rectangle(obstacle, clearance))


def snap_point_out_of_expanded_obstacle(
    point: Vec2,
    obstacle: RectangleObstacle,
    clearance: float,
) -> Vec2:
    ranked_candidates = [
        (distance_to_target(point, candidate), candidate)
        for candidate in snap_candidates_out_of_expanded_obstacle(
            point,
            obstacle,
            clearance,
        )
    ]
    ranked_candidates.sort(key=lambda item: item[0])
    return ranked_candidates[0][1]


def snap_candidates_out_of_expanded_obstacle(
    point: Vec2,
    obstacle: RectangleObstacle,
    clearance: float,
) -> list[Vec2]:
    expanded = expand_rectangle(obstacle, clearance)
    outside_offset = 1.0
    clamped_x = min(max(point.x, expanded.left), expanded.right)
    clamped_y = min(max(point.y, expanded.top), expanded.bottom)
    return [
        Vec2(expanded.left - outside_offset, clamped_y),
        Vec2(expanded.right + outside_offset, clamped_y),
        Vec2(clamped_x, expanded.top - outside_offset),
        Vec2(clamped_x, expanded.bottom + outside_offset),
    ]


def resolve_clicked_target_against_obstacles(
    clicked_target: Vec2,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    clearance: float,
) -> Vec2:
    resolved_target = clicked_target

    for _ in range(max(1, len(obstacles) * 4)):
        blocking_obstacles = [
            obstacle
            for obstacle in obstacles
            if point_is_inside_expanded_obstacle(resolved_target, obstacle, clearance)
        ]
        if not blocking_obstacles:
            return resolved_target

        ranked_candidates: list[tuple[int, float, Vec2]] = []
        for obstacle in blocking_obstacles:
            for candidate in snap_candidates_out_of_expanded_obstacle(
                resolved_target,
                obstacle,
                clearance,
            ):
                blocking_count = sum(
                    point_is_inside_expanded_obstacle(candidate, other, clearance)
                    for other in obstacles
                )
                ranked_candidates.append(
                    (
                        blocking_count,
                        distance_to_target(clicked_target, candidate),
                        candidate,
                    )
                )

        ranked_candidates.sort(key=lambda item: (item[0], item[1]))
        resolved_target = ranked_candidates[0][2]

    return resolved_target


def apply_clicked_target(
    clicked_target: Vec2,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    config: SteeringConfig,
    circle_radius: float,
    active_detour: Vec2 | None,
) -> tuple[Vec2, Vec2 | None]:
    clearance = circle_radius + config.detour_margin
    safe_target = resolve_clicked_target_against_obstacles(
        clicked_target,
        obstacles,
        clearance,
    )
    return safe_target, None


def point_is_outside_all_obstacles(
    point: Vec2,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    clearance: float,
) -> bool:
    for obstacle in obstacles:
        if point_is_inside_rectangle(point, expand_rectangle(obstacle, clearance)):
            return False
    return True


def line_segment_is_clear_of_obstacles(
    start: Vec2,
    end: Vec2,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    clearance: float,
) -> bool:
    for obstacle in obstacles:
        if line_segment_intersects_rectangle(start, end, expand_rectangle(obstacle, clearance)):
            return False
    return True


def find_blocking_obstacle_on_path(
    start: Vec2,
    target: Vec2,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    clearance: float,
) -> RectangleObstacle | None:
    blocking_obstacle = None
    earliest_hit = None

    for obstacle in obstacles:
        expanded_obstacle = expand_rectangle(obstacle, clearance)
        hit_time = _segment_rectangle_hit_time(start, target, expanded_obstacle)
        if hit_time is None:
            continue
        if earliest_hit is None or hit_time < earliest_hit:
            earliest_hit = hit_time
            blocking_obstacle = obstacle

    return blocking_obstacle


def choose_detour_point_around_rectangle(
    start: Vec2,
    target: Vec2,
    rectangle: RectangleObstacle,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    clearance: float,
) -> Vec2 | None:
    expanded_rectangle = expand_rectangle(rectangle, clearance)
    candidate_offset = 1.0
    center_x = (expanded_rectangle.left + expanded_rectangle.right) / 2.0
    center_y = (expanded_rectangle.top + expanded_rectangle.bottom) / 2.0
    horizontal_escape = expanded_rectangle.height + candidate_offset
    vertical_escape = expanded_rectangle.width + candidate_offset
    left_middle = Vec2(expanded_rectangle.left - horizontal_escape, center_y)
    right_middle = Vec2(expanded_rectangle.right + horizontal_escape, center_y)
    top_middle = Vec2(center_x, expanded_rectangle.top - vertical_escape)
    bottom_middle = Vec2(center_x, expanded_rectangle.bottom + vertical_escape)

    if rectangle.width >= rectangle.height:
        candidates = [
            ("left", left_middle, 0),
            ("right", right_middle, 0),
            ("top", top_middle, 1),
            ("bottom", bottom_middle, 1),
        ]
    else:
        candidates = [
            ("top", top_middle, 0),
            ("bottom", bottom_middle, 0),
            ("left", left_middle, 1),
            ("right", right_middle, 1),
        ]

    ranked_candidates: list[tuple[int, int, float, Vec2]] = []
    for _, candidate, orientation_priority in candidates:
        if not line_segment_is_clear_of_obstacles(
            start,
            candidate,
            obstacles,
            clearance,
        ):
            continue

        outside_all_obstacles = point_is_outside_all_obstacles(
            candidate,
            obstacles,
            clearance,
        )
        outside_priority = 0 if outside_all_obstacles else 1
        total_route = distance_to_target(start, candidate) + distance_to_target(
            candidate,
            target,
        )
        ranked_candidates.append(
            (
                orientation_priority,
                outside_priority,
                total_route,
                candidate,
            )
        )

    if not ranked_candidates:
        return None

    ranked_candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return ranked_candidates[0][3]


def choose_persistent_detour(
    start: Vec2,
    target: Vec2,
    active_detour: Vec2 | None,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    clearance: float,
) -> Vec2 | None:
    if active_detour is None:
        return None

    if not point_is_outside_all_obstacles(active_detour, obstacles, clearance):
        return None

    if not line_segment_is_clear_of_obstacles(start, active_detour, obstacles, clearance):
        return None

    if line_segment_is_clear_of_obstacles(start, target, obstacles, clearance):
        return None

    return active_detour


def choose_active_steering_target(
    position: Vec2,
    target: Vec2 | None,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
    config: SteeringConfig,
    circle_radius: float,
    active_detour: Vec2 | None = None,
) -> SteeringTargetChoice:
    if target is None:
        return SteeringTargetChoice(active_target=None)

    clearance = circle_radius + config.detour_margin
    if line_segment_is_clear_of_obstacles(position, target, obstacles, clearance):
        return SteeringTargetChoice(active_target=target)

    persistent_detour = choose_persistent_detour(
        position,
        target,
        active_detour,
        obstacles,
        clearance,
    )
    if persistent_detour is not None:
        return SteeringTargetChoice(
            active_target=persistent_detour,
            detour_point=persistent_detour,
        )

    blocking_obstacle = find_blocking_obstacle_on_path(
        position,
        target,
        obstacles,
        clearance,
    )
    if blocking_obstacle is None:
        return SteeringTargetChoice(active_target=target)

    detour_point = choose_detour_point_around_rectangle(
        position,
        target,
        blocking_obstacle,
        obstacles,
        clearance,
    )
    if detour_point is None:
        return SteeringTargetChoice(active_target=target)

    return SteeringTargetChoice(
        active_target=detour_point,
        detour_point=detour_point,
        blocking_obstacle=blocking_obstacle,
    )
