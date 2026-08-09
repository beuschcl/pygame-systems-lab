from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from pygame_systems_lab.engine.settings import (
    DEFAULT_ENGINE_SETTINGS,
    AgentSettings,
    EngineSettings,
    MovementSettings,
    WorldSettings,
)


def test_default_engine_settings_are_positive_and_usable() -> None:
    settings = DEFAULT_ENGINE_SETTINGS

    assert isinstance(settings, EngineSettings)
    assert settings.movement.max_speed > 0.0
    assert settings.movement.arrival_radius > 0.0
    assert settings.movement.default_dt > 0.0
    assert settings.agent.radius > 0.0
    assert settings.agent.interaction_radius > 0.0
    assert settings.agent.base_interaction_radius > 0.0
    assert settings.agent.detection_radius > 0.0
    assert settings.agent.wander_step_distance > 0.0
    assert settings.world.width > 0
    assert settings.world.height > 0


def test_engine_setting_dataclasses_are_frozen() -> None:
    movement = MovementSettings(max_speed=80.0, arrival_radius=4.0, default_dt=0.1)
    agent = AgentSettings(
        radius=10.0,
        interaction_radius=24.0,
        base_interaction_radius=48.0,
        detection_radius=60.0,
        wander_step_distance=20.0,
    )
    world = WorldSettings(width=320, height=240)
    settings = EngineSettings(movement=movement, agent=agent, world=world)

    assert is_dataclass(movement)
    assert is_dataclass(agent)
    assert is_dataclass(world)
    assert is_dataclass(settings)

    with pytest.raises(FrozenInstanceError):
        type(movement).__setattr__(movement, "max_speed", 100.0)
