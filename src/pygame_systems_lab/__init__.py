"""Starter package for pygame_systems_lab."""


def run() -> None:
    from .app import run as run_app

    run_app()


def main() -> None:
    from .app import main as main_app

    main_app()


__all__ = ["main", "run"]
