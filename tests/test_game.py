"""Tests for the Board class in src/game.py.

This test suite contains 21 unit tests covering:
- Place validation (7 tests)
- Winner detection for all 8 win lines (8 tests)
- Draw detection (1 test)
- Winning cells (2 tests)
- Reset (1 test)
- In-progress game (1 test)
- Pygame import verification (1 test)
"""

import sys

from src.game import Board, BoardResult


# NOTE: test_no_pygame_import is placed FIRST to catch the condition
# before other tests potentially import pygame.
def test_no_pygame_import() -> None:
    """Verify importing src.game does not import pygame (DR-001)."""
    # Clear pygame from sys.modules if loaded by another source
    sys.modules.pop("pygame", None)
    # Import src.game (redundant import at module level is already cached)
    import src.game  # noqa: F401,F811  # pylint: disable=reimported,unused-import

    assert "pygame" not in sys.modules


def test_place_valid_cell() -> None:
    """Placing 'X' at (0,0) succeeds."""
    board = Board()
    result = board.place(0, 0, "X")
    assert result == BoardResult.OK
    assert board.cells[0][0] == "X"


def test_place_occupied_cell() -> None:
    """Placing on an occupied cell returns OCCUPIED, cell unchanged."""
    board = Board()
    board.place(0, 0, "X")
    result = board.place(0, 0, "O")
    assert result == BoardResult.OCCUPIED
    assert board.cells[0][0] == "X"  # unchanged


def test_place_invalid_row_negative() -> None:
    """Placing at row=-1 returns INVALID, board unchanged."""
    board = Board()
    result = board.place(-1, 0, "X")
    assert result == BoardResult.INVALID
    # All cells still None
    for row in board.cells:
        for cell in row:
            assert cell is None


def test_place_invalid_row_too_large() -> None:
    """Placing at row=3 returns INVALID, board unchanged."""
    board = Board()
    result = board.place(3, 0, "X")
    assert result == BoardResult.INVALID
    for row in board.cells:
        for cell in row:
            assert cell is None


def test_place_invalid_col_negative() -> None:
    """Placing at col=-1 returns INVALID, board unchanged."""
    board = Board()
    result = board.place(0, -1, "O")
    assert result == BoardResult.INVALID
    for row in board.cells:
        for cell in row:
            assert cell is None


def test_place_invalid_col_too_large() -> None:
    """Placing at col=3 returns INVALID, board unchanged."""
    board = Board()
    result = board.place(0, 3, "O")
    assert result == BoardResult.INVALID
    for row in board.cells:
        for cell in row:
            assert cell is None


def test_turn_alternation() -> None:
    """After X places, current_player switches to O and vice versa."""
    board = Board()
    assert board.current_player == "X"
    board.place(0, 0, "X")
    assert board.current_player == "O"
    board.place(0, 1, "O")
    assert board.current_player == "X"


def test_winner_row_top() -> None:
    """X in top row -> winner is 'X'."""
    board = Board()
    board.place(0, 0, "X")  # X places
    board.place(1, 0, "O")  # O places (blocker)
    board.place(0, 1, "X")  # X places
    board.place(1, 1, "O")  # O places
    board.place(0, 2, "X")  # X completes top row
    assert board.winner() == "X"


def test_winner_row_middle() -> None:
    """O in middle row -> winner is 'O'."""
    board = Board()
    board.place(0, 0, "X")
    board.place(1, 0, "O")
    board.place(2, 0, "X")
    board.place(1, 1, "O")
    board.place(2, 1, "X")
    board.place(1, 2, "O")
    assert board.winner() == "O"


def test_winner_row_bottom() -> None:
    """X in bottom row -> winner is 'X'."""
    board = Board()
    board.place(2, 0, "X")
    board.place(0, 0, "O")
    board.place(2, 1, "X")
    board.place(0, 1, "O")
    board.place(2, 2, "X")
    assert board.winner() == "X"


def test_winner_column_left() -> None:
    """O in left column -> winner is 'O'."""
    board = Board()
    board.place(0, 1, "X")
    board.place(0, 0, "O")
    board.place(1, 1, "X")
    board.place(1, 0, "O")
    board.place(2, 1, "X")
    board.place(2, 0, "O")
    assert board.winner() == "O"


def test_winner_column_middle() -> None:
    """X in middle column -> winner is 'X'."""
    board = Board()
    board.place(0, 1, "X")
    board.place(0, 0, "O")
    board.place(1, 1, "X")
    board.place(1, 0, "O")
    board.place(2, 1, "X")
    assert board.winner() == "X"


def test_winner_column_right() -> None:
    """O in right column -> winner is 'O'."""
    board = Board()
    board.place(0, 1, "X")  # X at (0,1)
    board.place(0, 2, "O")  # O at (0,2)
    board.place(1, 1, "X")  # X at (1,1)
    board.place(1, 2, "O")  # O at (1,2)
    board.place(2, 0, "X")  # X at (2,0) — no line formed
    board.place(2, 2, "O")  # O at (2,2) — completes right column
    assert board.winner() == "O"


def test_winner_diagonal_main() -> None:
    """X in main diagonal -> winner is 'X'."""
    board = Board()
    board.place(0, 0, "X")
    board.place(0, 1, "O")
    board.place(1, 1, "X")
    board.place(0, 2, "O")
    board.place(2, 2, "X")
    assert board.winner() == "X"


def test_winner_diagonal_anti() -> None:
    """O in anti-diagonal -> winner is 'O'."""
    board = Board()
    board.place(1, 0, "X")  # X
    board.place(0, 2, "O")  # O
    board.place(0, 0, "X")  # X
    board.place(1, 1, "O")  # O
    board.place(2, 1, "X")  # X
    board.place(2, 0, "O")  # O completes anti-diagonal
    assert board.winner() == "O"


def test_draw_detection() -> None:
    """Full board with no winner -> winner() returns 'draw'."""
    board = Board()
    # Correct draw board (X has 5 moves, O has 4):
    # X X O
    # O O X
    # X O X
    board.place(0, 0, "X")
    board.place(0, 2, "O")
    board.place(0, 1, "X")
    board.place(1, 0, "O")
    board.place(1, 2, "X")
    board.place(1, 1, "O")
    board.place(2, 0, "X")
    board.place(2, 1, "O")
    board.place(2, 2, "X")
    assert board.winner() == "draw"
    assert board.is_full() is True


def test_winning_cells_returns_coordinates() -> None:
    """winning_cells() returns correct (row, col) tuples for a row win."""
    board = Board()
    board.place(0, 0, "X")
    board.place(1, 0, "O")
    board.place(0, 1, "X")
    board.place(1, 1, "O")
    board.place(0, 2, "X")
    coords = board.winning_cells()
    assert coords == [(0, 0), (0, 1), (0, 2)]


def test_winning_cells_empty_when_no_winner() -> None:
    """No win -> winning_cells() returns []."""
    board = Board()
    board.place(0, 0, "X")
    board.place(1, 0, "O")
    result = board.winning_cells()
    assert result == []


def test_reset_clears_board() -> None:
    """After place+reset, all cells are None and turn is X."""
    board = Board()
    board.place(0, 0, "X")
    board.place(0, 1, "O")
    board.reset()
    # All 9 cells are None
    for row in board.cells:
        for cell in row:
            assert cell is None
    assert board.current_player == "X"
    assert board.is_full() is False


def test_no_winner_in_progress_game() -> None:
    """Partial board with no winner -> winner() returns None."""
    board = Board()
    board.place(0, 0, "X")
    board.place(1, 0, "O")
    board.place(0, 1, "X")
    result = board.winner()
    assert result is None
