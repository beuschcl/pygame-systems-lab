from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto

from .geometry import Vec2


class AgentTaskState(StrEnum):
    WANDERING = auto()
    SEEKING_TARGET = auto()
    CARRYING_ITEM = auto()
    RETURNING_TO_BASE = auto()
    WAITING = auto()


@dataclass(frozen=True)
class AgentState:
    id: int
    name: str
    position: Vec2
    facing: Vec2
    speed: float
    task_state: AgentTaskState
    target_position: Vec2 | None = None
    carried_item_id: int | None = None
