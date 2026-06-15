"""Pure-Python tic-tac-toe Board logic.

This module contains the Board class, BoardResult enum, and WIN_LINES constant
for a 3x3 tic-tac-toe game. Zero pygame imports (per architecture DR-001).
All game logic is headlessly testable.

Typical usage:
    board = Board()
    board.place(0, 0, "X")  # -> BoardResult.OK
    board.winner()           # -> "X" | "O" | "draw" | None
"""

from enum import Enum


class BoardResult(Enum):
    """Result of a board placement operation."""

    OK = "ok"
    OCCUPIED = "occupied"
    INVALID = "invalid"


WIN_LINES: list[list[tuple[int, int]]] = [
    # Rows (3)
    [(0, 0), (0, 1), (0, 2)],  # top row
    [(1, 0), (1, 1), (1, 2)],  # middle row
    [(2, 0), (2, 1), (2, 2)],  # bottom row
    # Columns (3)
    [(0, 0), (1, 0), (2, 0)],  # left column
    [(0, 1), (1, 1), (2, 1)],  # middle column
    [(0, 2), (1, 2), (2, 2)],  # right column
    # Diagonals (2)
    [(0, 0), (1, 1), (2, 2)],  # main diagonal (top-left to bottom-right)
    [(0, 2), (1, 1), (2, 0)],  # anti-diagonal (top-right to bottom-left)
]


class Board:
    """A 3x3 tic-tac-toe board with pure-Python game logic.

    Manages cell state, turn alternation, win/draw detection, and reset.
    All game rules are enforced through return values, not exceptions.
    """

    def __init__(self) -> None:
        """Initialize an empty board with player X to move."""
        self._cells: list[list[str | None]] = [
            [None, None, None],
            [None, None, None],
            [None, None, None],
        ]
        self._current_player: str = "X"
        self._move_count: int = 0
        self._winning_cells: list[tuple[int, int]] = []

    @property
    def cells(self) -> list[list[str | None]]:
        """Read-only access to the 3x3 cell grid."""
        return self._cells

    @property
    def current_player(self) -> str:
        """Read-only access to the current player mark ("X" or "O")."""
        return self._current_player

    def place(self, row: int, col: int, mark: str) -> BoardResult:
        """Place a mark on the board.

        Validates bounds, mark match, and cell availability before placing.
        After a successful placement, the current player toggles and the
        winner is re-evaluated.

        Args:
            row: Row index (0-2).
            col: Column index (0-2).
            mark: The player's mark ("X" or "O"). Must match current_player.

        Returns:
            BoardResult.OK if placed successfully.
            BoardResult.INVALID if row/col out of bounds or mark doesn't match.
            BoardResult.OCCUPIED if the cell is already taken.
        """
        # Step 1: Validate bounds.
        if row not in range(0, 3) or col not in range(0, 3):
            return BoardResult.INVALID

        # Step 2: Validate the mark matches the current player.
        if mark != self._current_player:
            return BoardResult.INVALID

        # Step 3: Validate occupancy.
        if self._cells[row][col] is not None:
            return BoardResult.OCCUPIED

        # Step 4: Place the mark.
        self._cells[row][col] = mark
        self._move_count += 1

        # Step 5: Toggle current player.
        if self._current_player == "X":
            self._current_player = "O"
        else:
            self._current_player = "X"

        # Step 6: Re-evaluate winner and cache winning cells.
        self.winner()

        # Step 7: Return OK.
        return BoardResult.OK

    def winner(self) -> str | None:
        """Determine the game winner or draw state.

        Checks all 8 win lines. If a line has three of the same non-None mark,
        the winner is that mark. If the board is full with no winner, returns
        "draw". Otherwise returns None for an in-progress game.

        Returns:
            "X" or "O" if that player has three in a row.
            "draw" if the board is full with no winner.
            None if the game is still in progress.

        Note:
            This method also updates the internal ``_winning_cells`` cache as a
            side effect, clearing it when there is no winner and setting it to
            the winning line's coordinates when a winner is detected.
        """
        # Step 1: Check each win line in WIN_LINES.
        for line in WIN_LINES:
            (r1, c1), (r2, c2), (r3, c3) = line
            m1 = self._cells[r1][c1]
            m2 = self._cells[r2][c2]
            m3 = self._cells[r3][c3]

            if m1 is not None and m1 == m2 and m2 == m3:
                # All three same non-None mark -> winner found
                self._winning_cells = [(r1, c1), (r2, c2), (r3, c3)]
                return m1  # returns "X" or "O"

        # Step 2: No winner found — check for draw.
        if self._move_count == 9:
            self._winning_cells = []
            return "draw"

        # Step 3: Game still in progress.
        self._winning_cells = []
        return None

    def is_full(self) -> bool:
        """Check if the board is completely filled.

        Returns:
            True if all 9 cells are occupied, False otherwise.
        """
        return self._move_count == 9

    def winning_cells(self) -> list[tuple[int, int]]:
        """Get the coordinates of the winning line.

        Returns a shallow copy to prevent external mutation of internal state.

        Returns:
            List of three (row, col) tuples for the winning line, or
            an empty list if there is no winner.
        """
        return self._winning_cells.copy()

    def reset(self) -> None:
        """Reset the board to its initial empty state.

        Clears all cells, resets the current player to "X", and clears
        the move counter and winning cells cache.
        """
        self._cells = [
            [None, None, None],
            [None, None, None],
            [None, None, None],
        ]
        self._current_player = "X"
        self._move_count = 0
        self._winning_cells = []
