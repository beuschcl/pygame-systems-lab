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

This launches **Motion Playground (Lab 7: Resource Pickup Loop)**.

## Motion Playground controls

- A: toggle autonomous steering on or off
- Left click an agent: select it
- Left click empty space: set selected agent target (if no selected agent, no action)
- Space: pause or unpause
- T: toggle trails on or off
- C: clear all trails
- S: drop a signal marker
- H: show or hide hitboxes
- R: reset all agents
- Escape or close window: quit

The demo shows multiple autonomous agents that seek resources, carry them back to base, and increase a collected count. It also includes obstacle rectangles, fading trails, fading signal markers, a debug overlay, and a right-side inspector panel for the selected agent.

## Run the test suite

```powershell
pytest
```
