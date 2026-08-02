from dataclasses import dataclass, field
from math import sqrt

from .motion import Vec2


@dataclass(frozen=True)
class RectangleObstacle:
    name: str
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height


@dataclass(frozen=True)
class CollisionResult:
    position: Vec2
    velocity: Vec2 = field(default_factory=lambda: Vec2(0.0, 0.0))
    collided: bool = False
    blocked_x: bool = False
    blocked_y: bool = False
    normal: Vec2 = field(default_factory=lambda: Vec2(0.0, 0.0))


def clamp_point_to_rectangle(point: Vec2, rectangle: RectangleObstacle) -> Vec2:
    return Vec2(
        min(max(point.x, rectangle.left), rectangle.right),
        min(max(point.y, rectangle.top), rectangle.bottom),
    )


def circle_intersects_rectangle(
    center: Vec2,
    radius: float,
    rectangle: RectangleObstacle,
) -> bool:
    closest_point = clamp_point_to_rectangle(center, rectangle)
    dx = center.x - closest_point.x
    dy = center.y - closest_point.y
    return (dx * dx) + (dy * dy) <= radius * radius


def inward_speed_along_normal(velocity: Vec2, normal: Vec2) -> float:
    return (velocity.x * normal.x) + (velocity.y * normal.y)


def slide_velocity_along_normal(velocity: Vec2, normal: Vec2) -> Vec2:
    speed_toward_surface = inward_speed_along_normal(velocity, normal)
    if speed_toward_surface >= 0.0:
        return velocity

    return Vec2(
        velocity.x - (speed_toward_surface * normal.x),
        velocity.y - (speed_toward_surface * normal.y),
    )


def resolve_center_inside_rectangle(
    position: Vec2,
    previous_position: Vec2,
    radius: float,
    rectangle: RectangleObstacle,
) -> CollisionResult:
    move_x = position.x - previous_position.x
    move_y = position.y - previous_position.y
    horizontal_priority = abs(move_x) >= abs(move_y)

    candidates = [
        (
            position.x - rectangle.left,
            0 if horizontal_priority and move_x > 0.0 else 1,
            CollisionResult(
                position=Vec2(rectangle.left - radius, position.y),
                collided=True,
                blocked_x=True,
                normal=Vec2(-1.0, 0.0),
            ),
        ),
        (
            rectangle.right - position.x,
            0 if horizontal_priority and move_x < 0.0 else 1,
            CollisionResult(
                position=Vec2(rectangle.right + radius, position.y),
                collided=True,
                blocked_x=True,
                normal=Vec2(1.0, 0.0),
            ),
        ),
        (
            position.y - rectangle.top,
            0 if (not horizontal_priority) and move_y > 0.0 else 1,
            CollisionResult(
                position=Vec2(position.x, rectangle.top - radius),
                collided=True,
                blocked_y=True,
                normal=Vec2(0.0, -1.0),
            ),
        ),
        (
            rectangle.bottom - position.y,
            0 if (not horizontal_priority) and move_y < 0.0 else 1,
            CollisionResult(
                position=Vec2(position.x, rectangle.bottom + radius),
                collided=True,
                blocked_y=True,
                normal=Vec2(0.0, 1.0),
            ),
        ),
    ]

    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def resolve_circle_position_against_rectangle(
    position: Vec2,
    previous_position: Vec2,
    radius: float,
    rectangle: RectangleObstacle,
) -> CollisionResult:
    if not circle_intersects_rectangle(position, radius, rectangle):
        return CollisionResult(position=position)

    closest_point = clamp_point_to_rectangle(position, rectangle)
    dx = position.x - closest_point.x
    dy = position.y - closest_point.y
    distance_squared = (dx * dx) + (dy * dy)

    if distance_squared == 0.0:
        return resolve_center_inside_rectangle(
            position=position,
            previous_position=previous_position,
            radius=radius,
            rectangle=rectangle,
        )

    distance = sqrt(distance_squared)
    separation_distance = radius - distance
    normal = Vec2(dx / distance, dy / distance)
    resolved_position = Vec2(
        position.x + (normal.x * separation_distance),
        position.y + (normal.y * separation_distance),
    )

    return CollisionResult(
        position=resolved_position,
        collided=True,
        blocked_x=abs(normal.x) > 0.0001,
        blocked_y=abs(normal.y) > 0.0001,
        normal=normal,
    )


def check_circle_against_obstacles(
    position: Vec2,
    previous_position: Vec2,
    velocity: Vec2,
    radius: float,
    obstacles: list[RectangleObstacle] | tuple[RectangleObstacle, ...],
) -> CollisionResult:
    current_position = position
    current_velocity = velocity
    blocked_x = False
    blocked_y = False
    collided = False
    collision_normal = Vec2(0.0, 0.0)

    for obstacle in obstacles:
        result = resolve_circle_position_against_rectangle(
            current_position,
            previous_position,
            radius,
            obstacle,
        )
        if result.collided:
            current_position = result.position
            current_velocity = slide_velocity_along_normal(current_velocity, result.normal)
            blocked_x = blocked_x or result.blocked_x
            blocked_y = blocked_y or result.blocked_y
            collided = True
            collision_normal = result.normal

    return CollisionResult(
        position=current_position,
        velocity=current_velocity,
        collided=collided,
        blocked_x=blocked_x,
        blocked_y=blocked_y,
        normal=collision_normal,
    )
