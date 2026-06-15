"""Unit tests for the GameScene class (src/scenes.py).

Tests cover all 8 acceptance criteria from Sprint 4 Task 3, organized into
10 unit tests matching the testing boundary defined in §11 of the pseudocode
document. All tests use a mocked AssetManager returning real pygame.Surfaces,
real Board instances, and the real event_to_reaction function.

NOTE: These tests will fail at import time with ImportError/ModuleNotFoundError
because GameScene has not been implemented yet (src/scenes.py does not exist).
This is the expected TDD red-phase outcome — the tests validate the API contract
that GameScene must satisfy once implemented.

Usage:
    poetry run pytest tests/test_game_scene.py -v
"""

from __future__ import annotations

import pygame
import pytest

# ---------------------------------------------------------------------------
# Constants matching GameScene / src/sprite_config.py
# ---------------------------------------------------------------------------
BOARD_ORIGIN_X = 180
BOARD_ORIGIN_Y = 160
CELL_SIZE = 120
COACH_PANEL_X = 600
COACH_PANEL_Y = 50


def _cell_center(row: int, col: int) -> tuple[int, int]:
    """Compute the pixel center of a board cell for mouse-click events."""
    x = BOARD_ORIGIN_X + col * CELL_SIZE + CELL_SIZE // 2
    y = BOARD_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
    return (x, y)


# ---------------------------------------------------------------------------
# Mock AssetManager  —  returns real pygame.Surfaces of correct dimensions
# ---------------------------------------------------------------------------
_SPRITE_DIMENSIONS: dict[str, tuple[int, int]] = {
    "bg_game": (960, 720),
    "board_frame": (440, 440),
    "team1_cell": (120, 120),
    "team2_cell": (120, 120),
    "coach_wave": (200, 200),
    "coach_point": (200, 200),
    "coach_cheer_small": (200, 200),
    "coach_cheer": (200, 200),
    "coach_aww": (200, 200),
    "coach_idle": (200, 200),
}


class _MockAssetManager:
    """Returns real pygame.Surfaces with correct dimensions per sprite key."""

    def __init__(self) -> None:
        self._surfaces: dict[str, pygame.Surface] = {}
        for key, (w, h) in _SPRITE_DIMENSIONS.items():
            self._surfaces[key] = pygame.Surface((w, h))

    def get_sprite(self, key: str) -> pygame.Surface:
        """Get a sprite surface by key."""
        if key not in self._surfaces:
            raise KeyError(f"Unknown asset key: '{key}'")
        return self._surfaces[key]

    def get_sprite_size(self, key: str) -> tuple[int, int]:
        """Get sprite dimensions by key."""
        if key not in _SPRITE_DIMENSIONS:
            raise KeyError(f"Unknown asset key: '{key}'")
        return _SPRITE_DIMENSIONS[key]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_asset_manager() -> _MockAssetManager:
    """Fixture returning a mock AssetManager with real Surfaces."""
    return _MockAssetManager()


@pytest.fixture
def board():
    """Fixture returning a fresh real Board instance."""
    from src.game import Board

    return Board()


@pytest.fixture
def get_coach_reaction():
    """Fixture returning the real event_to_reaction callable."""
    from src.coach import event_to_reaction

    return event_to_reaction


@pytest.fixture
def draw_surface() -> pygame.Surface:
    """Fixture returning a 960x720 draw surface (window-sized)."""
    return pygame.Surface((960, 720))


@pytest.fixture
def scene(mock_asset_manager, board, get_coach_reaction):
    """Fixture constructing a GameScene with injected dependencies.

    Note: Will raise ImportError until GameScene is implemented (red phase).
    """
    from src.scenes import GameScene

    return GameScene(mock_asset_manager, board, get_coach_reaction)


# ===================================================================
# Tests
# ===================================================================


def test_game_scene_selector_start_position(scene) -> None:
    """Keyboard selector starts at (0, 0)."""
    assert scene.keyboard_selector == (0, 0)


def test_game_scene_initial_state(scene, board) -> None:
    """Scene constructs with empty board, current_player 'X', turn call."""
    # Board starts empty with X to move
    assert board.current_player == "X"
    for row in range(3):
        for col in range(3):
            assert board.cells[row][col] is None

    # Coach reaction should be the turn call for the starting player ("X")
    expression, line = scene.coach_reaction
    assert expression == "point"
    assert "turn" in line.lower() or "Kittens" in line


def test_game_scene_mouse_click_places_mark(scene, board, draw_surface) -> None:
    """MOUSEBUTTONDOWN on empty cell places mark via board.place()."""
    pos = _cell_center(0, 0)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    result = scene.handle_event(event)

    # Mark should be placed — board cell (0,0) now occupied by "X"
    assert board.cells[0][0] == "X"
    # Result is None because the game continues (no win/draw yet)
    assert result is None


def test_game_scene_occupied_cell_noop(scene, board) -> None:
    """Clicking occupied cell no-ops; board unchanged, no exception."""
    # Pre-place a mark at (0, 0)
    board.place(0, 0, "X")  # places X, toggles to O

    # Capture current coach reaction
    original_reaction = scene.coach_reaction

    # Click the same cell (now occupied)
    pos = _cell_center(0, 0)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    result = scene.handle_event(event)

    # Board state unchanged — cell (0,0) still "X", only 1 move
    assert board.cells[0][0] == "X"
    # Other cells remain empty
    assert board.cells[0][1] is None
    assert board.cells[1][0] is None
    # Coach reaction should be unchanged
    assert scene.coach_reaction == original_reaction
    # No scene transition
    assert result is None


def test_game_scene_keyboard_movement(scene) -> None:
    """Arrow keys move keyboard_selector; clamped at grid edges."""
    # Start at (0, 0)
    assert scene.keyboard_selector == (0, 0)

    # Press DOWN -> should move to (1, 0)
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}))
    assert scene.keyboard_selector == (1, 0), "K_DOWN should move to row 1"

    # Press RIGHT -> should move to (1, 1)
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
    assert scene.keyboard_selector == (1, 1), "K_RIGHT should move to col 1"

    # Press UP twice: (1,1) -> (0,1) -> stays at (0,1)
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP}))
    assert scene.keyboard_selector == (0, 1), "K_UP should move to row 0"
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP}))
    assert scene.keyboard_selector == (0, 1), "K_UP at row 0 should clamp to 0"

    # Press RIGHT twice from (0,1): (0,1) -> (0,2) -> stays at (0,2)
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
    assert scene.keyboard_selector == (0, 2), "K_RIGHT should move to col 2"
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
    assert scene.keyboard_selector == (0, 2), "K_RIGHT at col 2 should clamp to 2"

    # Press LEFT three times: (0,2) -> (0,1) -> (0,0) -> (0,0)
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT}))
    assert scene.keyboard_selector == (0, 1), "K_LEFT should move to col 1"
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT}))
    assert scene.keyboard_selector == (0, 0), "K_LEFT should move to col 0"
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT}))
    assert scene.keyboard_selector == (0, 0), "K_LEFT at col 0 should clamp to 0"

    # Press DOWN: (0,0) -> (1,0) — K_UP at row 0 clamping already confirmed above
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}))
    assert scene.keyboard_selector == (1, 0), "K_DOWN should move to row 1"


def test_game_scene_keyboard_placement(scene, board) -> None:
    """K_RETURN at empty cell places mark; K_SPACE also places mark."""
    # Selector starts at (0, 0). Press RETURN -> places "X" at (0, 0).
    result = scene.handle_event(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}),
    )
    assert board.cells[0][0] == "X"
    assert result is None  # game continues

    # Current player is now "O". Move selector to (0, 1) and press SPACE.
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
    result = scene.handle_event(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}),
    )
    assert board.cells[0][1] == "O"
    assert result is None


def test_game_scene_transition_on_win(scene, board) -> None:
    """Pre-place marks for win, final click returns 'celebration' + coach cheer."""
    # Pre-place 4 marks to set up a top-row win for X:
    # X at (0,0), O at (1,0), X at (0,1), O at (1,1)
    # Now it's X's turn. Clicking (0,2) completes the top row.
    board.place(0, 0, "X")  # OK, O's turn
    board.place(1, 0, "O")  # OK, X's turn
    board.place(0, 1, "X")  # OK, O's turn
    board.place(1, 1, "O")  # OK, X's turn

    # Dispatch click on (0, 2) which should place X and win
    pos = _cell_center(0, 2)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    result = scene.handle_event(event)

    # Verify win
    assert board.cells[0][2] == "X"
    assert board.winner() == "X"
    assert result == "celebration"

    # Coach should show cheer reaction
    expression, line = scene.coach_reaction
    assert expression == "cheer", f"Expected 'cheer', got '{expression}'"
    win_keywords = ["win", "wins", "victory", "hooray", "yay"]
    assert any(kw in line.lower() for kw in win_keywords)


def test_game_scene_transition_on_draw(scene, board) -> None:
    """Fill 8 cells no-winner, 9th cell -> 'celebration' + coach aww."""
    # Set up a draw board (no winner after 8 placements):
    # X O X
    # O O X
    # X X O  (last cell (2,1) is X's 5th move, making draw)
    board.place(0, 0, "X")  # 1
    board.place(0, 1, "O")  # 2
    board.place(0, 2, "X")  # 3
    board.place(1, 0, "O")  # 4
    board.place(1, 2, "X")  # 5
    board.place(1, 1, "O")  # 6
    board.place(2, 0, "X")  # 7
    board.place(2, 2, "O")  # 8

    # Verify no winner yet and it's X's turn
    assert board.winner() is None
    assert board.current_player == "X"

    # Dispatch click on (2, 1) — the 9th cell
    pos = _cell_center(2, 1)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    result = scene.handle_event(event)

    # Verify draw
    assert board.winner() == "draw"
    assert result == "celebration"

    # Coach should show aww reaction
    expression, line = scene.coach_reaction
    assert expression == "aww", f"Expected 'aww', got '{expression}'"
    assert "tie" in line.lower() or "draw" in line.lower()


def test_game_scene_coach_update_on_placement(scene, board) -> None:
    """After OK placement with no winner, coach_reaction shows next turn call."""
    pos = _cell_center(1, 1)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    scene.handle_event(event)

    expression, line = scene.coach_reaction
    assert expression == "point", (
        f"Expected 'point' (next turn call), got '{expression}'"
    )
    # After X places, it's O's turn → ("point", "Puppies' turn! You've got this!")
    assert "puppies" in line.lower() or "turn" in line.lower()


def test_game_scene_turn_indicator(scene, board, draw_surface) -> None:
    """draw() renders without error; turn toggles after placement."""
    # draw() should not raise
    scene.draw(draw_surface)

    # Verify initial turn
    assert board.current_player == "X"

    # Place a move and verify turn switches
    pos = _cell_center(0, 0)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    scene.handle_event(event)

    # Current player should now be O (Team 2)
    assert board.current_player == "O"

    # draw() should render without error after the state change
    scene.draw(draw_surface)
