"""Pure-Python Coach reaction mapping module.

Maps game lifecycle events to Coach character expression + speech-bubble line
tuples. Zero pygame imports (DR-001). All mappings are stateless and
deterministic — a pure function lookup into a module-level dictionary.

Typical usage:
    reaction = event_to_reaction("greeting")  # -> ("wave", "Hiii! ...")
    expression, line = reaction
"""

# CHANGELOG: Sprint 4, Task 1 — Coach reaction mapping module

from __future__ import annotations

from typing import Literal

GameEvent = Literal[
    "greeting",
    "turn:X",
    "turn:O",
    "move_placed",
    "win:X",
    "win:O",
    "draw",
    "idle",
]

CoachExpression = Literal[
    "wave",
    "point",
    "cheer_small",
    "cheer",
    "aww",
    "idle",
]

CoachReaction = tuple[CoachExpression, str]


class UnrecognizedEventError(Exception):
    """Raised when event_to_reaction() receives an unrecognized game event.

    Args:
        event: The unrecognized event string value.
    """

    def __init__(self, event: str) -> None:
        super().__init__(f"Unrecognized game event: {event}")


EVENT_REACTION_MAP: dict[GameEvent, CoachReaction] = {
    "greeting": ("wave", "Hiii! Pick your team and let's play!"),
    "turn:X": ("point", "Kittens' turn! Where will you go?"),
    "turn:O": ("point", "Puppies' turn! You've got this!"),
    "move_placed": ("cheer_small", "Ooh, nice spot!"),
    "win:X": ("cheer", "Kittens win! Hooray! \U0001f389"),
    "win:O": ("cheer", "Puppies win! Yay! \U0001f389"),
    "draw": ("aww", "It's a tie \u2014 great game, friends!"),
    "idle": ("idle", ""),
}


def event_to_reaction(event: GameEvent) -> CoachReaction:
    """Map a game lifecycle event to a Coach reaction tuple.

    Pure deterministic lookup — same event always returns the same
    (expression, speech_line) pair. No side effects, no I/O, no state
    mutation.

    Args:
        event: A game lifecycle event string. Must be one of the 8 valid
            GameEvent values.

    Returns:
        A CoachReaction tuple of (expression_key, speech_bubble_line).

    Raises:
        UnrecognizedEventError: If the event string is not a valid
            GameEvent.
    """
    if event in EVENT_REACTION_MAP:
        return EVENT_REACTION_MAP[event]
    raise UnrecognizedEventError(event)


__all__ = [
    "event_to_reaction",
    "GameEvent",
    "CoachExpression",
    "CoachReaction",
    "UnrecognizedEventError",
]
