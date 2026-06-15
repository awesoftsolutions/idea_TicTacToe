"""Unit tests for the CelebrationScene class (src/scenes.py).

Covers all 9 test cases from pseudocode sprint_4_task_4_code.md §10,
including 6 required tests and 3 bonus edge-case tests:

- Win display (team1_celebrate / team2_celebrate)
- Draw display (tie text, Coach aww reaction)
- Play Again button click → "team_select"
- Click outside button → None (friendly no-op)
- R key → "team_select"
- ESCAPE key → "team_select"
- Non-trigger key → None
- update(dt) → None

NOTE: All tests will fail at import time with ImportError / ModuleNotFoundError
because the CelebrationScene class has not been implemented yet
(src/scenes.py does not exist). This is the expected TDD red-phase outcome.

Usage:
    poetry run pytest tests/test_celebration.py -v
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock

# Ensure dummy video driver is set before importing pygame.
# src/assets.py also sets this, but we set it here to guarantee
# headless operation even if src/assets.py hasn't been imported yet.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

# ---------------------------------------------------------------------------
# Constants matching pseudocode §4.1 and architecture §9
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720

# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

_SPRITE_DIMENSIONS: dict[str, tuple[int, int]] = {
    "bg_celebration": (960, 720),
    "team1_celebrate": (120, 120),
    "team2_celebrate": (120, 120),
    "coach_cheer": (200, 200),
    "coach_aww": (200, 200),
    "coach_idle": (200, 200),
    "btn_play_again": (200, 60),
}


def _make_mock_asset_manager() -> MagicMock:
    """Create a mocked AssetManager.

    Returns:
        A MagicMock where:
        - ``get_sprite(key)`` returns a real ``pygame.Surface`` for any key.
        - ``get_sprite_size(key)`` returns manifest-correct dimensions:
          ``btn_play_again`` → ``(200, 60)``, team sprites → ``(120, 120)``,
          coach sprites → ``(200, 200)``, background → ``(960, 720)``.
    """
    manager = MagicMock()

    # get_sprite returns a real Surface (any size works for mock assertions)
    manager.get_sprite.return_value = pygame.Surface((1, 1))

    # get_sprite_size returns correct dimensions per sprite key
    def _size_side_effect(key: str) -> tuple[int, int]:
        if key in _SPRITE_DIMENSIONS:
            return _SPRITE_DIMENSIONS[key]
        return (1, 1)

    manager.get_sprite_size.side_effect = _size_side_effect

    return manager


def _make_mock_coach() -> MagicMock:
    """Create a mocked coach reaction callable.

    Returns tuples matching ``src/coach.py`` ``event_to_reaction()``:
    - ``"win:X"`` → ``("cheer", "Kittens win! Hooray! 🎉")``
    - ``"win:O"`` → ``("cheer", "Puppies win! Yay! 🎉")``
    - ``"draw"`` → ``("aww", "It's a tie — great game, friends!")``
    """
    coach = MagicMock()

    def _side_effect(event: str) -> tuple[str, str]:
        mapping: dict[str, tuple[str, str]] = {
            "win:X": ("cheer", "Kittens win! Hooray! 🎉"),
            "win:O": ("cheer", "Puppies win! Yay! 🎉"),
            "draw": ("aww", "It's a tie — great game, friends!"),
        }
        return mapping.get(event, ("idle", ""))

    coach.side_effect = _side_effect
    return coach


def _make_mock_board() -> MagicMock:
    """Create a mocked Board with a ``reset()`` spy.

    Returns:
        A MagicMock where ``reset()`` is a ``MagicMock`` that can be
        asserted with ``assert_called_once()``.
    """
    board = MagicMock()
    board.reset = MagicMock()
    return board


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestCelebrationScene(unittest.TestCase):
    """Unit tests for CelebrationScene (TDD red-phase: ImportError expected).

    All test methods import ``CelebrationScene`` from ``src.scenes`` at
    call time, so each test will fail with ``ImportError`` until the class
    is implemented.  This is correct RED-phase TDD behaviour.
    """

    def setUp(self) -> None:
        """Create fresh mocks before each test."""
        self.asset_manager = _make_mock_asset_manager()
        self.board = _make_mock_board()
        self.get_coach_reaction = _make_mock_coach()

    # ── 6 required tests ──────────────────────────────────────────────────

    def test_celebration_win_shows_team1_sprite(self) -> None:
        """AC-1: result='X' → team1_celebrate sprite + Coach cheer.

        Verifies:
        - ``get_coach_reaction`` was called with ``"win:X"``
        - ``get_sprite`` was called with ``"team1_celebrate"``
        - ``get_sprite`` was called with ``"coach_cheer"``
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(  # noqa: F841  # used once CelebrationScene exists
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "X",
        )

        # Coach reaction requested
        self.get_coach_reaction.assert_called_with("win:X")

        # Team 1 celebrate sprite fetched
        self.asset_manager.get_sprite.assert_any_call("team1_celebrate")

        # Coach cheer sprite fetched
        self.asset_manager.get_sprite.assert_any_call("coach_cheer")

        # Background and button sprites also fetched
        self.asset_manager.get_sprite.assert_any_call("bg_celebration")
        self.asset_manager.get_sprite.assert_any_call("btn_play_again")

        # Verify button size was looked up
        self.asset_manager.get_sprite_size.assert_any_call("btn_play_again")

    def test_celebration_draw_shows_tie_message(self) -> None:
        """AC-2: result='draw' → tie text + Coach aww.

        Verifies:
        - ``get_coach_reaction`` was called with ``"draw"``
        - ``get_sprite`` was called with ``"coach_aww"``
        - ``get_sprite`` was NOT called with ``"team1_celebrate"`` or
          ``"team2_celebrate"``
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(  # noqa: F841  # used once CelebrationScene exists
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "draw",
        )

        # Coach reaction requested for draw
        self.get_coach_reaction.assert_called_with("draw")

        # Coach aww sprite fetched (not cheer)
        self.asset_manager.get_sprite.assert_any_call("coach_aww")

        # No team celebration sprites should be fetched
        team_calls = [
            c
            for c in self.asset_manager.get_sprite.call_args_list
            if c[0][0] in ("team1_celebrate", "team2_celebrate")
        ]
        self.assertEqual(
            team_calls,
            [],
            "get_sprite should NOT be called with team1_celebrate "
            "or team2_celebrate for a draw result",
        )

    def test_celebration_win_o_shows_team2_sprite(self) -> None:
        """Edge case: result='O' → team2_celebrate sprite + Coach cheer.

        Verifies:
        - ``get_coach_reaction`` was called with ``"win:O"``
        - ``get_sprite`` was called with ``"team2_celebrate"``
        - ``get_sprite`` was NOT called with ``"team1_celebrate"``
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(  # noqa: F841  # used once CelebrationScene exists
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "O",
        )

        # Coach reaction requested for win:O
        self.get_coach_reaction.assert_called_with("win:O")

        # Team 2 celebrate sprite fetched
        self.asset_manager.get_sprite.assert_any_call("team2_celebrate")

        # Team 1 celebrate sprite should NOT be fetched
        team1_calls = [
            c
            for c in self.asset_manager.get_sprite.call_args_list
            if c[0][0] == "team1_celebrate"
        ]
        self.assertEqual(
            team1_calls,
            [],
            "get_sprite should NOT be called with team1_celebrate " "for result='O'",
        )

        # Coach cheer sprite fetched
        self.asset_manager.get_sprite.assert_any_call("coach_cheer")

    # ── 6 continued: event handling ───────────────────────────────────────

    def test_celebration_click_play_again(self) -> None:
        """AC-3: MOUSEBUTTONDOWN on btn_play_again → 'team_select'.

        Verifies:
        - ``handle_event()`` returns ``"team_select"``
        - ``board.reset()`` was called exactly once
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "X",
        )

        # Click at the button centre
        # btn_play_again is 200x60, positioned at:
        #   x = WINDOW_WIDTH//2 - 100 = 380
        #   y = WINDOW_HEIGHT*2//3 - 30 = 450
        # Centre = (480, 480)
        click_x = WINDOW_WIDTH // 2  # 480
        click_y = WINDOW_HEIGHT * 2 // 3  # 480
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (click_x, click_y)},
        )

        result = scene.handle_event(event)

        self.assertEqual(result, "team_select")
        self.board.reset.assert_called_once()

    def test_celebration_click_outside_button(self) -> None:
        """§7 Edge: MOUSEBUTTONDOWN outside button → None (friendly no-op).

        Verifies:
        - ``handle_event()`` returns ``None``
        - ``board.reset()`` was NOT called
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "X",
        )

        # Click far outside the button region: top-left corner (0, 0)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (0, 0)},
        )

        result = scene.handle_event(event)

        self.assertIsNone(result)
        self.board.reset.assert_not_called()

    # ── R key and ESCAPE key ──────────────────────────────────────────────

    def test_celebration_r_key_restarts(self) -> None:
        """AC-4: K_R keydown → 'team_select' + board.reset().

        Verifies:
        - ``handle_event()`` returns ``"team_select"``
        - ``board.reset()`` was called exactly once
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "X",
        )

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r})

        result = scene.handle_event(event)

        self.assertEqual(result, "team_select")
        self.board.reset.assert_called_once()

    def test_celebration_escape_key_restarts(self) -> None:
        """§7 Edge: K_ESCAPE keydown → 'team_select' + board.reset().

        Verifies:
        - ``handle_event()`` returns ``"team_select"``
        - ``board.reset()`` was called exactly once
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "X",
        )

        event = pygame.event.Event(
            pygame.KEYDOWN,
            {"key": pygame.K_ESCAPE},
        )

        result = scene.handle_event(event)

        self.assertEqual(result, "team_select")
        self.board.reset.assert_called_once()

    # ── 3 bonus edge-case tests ───────────────────────────────────────────

    def test_celebration_non_trigger_key(self) -> None:
        """§7 Edge: non-R/ESCAPE key → None (no transition).

        Verifies:
        - ``handle_event()`` returns ``None``
        - ``board.reset()`` was NOT called
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "X",
        )

        event = pygame.event.Event(
            pygame.KEYDOWN,
            {"key": pygame.K_SPACE},
        )

        result = scene.handle_event(event)

        self.assertIsNone(result)
        self.board.reset.assert_not_called()

    def test_celebration_update_returns_none(self) -> None:
        """§4.3: update(dt) returns None (no continuous behaviour).

        Verifies:
        - ``update(16.67)`` returns ``None``
        - ``update(100.0)`` returns ``None``
        - ``update(0.0)`` returns ``None``
        """
        from src.scenes import CelebrationScene  # type: ignore[import-untyped]

        scene = CelebrationScene(
            self.asset_manager,
            self.board,
            self.get_coach_reaction,
            "X",
        )

        # ~60 FPS frame
        self.assertIsNone(scene.update(16.67))
        # Max dt clamp
        self.assertIsNone(scene.update(100.0))
        # Zero dt
        self.assertIsNone(scene.update(0.0))


if __name__ == "__main__":
    unittest.main()
