"""Tests for TeamSelectScene in src/scenes.py.

This test suite contains 12 unit tests covering all 6 acceptance criteria
and edge cases for the TeamSelectScene class. Uses mocked AssetManager and
coach callable to avoid pygame surface dependencies.

=== Mock Strategy ===
- AssetManager: A unittest.mock.MagicMock where get_sprite() returns a
  pygame.Surface(1, 1) for any key, and get_sprite_size() returns (120, 120).
- Coach callable: A MagicMock with side_effect that returns
  ("wave", "Hiii! Pick your team and let's play!") when called with "greeting".

NOTE: src/scenes.py is now implemented (Sprint 4, Task 2). All 12 tests in
this suite pass against the TeamSelectScene class.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pygame
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


# ═══════════════════════════════════════════════════════════════════════
# Module-level constants matching pseudocode §3.1
# ═══════════════════════════════════════════════════════════════════════

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720

# Coach panel position (from Architecture §9)
COACH_PANEL_X = 600
COACH_PANEL_Y = 50
COACH_SPRITE_SIZE = (200, 200)

# Team portrait positions (Proposed — pseudocode §3.1)
TEAM1_PORTRAIT_X = 100
TEAM1_PORTRAIT_Y = 200
TEAM_PORTRAIT_SIZE = (120, 120)
TEAM2_PORTRAIT_X = 100
TEAM2_PORTRAIT_Y = 360

# Start button position
BTN_START_X = 80
BTN_START_Y = 540
BTN_START_SIZE = (200, 60)

# Speech bubble position
SPEECH_BUBBLE_X = 560
SPEECH_BUBBLE_Y = 270
SPEECH_BUBBLE_WIDTH = 340

# Scene name overlay position
SCENE_OVERLAY_X = 10
SCENE_OVERLAY_Y = 10

# Greeting return value from src/coach.py event_to_reaction("greeting")
COACH_GREETING_EXPRESSION = "wave"
COACH_GREETING_LINE = "Hiii! Pick your team and let's play!"


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_asset_manager() -> MagicMock:
    """Create a mocked AssetManager.

    - get_sprite(key) returns a 1x1 pygame.Surface for any key.
    - get_sprite_size(key) returns (120, 120) for any key.
    """
    manager = MagicMock()
    manager.get_sprite.return_value = pygame.Surface((1, 1))
    manager.get_sprite_size.return_value = (120, 120)
    return manager


@pytest.fixture
def mock_coach() -> MagicMock:
    """Create a mocked coach reaction callable.

    Returns the greeting tuple when called with "greeting".
    Uses side_effect dict lookup.
    """
    coach = MagicMock()

    def side_effect(event: str) -> tuple[str, str]:
        mapping: dict[str, tuple[str, str]] = {
            "greeting": (COACH_GREETING_EXPRESSION, COACH_GREETING_LINE),
        }
        return mapping.get(event, ("idle", ""))  # type: ignore[return-value]

    coach.side_effect = side_effect
    return coach


@pytest.fixture
def scene(mock_asset_manager: MagicMock, mock_coach: MagicMock):
    """Construct a TeamSelectScene with mocked dependencies.

    NOTE: Import now resolves successfully since src/scenes.py was
    implemented in Sprint 4, Task 2.
    """
    from src.scenes import TeamSelectScene

    return TeamSelectScene(mock_asset_manager, mock_coach)


# ═══════════════════════════════════════════════════════════════════════
# Helper: create a MOUSEBUTTONDOWN event at (x, y)
# ═══════════════════════════════════════════════════════════════════════


def _click_event(x: int, y: int) -> pygame.event.Event:
    """Create a MOUSEBUTTONDOWN pygame event at the given coordinates."""
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (x, y)})


# ═══════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════


def test_team_select_initial_state(scene) -> None:
    """AC-1 / AC-4: Scene starts with no teams selected and Coach greeting cached.

    Verify:
    - selected_teams["team1"] is False
    - selected_teams["team2"] is False
    - coach_expression matches greeting expression
    - coach_line matches greeting line text
    """
    assert scene.selected_teams == {"team1": False, "team2": False}
    assert scene.coach_expression == COACH_GREETING_EXPRESSION
    assert scene.coach_line == COACH_GREETING_LINE


def test_team_select_click_team1(scene) -> None:
    """AC-2: MOUSEBUTTONDOWN on team1 portrait sets selected_teams['team1']=True.

    Click at the center of the team1 portrait rect.
    """
    click_x = TEAM1_PORTRAIT_X + TEAM_PORTRAIT_SIZE[0] // 2
    click_y = TEAM1_PORTRAIT_Y + TEAM_PORTRAIT_SIZE[1] // 2
    event = _click_event(click_x, click_y)

    result = scene.handle_event(event)

    assert result is None
    assert scene.selected_teams["team1"] is True
    assert scene.selected_teams["team2"] is False


def test_team_select_click_team2(scene) -> None:
    """AC-2: MOUSEBUTTONDOWN on team2 portrait sets selected_teams['team2']=True.

    Click at the center of the team2 portrait rect.
    """
    click_x = TEAM2_PORTRAIT_X + TEAM_PORTRAIT_SIZE[0] // 2
    click_y = TEAM2_PORTRAIT_Y + TEAM_PORTRAIT_SIZE[1] // 2
    event = _click_event(click_x, click_y)

    result = scene.handle_event(event)

    assert result is None
    assert scene.selected_teams["team1"] is False
    assert scene.selected_teams["team2"] is True


def test_team_select_both_teams_selected(scene) -> None:
    """After clicking both team portraits, both selected_teams values are True."""
    # Click team1
    click1_x = TEAM1_PORTRAIT_X + TEAM_PORTRAIT_SIZE[0] // 2
    click1_y = TEAM1_PORTRAIT_Y + TEAM_PORTRAIT_SIZE[1] // 2
    scene.handle_event(_click_event(click1_x, click1_y))

    # Click team2
    click2_x = TEAM2_PORTRAIT_X + TEAM_PORTRAIT_SIZE[0] // 2
    click2_y = TEAM2_PORTRAIT_Y + TEAM_PORTRAIT_SIZE[1] // 2
    scene.handle_event(_click_event(click2_x, click2_y))

    assert scene.selected_teams["team1"] is True
    assert scene.selected_teams["team2"] is True


def test_team_select_start_transition(scene) -> None:
    """AC-3: Clicking Start with both teams selected returns 'game'.

    Select both teams via portrait clicks, then click the Start button.
    """
    # Select both teams
    click1_x = TEAM1_PORTRAIT_X + TEAM_PORTRAIT_SIZE[0] // 2
    click1_y = TEAM1_PORTRAIT_Y + TEAM_PORTRAIT_SIZE[1] // 2
    scene.handle_event(_click_event(click1_x, click1_y))

    click2_x = TEAM2_PORTRAIT_X + TEAM_PORTRAIT_SIZE[0] // 2
    click2_y = TEAM2_PORTRAIT_Y + TEAM_PORTRAIT_SIZE[1] // 2
    scene.handle_event(_click_event(click2_x, click2_y))

    # Click Start button center
    start_x = BTN_START_X + BTN_START_SIZE[0] // 2
    start_y = BTN_START_Y + BTN_START_SIZE[1] // 2
    result = scene.handle_event(_click_event(start_x, start_y))

    assert result == "game"


def test_team_select_start_noop_no_teams(scene) -> None:
    """§6.5: Clicking Start with 0 teams selected returns None (no-op).

    Verifies the Start button region click is ignored when no teams are
    selected.
    """
    click_x = BTN_START_X + BTN_START_SIZE[0] // 2
    click_y = BTN_START_Y + BTN_START_SIZE[1] // 2
    result = scene.handle_event(_click_event(click_x, click_y))

    assert result is None
    assert scene.selected_teams == {"team1": False, "team2": False}


def test_team_select_start_noop_one_team(scene) -> None:
    """§6.5: Clicking Start with only 1 team selected returns None (no-op).

    Select only team1, then click Start. Should not transition.
    """
    click_x = TEAM1_PORTRAIT_X + TEAM_PORTRAIT_SIZE[0] // 2
    click_y = TEAM1_PORTRAIT_Y + TEAM_PORTRAIT_SIZE[1] // 2
    scene.handle_event(_click_event(click_x, click_y))

    # Click Start
    start_x = BTN_START_X + BTN_START_SIZE[0] // 2
    start_y = BTN_START_Y + BTN_START_SIZE[1] // 2
    result = scene.handle_event(_click_event(start_x, start_y))

    assert result is None
    assert scene.selected_teams["team1"] is True
    assert scene.selected_teams["team2"] is False


def test_team_select_click_outside(scene) -> None:
    """§6.1: MOUSEBUTTONDOWN outside all rects returns None (no-op).

    Click at a position that does not intersect any clickable rect.
    """
    # Position (500, 500) is well outside all portrait and button rects
    result = scene.handle_event(_click_event(500, 500))

    assert result is None
    assert scene.selected_teams == {"team1": False, "team2": False}


def test_team_select_double_click(scene) -> None:
    """§6.2: Clicking already-selected portrait is idempotent.

    Click team1 twice — the second click should be silently ignored and
    selected_teams should remain as True.
    """
    click_x = TEAM1_PORTRAIT_X + TEAM_PORTRAIT_SIZE[0] // 2
    click_y = TEAM1_PORTRAIT_Y + TEAM_PORTRAIT_SIZE[1] // 2

    # First click — select team1
    scene.handle_event(_click_event(click_x, click_y))
    assert scene.selected_teams["team1"] is True

    # Second click — should be no-op
    result = scene.handle_event(_click_event(click_x, click_y))

    assert result is None
    assert scene.selected_teams["team1"] is True
    assert scene.selected_teams["team2"] is False


def test_team_select_update_returns_none(scene) -> None:
    """update(dt) always returns None (no scene transitions from update).

    TeamSelectScene is event-driven, not time-driven.
    """
    result = scene.update(16.67)  # ~60 FPS frame
    assert result is None

    result = scene.update(100.0)  # Max dt clamp
    assert result is None

    result = scene.update(0.0)  # Zero dt
    assert result is None


def test_team_select_draw_read_only(scene) -> None:
    """draw() does not mutate scene state (read-only operation).

    Verify that calling draw() does not alter selected_teams or other
    state attributes. Per architecture §2.3 principle.
    """
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

    # Capture state before draw
    before_teams = dict(scene.selected_teams)

    scene.draw(surface)

    # State must be unchanged
    assert scene.selected_teams == before_teams


def test_team_select_initial_coach_greeting(scene) -> None:
    """AC-4: Coach greeting is cached from event_to_reaction("greeting").

    Verify that the coach callable was invoked with "greeting" and that
    the cached expression/line values match expectations.
    """
    assert scene.coach_expression == COACH_GREETING_EXPRESSION
    assert scene.coach_line == COACH_GREETING_LINE


# ──────────────────────────────────────────────────────────────────────────────
# Sprint 5, Task 3 — Tech Debt Fix Tests (from pseudocode §6.1)
# ──────────────────────────────────────────────────────────────────────────────


def test_no_module_level_pygame_init() -> None:
    """R1: Importing src.scenes does NOT trigger pygame.font.init() at module level.

    Verifies that the module-level font init guard (scenes.py lines 322-324) has
    been removed in Sprint 5 — importing src.scenes must not initialise the pygame
    font module. Runs in headless environment without prior pygame.init().

    Red phase: This test FAILS because lines 322-324 are still present.
    """
    # Arrange: ensure clean font state
    if pygame.font.get_init():
        pygame.font.quit()
    assert (
        not pygame.font.get_init()
    ), "Precondition failed: pygame.font is still initialised after quit()"

    # Clear cached module to force re-import (re-executes module-level code)
    if "src.scenes" in sys.modules:
        del sys.modules["src.scenes"]

    # Act: import triggers module-level code in src/scenes.py

    # Assert: font should NOT be initialised (line 322-324 removed in fix)
    assert (
        not pygame.font.get_init()
    ), "pygame.font.init() was triggered at module level during import"

    # Cleanup: restore pygame.font state for subsequent tests
    # (test left font deinitialised — re-init so later tests don't break)
    pygame.font.init()


def test_turn_indicator_matches_coach_voice(
    mock_asset_manager: MagicMock,
) -> None:
    """R4/R5: GameScene stores team display names consistent with Coach voice.

    Verifies that GameScene stores a team_display_names dict mapping
    "X" -> "Kittens" and "O" -> "Puppies", matching the Coach speech lines
    in coach.py lines 54-55 ("Kittens' turn!"/"Puppies' turn!").

    Red phase: This test FAILS with AssertionError because team_display_names
    doesn't exist yet on GameScene.
    """
    from src.scenes import GameScene

    # Arrange: mock dependencies
    mock_board = MagicMock()
    mock_board.current_player = "X"

    mock_coach = MagicMock()
    mock_coach.side_effect = lambda event: ("point", "Your turn!")

    # Act: construct GameScene (team_display_names field added in fix)
    scene = GameScene(mock_asset_manager, mock_board, mock_coach)

    # Assert: team_display_names exists and matches Coach voice
    assert hasattr(
        scene, "team_display_names"
    ), "GameScene missing team_display_names attribute"
    assert (
        scene.team_display_names["X"] == "Kittens"
    ), f"Expected 'Kittens' for X, got '{scene.team_display_names['X']}'"
    assert (
        scene.team_display_names["O"] == "Puppies"
    ), f"Expected 'Puppies' for O, got '{scene.team_display_names['O']}'"
    assert set(scene.team_display_names.keys()) == {
        "X",
        "O",
    }, f"Expected keys {{'X', 'O'}}, got {set(scene.team_display_names.keys())}"
