"""Animation and particle effects module for Tic-Tac-Toe: Critter Clash.

Provides frame-rate-independent animation and particle system classes:

- Particle (dataclass) — data model for a single particle
- ParticleSystem — particle lifecycle manager (add, update, draw, cap at 200)
- PopInAnimation — scale 0→1 bounce when a mark is placed
- SparkleBurst — particle burst emitted on successful placement
- WiggleAnimation — sinusoidal idle oscillation for placed cells
- OccupiedCellWobble — decaying horizontal shake on occupied-cell click
- ConfettiRain — celebratory gravity-driven particle rain
- WinningTrail — color-cycling polyline through winning cells
- LastMoveHighlight — subtle glow border on the most recent move

All ``update(dt)`` methods accept delta-time in milliseconds (DR-003),
ensuring consistent animation speed across any frame rate.
Particle count is capped at 200 concurrent particles (architecture §14).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from src.assets import AssetManager


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

MAX_PARTICLES: int = 200

# Animation durations (milliseconds)
POPIN_DURATION_MS: float = 300.0
SPARKLE_DURATION_MS: float = 600.0
CONFETTI_DURATION_MS: float = 3000.0

# Wiggle animation parameters
WIGGLE_SPEED: float = 0.003
WIGGLE_AMPLITUDE: float = 3.0

# Wobble animation parameters
WOBBLE_DURATION_MS: float = 200.0
WOBBLE_AMPLITUDE: float = 5.0

# Highlight colors
LAST_MOVE_COLOR: tuple[int, int, int] = (255, 255, 200)  # Soft yellow glow
TRAIL_COLOR_CYCLE: list[tuple[int, int, int]] = [
    (255, 100, 100),  # Red
    (100, 255, 100),  # Green
    (100, 100, 255),  # Blue
]


# ---------------------------------------------------------------------------
# Particle dataclass
# ---------------------------------------------------------------------------


@dataclass
class Particle:
    """A single particle managed by :class:`ParticleSystem`.

    Attributes:
        x: Subpixel x position.
        y: Subpixel y position.
        vx: Velocity x (pixels / second).
        vy: Velocity y (pixels / second).
        lifetime: Remaining lifetime in milliseconds.
        max_lifetime: Total lifetime for alpha-ratio computation.
        sprite_key: AssetManager key for sprite lookup (e.g. ``"sparkle"``).
        scale: Render scale factor (0.0–1.0).
    """

    x: float
    y: float
    vx: float
    vy: float
    lifetime: float
    max_lifetime: float
    sprite_key: str
    scale: float = 1.0


# ---------------------------------------------------------------------------
# ParticleSystem
# ---------------------------------------------------------------------------


class ParticleSystem:
    """Manages the lifecycle of all particles.

    Handles adding, updating positions/velocities/lifetimes, removing
    expired particles, and rendering with per-pixel alpha fade.
    Particle count is capped at ``MAX_PARTICLES``.
    """

    def __init__(self, asset_manager: AssetManager) -> None:
        """Initialise the particle system.

        Args:
            asset_manager: Injected AssetManager for sprite lookups via
                ``get_sprite(key)``.
        """
        self._asset_manager: AssetManager = asset_manager
        self.active_particles: list[Particle] = []

    def add_particle(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        lifetime: float,
        sprite_key: str,
        scale: float = 1.0,
    ) -> None:
        """Append a new particle if under the capacity limit.

        Args:
            x: Initial x position.
            y: Initial y position.
            vx: Velocity x (pixels / second).
            vy: Velocity y (pixels / second).
            lifetime: Remaining lifetime in milliseconds.
            sprite_key: AssetManager sprite key.
            scale: Render scale factor (default 1.0).
        """
        if len(self.active_particles) >= MAX_PARTICLES:
            return

        particle = Particle(
            x=x,
            y=y,
            vx=vx,
            vy=vy,
            lifetime=lifetime,
            max_lifetime=lifetime,
            sprite_key=sprite_key,
            scale=scale,
        )
        self.active_particles.append(particle)

    def update(self, dt: float) -> None:
        """Advance all particles by *dt* milliseconds.

        Updates positions using velocity (pixels/second) and decreases
        lifetime. Expired particles (lifetime <= 0) are removed.

        Args:
            dt: Elapsed time since last frame in milliseconds.
        """
        for particle in self.active_particles:
            particle.x += particle.vx * dt / 1000.0
            particle.y += particle.vy * dt / 1000.0
            particle.lifetime -= dt

        self.active_particles = [
            p for p in self.active_particles if p.lifetime > 0
        ]

    def draw(self, surface: pygame.Surface) -> None:
        """Render all active particles onto *surface*.

        Each particle is drawn with an alpha value proportional to its
        remaining lifetime.  The sprite is optionally scaled before
        blitting.

        Args:
            surface: Target display surface.
        """
        for particle in self.active_particles:
            sprite = self._asset_manager.get_sprite(particle.sprite_key)
            alpha_ratio = particle.lifetime / particle.max_lifetime
            alpha_ratio = max(0.0, min(1.0, alpha_ratio))
            alpha = int(alpha_ratio * 255)

            sprite_copy = sprite.copy()
            sprite_copy.set_alpha(alpha)

            if particle.scale != 1.0:
                scaled_w = int(sprite.get_width() * particle.scale)
                scaled_h = int(sprite.get_height() * particle.scale)
                sprite_copy = pygame.transform.scale(
                    sprite_copy, (scaled_w, scaled_h)
                )
                blit_x = int(particle.x) - scaled_w // 2
                blit_y = int(particle.y) - scaled_h // 2
            else:
                blit_x = int(particle.x) - sprite.get_width() // 2
                blit_y = int(particle.y) - sprite.get_height() // 2

            surface.blit(sprite_copy, (blit_x, blit_y))


# ---------------------------------------------------------------------------
# PopInAnimation
# ---------------------------------------------------------------------------


class PopInAnimation:
    """Animates a newly placed mark from scale 0 → 1 with a smooth fade-in.

    Each cell has its own independent animation stored in a dictionary
    keyed by ``(row, col)``.  Uses a smoothstep ease formula
    (``3t² - 2t³``) that starts at 0.0 and settles at 1.0 without overshoot.
    """

    _animations: dict[tuple[int, int], dict[str, Any]]

    def __init__(self) -> None:
        """Initialise the pop-in animation tracker."""
        self._animations = {}

    def start(
        self,
        row: int,
        col: int,
        cell_center_x: float,
        cell_center_y: float,
        team_key: str,
    ) -> None:
        """Begin a pop-in animation for the given cell.

        Args:
            row: Cell row index.
            col: Cell column index.
            cell_center_x: Pixel centre x of the cell.
            cell_center_y: Pixel centre y of the cell.
            team_key: AssetManager sprite key for the team (e.g. ``"team1_cell"``).
        """
        self._animations[(row, col)] = {
            "elapsed_ms": 0.0,
            "duration_ms": POPIN_DURATION_MS,
            "cell_center_x": cell_center_x,
            "cell_center_y": cell_center_y,
            "team_key": team_key,
        }

    def update(self, dt: float) -> None:
        """Advance all active pop-in animations by *dt* milliseconds.

        Completed animations (elapsed >= duration) are removed.

        Args:
            dt: Elapsed milliseconds since last frame.
        """
        for state in self._animations.values():
            state["elapsed_ms"] += dt

        self._animations = {
            k: v
            for k, v in self._animations.items()
            if v["elapsed_ms"] < v["duration_ms"]
        }

    def get_scale(self, row: int, col: int) -> float:
        """Return the current scale for the given cell.

        Returns 1.0 if the cell has no active animation (not started or
        already complete).  Uses a smoothstep ease formula
        (``3*t² - 2*t³``) that starts at 0.0 and settles at 1.0 without overshoot.

        Args:
            row: Cell row index.
            col: Cell column index.

        Returns:
            Current scale factor (0.0 → 1.0).
        """
        state = self._animations.get((row, col))
        if state is None:
            return 1.0

        t = state["elapsed_ms"] / state["duration_ms"]
        t = max(0.0, min(1.0, t))

        # Smoothstep ease formula: starts at 0, ends at 1.
        return 3.0 * t * t - 2.0 * t * t * t

    def is_active(self, row: int, col: int) -> bool:
        """Check whether a pop-in is still running for the given cell.

        Args:
            row: Cell row index.
            col: Cell column index.

        Returns:
            ``True`` if the animation is still in progress.
        """
        return (row, col) in self._animations


# ---------------------------------------------------------------------------
# SparkleBurst
# ---------------------------------------------------------------------------


class SparkleBurst:
    """Emits a burst of sparkle particles at a given position.

    Used on successful mark placement to create a brief celebratory
    sparkle effect.
    """

    def __init__(self, particle_system: ParticleSystem) -> None:
        """Initialise the sparkle burst emitter.

        Args:
            particle_system: The shared :class:`ParticleSystem` to add
                particles to.
        """
        self._particle_system: ParticleSystem = particle_system

    def emit(self, cx: float, cy: float, count: int = 10) -> None:
        """Emit *count* sparkle particles at position (cx, cy).

        Particles burst upward (vy negative) with random horizontal
        drift and random scale between 0.5 and 1.0.

        Args:
            cx: Centre x pixel position.
            cy: Centre y pixel position.
            count: Number of particles to emit (default 10).
        """
        if count < 1:
            return

        for _ in range(count):
            vx = random.uniform(-80.0, 80.0)
            vy = random.uniform(-120.0, 0.0)
            scale = random.uniform(0.5, 1.0)
            self._particle_system.add_particle(
                x=cx,
                y=cy,
                vx=vx,
                vy=vy,
                lifetime=SPARKLE_DURATION_MS,
                sprite_key="sparkle",
                scale=scale,
            )


# ---------------------------------------------------------------------------
# WiggleAnimation
# ---------------------------------------------------------------------------


class WiggleAnimation:
    """Provides a gentle sinusoidal y-offset for idle placed cells.

    Each cell has a randomised phase offset so cells do not wiggle in
    sync.
    """

    _wiggles: dict[tuple[int, int], float]

    def __init__(self) -> None:
        """Initialise the wiggle tracker."""
        self._wiggles = {}

    def add_cell(self, row: int, col: int) -> None:
        """Add a cell to the wiggle system.

        The cell is assigned a random time offset for phase variety.
        If the cell is already tracked, this is a no-op.

        Args:
            row: Cell row index.
            col: Cell column index.
        """
        if (row, col) in self._wiggles:
            return
        time_offset = random.uniform(0.0, math.pi * 2.0)
        self._wiggles[(row, col)] = time_offset

    def remove_cell(self, row: int, col: int) -> None:
        """Remove a cell from the wiggle system.

        Args:
            row: Cell row index.
            col: Cell column index.
        """
        self._wiggles.pop((row, col), None)

    def get_offset(self, row: int, col: int, elapsed_ms: float) -> float:
        """Compute the sinusoidal y-offset for a cell.

        Returns 0.0 if the cell is not being wiggled.

        Args:
            row: Cell row index.
            col: Cell column index.
            elapsed_ms: Global elapsed time in milliseconds.

        Returns:
            Y-offset in pixels (positive = downward).
        """
        time_offset = self._wiggles.get((row, col))
        if time_offset is None:
            return 0.0

        return (
            math.sin(elapsed_ms * WIGGLE_SPEED + time_offset)
            * WIGGLE_AMPLITUDE
        )


# ---------------------------------------------------------------------------
# OccupiedCellWobble
# ---------------------------------------------------------------------------


class OccupiedCellWobble:
    """Creates a brief decaying horizontal oscillation on occupied-cell click.

    Duration is ``WOBBLE_DURATION_MS`` (200 ms).  The oscillation
    amplitude decays linearly to zero over the wobble duration.
    """

    _wobbles: dict[tuple[int, int], float]

    def __init__(self) -> None:
        """Initialise the wobble tracker."""
        self._wobbles = {}

    def trigger(self, row: int, col: int) -> None:
        """Begin a wobble cycle for the given cell.

        If a wobble is already active, it is reset to the start.

        Args:
            row: Cell row index.
            col: Cell column index.
        """
        self._wobbles[(row, col)] = 0.0

    def update(self, dt: float) -> None:
        """Advance all active wobbles by *dt* milliseconds.

        Completed wobbles (elapsed >= WOBBLE_DURATION_MS) are removed.

        Args:
            dt: Elapsed milliseconds since last frame.
        """
        for key in list(self._wobbles.keys()):
            self._wobbles[key] += dt

        self._wobbles = {
            k: v
            for k, v in self._wobbles.items()
            if v < WOBBLE_DURATION_MS
        }

    def get_offset(self, row: int, col: int) -> float:
        """Compute the current x-offset for a wobbling cell.

        Returns 0.0 if the cell is not wobbling.

        The formula is a decaying oscillation:
        ``sin(t * π * 4) * WOBBLE_AMPLITUDE * (1 - t)``
        where ``t = elapsed / WOBBLE_DURATION_MS``.

        Args:
            row: Cell row index.
            col: Cell column index.

        Returns:
            X-offset in pixels (positive = rightward).
        """
        elapsed = self._wobbles.get((row, col))
        if elapsed is None:
            return 0.0

        t = elapsed / WOBBLE_DURATION_MS
        # t is in [0, 1) while the wobble is active.
        return (
            math.sin(t * math.pi * 4.0) * WOBBLE_AMPLITUDE * (1.0 - t)
        )


# ---------------------------------------------------------------------------
# ConfettiRain
# ---------------------------------------------------------------------------


class ConfettiRain:
    """Celebratory confetti rain effect.

    Spawns 50–100 particles at random x positions near the top of the
    screen with downward velocity and random horizontal drift.
    Delegates rendering and updates to the shared :class:`ParticleSystem`.
    """

    def __init__(
        self,
        particle_system: ParticleSystem,
        screen_width: int,
        screen_height: int,
    ) -> None:
        """Initialise the confetti rain effect.

        Args:
            particle_system: The shared :class:`ParticleSystem` instance.
            screen_width: Window width in pixels.
            screen_height: Window height in pixels.
        """
        self._particle_system: ParticleSystem = particle_system
        self._screen_width: int = screen_width
        self._screen_height: int = screen_height
        self._started: bool = False

    def start(self) -> None:
        """Emit all confetti particles.

        Particles are spawned just above the visible area (y = -20 to
        -5 pixels).  Has no effect if already started.
        """
        if self._started:
            return

        particle_count = random.randint(50, 100)
        for _ in range(particle_count):
            x = random.uniform(0.0, float(self._screen_width))
            y = random.uniform(-20.0, -5.0)
            vx = random.uniform(-30.0, 30.0)
            vy = random.uniform(80.0, 160.0)
            self._particle_system.add_particle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                lifetime=CONFETTI_DURATION_MS,
                sprite_key="confetti",
            )

        self._started = True

    def update(self, dt: float) -> None:
        """Advance all confetti particles by *dt* milliseconds.

        Args:
            dt: Elapsed milliseconds since last frame.
        """
        self._particle_system.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Render all confetti particles onto *surface*.

        Args:
            surface: Target display surface.
        """
        self._particle_system.draw(surface)

    def is_active(self) -> bool:
        """Check whether any confetti particles remain.

        Note: This checks *all* active particles in the shared system,
        not just confetti.  Acceptable because confetti is the dominant
        particle type during celebration.

        Returns:
            ``True`` if at least one particle is still active.
        """
        return len(self._particle_system.active_particles) > 0


# ---------------------------------------------------------------------------
# WinningTrail
# ---------------------------------------------------------------------------


class WinningTrail:
    """Draws a playful colour-cycling polyline through winning cell centres.

    The trail is revealed progressively over ``_duration_ms`` (800 ms).
    Each segment is drawn with a colour from ``TRAIL_COLOR_CYCLE`` that
    cycles every ~200 ms, creating a moving gradient effect.
    """

    def __init__(self) -> None:
        """Initialise the winning trail."""
        self._cells: list[tuple[int, int]] = []
        self._centers: list[tuple[int, int]] = []
        self._elapsed_ms: float = 0.0
        self._duration_ms: float = 800.0
        self._color_index: int = 0
        self._started: bool = False

    def start(
        self,
        cells: list[tuple[int, int]],
        centers: list[tuple[int, int]],
    ) -> None:
        """Initialise the trail for the given winning cells.

        Args:
            cells: The three winning cell coordinates in order.
            centers: Pixel-centre positions for each winning cell.
        """
        self._cells = cells
        self._centers = centers
        self._elapsed_ms = 0.0
        self._color_index = 0
        self._started = True

    def update(self, dt: float) -> None:
        """Advance the trail state by *dt* milliseconds.

        Clamps elapsed to the duration and advances the colour cycle
        every ~200 ms.

        Args:
            dt: Elapsed milliseconds since last frame.
        """
        if not self._started:
            return

        self._elapsed_ms += dt
        if self._elapsed_ms >= self._duration_ms:
            self._elapsed_ms = self._duration_ms

        cycle_progress = self._elapsed_ms // 200
        self._color_index = int(cycle_progress) % len(TRAIL_COLOR_CYCLE)

    def draw(
        self,
        surface: pygame.Surface,
        grid_origin_x: int,
        grid_origin_y: int,
        cell_size: int,
    ) -> None:
        """Render the trail polyline onto *surface*.

        Draws progressively based on the reveal progress.  Does nothing
        if not started or if fewer than 2 centres exist.

        Args:
            surface: Target display surface.
            grid_origin_x: Board left-edge pixel (unused, centres are
                already world coordinates).
            grid_origin_y: Board top-edge pixel (unused).
            cell_size: Cell width/height in pixels (unused).
        """
        if not self._started or len(self._centers) < 2:
            return

        reveal_progress = self._elapsed_ms / self._duration_ms
        reveal_progress = max(0.0, min(1.0, reveal_progress))

        num_segments = len(self._centers) - 1
        draw_count = int(reveal_progress * num_segments) + 1
        draw_count = max(1, min(draw_count, len(self._centers)))

        for segment_index in range(draw_count - 1):
            segment_color = TRAIL_COLOR_CYCLE[
                (self._color_index + segment_index)
                % len(TRAIL_COLOR_CYCLE)
            ]
            start_pt = self._centers[segment_index]
            end_pt = self._centers[segment_index + 1]
            pygame.draw.line(
                surface,
                segment_color,
                start_pt,
                end_pt,
                width=5,
            )

    def reset(self) -> None:
        """Clear all trail state."""
        self._cells = []
        self._centers = []
        self._elapsed_ms = 0.0
        self._color_index = 0
        self._started = False

    def is_active(self) -> bool:
        """Check whether the trail is still animating.

        Returns:
            ``True`` if the trail is started and has not yet reached
            its full duration.
        """
        return self._started and self._elapsed_ms < self._duration_ms


# ---------------------------------------------------------------------------
# LastMoveHighlight
# ---------------------------------------------------------------------------


class LastMoveHighlight:
    """Tracks and renders a subtle highlight on the most recently placed cell.

    The highlight is a 2-pixel border in ``LAST_MOVE_COLOR`` (soft yellow)
    with rounded corners (``border_radius=8``).
    """

    def __init__(self) -> None:
        """Initialise the highlight tracker."""
        self._last_cell: tuple[int, int] | None = None

    def set_last(self, row: int, col: int) -> None:
        """Record the most recently placed cell.

        Args:
            row: Cell row index.
            col: Cell column index.
        """
        self._last_cell = (row, col)

    def clear(self) -> None:
        """Remove the highlight."""
        self._last_cell = None

    def get_cell(self) -> tuple[int, int] | None:
        """Return the last-move cell coordinate, or ``None``.

        Returns:
            The ``(row, col)`` of the most recent move, or ``None``.
        """
        return self._last_cell

    def draw(
        self,
        surface: pygame.Surface,
        grid_origin_x: int,
        grid_origin_y: int,
        cell_size: int,
        cell_pixel_x: int,
        cell_pixel_y: int,
    ) -> None:
        """Render the highlight border on the last-move cell.

        Does nothing if no cell has been recorded yet.

        Args:
            surface: Target display surface.
            grid_origin_x: Board left-edge pixel (unused).
            grid_origin_y: Board top-edge pixel (unused).
            cell_size: Cell width/height in pixels.
            cell_pixel_x: Pixel x of the cell centre.
            cell_pixel_y: Pixel y of the cell centre.
        """
        if self._last_cell is None:
            return

        cell_left = cell_pixel_x - cell_size // 2
        cell_top = cell_pixel_y - cell_size // 2
        rect = pygame.Rect(cell_left, cell_top, cell_size, cell_size)
        pygame.draw.rect(
            surface,
            LAST_MOVE_COLOR,
            rect,
            width=2,
            border_radius=8,
        )
