from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vec2":
        return self * scalar


@dataclass(frozen=True)
class InputState:
    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False

    def any_pressed(self) -> bool:
        return self.left or self.right or self.up or self.down


@dataclass(frozen=True)
class MotionState:
    position: Vec2
    velocity: Vec2
    acceleration: Vec2


@dataclass(frozen=True)
class MotionConfig:
    size: tuple[int, int] = (800, 600)
    radius: int = 20
    acceleration: float = 900.0
    friction: float = 4.0


def make_initial_state(config: MotionConfig) -> MotionState:
    width, height = config.size
    center = Vec2(width / 2, height / 2)
    return MotionState(
        position=center,
        velocity=Vec2(0.0, 0.0),
        acceleration=Vec2(0.0, 0.0),
    )


def acceleration_from_input(inputs: InputState, acceleration: float) -> Vec2:
    horizontal = float(inputs.right) - float(inputs.left)
    vertical = float(inputs.down) - float(inputs.up)
    return Vec2(horizontal * acceleration, vertical * acceleration)


def distance_between_points(first: Vec2, second: Vec2) -> float:
    return hypot(second.x - first.x, second.y - first.y)


def point_is_inside_circle(point: Vec2, center: Vec2, radius: float) -> bool:
    return distance_between_points(point, center) <= radius


def speed_from_velocity(velocity: Vec2) -> float:
    return hypot(velocity.x, velocity.y)


def apply_friction(velocity: Vec2, friction: float, dt: float) -> Vec2:
    factor = max(0.0, 1.0 - friction * dt)
    return velocity * factor


def bounce_off_edges(
    position: Vec2,
    velocity: Vec2,
    radius: int,
    size: tuple[int, int],
) -> tuple[Vec2, Vec2]:
    width, height = size
    x = position.x
    y = position.y
    vx = velocity.x
    vy = velocity.y

    if x - radius < 0:
        x = float(radius)
        vx = abs(vx)
    elif x + radius > width:
        x = float(width - radius)
        vx = -abs(vx)

    if y - radius < 0:
        y = float(radius)
        vy = abs(vy)
    elif y + radius > height:
        y = float(height - radius)
        vy = -abs(vy)

    return Vec2(x, y), Vec2(vx, vy)


def update_motion(
    state: MotionState,
    inputs: InputState,
    dt: float,
    config: MotionConfig,
) -> MotionState:
    acceleration = acceleration_from_input(inputs, config.acceleration)
    velocity = state.velocity + acceleration * dt

    if not inputs.any_pressed():
        velocity = apply_friction(velocity, config.friction, dt)

    position = state.position + velocity * dt
    position, velocity = bounce_off_edges(
        position=position,
        velocity=velocity,
        radius=config.radius,
        size=config.size,
    )

    return MotionState(
        position=position,
        velocity=velocity,
        acceleration=acceleration,
    )
