from pygame_systems_lab.labs.history import (
    SignalMarker,
    TrailPoint,
    add_signal_marker,
    add_trail_point,
    age_signal_markers,
    age_trail_points,
    remove_expired_signal_markers,
    remove_expired_trail_points,
)
from pygame_systems_lab.labs.motion import Vec2


def test_add_trail_point_appends_a_new_point() -> None:
    trail_points = add_trail_point([], Vec2(10.0, 20.0), 1.5)

    assert trail_points == [
        TrailPoint(position=Vec2(10.0, 20.0), age=0.0, lifetime=1.5)
    ]


def test_age_trail_points_increases_age_by_dt() -> None:
    trail_points = [TrailPoint(position=Vec2(5.0, 5.0), age=0.2, lifetime=1.0)]

    aged_points = age_trail_points(trail_points, 0.3)

    assert aged_points[0].age == 0.5


def test_remove_expired_trail_points_keeps_only_live_points() -> None:
    trail_points = [
        TrailPoint(position=Vec2(0.0, 0.0), age=0.4, lifetime=1.0),
        TrailPoint(position=Vec2(1.0, 1.0), age=1.0, lifetime=1.0),
    ]

    live_points = remove_expired_trail_points(trail_points)

    assert live_points == [TrailPoint(position=Vec2(0.0, 0.0), age=0.4, lifetime=1.0)]


def test_add_signal_marker_appends_a_new_marker() -> None:
    signal_markers = add_signal_marker([], Vec2(30.0, 40.0), 2.0)

    assert signal_markers == [
        SignalMarker(position=Vec2(30.0, 40.0), age=0.0, lifetime=2.0)
    ]


def test_age_signal_markers_increases_age_by_dt() -> None:
    signal_markers = [
        SignalMarker(position=Vec2(3.0, 4.0), age=0.5, lifetime=2.0)
    ]

    aged_markers = age_signal_markers(signal_markers, 0.25)

    assert aged_markers[0].age == 0.75


def test_remove_expired_signal_markers_keeps_only_live_markers() -> None:
    signal_markers = [
        SignalMarker(position=Vec2(0.0, 0.0), age=0.1, lifetime=1.0),
        SignalMarker(position=Vec2(2.0, 2.0), age=1.2, lifetime=1.0),
    ]

    live_markers = remove_expired_signal_markers(signal_markers)

    assert live_markers == [
        SignalMarker(position=Vec2(0.0, 0.0), age=0.1, lifetime=1.0)
    ]
