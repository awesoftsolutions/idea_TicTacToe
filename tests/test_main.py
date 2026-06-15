"""Tests for the game entry point module in src/main.py.

This test suite contains 2 tests covering:
- Module-level constant verification (WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
- Clean import verification (all dependencies resolve at import time)

NOTE: src/main.py was implemented in Sprint 4, Task 5 (Step 3). Both
tests now pass with exit code 0, verifying constants and clean import.
"""

# Sprint 4, Task 5 — Entry point tests

from __future__ import annotations

import os

# Set headless video driver before any pygame import (matching the pattern
# from src/assets.py line 17 and tests/test_scenes.py line 25).
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_main_constants_exist() -> None:
    """Verify module-level constants in src/main.py match architecture §9.

    Expected values (from architecture §9 and pseudocode §3.1):
    - WINDOW_WIDTH  = 960   (pixels, non-resizable window)
    - WINDOW_HEIGHT = 720   (pixels, non-resizable window)
    - WINDOW_TITLE  = "Favur Tic-Tac-Toe"  (SOW-mandated exact title)
    - FPS_LIMIT     = 60    (target frame rate)
    """
    from src.main import FPS_LIMIT, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH

    assert WINDOW_WIDTH == 960
    assert WINDOW_HEIGHT == 720
    assert WINDOW_TITLE == "Favur Tic-Tac-Toe"
    assert FPS_LIMIT == 60


def test_main_imports_cleanly() -> None:
    """Import src.main module without raising ImportError.

    This validates that all scene dependencies (TeamSelectScene, GameScene,
    CelebrationScene), the AssetManager manifest reading path, and module-
    level constants resolve at import time without error. If src/main.py
    has a missing import, broken reference, or unhandled ImportError at
    module level, this test will catch it.
    """
    import src.main  # noqa: F401
