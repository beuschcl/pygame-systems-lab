from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Protocol, Self

from .settings import MovementSettings


class Vec2(Protocol):
    @property
    def x(self) -> float: ...

    @property
    def y(self) -> float: ...

    def __add__(self, other: Self) -> Self: ...

    def __sub__(self, other: Self) -> Self: ...

    def __mul__(self, scalar: float) -> Self: ...

    def __rmul__(self, scalar: float) -> Self: ...


@dataclass(frozen=True)
class MovementPlan:
    target_position: Vec2 | None
    speed: float
    arrival_radius: float


@dataclass(frozen=True)
class MovementResult:
    position: Vec2
    facing: Vec2
    reached_target: bool


def plan_direct_movement(
    position: Vec2,
    target_position: Vec2 | None,
    settings: MovementSettings,
) -> MovementPlan:
    if target_position is None:
        return MovementPlan(
            target_position=None,
            speed=0.0,
            arrival_radius=settings.arrival_radius,
        )

    distance = _distance_between(position, target_position)
    speed = 0.0 if distance <= settings.arrival_radius else settings.max_speed
    return MovementPlan(
        target_position=target_position,
        speed=speed,
        arrival_radius=settings.arrival_radius,
    )


def apply_movement_plan(
    position: Vec2,
    facing: Vec2,
    plan: MovementPlan,
    dt: float,
) -> MovementResult:
    target_position = plan.target_position
    if target_position is None:
        return MovementResult(
            position=position,
            facing=facing,
            reached_target=False,
        )

    offset = target_position - position
    distance = _vector_length(offset)
    if distance <= plan.arrival_radius:
        new_facing = facing if distance == 0.0 else offset * (1.0 / distance)
        return MovementResult(
            position=target_position,
            facing=new_facing,
            reached_target=True,
        )

    max_travel = plan.speed * dt
    if max_travel <= 0.0:
        return MovementResult(
            position=position,
            facing=facing,
            reached_target=False,
        )

    direction = offset * (1.0 / distance)
    if max_travel >= distance:
        return MovementResult(
            position=target_position,
            facing=direction,
            reached_target=True,
        )

    new_position = position + (direction * max_travel)
    return MovementResult(
        position=new_position,
        facing=direction,
        reached_target=False,
    )


def _distance_between(first: Vec2, second: Vec2) -> float:
    return hypot(second.x - first.x, second.y - first.y)


def _vector_length(vector: Vec2) -> float:
    return hypot(vector.x, vector.y)
