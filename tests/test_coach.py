"""Tests for the Coach reaction mapping module in src/coach.py.

This test suite contains 13 unit tests covering:
- No-pygame import verification (DR-001)
- All 8 event-to-reaction mappings (8 tests)
- Determinism verification (1 test)
- Unknown event error handling (1 test)
- Expression known-set validation (1 test)
- Speech line non-empty validation (1 test)
"""

import sys

import pytest


# NOTE: test_coach_no_pygame_import is placed FIRST to catch the condition
# before other tests potentially import pygame.
def test_coach_no_pygame_import() -> None:
    """Verify importing src.coach does not import pygame (DR-001)."""
    # Clear pygame from sys.modules if loaded by another source
    sys.modules.pop("pygame", None)
    # Import src.coach at function level
    import src.coach  # noqa: F401,F811  # pylint: disable=reimported,unused-import

    assert "pygame" not in sys.modules


def test_coach_greeting_maps_to_wave() -> None:
    """Event 'greeting' maps to ('wave', 'Hiii! Pick your team and let's play!')."""
    from src.coach import event_to_reaction

    result = event_to_reaction("greeting")
    assert result == ("wave", "Hiii! Pick your team and let's play!")


def test_coach_turn_x_maps_to_point() -> None:
    """Event 'turn:X' maps to ('point', "Kittens' turn! Where will you go?")."""
    from src.coach import event_to_reaction

    result = event_to_reaction("turn:X")
    assert result == ("point", "Kittens' turn! Where will you go?")


def test_coach_turn_o_maps_to_point() -> None:
    """Event 'turn:O' maps to ('point', "Puppies' turn! You've got this!")."""
    from src.coach import event_to_reaction

    result = event_to_reaction("turn:O")
    assert result == ("point", "Puppies' turn! You've got this!")


def test_coach_move_placed_maps_to_cheer_small() -> None:
    """Event 'move_placed' maps to ('cheer_small', 'Ooh, nice spot!')."""
    from src.coach import event_to_reaction

    result = event_to_reaction("move_placed")
    assert result == ("cheer_small", "Ooh, nice spot!")


def test_coach_win_x_maps_to_cheer() -> None:
    """Event 'win:X' maps to ('cheer', 'Kittens win! Hooray! \U0001f389')."""
    from src.coach import event_to_reaction

    result = event_to_reaction("win:X")
    assert result == ("cheer", "Kittens win! Hooray! \U0001f389")


def test_coach_win_o_maps_to_cheer() -> None:
    """Event 'win:O' maps to ('cheer', 'Puppies win! Yay! \U0001f389')."""
    from src.coach import event_to_reaction

    result = event_to_reaction("win:O")
    assert result == ("cheer", "Puppies win! Yay! \U0001f389")


def test_coach_draw_maps_to_aww() -> None:
    """Event 'draw' maps to ('aww', 'It's a tie \u2014 great game, friends!')."""
    from src.coach import event_to_reaction

    result = event_to_reaction("draw")
    assert result == ("aww", "It's a tie \u2014 great game, friends!")


def test_coach_idle_maps_to_idle() -> None:
    """Event 'idle' maps to ('idle', '')."""
    from src.coach import event_to_reaction

    result = event_to_reaction("idle")
    assert result == ("idle", "")


def test_coach_reaction_is_deterministic() -> None:
    """Same event always returns identical (expression, line) tuple."""
    from src.coach import event_to_reaction

    result1 = event_to_reaction("greeting")
    result2 = event_to_reaction("greeting")
    assert result1 == result2

    result3 = event_to_reaction("win:X")
    result4 = event_to_reaction("win:X")
    assert result3 == result4


def test_coach_unknown_event_raises() -> None:
    """Invalid event string raises UnrecognizedEventError with value in message."""
    from src.coach import UnrecognizedEventError, event_to_reaction

    with pytest.raises(UnrecognizedEventError) as exc_info:
        event_to_reaction("nonexistent_event")
    assert "nonexistent_event" in str(exc_info.value)

    with pytest.raises(UnrecognizedEventError) as exc_info:
        event_to_reaction("")
    assert "" in str(exc_info.value)


def test_coach_expressions_known_set() -> None:
    """All 8 events return expressions in the valid 6-expression set."""
    from src.coach import event_to_reaction

    valid_expressions = {"wave", "point", "cheer_small", "cheer", "aww", "idle"}

    for event in [
        "greeting",
        "turn:X",
        "turn:O",
        "move_placed",
        "win:X",
        "win:O",
        "draw",
        "idle",
    ]:
        expression, _line = event_to_reaction(event)
        assert expression in valid_expressions


def test_coach_speech_lines_not_empty() -> None:
    """All 7 non-idle events map to non-empty lines; idle maps to empty string."""
    from src.coach import event_to_reaction

    for event in [
        "greeting",
        "turn:X",
        "turn:O",
        "move_placed",
        "win:X",
        "win:O",
        "draw",
    ]:
        _expression, line = event_to_reaction(event)
        assert len(line) > 0

    _expression, line = event_to_reaction("idle")
    assert line == ""
