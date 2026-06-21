# CHANGELOG:
# - Sprint 4, Task 5 — Game entry point
# - Sprint 5 — ParticleSystem dependency injection wiring for GameScene
#   and CelebrationScene

"""Game entry point for Tic-Tac-Toe: Critter Clash.

Initialises Pygame, creates the 960×720 "Favur Tic-Tac-Toe" window,
constructs all three scenes with dependency injection, runs the main
event loop (event dispatch → dt-based update → draw → flip), and
provides an exception boundary (ERR-007, ERR-008).

Architecture §12 dependency injection wiring:
    main()
    ├─ pygame.init()
    ├─ AssetManager(manifest_path)          → shared across scenes
    ├─ Board()                               → owned by GameScene
    ├─ TeamSelectScene(assets, event_to_reaction)
#     ├── GameScene(assets, board, event_to_reaction, particle_system)
#     └── CelebrationScene(assets, board, event_to_reaction, result,
#                           particle_system, winning_cells=None)
"""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

import pygame

from src.assets import AssetLoadError, AssetManager, ManifestMissingError
from src.coach import event_to_reaction
from src.effects import ParticleSystem
from src.game import Board
from src.scenes import CelebrationScene, GameScene, TeamSelectScene

logger = logging.getLogger("src.main")

# ─────────────────────────────────────────────────────────────────────────────
# Module-level constants (Architecture §9)
# ─────────────────────────────────────────────────────────────────────────────

WINDOW_WIDTH: int = 960
"""Window width in pixels (non-resizable)."""

WINDOW_HEIGHT: int = 720
"""Window height in pixels (non-resizable)."""

WINDOW_TITLE: str = "Favur Tic-Tac-Toe"
"""Exact window title (SOW-mandated)."""

FPS_LIMIT: int = 60
"""Target frame rate; animation timing is dt-based regardless."""

ASSET_MANIFEST_PATH: str = "assets/manifest.json"
"""Path to the asset manifest JSON file."""


# ─────────────────────────────────────────────────────────────────────────────
# Custom exceptions (ERR-007)
# ─────────────────────────────────────────────────────────────────────────────


class PygameInitError(Exception):
    """Raised when pygame.init() fails (ERR-007).

    Indicates that the display or SDL subsystem could not be initialised,
    typically because no graphical environment is available.
    """


# ─────────────────────────────────────────────────────────────────────────────
# main() function
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """Initialise Pygame, construct all scenes, and run the main loop.

    Raises:
        PygameInitError: If pygame.init() fails.
        AssetLoadError: If an asset cannot be loaded.
        ManifestMissingError: If the manifest file is missing.
    """
    # ── 3.3.1 Pygame Initialisation ──────────────────────────────────────
    try:
        display_success, _ = pygame.init()
        if display_success < 0:
            raise PygameInitError("Could not open the game window")
    except Exception as exc:
        raise PygameInitError(f"Pygame init failed: {exc}") from exc

    pygame.display.set_caption(WINDOW_TITLE)

    # NO SCALED flag. Window is exactly 960×720 and non-resizable.
    screen: pygame.Surface = pygame.display.set_mode(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
    )

    clock = pygame.time.Clock()

    # -- 3.3.2 Asset Loading (fail-loudly) --
    assets = AssetManager(ASSET_MANIFEST_PATH)

    # -- 3.3.2b ParticleSystem (shared across scenes) --
    particle_system = ParticleSystem(assets)

    # -- 3.3.3 Board and Coach --
    board = Board()

    # -- 3.3.4 Scene Construction with Dependency Injection --
    team_select = TeamSelectScene(assets, event_to_reaction)
    game = GameScene(assets, board, event_to_reaction, particle_system)
    # CelebrationScene is NOT constructed here -- it is constructed on-demand
    # during the game->celebration transition (lines 149-157 below).

    # ── 3.3.5 Scene Manager ───────────────────────────────────────────────
    scenes: dict[str, object] = {
        "team_select": team_select,
        "game": game,
    }
    current_scene: str = "team_select"

    # ── 3.4 Main Loop ────────────────────────────────────────────────────
    while True:
        # Step 1: Clock tick and dt clamping (DR-003)
        dt: float = float(clock.tick(FPS_LIMIT))
        dt = min(dt, 100.0)

        # Step 2: Event processing
        next_scene: str | None = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

            # Dispatch event to active scene
            transition = getattr(scenes[current_scene], "handle_event")(event)
            if transition is not None:
                next_scene = transition
                break  # Process transition immediately

        # Step 3: Scene update
        update_transition = getattr(scenes[current_scene], "update")(dt)
        if next_scene is None and update_transition is not None:
            next_scene = update_transition

        # Step 4: Scene transitions
        if next_scene is not None:
            if next_scene == "celebration":
                winner_result = board.winner()
                celebration = CelebrationScene(
                    assets,
                    board,
                    event_to_reaction,
                    winner_result or "draw",
                    particle_system,
                    board.winning_cells(),
                )
                scenes["celebration"] = celebration
                current_scene = "celebration"

            elif next_scene == "team_select":
                board.reset()
                particle_system = ParticleSystem(assets)
                team_select = TeamSelectScene(assets, event_to_reaction)
                scenes["team_select"] = team_select
                current_scene = "team_select"

            elif next_scene == "game":
                particle_system = ParticleSystem(assets)
                new_board = Board()
                game = GameScene(assets, new_board, event_to_reaction, particle_system)
                scenes["game"] = game
                board = new_board
                current_scene = "game"

        # Step 5: Draw current scene
        getattr(scenes[current_scene], "draw")(screen)

        # Step 6: Flip display buffer
        pygame.display.flip()


# ─────────────────────────────────────────────────────────────────────────────
# Exception boundary (ERR-008) and __main__ guard
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    try:
        main()
    except PygameInitError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except (AssetLoadError, ManifestMissingError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        # Step 1: Try to display an error overlay if a screen exists
        try:
            _screen = pygame.display.get_surface()
            if _screen is not None:
                _error_font = pygame.font.SysFont(None, 48)
                _error_text = "Oops! Something went wrong"
                _text_surface = _error_font.render(
                    _error_text,
                    True,
                    (90, 74, 92),
                )
                _text_x = (960 - _text_surface.get_width()) // 2
                _text_y = (720 - _text_surface.get_height()) // 2
                _screen.fill((255, 245, 186))
                _screen.blit(_text_surface, (_text_x, _text_y))
                pygame.display.flip()
                pygame.time.wait(3000)
        except Exception:
            pass  # No display surface available — skip overlay

        # Step 2: Log traceback to logs/error.log
        _log_dir = Path("logs")
        _log_dir.mkdir(exist_ok=True)
        _log_path = _log_dir / "error.log"
        with _log_path.open("a", encoding="utf-8") as _log_file:
            _log_file.write(f"--- {type(exc).__name__} ---\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=_log_file)
            _log_file.write("\n")

        # Step 3: Exit with error code
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit(1)
