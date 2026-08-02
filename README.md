# pygame-systems-lab

Small Pygame learning project with a clean `src` layout.

## Setup

1. Create and activate a virtual environment.
2. Install the project in editable mode with dev tools:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run the app

```powershell
python -m pygame_systems_lab
```

This launches **Motion Playground**, the first lab.

## Motion Playground controls

- Arrow keys: apply acceleration
- Space: pause or unpause
- R: reset to the center
- Escape or close window: quit

The demo shows a moving circle, a velocity vector, and a small debug overlay with position, velocity, acceleration, FPS, and pause state.

## Run the test suite

```powershell
pytest
```
