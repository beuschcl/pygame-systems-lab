# pygame-systems-lab

Small starter project for learning Pygame with a clean `src` layout.

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

This opens a window, fills the screen with a background color, processes quit events, and runs at a steady frame rate.

## Run the test suite

```powershell
pytest
```
