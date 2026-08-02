import pygame
import pytest

from pygame_systems_lab.app import DEFAULT_CONFIG, handle_events


def test_handle_events_stops_on_quit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [pygame.event.Event(pygame.QUIT)],
    )

    assert handle_events() is False


def test_default_config_is_beginner_friendly() -> None:
    assert DEFAULT_CONFIG.size == (800, 600)
    assert DEFAULT_CONFIG.fps == 60
