from dataclasses import dataclass, replace
from enum import StrEnum, auto

from .agent import AgentState
from .geometry import Vec2


class InteractionKind(StrEnum):
    CLAIM = auto()
    PICKUP = auto()
    DROPOFF = auto()
    RELEASE = auto()


@dataclass(frozen=True)
class InteractionTarget:
    id: int
    kind: str
    position: Vec2
    radius: float
    available: bool = True
    claimed_by_id: int | None = None


@dataclass(frozen=True)
class InteractionResult:
    succeeded: bool
    kind: InteractionKind
    agent_id: int
    target_id: int | None = None
    message: str = ""


def is_within_interaction_range(
    agent_position: Vec2,
    target_position: Vec2,
    interaction_radius: float,
) -> bool:
    return agent_position.distance_to(target_position) <= interaction_radius


def can_claim_target(agent: AgentState, target: InteractionTarget) -> bool:
    return target.available and (
        target.claimed_by_id is None or target.claimed_by_id == agent.id
    )


def claim_target(
    agent: AgentState,
    target: InteractionTarget,
) -> tuple[InteractionTarget, InteractionResult]:
    if can_claim_target(agent, target):
        claimed_target = replace(target, claimed_by_id=agent.id)
        return claimed_target, InteractionResult(
            succeeded=True,
            kind=InteractionKind.CLAIM,
            agent_id=agent.id,
            target_id=target.id,
        )

    return target, InteractionResult(
        succeeded=False,
        kind=InteractionKind.CLAIM,
        agent_id=agent.id,
        target_id=target.id,
    )


def can_pickup_target(
    agent: AgentState,
    target: InteractionTarget,
    interaction_radius: float,
) -> bool:
    return (
        target.available
        and agent.carried_item_id is None
        and is_within_interaction_range(agent.position, target.position, interaction_radius)
        and (target.claimed_by_id is None or target.claimed_by_id == agent.id)
    )


def pickup_target(
    agent: AgentState,
    target: InteractionTarget,
    interaction_radius: float,
) -> tuple[AgentState, InteractionTarget, InteractionResult]:
    if can_pickup_target(agent, target, interaction_radius):
        return (
            replace(agent, carried_item_id=target.id),
            replace(target, available=False),
            InteractionResult(
                succeeded=True,
                kind=InteractionKind.PICKUP,
                agent_id=agent.id,
                target_id=target.id,
            ),
        )

    return (
        agent,
        target,
        InteractionResult(
            succeeded=False,
            kind=InteractionKind.PICKUP,
            agent_id=agent.id,
            target_id=target.id,
        ),
    )


def can_dropoff(agent: AgentState, base_position: Vec2, base_radius: float) -> bool:
    return agent.carried_item_id is not None and is_within_interaction_range(
        agent.position,
        base_position,
        base_radius,
    )


def dropoff_item(
    agent: AgentState,
    base_position: Vec2,
    base_radius: float,
) -> tuple[AgentState, InteractionResult]:
    if can_dropoff(agent, base_position, base_radius):
        carried_item_id = agent.carried_item_id
        dropped_off_agent = replace(agent, carried_item_id=None)
        return dropped_off_agent, InteractionResult(
            succeeded=True,
            kind=InteractionKind.DROPOFF,
            agent_id=agent.id,
            target_id=carried_item_id,
        )

    return agent, InteractionResult(
        succeeded=False,
        kind=InteractionKind.DROPOFF,
        agent_id=agent.id,
        target_id=agent.carried_item_id,
    )
