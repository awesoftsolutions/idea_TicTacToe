"""Pytest session configuration for headless pygame.

Sets the SDL_VIDEODRIVER to "dummy" and pre-imports pygame before any
test modules are collected, preventing the pygame lazy-submodule circular
import error when ``import pygame`` is triggered from ``src/scenes.py``
during test execution.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

# Pre-import pygame at conftest module level so it is loaded, fully
# initialised, and cached in sys.modules before any test module is
# collected. This ensures ``import pygame`` inside src/scenes.py
# returns the cached module rather than triggering pygame's lazy
# submodule loader from a different module context.
import pygame  # noqa: E402

# Snapshot the pygame module object so we can restore it to sys.modules
# after test_no_pygame_import (test_game.py) pops it. Re-importing pygame
# from scratch fails because its lazy submodule loader accesses the
# partially-initialised module. Saving and restoring avoids this.
_pygame_module: object = pygame

import pytest


@pytest.fixture(autouse=True)
def _restore_pygame_sys_module() -> None:
    """Restore pygame in sys.modules after each test.

    The ``test_no_pygame_import`` test (test_game.py) calls
    ``sys.modules.pop("pygame", None)`` to verify that importing
    ``src.game`` does not re-import pygame. This fixture puts
    the saved pygame module reference back into ``sys.modules``
    after that test, preventing cascading import failures in
    subsequent tests that import ``src.scenes``.
    """
    yield
    if "pygame" not in sys.modules:
        sys.modules["pygame"] = _pygame_module