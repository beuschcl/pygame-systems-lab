from dataclasses import dataclass


@dataclass(frozen=True)
class MovementSettings:
    max_speed: float
    arrival_radius: float
    default_dt: float


@dataclass(frozen=True)
class AgentSettings:
    radius: float
    interaction_radius: float
    base_interaction_radius: float


@dataclass(frozen=True)
class WorldSettings:
    width: int
    height: int


@dataclass(frozen=True)
class EngineSettings:
    movement: MovementSettings
    agent: AgentSettings
    world: WorldSettings


DEFAULT_ENGINE_SETTINGS = EngineSettings(
    movement=MovementSettings(
        max_speed=120.0,
        arrival_radius=6.0,
        default_dt=1.0 / 60.0,
    ),
    agent=AgentSettings(
        radius=12.0,
        interaction_radius=48.0,
        base_interaction_radius=96.0,
    ),
    world=WorldSettings(
        width=800,
        height=600,
    ),
)
