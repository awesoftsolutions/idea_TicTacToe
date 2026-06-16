"""Three playable scenes for Tic-Tac-Toe: Critter Clash.

This module implements the Scene protocol (Architecture §6.1) with:
- TeamSelectScene: team selection with Coach greeting and speech bubble
- GameScene: core gameplay with board rendering, mouse/keyboard input
- CelebrationScene: win/draw display with Play Again option

Module-level constants define sprite positioning for the TeamSelectScene layout.
"""

# CHANGELOG:
# - Sprint 4, Task 2 — TeamSelectScene + render_speech_bubble
# - Sprint 4, Task 3 — GameScene class
# - Sprint 4, Task 4 — CelebrationScene class

from __future__ import annotations

import pygame
import pygame.color  # noqa: F401 — force pygame.color submodule into the

# pygame namespace so that pygame.font.Font (and other C extensions that
# reference pygame.color.Color internally) do not trigger a lazy-load
# circular import during test execution.
import pygame.font  # noqa: F401 — ensure font submodule is available before

# any scene constructor tries to use SysFont.
from src.effects import (
    ConfettiRain,
    LastMoveHighlight,
    OccupiedCellWobble,
    PopInAnimation,
    SparkleBurst,
    WiggleAnimation,
    WinningTrail,
)
from src.game import Board, BoardResult
from src.sprite_config import OUTLINE_COLOR, OUTLINE_WIDTH, PALETTE

# ═══════════════════════════════════════════════════════════════════════════════
# §3.1 — Module-Level Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Window configuration (from Architecture §9)
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720

# Board grid constants
BOARD_ORIGIN_X = 180
BOARD_ORIGIN_Y = 160
CELL_SIZE = 120

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

# Colors from sprite_config.py
BUTTER_COLOR = PALETTE["butter"]
SPEECH_OUTLINE_COLOR = OUTLINE_COLOR
SPEECH_OUTLINE_WIDTH = OUTLINE_WIDTH


# ═══════════════════════════════════════════════════════════════════════════════
# §3.2 — render_speech_bubble() Helper Function
# ═══════════════════════════════════════════════════════════════════════════════


def render_speech_bubble(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    font: pygame.font.Font | None = None,
) -> None:
    """Draw a rounded-rectangle speech bubble at (x, y) on the given surface.

    Fill: Butter (#FFF5BA), Outline: 4px #5A4A5C border_radius=15.
    Text is rendered using the provided font (or SysFont 24pt if None),
    word-wrapped to ~25 characters, and centred inside the bubble.

    Args:
        surface: Target pygame.Surface to draw on.
        text: The text string to display inside the bubble.
        x: Left edge x-coordinate of the bubble.
        y: Top edge y-coordinate of the bubble.
        font: pygame.font.Font instance for text rendering (optional).
              Defaults to pygame.font.SysFont(None, 24) if None.
    """
    if font is None:
        font = pygame.font.SysFont(None, 24)

    bubble_width = SPEECH_BUBBLE_WIDTH
    bubble_height = 100

    rect = pygame.Rect(x, y, bubble_width, bubble_height)

    # Draw the filled rounded rectangle
    pygame.draw.rect(surface, BUTTER_COLOR, rect, border_radius=15)

    # Draw the outline
    pygame.draw.rect(
        surface,
        SPEECH_OUTLINE_COLOR,
        rect,
        width=SPEECH_OUTLINE_WIDTH,
        border_radius=15,
    )

    # Render text with word wrapping (skip if empty or None)
    if not text:
        return

    # Word-wrap text to lines of ~25 characters
    lines: list[str] = []
    current_line = ""
    for word in text.split(" "):
        if current_line and len(current_line) + len(word) + 1 > 25:
            lines.append(current_line)
            current_line = word
        elif not current_line:
            current_line = word
        else:
            current_line = current_line + " " + word
    if current_line:
        lines.append(current_line)

    line_height = font.get_linesize()
    total_text_height = len(lines) * line_height
    text_start_y = y + (bubble_height - total_text_height) // 2

    for line in lines:
        text_surface = font.render(line, True, SPEECH_OUTLINE_COLOR)
        text_x = x + (bubble_width - text_surface.get_width()) // 2
        surface.blit(text_surface, (text_x, text_start_y))
        text_start_y += line_height


# ═══════════════════════════════════════════════════════════════════════════════
# §3.3 — TeamSelectScene Class
# ═══════════════════════════════════════════════════════════════════════════════


class TeamSelectScene:
    """The team selection scene.

    Displays team portraits, Coach greeting with speech bubble, and Start
    button. Implements the Scene interface per Architecture §6.1.
    """

    def __init__(
        self,
        asset_manager: object,
        get_coach_reaction: callable,
    ) -> None:
        """Initialise the TeamSelectScene with injected dependencies.

        Args:
            asset_manager: AssetManager instance providing get_sprite(key)
                and get_sprite_size(key).
            get_coach_reaction: callable — the event_to_reaction() function
                from src/coach.py. Called with event string, returns
                (expression_key: str, line_text: str).

        Raises:
            KeyError: If asset_manager.get_sprite() fails for any required key.
        """
        # Step 1: Store injected dependencies
        self.asset_manager = asset_manager
        self.get_coach_reaction = get_coach_reaction

        # Step 2: Initialise selected_teams tracking dict
        self.selected_teams: dict[str, bool] = {
            "team1": False,
            "team2": False,
        }

        # Step 3: Cache the Coach greeting reaction
        self.coach_expression: str
        self.coach_line: str
        self.coach_expression, self.coach_line = self.get_coach_reaction("greeting")

        # Step 4: Initialise font for text rendering
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 24)

        # Step 5: Pre-calculate clickable rects for hit testing
        self.team1_rect = pygame.Rect(
            TEAM1_PORTRAIT_X,
            TEAM1_PORTRAIT_Y,
            TEAM_PORTRAIT_SIZE[0],
            TEAM_PORTRAIT_SIZE[1],
        )
        self.team2_rect = pygame.Rect(
            TEAM2_PORTRAIT_X,
            TEAM2_PORTRAIT_Y,
            TEAM_PORTRAIT_SIZE[0],
            TEAM_PORTRAIT_SIZE[1],
        )
        self.start_btn_rect = pygame.Rect(
            BTN_START_X,
            BTN_START_Y,
            BTN_START_SIZE[0],
            BTN_START_SIZE[1],
        )

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Process a pygame event for the team select scene.

        Args:
            event: A pygame event object (typically MOUSEBUTTONDOWN).

        Returns:
            "game" — when both teams are selected and Start button is clicked.
            None — to stay on this scene (no transition).
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_x = event.pos[0]
            click_y = event.pos[1]

            # Check if team1 portrait was clicked and team1 not yet assigned
            if (
                self.team1_rect.collidepoint(click_x, click_y)
                and not self.selected_teams["team1"]
            ):
                self.selected_teams["team1"] = True

            # Check if team2 portrait was clicked and team2 not yet assigned
            elif (
                self.team2_rect.collidepoint(click_x, click_y)
                and not self.selected_teams["team2"]
            ):
                self.selected_teams["team2"] = True

            # Check if Start button was clicked (only when both teams selected)
            elif (
                self.selected_teams["team1"]
                and self.selected_teams["team2"]
                and self.start_btn_rect.collidepoint(click_x, click_y)
            ):
                return "game"

        return None

    def update(self, dt: float) -> str | None:
        """Advance scene state by dt milliseconds.

        TeamSelectScene has no continuous animations — this is a passive
        selection scene. Returns None (no transition) always.

        Args:
            dt: Elapsed time since last frame in milliseconds (float).

        Returns:
            None — always. No scene transition from update().
        """
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Render the TeamSelectScene to the given display surface.

        Read-only — no state mutation.

        Rendering order (back to front):
            1. Background (bg_team_select)
            2. Team 1 portrait (team1_cell)
            3. Team 2 portrait (team2_cell)
            4. Coach greeting sprite (coach_wave) + speech bubble
            5. Start button (btn_start) — only if both teams selected
            6. Scene name overlay "Team Select"

        Args:
            surface: The pygame display surface (960x720) to draw on.
        """
        # Step 1: Draw background
        bg = self.asset_manager.get_sprite("bg_team_select")
        surface.blit(bg, (0, 0))

        # Step 2: Draw team 1 portrait
        team1_sprite = self.asset_manager.get_sprite("team1_cell")
        surface.blit(team1_sprite, (TEAM1_PORTRAIT_X, TEAM1_PORTRAIT_Y))

        # Step 3: Draw team 2 portrait
        team2_sprite = self.asset_manager.get_sprite("team2_cell")
        surface.blit(team2_sprite, (TEAM2_PORTRAIT_X, TEAM2_PORTRAIT_Y))

        # Step 4: Draw Coach greeting sprite and speech bubble
        coach_sprite_key = f"coach_{self.coach_expression}"
        coach_sprite = self.asset_manager.get_sprite(coach_sprite_key)
        surface.blit(coach_sprite, (COACH_PANEL_X, COACH_PANEL_Y))

        render_speech_bubble(
            surface=surface,
            text=self.coach_line,
            x=SPEECH_BUBBLE_X,
            y=SPEECH_BUBBLE_Y,
            font=self.font,
        )

        # Step 5: Draw Start button (only when both teams selected)
        if self.selected_teams["team1"] and self.selected_teams["team2"]:
            start_sprite = self.asset_manager.get_sprite("btn_start")
            surface.blit(start_sprite, (BTN_START_X, BTN_START_Y))

        # Step 6: Draw scene name overlay in top-left corner
        overlay_surface = self.font.render("Team Select", True, SPEECH_OUTLINE_COLOR)
        surface.blit(overlay_surface, (SCENE_OVERLAY_X, SCENE_OVERLAY_Y))


# ═══════════════════════════════════════════════════════════════════════════════
# §3.4 — CelebrationScene Class (Sprint 4, Task 4)
# ═══════════════════════════════════════════════════════════════════════════════

# CHANGELOG: Sprint 4, Task 4 — CelebrationScene class


class CelebrationScene:
    """Celebration scene displayed after a win or draw.

    Implements the Scene interface per Architecture §6.1.
    Displays the winning team's celebration sprite (or a tie message),
    the Coach character's win/draw reaction with speech bubble, and
    a Play Again button.  R or ESCAPE key resets the board and returns
    to team_select.
    """

    def __init__(
        self,
        asset_manager: object,
        board: object,
        get_coach_reaction: callable,
        result: str,
        particle_system: object,
        winning_cells: list[tuple[int, int]] | None = None,
    ) -> None:
        """Initialise the CelebrationScene with injected dependencies.

        Args:
            asset_manager: AssetManager providing get_sprite/get_sprite_size.
            board: Board instance (uses reset() on transition).
            get_coach_reaction: Callable accepting event string, returning
                (expression_key, line_text).
            result: "X", "O", or "draw" from Board.winner().
            particle_system: Shared ParticleSystem for confetti effects.
            winning_cells: List of (row, col) winning cell coordinates from
                Board.winning_cells().  Used to compute trail positions.
        """
        # Step 1: Store injected dependencies
        self._asset_manager = asset_manager
        self._board = board
        self._get_coach_reaction = get_coach_reaction
        self._result = result
        self.particle_system = particle_system

        # Step 2: Compute celebration sprite key based on winner
        if result == "X":
            self._celebrate_sprite_key = "team1_celebrate"
        elif result == "O":
            self._celebrate_sprite_key = "team2_celebrate"
        else:
            self._celebrate_sprite_key = None

        # Step 3: Get Coach reaction
        if result == "X" or result == "O":
            self._reaction = self._get_coach_reaction(f"win:{result}")
        else:
            self._reaction = self._get_coach_reaction("draw")

        # Step 4: Build coach sprite key from expression
        expression_key = self._reaction[0]
        self._coach_sprite_key = "coach_" + expression_key

        # Step 5: Extract speech line text
        self._speech_line = self._reaction[1]

        # Step 6: Pre-load sprites from AssetManager
        self._bg_sprite = self._asset_manager.get_sprite("bg_celebration")

        if self._celebrate_sprite_key is not None:
            self._celebrate_sprite = self._asset_manager.get_sprite(
                self._celebrate_sprite_key,
            )

        self._coach_sprite = self._asset_manager.get_sprite(self._coach_sprite_key)

        # Step 7: Get button sprite and dimensions
        self._btn_sprite = self._asset_manager.get_sprite("btn_play_again")
        self._btn_size = self._asset_manager.get_sprite_size("btn_play_again")

        # Step 8: Initialise font for text rendering (matches TeamSelectScene
        #         and GameScene pattern — SysFont does not auto-init)
        pygame.font.init()
        self._font_large = pygame.font.SysFont(None, 48)  # tie text
        self._font_small = pygame.font.SysFont(None, 20)  # overlay/instruction
        self._font_bubble = pygame.font.SysFont(None, 24)  # speech bubble

        # Step 9: Compute button position (centred horizontally, bottom third)
        btn_w, btn_h = self._btn_size
        self._btn_x = (WINDOW_WIDTH // 2) - (btn_w // 2)
        self._btn_y = (WINDOW_HEIGHT * 2 // 3) - (btn_h // 2)

        # Step 10: Compute celebration sprite centre position
        if self._celebrate_sprite_key is not None:
            celebrate_size = self._asset_manager.get_sprite_size(
                self._celebrate_sprite_key,
            )
            cw, ch = celebrate_size
            self._celebrate_x = (WINDOW_WIDTH // 2) - (cw // 2)
            self._celebrate_y = (WINDOW_HEIGHT // 2) - (ch // 2) - 60

        # Step 11: Instantiate effect objects
        self.confetti = ConfettiRain(particle_system, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.trail = WinningTrail()

        # Step 12: Start effects based on result
        if (
            result in ("X", "O")
            and winning_cells is not None
            and len(winning_cells) > 0
        ):
            self.confetti.start()
            centres: list[tuple[int, int]] = []
            for win_row, win_col in winning_cells:
                cx = BOARD_ORIGIN_X + win_col * CELL_SIZE + CELL_SIZE // 2
                cy = BOARD_ORIGIN_Y + win_row * CELL_SIZE + CELL_SIZE // 2
                centres.append((cx, cy))
            self.trail.start(winning_cells, centres)
        # Else (draw): no confetti, no trail — tie celebration only

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Process a pygame event for the celebration scene.

        MOUSEBUTTONDOWN on Play Again button, or KEYDOWN with K_r /
        K_ESCAPE: calls board.reset() and returns "team_select".
        All other events return None (stay on scene).

        Args:
            event: A pygame event object.

        Returns:
            "team_select" on transition trigger, None otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            btn_w, btn_h = self._btn_size
            btn_rect = pygame.Rect(self._btn_x, self._btn_y, btn_w, btn_h)

            if btn_rect.collidepoint(mouse_x, mouse_y):
                self._board.reset()
                return "team_select"

            # Click outside button — friendly no-op
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._board.reset()
                return "team_select"
            if event.key == pygame.K_ESCAPE:
                self._board.reset()
                return "team_select"

        # Unhandled events — stay on this scene
        return None

    def update(self, dt: float) -> str | None:
        """Advance scene state and effects by dt milliseconds.

        Updates confetti rain particles and winning trail animation.

        Args:
            dt: Elapsed time since last frame in milliseconds.

        Returns:
            None — always. No scene transition from update().
        """
        # Step 1: Update effects
        self.confetti.update(dt)
        self.trail.update(dt)

        # Step 2: No scene transitions from update
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Render the CelebrationScene to the given display surface.

        Rendering order (back to front):
            1. Background (bg_celebration)
            2. Winning trail polyline (behind celebration sprite)
            3. Win: celebration sprite / Draw: "It's a tie!" text
            4. Coach expression sprite
            5. Speech bubble below Coach
            6. Play Again button
            7. Confetti rain (on top of everything)
            8. "Press R or click Play Again to restart" instruction
            9. Scene name overlay "Celebration"

        Args:
            surface: The pygame display surface (960x720) to draw on.
        """
        # Layer 1: Background
        surface.blit(self._bg_sprite, (0, 0))

        # Layer 2: Winning trail (drawn behind celebration sprite)
        self.trail.draw(
            surface=surface,
            grid_origin_x=BOARD_ORIGIN_X,
            grid_origin_y=BOARD_ORIGIN_Y,
            cell_size=CELL_SIZE,
        )

        # Layer 3: Win display or Draw message
        if self._celebrate_sprite_key is not None:
            # Win: blit winning team's celebration sprite
            surface.blit(
                self._celebrate_sprite,
                (self._celebrate_x, self._celebrate_y),
            )
        else:
            # Draw: render "It's a tie!" text centred
            tie_text = "It's a tie!"
            text_surface = self._font_large.render(
                tie_text,
                True,
                OUTLINE_COLOR,
            )
            text_x = (WINDOW_WIDTH // 2) - (text_surface.get_width() // 2)
            text_y = (WINDOW_HEIGHT // 2) - (text_surface.get_height() // 2) - 60
            surface.blit(text_surface, (text_x, text_y))

        # Layer 4: Coach character
        surface.blit(self._coach_sprite, (COACH_PANEL_X, COACH_PANEL_Y))

        # Layer 5: Speech bubble below Coach sprite
        render_speech_bubble(
            surface=surface,
            text=self._speech_line,
            x=COACH_PANEL_X,
            y=COACH_PANEL_Y + COACH_SPRITE_SIZE[1] + 10,
            font=self._font_bubble,
        )

        # Layer 6: Play Again button
        surface.blit(self._btn_sprite, (self._btn_x, self._btn_y))

        # Layer 7: Confetti rain (drawn on top of everything)
        self.confetti.draw(surface)

        # Layer 8: Instruction text below button
        instruction_text = "Press R or click Play Again to restart"
        instr_surface = self._font_small.render(
            instruction_text,
            True,
            OUTLINE_COLOR,
        )
        instr_x = (WINDOW_WIDTH // 2) - (instr_surface.get_width() // 2)
        instr_y = self._btn_y + self._btn_size[1] + 10
        surface.blit(instr_surface, (instr_x, instr_y))

        # Layer 9: Scene name overlay (top-left corner)
        overlay_text = "Celebration"
        overlay_surface = self._font_small.render(
            overlay_text,
            True,
            OUTLINE_COLOR,
        )
        surface.blit(overlay_surface, (8, 8))


# ═══════════════════════════════════════════════════════════════════════════════
# §3.5 — GameScene Class (Sprint 4, Task 3)
# ═══════════════════════════════════════════════════════════════════════════════


class GameScene:
    """Core gameplay scene rendering the 3x3 board with mouse and keyboard input.

    Implements the Scene interface per Architecture §6.1.
    Handles mouse click placement, keyboard navigation (arrow keys + Enter/Space),
    Coach reactions on every game event, and win/draw detection with scene
    transition to "celebration".
    """

    def __init__(
        self,
        asset_manager: object,
        board: Board,
        get_coach_reaction: callable,
        particle_system: object,
    ) -> None:
        """Initialise the GameScene with injected dependencies.

        Args:
            asset_manager: AssetManager instance providing get_sprite(key).
            board: Board instance for game state management.
            get_coach_reaction: Callable accepting event string, returning
                (expression_key, speech_line) tuple.
            particle_system: Shared ParticleSystem instance for effect particles.
        """
        # Step 1: Store injected dependencies
        self.asset_manager = asset_manager
        self.board = board
        self.get_coach_reaction = get_coach_reaction
        self.particle_system = particle_system

        # Step 2: Map board marks to team sprite key prefixes
        self.team_assignments: dict[str, str] = {
            "X": "team1",
            "O": "team2",
        }

        # Step 2b: Map board marks to team display names (matching Coach voice)
        self.team_display_names: dict[str, str] = {
            "X": "Kittens",
            "O": "Puppies",
        }

        # Step 3: Initial Coach reaction for the starting player's turn
        self.coach_reaction: tuple[str, str] = self.get_coach_reaction(
            f"turn:{board.current_player}"
        )

        # Step 4: Keyboard selector starting at top-left cell
        self.keyboard_selector: tuple[int, int] = (0, 0)

        # Step 5: Font for overlay text and turn indicator
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 20)

        # Step 6: Instantiate real effect objects
        self.pop_in = PopInAnimation()
        self.sparkle = SparkleBurst(particle_system)
        self.wiggle = WiggleAnimation()
        self.wobble = OccupiedCellWobble()
        self.last_move = LastMoveHighlight()

        # Step 7: Initialise elapsed time tracker (milliseconds)
        self.elapsed_ms: float = 0.0

    def _try_place(self, row: int, col: int) -> str | None:
        """Attempt to place a mark at (row, col) with full Coach reaction chain.

        Shared by both mouse click and keyboard placement paths.

        Args:
            row: Row index (0-2).
            col: Column index (0-2).

        Returns:
            "celebration" if placement resulted in a win or draw,
            None if the game continues or placement was rejected.
        """
        current_mark = self.board.current_player
        result = self.board.place(row, col, current_mark)

        if result == BoardResult.OK:
            # Step 2a: Compute cell pixel centre
            cell_center_x = BOARD_ORIGIN_X + col * CELL_SIZE + CELL_SIZE // 2
            cell_center_y = BOARD_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE // 2

            # Step 2b: Determine team sprite key for current mark
            team_prefix = self.team_assignments[current_mark]
            team_key = f"{team_prefix}_cell"

            # Step 2c: Trigger placement effects
            self.pop_in.start(row, col, cell_center_x, cell_center_y, team_key)
            self.sparkle.emit(cell_center_x, cell_center_y)
            self.wiggle.add_cell(row, col)
            self.last_move.set_last(row, col)

            # Coach reaction for successful placement
            self.coach_reaction = self.get_coach_reaction("move_placed")

            # Check for win or draw
            winner_result = self.board.winner()
            if winner_result in ("X", "O"):
                self.coach_reaction = self.get_coach_reaction(f"win:{winner_result}")
                return "celebration"
            if winner_result == "draw":
                self.coach_reaction = self.get_coach_reaction("draw")
                return "celebration"
            # Game continues — update coach_reaction to next turn call
            self.coach_reaction = self.get_coach_reaction(
                f"turn:{self.board.current_player}"
            )
            return None

        # OCCUPIED — trigger wobble as friendly visual feedback
        if result == BoardResult.OCCUPIED:
            self.wobble.trigger(row, col)

        # OCCUPIED or INVALID — no scene transition
        return None

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Process a pygame event for the game scene.

        MOUSEBUTTONDOWN: compute cell from click coordinates and place.
        KEYDOWN (arrows): move keyboard selector clamped to 0-2.
        KEYDOWN (Return/Space): place at keyboard selector position.

        Args:
            event: A pygame event object.

        Returns:
            "celebration" on win/draw, None to stay on scene.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Compute cell coordinates from mouse position
            col = (event.pos[0] - BOARD_ORIGIN_X) // CELL_SIZE
            row = (event.pos[1] - BOARD_ORIGIN_Y) // CELL_SIZE

            # Clamp to grid bounds 0-2
            row = max(0, min(row, 2))
            col = max(0, min(col, 2))

            return self._try_place(row, col)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.keyboard_selector = (
                    max(0, self.keyboard_selector[0] - 1),
                    self.keyboard_selector[1],
                )
                return None
            if event.key == pygame.K_DOWN:
                self.keyboard_selector = (
                    min(2, self.keyboard_selector[0] + 1),
                    self.keyboard_selector[1],
                )
                return None
            if event.key == pygame.K_LEFT:
                self.keyboard_selector = (
                    self.keyboard_selector[0],
                    max(0, self.keyboard_selector[1] - 1),
                )
                return None
            if event.key == pygame.K_RIGHT:
                self.keyboard_selector = (
                    self.keyboard_selector[0],
                    min(2, self.keyboard_selector[1] + 1),
                )
                return None
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                row, col = self.keyboard_selector
                return self._try_place(row, col)

        return None

    def update(self, dt: float) -> str | None:
        """Advance scene state and effects by dt milliseconds.

        Updates elapsed time tracker, pop-in animations, particles,
        and wobble animations each frame.

        Args:
            dt: Elapsed time since last frame in milliseconds.

        Returns:
            None always — no scene transition from update().
        """
        # Step 1: Accumulate elapsed time
        self.elapsed_ms += dt

        # Step 2: Update effects
        self.pop_in.update(dt)
        self.particle_system.update(dt)
        self.wobble.update(dt)

        # Step 3: No scene transitions from update
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Render the GameScene to the given display surface.

        Rendering order (back to front):
            1. Background (bg_game)
            2. Board frame (board_frame)
            3. Team sprites with wiggle y-offset, wobble x-offset, and pop-in scaling
            4. Keyboard selector highlight (periwinkle 3px border)
            5. Last-move highlight (subtle yellow border)
            6. Coach expression sprite + speech bubble
            7. Turn indicator text
            8. Particle system draw (sparkle bursts, etc.)
            9. Scene name overlay "Game"

        Args:
            surface: The pygame display surface (960x720) to draw on.
        """
        # Layer 1: Background
        bg = self.asset_manager.get_sprite("bg_game")
        surface.blit(bg, (0, 0))

        # Layer 2: Board frame (440x440 centred on 360x360 grid)
        board_frame = self.asset_manager.get_sprite("board_frame")
        surface.blit(
            board_frame,
            (BOARD_ORIGIN_X - 40, BOARD_ORIGIN_Y - 40),
        )

        # Layer 3: Team sprites with wiggle y-offset, wobble x-offset,
        #           and pop-in scaling
        for row in range(3):
            for col in range(3):
                cell_mark = self.board.cells[row][col]
                if cell_mark is not None:
                    team_prefix = self.team_assignments[cell_mark]
                    sprite_key = f"{team_prefix}_cell"
                    sprite = self.asset_manager.get_sprite(sprite_key)

                    cell_top_left_x = BOARD_ORIGIN_X + col * CELL_SIZE
                    cell_top_left_y = BOARD_ORIGIN_Y + row * CELL_SIZE

                    # Compute wiggle y-offset (sinusoidal idle oscillation)
                    wy = self.wiggle.get_offset(row, col, self.elapsed_ms)

                    # Compute wobble x-offset (decaying shake on occupied click)
                    wx = self.wobble.get_offset(row, col)

                    # Compute pop-in scale (1.0 if not animating)
                    scale = self.pop_in.get_scale(row, col)

                    if scale != 1.0:
                        # Draw scaled sprite centred on cell
                        scaled_w = int(sprite.get_width() * scale)
                        scaled_h = int(sprite.get_height() * scale)
                        scaled_sprite = pygame.transform.scale(
                            sprite, (scaled_w, scaled_h)
                        )
                        centre_x = cell_top_left_x + CELL_SIZE // 2
                        centre_y = cell_top_left_y + CELL_SIZE // 2
                        blit_x = centre_x - scaled_w // 2 + int(wx)
                        blit_y = centre_y - scaled_h // 2 + int(wy)
                        surface.blit(scaled_sprite, (blit_x, blit_y))
                    else:
                        # Draw normal sprite at cell position with offsets
                        blit_x = cell_top_left_x + int(wx)
                        blit_y = cell_top_left_y + int(wy)
                        surface.blit(sprite, (blit_x, blit_y))

        # Layer 4: Keyboard selector highlight
        sel_row, sel_col = self.keyboard_selector
        sel_x = BOARD_ORIGIN_X + (sel_col * CELL_SIZE)
        sel_y = BOARD_ORIGIN_Y + (sel_row * CELL_SIZE)
        sel_rect = pygame.Rect(sel_x, sel_y, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(
            surface,
            PALETTE["periwinkle"],
            sel_rect,
            width=3,
        )

        # Layer 5: Last-move highlight (subtle yellow border)
        last_cell = self.last_move.get_cell()
        if last_cell is not None:
            last_row, last_col = last_cell
            last_cell_centre_x = BOARD_ORIGIN_X + last_col * CELL_SIZE + CELL_SIZE // 2
            last_cell_centre_y = BOARD_ORIGIN_Y + last_row * CELL_SIZE + CELL_SIZE // 2
            self.last_move.draw(
                surface=surface,
                grid_origin_x=BOARD_ORIGIN_X,
                grid_origin_y=BOARD_ORIGIN_Y,
                cell_size=CELL_SIZE,
                cell_pixel_x=last_cell_centre_x,
                cell_pixel_y=last_cell_centre_y,
            )

        # Layer 6: Coach expression sprite + speech bubble
        expression_key = self.coach_reaction[0]
        coach_sprite_key = f"coach_{expression_key}"
        coach_sprite = self.asset_manager.get_sprite(coach_sprite_key)
        surface.blit(coach_sprite, (COACH_PANEL_X, COACH_PANEL_Y))

        coach_line_text = self.coach_reaction[1]
        render_speech_bubble(
            surface=surface,
            text=coach_line_text,
            x=COACH_PANEL_X,
            y=COACH_PANEL_Y + COACH_SPRITE_SIZE[1] + 10,
            font=None,
        )

        # Layer 7: Turn indicator (use team display names matching Coach voice)
        team_name = self.team_display_names[self.board.current_player]
        turn_text = f"{team_name}' turn"
        text_surface = self.font.render(turn_text, True, OUTLINE_COLOR)
        text_rect = text_surface.get_rect()
        text_rect.topleft = (
            COACH_PANEL_X,
            COACH_PANEL_Y + COACH_SPRITE_SIZE[1] + 120,
        )
        # Semi-transparent background behind turn text
        bg_rect = text_rect.inflate(8, 4)
        pygame.draw.rect(surface, (*PALETTE["butter"][:3], 180), bg_rect)
        surface.blit(text_surface, text_rect)

        # Layer 8: Particle system draw (sparkle bursts, etc.)
        self.particle_system.draw(surface)

        # Layer 9: Scene name overlay "Game" in top-left corner
        overlay_surface = self.font.render(
            "Game",
            True,
            OUTLINE_COLOR,
        )
        overlay_rect = overlay_surface.get_rect()
        overlay_rect.topleft = (10, 10)
        bg_overlay_rect = overlay_rect.inflate(8, 4)
        pygame.draw.rect(surface, (*PALETTE["butter"][:3], 180), bg_overlay_rect)
        surface.blit(overlay_surface, overlay_rect)
