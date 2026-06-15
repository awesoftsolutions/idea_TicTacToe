"""Tests for the effects module (src/effects.py).

13 unit tests covering all 8 animation and particle classes:
  ParticleSystem, PopInAnimation, SparkleBurst, WiggleAnimation,
  OccupiedCellWobble, ConfettiRain, WinningTrail, LastMoveHighlight.

TDD red-phase — these tests will fail with ImportError because
src/effects.py does not exist yet.  Once implemented in Step 3,
all 13 tests must pass.
"""

from __future__ import annotations

import os

# Headless pygame: SDL_VIDEODRIVER must be set before importing pygame
# so that Surface creation works without a display.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from src.effects import (
    ConfettiRain,
    LastMoveHighlight,
    MAX_PARTICLES,
    OccupiedCellWobble,
    ParticleSystem,
    PopInAnimation,
    POPIN_DURATION_MS,
    SPARKLE_DURATION_MS,
    SparkleBurst,
    WiggleAnimation,
    WinningTrail,
    WOBBLE_DURATION_MS,
)


# ---------------------------------------------------------------------------
# StubAssetManager — minimal sprite provider for headless tests
# ---------------------------------------------------------------------------


class StubAssetManager:
    """Minimal AssetManager stub that returns small pygame Surfaces.

    Satisfies the ``ParticleSystem`` constructor's dependency on
    ``AssetManager.get_sprite(key)`` without requiring a real manifest.json
    or generated sprite files.
    """

    _SIZES: dict[str, tuple[int, int]] = {
        "sparkle": (32, 32),
        "confetti": (16, 16),
    }

    def get_sprite(self, key: str) -> pygame.Surface:
        """Return a small per-pixel-alpha surface for the requested key.

        Args:
            key: Sprite key (e.g. ``"sparkle"``, ``"confetti"``).

        Returns:
            A ``pygame.Surface((w, h), pygame.SRCALPHA)``.

        Raises:
            KeyError: Unknown sprite key.
        """
        if key not in self._SIZES:
            raise KeyError(f"Unknown sprite key: '{key}'")
        w, h = self._SIZES[key]
        return pygame.Surface((w, h), pygame.SRCALPHA)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_asset_manager() -> StubAssetManager:
    """Fixture: a :class:`StubAssetManager` instance."""
    return StubAssetManager()


@pytest.fixture
def particle_system(stub_asset_manager: StubAssetManager) -> ParticleSystem:
    """Fixture: a :class:`ParticleSystem` wired to the stub asset manager."""
    return ParticleSystem(stub_asset_manager)


@pytest.fixture
def pop_in() -> PopInAnimation:
    """Fixture: a fresh :class:`PopInAnimation`."""
    return PopInAnimation()


@pytest.fixture
def sparkle(particle_system: ParticleSystem) -> SparkleBurst:
    """Fixture: a :class:`SparkleBurst` wired to the shared particle system."""
    return SparkleBurst(particle_system)


@pytest.fixture
def wiggle() -> WiggleAnimation:
    """Fixture: a fresh :class:`WiggleAnimation`."""
    return WiggleAnimation()


@pytest.fixture
def wobble() -> OccupiedCellWobble:
    """Fixture: a fresh :class:`OccupiedCellWobble`."""
    return OccupiedCellWobble()


@pytest.fixture
def confetti(particle_system: ParticleSystem) -> ConfettiRain:
    """Fixture: a :class:`ConfettiRain` wired to the shared particle system."""
    return ConfettiRain(particle_system, screen_width=960, screen_height=720)


@pytest.fixture
def trail() -> WinningTrail:
    """Fixture: a fresh :class:`WinningTrail`."""
    return WinningTrail()


@pytest.fixture
def highlight() -> LastMoveHighlight:
    """Fixture: a fresh :class:`LastMoveHighlight`."""
    return LastMoveHighlight()


# ===================================================================
# 13 Unit Tests  (pseudocode §7)
# ===================================================================


# --- ParticleSystem tests (1-3) ---

def test_particle_lifetime_decreases(
    particle_system: ParticleSystem,
) -> None:
    """Particle lifetime decreases by dt on update.

    Create a particle with lifetime=100, call update(25), verify
    the remaining lifetime ≈ 75 (AC-1, AC-2).
    """
    particle_system.add_particle(
        x=0.0, y=0.0, vx=0.0, vy=0.0, lifetime=100.0, sprite_key="sparkle",
    )
    particle_system.update(25.0)
    remaining = particle_system.active_particles[0].lifetime
    assert remaining == pytest.approx(75.0, abs=0.01)


def test_particle_expired_removed(
    particle_system: ParticleSystem,
) -> None:
    """Particle with lifetime <= 0 is removed from the active list (AC-2)."""
    particle_system.add_particle(
        x=0.0, y=0.0, vx=0.0, vy=0.0, lifetime=50.0, sprite_key="sparkle",
    )
    particle_system.update(100.0)
    assert len(particle_system.active_particles) == 0


def test_particle_system_capacity(
    particle_system: ParticleSystem,
) -> None:
    """ParticleSystem respects MAX_PARTICLES cap (AC-1)."""
    excess = MAX_PARTICLES + 5
    for _ in range(excess):
        particle_system.add_particle(
            x=0.0, y=0.0, vx=0.0, vy=0.0, lifetime=1000.0, sprite_key="sparkle",
        )
    assert len(particle_system.active_particles) <= MAX_PARTICLES


# --- PopInAnimation tests (4-6) ---

def test_pop_in_scale_0_at_start(pop_in: PopInAnimation) -> None:
    """Pop-in scale returns 0.0 before any update (AC-3)."""
    pop_in.start(0, 0, cell_center_x=100.0, cell_center_y=100.0, team_key="team1_cell")
    scale = pop_in.get_scale(0, 0)
    assert scale == pytest.approx(0.0, abs=0.01)


def test_pop_in_scale_1_at_end(pop_in: PopInAnimation) -> None:
    """Pop-in scale returns 1.0 after POPIN_DURATION_MS elapses (AC-4)."""
    pop_in.start(0, 0, cell_center_x=100.0, cell_center_y=100.0, team_key="team1_cell")
    pop_in.update(POPIN_DURATION_MS)
    scale = pop_in.get_scale(0, 0)
    assert scale == pytest.approx(1.0, abs=0.01)


def test_pop_in_completes_approximately_on_time(
    pop_in: PopInAnimation,
) -> None:
    """Pop-in is nearly complete at 95 % duration, fully complete at 100 % (AC-4)."""
    pop_in.start(0, 0, cell_center_x=100.0, cell_center_y=100.0, team_key="team1_cell")
    pop_in.update(POPIN_DURATION_MS * 0.95)
    scale_before = pop_in.get_scale(0, 0)
    assert scale_before < 1.0
    pop_in.update(POPIN_DURATION_MS * 0.05)
    scale_after = pop_in.get_scale(0, 0)
    assert scale_after >= 1.0


# --- SparkleBurst tests (7-8) ---

def test_sparkle_burst_emits_particles(
    particle_system: ParticleSystem,
    sparkle: SparkleBurst,
) -> None:
    """SparkleBurst.emit() adds 8–12 particles (sprite_key="sparkle") per AC-5."""
    sparkle.emit(cx=100.0, cy=100.0)
    count = len(particle_system.active_particles)
    assert 8 <= count <= 12
    for p in particle_system.active_particles:
        assert p.sprite_key == "sparkle"
        assert p.lifetime == pytest.approx(SPARKLE_DURATION_MS, abs=0.01)


def test_sparkle_particles_fade(
    particle_system: ParticleSystem,
    sparkle: SparkleBurst,
) -> None:
    """Sparkle particle lifetime decreases after update(300) — alpha fades (AC-5)."""
    sparkle.emit(cx=100.0, cy=100.0)
    initial_lifetimes = [p.lifetime for p in particle_system.active_particles]
    particle_system.update(300.0)
    for i, p in enumerate(particle_system.active_particles):
        assert p.lifetime < initial_lifetimes[i], (
            f"Particle {i}: expected lifetime < {initial_lifetimes[i]}, "
            f"got {p.lifetime}"
        )


# --- ConfettiRain test (9) ---

def test_confetti_rain_particles_fall(
    particle_system: ParticleSystem,
    confetti: ConfettiRain,
) -> None:
    """Confetti particle y-position increases (falls downward) after update (AC-8)."""
    confetti.start()
    initial_ys = [p.y for p in particle_system.active_particles]
    confetti.update(100.0)
    for i, p in enumerate(particle_system.active_particles):
        assert p.y > initial_ys[i], (
            f"Particle {i}: expected y > {initial_ys[i]}, got {p.y}"
        )


# --- WiggleAnimation test (10) ---

def test_wiggle_animation_oscillates(wiggle: WiggleAnimation) -> None:
    """Wiggle offsets at 1000 ms and 2000 ms have opposite signs (AC-6)."""
    wiggle.add_cell(0, 0)
    offset_1 = wiggle.get_offset(0, 0, elapsed_ms=1000.0)
    offset_2 = wiggle.get_offset(0, 0, elapsed_ms=2000.0)
    assert offset_1 * offset_2 < 0, (
        f"Expected opposite-sign offsets, got {offset_1} and {offset_2}"
    )


# --- OccupiedCellWobble test (11) ---

def test_wobble_decays_to_zero(wobble: OccupiedCellWobble) -> None:
    """Wobble offset is non-zero after trigger and trends to ~0 (AC-7)."""
    wobble.trigger(0, 0)
    # After a small time step the decaying oscillation should be non-zero.
    wobble.update(1.0)
    offset_mid = wobble.get_offset(0, 0)
    assert offset_mid != pytest.approx(0.0, abs=0.01), (
        f"Expected non-zero offset after trigger + 1ms, got {offset_mid}"
    )
    # After the full wobble duration the offset should be ~0.
    wobble.update(WOBBLE_DURATION_MS)
    offset_end = wobble.get_offset(0, 0)
    assert offset_end == pytest.approx(0.0, abs=0.01)


# --- LastMoveHighlight test (12) ---

def test_last_move_highlight_tracks(highlight: LastMoveHighlight) -> None:
    """set_last records cell, get_cell returns it; clear() removes it (AC-1)."""
    highlight.set_last(2, 1)
    assert highlight.get_cell() == (2, 1)
    highlight.clear()
    assert highlight.get_cell() is None


# --- WinningTrail test (13) ---

def test_winning_trail_start_initializes(trail: WinningTrail) -> None:
    """WinningTrail.start stores cells; is_active() returns True (AC-9)."""
    cells = [(0, 0), (0, 1), (0, 2)]
    centers = [(100, 100), (100, 220), (100, 340)]
    trail.start(cells, centers)
    assert trail._started is True
    assert trail.is_active() is True