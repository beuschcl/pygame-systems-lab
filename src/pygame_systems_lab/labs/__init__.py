"""Pygame learning labs."""


def run() -> None:
    from .motion_playground import run as run_motion_playground

    run_motion_playground()


__all__ = ["run"]
