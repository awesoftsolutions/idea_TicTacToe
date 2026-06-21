"""Demo Carrier — automated draw game screenshot capture.

Launches the game, selects both teams, plays the 9-move draw sequence,
and saves screenshots at the draw celebration scene using pygame.image.save.
Saves to docs/screenshots/d4_draw_celebration.png and
docs/screenshots/b4_coach_aww_draw.png.
"""
from __future__ import annotations

import os
import sys
import time

import pygame

# Disable DPI scaling so click coordinates map 1:1
os.environ["SDL_VIDEODRIVER"] = "windib"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.assets import AssetManager
from src.coach import event_to_reaction
from src.effects import ParticleSystem
from src.game import Board
from src.scenes import GameScene, TeamSelectScene

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720
ASSET_MANIFEST_PATH = "assets/manifest.json"

# Draw game move sequence: (client_x, client_y) centers at 1x scale
DRAW_MOVES = [
    (240, 220),   # 1: X at cell(0,0)
    (240, 340),   # 2: O at cell(1,0)
    (360, 220),   # 3: X at cell(0,1)
    (360, 340),   # 4: O at cell(1,1)
    (240, 460),   # 5: X at cell(2,0)
    (480, 220),   # 6: O at cell(0,2)
    (480, 340),   # 7: X at cell(1,2)
    (360, 460),   # 8: O at cell(2,1)
    (480, 460),   # 9: X at cell(2,2) -> DRAW
]

TEAM1_CLICK = (160, 260)
TEAM2_CLICK = (160, 420)
START_CLICK = (180, 570)


def main() -> None:
    """Launch game, play draw game, and save screenshots."""
    pygame.init()
    pygame.display.set_caption("Favur Tic-Tac-Toe")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    assets = AssetManager(ASSET_MANIFEST_PATH)
    particle_system = ParticleSystem(assets)
    board = Board()

    team_select = TeamSelectScene(assets, event_to_reaction)

    # Step 1: Show team select and click team 1
    team_select.draw(screen)
    pygame.display.flip()
    time.sleep(0.3)

    # Simulate team 1 click
    click_event_1 = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": TEAM1_CLICK, "button": 1}
    )
    team_select.handle_event(click_event_1)

    # Simulate team 2 click
    click_event_2 = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": TEAM2_CLICK, "button": 1}
    )
    team_select.handle_event(click_event_2)

    # Click start
    click_event_start = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": START_CLICK, "button": 1}
    )
    result = team_select.handle_event(click_event_start)

    # Transition to game
    if result != "game":
        print(f"ERROR: Team select did not transition to game, got: {result}")
        pygame.quit()
        sys.exit(1)

    game = GameScene(assets, board, event_to_reaction, particle_system)

    # Step 2: Play the draw game sequence (9 moves)
    for i, (cx, cy) in enumerate(DRAW_MOVES):
        click_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (cx, cy), "button": 1}
        )
        transition = game.handle_event(click_event)

        # Advance game loop
        game.update(16)
        game.draw(screen)
        pygame.display.flip()
        time.sleep(0.15)

        if transition == "celebration":
            print(f"Transition to celebration after move {i+1}")
            break

    # Step 3: Create celebration scene
    from src.scenes import CelebrationScene

    winner_result = board.winner()
    celebration = CelebrationScene(
        assets,
        board,
        event_to_reaction,
        winner_result or "draw",
        particle_system,
        board.winning_cells(),
    )

    # Step 4: Render celebration and capture screenshots
    for _ in range(10):
        celebration.update(33)
        celebration.draw(screen)
        pygame.display.flip()
        time.sleep(0.05)

    # Save D4 - draw celebration
    d4_path = "docs/screenshots/d4_draw_celebration.png"
    pygame.image.save(screen, d4_path)
    print(f"Saved: {d4_path}")

    time.sleep(0.3)

    # Save B4b - coach aww on draw
    b4b_path = "docs/screenshots/b4_coach_aww_draw.png"
    pygame.image.save(screen, b4b_path)
    print(f"Saved: {b4b_path}")

    pygame.quit()
    print("Draw game complete. All screenshots saved.")


if __name__ == "__main__":
    main()