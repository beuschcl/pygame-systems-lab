from enum import Enum


class ExperimentAgentState(Enum):
    """Small copy of the AntState idea from AntProtptype.

    The names are neutral enough for this learning repo, while keeping the
    original three-step ant movement loop easy to recognize.
    """

    WANDERING = "wandering"
    SEEKING_RESOURCE = "seeking_resource"
    CARRYING_RESOURCE = "carrying_resource"
