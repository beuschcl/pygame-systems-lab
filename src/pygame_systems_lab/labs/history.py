from dataclasses import dataclass

from .motion import Vec2


@dataclass(frozen=True)
class TrailPoint:
    position: Vec2
    age: float
    lifetime: float


@dataclass(frozen=True)
class SignalMarker:
    position: Vec2
    age: float
    lifetime: float


def add_trail_point(
    trail_points: list[TrailPoint],
    position: Vec2,
    lifetime: float,
) -> list[TrailPoint]:
    return trail_points + [TrailPoint(position=position, age=0.0, lifetime=lifetime)]


def age_trail_points(trail_points: list[TrailPoint], dt: float) -> list[TrailPoint]:
    return [
        TrailPoint(point.position, point.age + dt, point.lifetime)
        for point in trail_points
    ]


def remove_expired_trail_points(trail_points: list[TrailPoint]) -> list[TrailPoint]:
    return [point for point in trail_points if point.age < point.lifetime]


def add_signal_marker(
    signal_markers: list[SignalMarker],
    position: Vec2,
    lifetime: float,
) -> list[SignalMarker]:
    return signal_markers + [SignalMarker(position=position, age=0.0, lifetime=lifetime)]


def age_signal_markers(
    signal_markers: list[SignalMarker],
    dt: float,
) -> list[SignalMarker]:
    return [
        SignalMarker(marker.position, marker.age + dt, marker.lifetime)
        for marker in signal_markers
    ]


def remove_expired_signal_markers(
    signal_markers: list[SignalMarker],
) -> list[SignalMarker]:
    return [marker for marker in signal_markers if marker.age < marker.lifetime]


def fade_ratio(age: float, lifetime: float) -> float:
    if lifetime <= 0.0:
        return 0.0
    return max(0.0, 1.0 - (age / lifetime))
