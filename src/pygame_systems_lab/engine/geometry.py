from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vec2:
        return self * scalar

    def length(self) -> float:
        return hypot(self.x, self.y)

    def distance_to(self, other: Vec2) -> float:
        return (other - self).length()

    def normalized(self) -> Vec2:
        length = self.length()
        if length == 0.0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / length, self.y / length)

    def move_toward(self, target: Vec2, max_distance: float) -> Vec2:
        if max_distance <= 0.0:
            return self

        offset = target - self
        distance = offset.length()
        if distance <= max_distance:
            return target

        return self + (offset.normalized() * max_distance)
