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

This launches **Motion Playground**, the current playable lab.

## Motion Playground controls

- Arrow keys: apply acceleration
- A: toggle steering mode
- Left click the circle: select it
- Left click empty space: clear selection and set the steering target
- Space: pause or unpause
- T: toggle trails on or off
- C: clear all trails
- S: drop a signal marker
- H: show or hide hitboxes
- R: reset to the center
- Escape or close window: quit

The demo shows a moving circle, obstacle rectangles, a velocity vector, a steering target, a temporary detour point when a direct path is blocked, fading trails, fading signal markers, a debug overlay, and a right-side inspector panel when the circle is selected.

Right now, the inspector panel is only a visual overlay. It does not shrink the motion world's bounds, so the circle can move underneath it. A later camera or layout lab may split the screen into a world viewport and a UI sidebar.

## Run the test suite

```powershell
pytest
```
