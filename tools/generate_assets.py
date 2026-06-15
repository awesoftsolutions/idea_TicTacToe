#!/usr/bin/env python3
"""Reproducible asset generation pipeline — 22 Chunky Kawaii sprites + manifest.

Generates all character, background, effect, and UI chrome sprites using
PIL/Pillow geometric primitives following the Chunky Kawaii style guide:
    - 4px #5A4A5C outlines on every sprite
    - 7-color soft pastel palette from sprite_config
    - 60% head-to-body ratio for characters
    - Round shapes only (circles, ellipses, rounded rects)

Idempotent: running twice produces identical PNG file hashes.

Usage:
    python tools/generate_assets.py
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

from src.sprite_config import (
    BACKGROUND_KEYS,
    COACH_KEYS,
    EFFECT_KEYS,
    OUTLINE_COLOR,
    OUTLINE_WIDTH,
    PALETTE,
    SPRITE_SPECS,
    TEAM_KEYS,
    UI_KEYS,
    SCENE_COLORS,
)

# ── Paths ───────────────────────────────────────────────────────────────────

SPRITES_DIR = Path("assets/sprites")
MANIFEST_PATH = Path("assets/manifest.json")
SEED = 42  # deterministic seed for idempotency

# ── Geometry Helpers ────────────────────────────────────────────────────────


def star_points(
    cx: float, cy: float, outer_r: float, inner_r: float, points: int = 5
) -> list[tuple[float, float]]:
    """Generate vertices of a regular star polygon centered at (cx, cy).

    Args:
        cx: Center X coordinate of the star.
        cy: Center Y coordinate of the star.
        outer_r: Outer radius from center to star tips.
        inner_r: Inner radius from center to star valleys.
        points: Number of star points (default 5).

    Returns:
        list[tuple[float, float]]: List of (x, y) vertex coordinates,
        alternating between outer and inner radius.
    """
    coords: list[tuple[float, float]] = []
    for i in range(points * 2):
        angle = math.pi / 2 + math.pi * i / points
        r = outer_r if i % 2 == 0 else inner_r
        coords.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    return coords


def _rgba(color_name: str, alpha: int = 255) -> tuple[int, int, int, int]:
    """Get RGBA tuple from palette by color name, with optional alpha override."""
    r, g, b, _ = PALETTE[color_name]
    return (r, g, b, alpha)


def _lerp_color(
    c1: tuple[int, int, int, int],
    c2: tuple[int, int, int, int],
    t: float,
) -> tuple[int, int, int, int]:
    """Linearly interpolate between two RGBA colors."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
        255,
    )


# ── Drawing Primitives (Chunky Kawaii Style) ───────────────────────────────


def draw_rounded_rect(
    draw: object,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
    width: int = 0,
) -> None:
    """Draw a rounded rectangle."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_oval_eyes(
    draw: object,
    cx: int,
    cy: int,
    eye_w: int,
    eye_h: int,
    spacing: int,
    pupil_color: tuple[int, int, int, int] = (60, 50, 64, 255),
    eye_white: tuple[int, int, int, int] = (255, 255, 255, 255),
) -> None:
    """Draw two large oval eyes — kawaii style, 60%+ of face width."""
    draw.ellipse(
        [cx - spacing - eye_w, cy - eye_h, cx - spacing, cy + eye_h],
        fill=eye_white,
        outline=OUTLINE_COLOR,
        width=OUTLINE_WIDTH,
    )
    draw.ellipse(
        [cx + spacing, cy - eye_h, cx + spacing + eye_w, cy + eye_h],
        fill=eye_white,
        outline=OUTLINE_COLOR,
        width=OUTLINE_WIDTH,
    )
    pupil_r = max(eye_w // 4, 2)
    draw.ellipse(
        [cx - spacing - eye_w // 2 - pupil_r, cy - pupil_r,
         cx - spacing - eye_w // 2 + pupil_r, cy + pupil_r],
        fill=pupil_color,
    )
    draw.ellipse(
        [cx + spacing + eye_w // 2 - pupil_r, cy - pupil_r,
         cx + spacing + eye_w // 2 + pupil_r, cy + pupil_r],
        fill=pupil_color,
    )


def draw_crescent_mouth(
    draw: object,
    cx: int,
    cy: int,
    width: int,
    happy: bool = True,
) -> None:
    """Draw a crescent-shaped mouth."""
    half = width // 2
    if happy:
        draw.arc(
            [cx - half, cy - half, cx + half, cy + half],
            start=0, end=180,
            fill=OUTLINE_COLOR,
            width=OUTLINE_WIDTH,
        )
    else:
        draw.arc(
            [cx - half // 2, cy - half // 2, cx + half // 2, cy + half // 2],
            start=180, end=360,
            fill=OUTLINE_COLOR,
            width=OUTLINE_WIDTH,
        )


def draw_dot_nose(
    draw: object,
    cx: int,
    cy: int,
    r: int = 4,
    color: tuple[int, int, int, int] | None = None,
) -> None:
    """Draw a small dot nose."""
    if color is None:
        color = (60, 50, 64, 255)
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        fill=color, outline=None,
    )


def draw_blush(
    draw: object,
    cx: int,
    cy: int,
    r: int = 6,
    color: tuple[int, int, int, int] | None = None,
) -> None:
    """Draw kawaii blush circles on cheeks."""
    if color is None:
        color = _rgba("primary_pink", 160)
    draw.ellipse(
        [cx - 16 - r, cy + 2, cx - 16 + r, cy + 2 + r * 2],
        fill=color, outline=None,
    )
    draw.ellipse(
        [cx + 16 - r, cy + 2, cx + 16 + r, cy + 2 + r * 2],
        fill=color, outline=None,
    )


def draw_character_base(
    draw: object,
    cx: int,
    cy: int,
    head_r: int,
    body_rx: int,
    body_ry: int,
    body_cy_offset: int,
    fill: tuple[int, int, int, int],
    ear_type: str = "kitten",
    ear_offset: int = 0,
) -> None:
    """Draw base character body (body + ears + head layered).

    ear_type: 'kitten'=pointy triangles, 'puppy'=floppy ovals, 'coach'=round.
    """
    body_cy = cy + body_cy_offset

    # Body behind head
    draw.ellipse(
        [cx - body_rx, body_cy - body_ry, cx + body_rx, body_cy + body_ry],
        fill=fill,
        outline=OUTLINE_COLOR,
        width=OUTLINE_WIDTH,
    )

    if ear_type == "kitten":
        ear_top_y = cy - head_r - 2
        ear_base_y = cy - head_r + 8 + ear_offset
        # Left ear
        draw.polygon(
            [
                (cx - head_r + 4, ear_base_y),
                (cx - head_r - 6 + ear_offset, ear_top_y - 4),
                (cx - head_r + 4 + ear_offset, ear_base_y),
            ],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        # Inner ear pink
        draw.polygon(
            [
                (cx - head_r + 8, ear_base_y - 2),
                (cx - head_r - 2 + ear_offset, ear_top_y),
                (cx - head_r + 8 + ear_offset, ear_base_y - 2),
            ],
            fill=_rgba("primary_pink", 180),
        )
        # Right ear
        draw.polygon(
            [
                (cx + head_r - 4 - ear_offset, ear_base_y),
                (cx + head_r + 6 - ear_offset, ear_top_y - 4),
                (cx + head_r - 4, ear_base_y),
            ],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        draw.polygon(
            [
                (cx + head_r - 8 - ear_offset, ear_base_y - 2),
                (cx + head_r + 2 - ear_offset, ear_top_y),
                (cx + head_r - 8, ear_base_y - 2),
            ],
            fill=_rgba("primary_pink", 180),
        )
    elif ear_type == "puppy":
        ear_extra_y = ear_offset * 2
        draw.ellipse(
            [cx - head_r - 14, cy - head_r + 4 + ear_extra_y,
             cx - head_r - 2, cy - head_r + 22 + ear_extra_y],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        draw.ellipse(
            [cx + head_r + 2, cy - head_r + 4 + ear_extra_y,
             cx + head_r + 14, cy - head_r + 22 + ear_extra_y],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
    elif ear_type == "coach":
        ear_r = head_r // 3
        draw.ellipse(
            [cx - head_r + 2, cy - head_r - ear_r - 2 + ear_offset,
             cx - head_r + 2 + ear_r * 2, cy - head_r + ear_r - 2 + ear_offset],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        draw.ellipse(
            [cx - head_r + 5, cy - head_r - ear_r + 2 + ear_offset,
             cx - head_r + 5 + ear_r, cy - head_r + 2 + ear_offset],
            fill=_rgba("peach", 180),
        )
        draw.ellipse(
            [cx + head_r - 2 - ear_r * 2, cy - head_r - ear_r - 2 + ear_offset,
             cx + head_r - 2, cy - head_r + ear_r - 2 + ear_offset],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        draw.ellipse(
            [cx + head_r - 5 - ear_r, cy - head_r - ear_r + 2 + ear_offset,
             cx + head_r - 5, cy - head_r + 2 + ear_offset],
            fill=_rgba("peach", 180),
        )

    # Head on top
    draw.ellipse(
        [cx - head_r, cy - head_r, cx + head_r, cy + head_r],
        fill=fill,
        outline=OUTLINE_COLOR,
        width=OUTLINE_WIDTH,
    )


def draw_paws_up(
    draw: object,
    cx: int,
    cy: int,
    head_r: int,
    fill: tuple[int, int, int, int],
    paws_extra: int = 0,
) -> None:
    """Draw two paw nubbins raised above the head (celebrate pose)."""
    paw_r = max(head_r // 4, 6)
    offset_y = -head_r - 8 + paws_extra
    draw.ellipse(
        [cx - head_r // 2 - paw_r, cy + offset_y - paw_r,
         cx - head_r // 2 + paw_r, cy + offset_y + paw_r],
        fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
    )
    draw.ellipse(
        [cx + head_r // 2 - paw_r, cy + offset_y - paw_r,
         cx + head_r // 2 + paw_r, cy + offset_y + paw_r],
        fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
    )


def draw_paw_side(
    draw: object,
    cx: int,
    cy: int,
    head_r: int,
    fill: tuple[int, int, int, int],
    side: str = "left",
    wave_offset: int = 0,
) -> None:
    """Draw a single paw nubbin at side or raised (wave)."""
    paw_r = max(head_r // 4, 6)
    if side == "left":
        px = cx - head_r - 6 + wave_offset
        py = cy + 6 - abs(wave_offset)
    else:
        px = cx + head_r + 6 - wave_offset
        py = cy + 6 - abs(wave_offset)
    draw.ellipse(
        [px - paw_r, py - paw_r, px + paw_r, py + paw_r],
        fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
    )


def draw_tail(
    draw: object,
    cx: int,
    cy: int,
    body_cy: int,
    body_ry: int,
    fill: tuple[int, int, int, int],
    tail_type: str = "kitten",
    wag_offset: int = 0,
) -> None:
    """Draw a tail at the bottom of the character."""
    tail_base_y = body_cy + body_ry
    if tail_type == "kitten":
        draw.arc(
            [cx + 6 + wag_offset, tail_base_y - 4,
             cx + 18 + wag_offset, tail_base_y + 12],
            start=0, end=120,
            fill=OUTLINE_COLOR,
            width=OUTLINE_WIDTH,
        )
        draw.ellipse(
            [cx + 14 + wag_offset, tail_base_y + 4,
             cx + 22 + wag_offset, tail_base_y + 12],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
    elif tail_type == "puppy":
        tx = cx - 14 + wag_offset
        draw.polygon(
            [
                (tx, tail_base_y - 2),
                (tx - 8, tail_base_y - 10),
                (tx + 4, tail_base_y - 2),
            ],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )


# ── Team Sprite Generator ──────────────────────────────────────────────────


def _draw_team_face(
    draw: object,
    cx: int,
    cy: int,
    head_r: int,
    wide_eyes: bool = False,
    big_mouth: bool = False,
) -> None:
    """Draw face features for team characters (kittens/puppies)."""
    eye_w = 16 if wide_eyes else 12
    eye_h = 11 if wide_eyes else 8
    spacing = 8
    eye_cy = cy - 2
    draw_oval_eyes(draw, cx, eye_cy, eye_w, eye_h, spacing)
    draw_dot_nose(draw, cx, cy + 6, r=3)
    mouth_w = 14 if big_mouth else 10
    draw_crescent_mouth(draw, cx, cy + 12, mouth_w, happy=True)
    draw_blush(draw, cx, cy + 4, r=5)


def generate_team_sprite(
    key: str,
    team_num: int,
    variant: str,
) -> None:
    """Generate one team character sprite (kitten or puppy).

    Args:
        key: Sprite key (e.g. 'team1_cell')
        team_num: 1 (kitten, pink) or 2 (puppy, mint)
        variant: 'cell' (sitting), 'wiggle', 'celebrate'
    """
    spec = SPRITE_SPECS[key]
    w = int(spec["width"])
    h = int(spec["height"])
    base_color_name = str(spec["base_color"])
    fill = _rgba(base_color_name)

    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = w // 2, 48
    head_r = 34
    ear_offset = 0
    tail_wag = 0
    paws_up = False
    wide_eyes = False
    big_mouth = False

    ear_type = "kitten" if team_num == 1 else "puppy"
    tail_type = "kitten" if team_num == 1 else "puppy"

    if variant == "wiggle":
        ear_offset = 3 if team_num == 1 else 0
        tail_wag = 4 if team_num == 2 else 0
    elif variant == "celebrate":
        paws_up = True
        wide_eyes = True
        big_mouth = True

    draw_character_base(
        draw, cx, cy, head_r,
        body_rx=22, body_ry=26, body_cy_offset=38,
        fill=fill, ear_type=ear_type, ear_offset=ear_offset,
    )

    draw_tail(draw, cx, cy, cy + 38, 26, fill,
              tail_type=tail_type, wag_offset=tail_wag)

    if paws_up:
        draw_paws_up(draw, cx, cy, head_r, fill, paws_extra=4)

    _draw_team_face(draw, cx, cy, head_r,
                    wide_eyes=wide_eyes, big_mouth=big_mouth)

    _save_sprite(img, key)


# ── Coach Sprite Generator ─────────────────────────────────────────────────


def _draw_coach_face(
    draw: object,
    cx: int,
    cy: int,
    head_r: int,
    expression: str,
) -> None:
    """Draw Coach face features for the given expression."""
    eye_w = 16
    eye_h = 10
    spacing = 12
    eye_cy = cy - 4

    if expression == "wave":
        draw_oval_eyes(draw, cx, eye_cy, eye_w, eye_h, spacing)
        draw_dot_nose(draw, cx, cy + 10, r=4)
        draw_crescent_mouth(draw, cx, cy + 18, 16, happy=True)
        draw_blush(draw, cx, cy + 8, r=7)
    elif expression == "point":
        draw.ellipse(
            [cx - spacing - eye_w, eye_cy - eye_h,
             cx - spacing, eye_cy + eye_h],
            fill=(255, 255, 255, 255),
            outline=OUTLINE_COLOR,
            width=OUTLINE_WIDTH,
        )
        draw.arc(
            [cx + spacing, eye_cy - eye_h, cx + spacing + eye_w, eye_cy + eye_h],
            start=0, end=180,
            fill=OUTLINE_COLOR,
            width=OUTLINE_WIDTH,
        )
        draw_dot_nose(draw, cx, cy + 10, r=4)
        draw.ellipse(
            [cx - 5, cy + 16, cx + 5, cy + 22],
            fill=(255, 255, 255, 255),
            outline=OUTLINE_COLOR,
            width=OUTLINE_WIDTH,
        )
    elif expression == "cheer_small":
        draw_oval_eyes(draw, cx, eye_cy, 14, 9, spacing)
        draw_dot_nose(draw, cx, cy + 10, r=3)
        draw_crescent_mouth(draw, cx, cy + 18, 12, happy=True)
        draw_blush(draw, cx, cy + 8, r=6)
    elif expression == "cheer":
        draw_oval_eyes(draw, cx, eye_cy, 18, 12, spacing)
        draw_dot_nose(draw, cx, cy + 10, r=4)
        draw_crescent_mouth(draw, cx, cy + 18, 20, happy=True)
        draw_blush(draw, cx, cy + 8, r=8)
    elif expression == "aww":
        draw_oval_eyes(draw, cx, eye_cy + 2, 14, 9, spacing)
        draw_dot_nose(draw, cx, cy + 12, r=3)
        draw.arc(
            [cx - 6, cy + 16, cx + 6, cy + 22],
            start=180, end=360,
            fill=OUTLINE_COLOR,
            width=OUTLINE_WIDTH,
        )
    elif expression == "idle":
        draw_oval_eyes(draw, cx, eye_cy, 15, 10, spacing)
        draw_dot_nose(draw, cx, cy + 10, r=4)
        draw_crescent_mouth(draw, cx, cy + 18, 10, happy=True)


def generate_coach_sprite(key: str, expression: str) -> None:
    """Generate one Coach expression sprite (200x200)."""
    spec = SPRITE_SPECS[key]
    w = int(spec["width"])
    h = int(spec["height"])
    fill = _rgba("lavender")

    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = w // 2, 80
    head_r = 55
    ear_offset = 0
    paw_raise = None
    paw_offset = 0

    if expression == "wave":
        paw_raise = "left"
        paw_offset = -10
    elif expression == "point":
        paw_raise = "right"
        paw_offset = -6
    elif expression == "cheer_small":
        paw_raise = "left"
        paw_offset = -4
    elif expression == "cheer":
        paw_raise = "both"
        paw_offset = -12
    elif expression == "aww":
        ear_offset = 2

    draw_character_base(
        draw, cx, cy, head_r,
        body_rx=35, body_ry=40, body_cy_offset=58,
        fill=fill, ear_type="coach", ear_offset=ear_offset,
    )

    if paw_raise == "both":
        draw_paws_up(draw, cx, cy, head_r, fill, paws_extra=8)
    elif paw_raise == "left":
        draw_paw_side(draw, cx, cy, head_r, fill,
                      side="left", wave_offset=paw_offset)
    elif paw_raise == "right":
        draw_paw_side(draw, cx, cy, head_r, fill,
                      side="right", wave_offset=paw_offset)

    _draw_coach_face(draw, cx, cy, head_r, expression)

    _save_sprite(img, key)


# ── Background Sprite Generator ────────────────────────────────────────────


def generate_background_sprite(key: str, scene: str) -> None:
    """Generate one background sprite (960x720)."""
    spec = SPRITE_SPECS[key]
    w = int(spec["width"])
    h = int(spec["height"])

    scene_colors = SCENE_COLORS[scene]
    top_color = _rgba(scene_colors[0])
    mid_color = _rgba(scene_colors[1])
    bot_color = _rgba(scene_colors[2])

    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    band_h = h // 3
    for i in range(band_h * 2):
        t = i / (band_h * 2)
        c = _lerp_color(top_color, mid_color, t)
        draw.line([(0, i), (w, i)], fill=c, width=1)
    for i in range(band_h * 2, h):
        t = (i - band_h * 2) / (h - band_h * 2)
        c = _lerp_color(mid_color, bot_color, t)
        draw.line([(0, i), (w, i)], fill=c, width=1)

    rng = random.Random(SEED + (1 if scene == "team_select" else 2 if scene == "game" else 3))

    if scene == "team_select":
        for _ in range(8):
            sx = rng.randint(40, w - 40)
            sy = rng.randint(40, h - 40)
            sr = rng.randint(10, 25)
            sc = _rgba(rng.choice(scene_colors), 100)
            draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                         fill=sc, outline=None)
        draw.rounded_rectangle(
            [0, h - 80, w, h],
            radius=20, fill=top_color,
            outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
    elif scene == "game":
        draw.rounded_rectangle(
            [0, h - 100, w, h],
            radius=30, fill=_rgba("mint_accent", 200),
            outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        for _ in range(6):
            sx = rng.randint(50, w - 50)
            sy = rng.randint(30, h - 200)
            sr = rng.randint(15, 30)
            sc = _rgba("peach", 80)
            draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                         fill=sc, outline=None)
    elif scene == "celebration":
        for _ in range(12):
            sx = rng.randint(30, w - 30)
            sy = rng.randint(30, h - 30)
            pts = star_points(sx, sy, 8, 3, 4)
            sc = _rgba("butter", 180)
            draw.polygon(pts, fill=sc, outline=OUTLINE_COLOR, width=2)
        draw.rounded_rectangle(
            [0, h - 60, w, h],
            radius=15, fill=_rgba("lavender", 150),
            outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )

    _save_sprite(img, key)


# ── Effect Sprite Generator ────────────────────────────────────────────────


def generate_effect_sprite(key: str, effect_type: str) -> None:
    """Generate one effect particle sprite."""
    spec = SPRITE_SPECS[key]
    w = int(spec["width"])
    h = int(spec["height"])
    base_color_name = str(spec["base_color"])
    fill = _rgba(base_color_name)

    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    if effect_type == "sparkle":
        pts = star_points(cx, cy, w * 0.4, h * 0.12, 4)
        draw.polygon(pts, fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH)
        draw.ellipse(
            [cx - 4, cy - 4, cx + 4, cy + 4],
            fill=_rgba("butter", 200),
        )
    elif effect_type == "confetti":
        draw_rounded_rect(
            draw, (2, 2, w - 2, h - 2),
            radius=4, fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
    elif effect_type == "heart":
        cr = w // 5
        draw.ellipse(
            [cx - cr * 2, cy - cr, cx, cy + cr],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        draw.ellipse(
            [cx, cy - cr, cx + cr * 2, cy + cr],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        draw.polygon(
            [
                (cx - cr * 2, cy + cr // 2),
                (cx, cy + cr * 3),
                (cx + cr * 2, cy + cr // 2),
            ],
            fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
    elif effect_type == "star":
        pts = star_points(cx, cy, w * 0.4, w * 0.16, 5)
        draw.polygon(pts, fill=fill, outline=OUTLINE_COLOR, width=OUTLINE_WIDTH)

    _save_sprite(img, key)


# ── UI Chrome Sprite Generator ─────────────────────────────────────────────


def generate_ui_sprite(key: str, ui_type: str) -> None:
    """Generate one UI chrome sprite."""
    spec = SPRITE_SPECS[key]
    w = int(spec["width"])
    h = int(spec["height"])
    base_color_name = str(spec["base_color"])
    fill = _rgba(base_color_name)

    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if ui_type in ("btn_start", "btn_play_again"):
        radius = h // 2
        draw_rounded_rect(
            draw, (0, 0, w, h),
            radius=radius, fill=fill,
            outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        inner_margin = 8
        draw_rounded_rect(
            draw, (inner_margin, inner_margin, w - inner_margin, h - inner_margin),
            radius=radius - 4,
            fill=_rgba(base_color_name, 200),
        )
        highlight = _rgba("butter", 40)
        draw_rounded_rect(
            draw, (inner_margin, inner_margin, w - inner_margin, h // 2),
            radius=radius - 4,
            fill=highlight,
        )
    elif ui_type == "board_frame":
        picket_count = 7
        picket_w = w // (picket_count * 2)
        gap = picket_w // 2
        rail_h = 12
        rail_y = h // 2 - rail_h

        draw_rounded_rect(
            draw, (0, rail_y, w, rail_y + rail_h),
            radius=6, fill=fill,
            outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        draw_rounded_rect(
            draw, (0, rail_y + rail_h + 6, w, rail_y + rail_h * 2 + 6),
            radius=6, fill=fill,
            outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
        )
        picket_top = 4
        picket_bot = h - 4
        for i in range(picket_count):
            px = gap + i * (picket_w + gap * 2)
            draw_rounded_rect(
                draw, (px, picket_top, px + picket_w, picket_bot),
                radius=8, fill=fill,
                outline=OUTLINE_COLOR, width=OUTLINE_WIDTH,
            )
            tip_h = 12
            draw_rounded_rect(
                draw, (px + 2, picket_top, px + picket_w - 2, picket_top + tip_h),
                radius=6, fill=_rgba("butter", 100),
            )

    _save_sprite(img, key)


# ── POC Sprite (Preserved) ─────────────────────────────────────────────────


def generate_poc_sprite() -> None:
    """Generate the proof-of-concept star sprite (preserved)."""
    from PIL import Image, ImageDraw

    SPRITES_DIR.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = 120 / 2, 120 / 2
    outer_r = 120 * 0.42
    inner_r = outer_r * 0.382
    points = star_points(cx, cy, outer_r, inner_r, 5)

    fill_color = (255, 215, 0, 255)
    draw.polygon(points, fill=fill_color, outline=(255, 180, 0, 255))

    inner_points = star_points(cx, cy, outer_r * 0.4, inner_r * 0.4, 5)
    draw.polygon(inner_points, fill=(255, 240, 150, 200))

    sprite_path = SPRITES_DIR / "poc.png"
    img.save(str(sprite_path), "PNG")
    print(f"  [OK] Generated {sprite_path} (120x120 RGBA)")


# ── Sprite Save Helper ─────────────────────────────────────────────────────


def _save_sprite(img: object, key: str) -> None:
    """Save a PIL image to assets/sprites/{key}.png."""
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)
    spec = SPRITE_SPECS[key]
    w = int(spec["width"])
    h = int(spec["height"])
    sprite_path = SPRITES_DIR / f"{key}.png"
    img.save(str(sprite_path), "PNG")
    print(f"  [OK] Generated {sprite_path} ({w}x{h} RGBA)")


def _generate_sprite_for_key(key: str) -> None:
    """Route a sprite key to its appropriate generator function."""
    if key in TEAM_KEYS:
        team_num = 1 if key.startswith("team1") else 2
        if "_cell" in key:
            variant = "cell"
        elif "_wiggle" in key:
            variant = "wiggle"
        elif "_celebrate" in key:
            variant = "celebrate"
        else:
            variant = "cell"
        generate_team_sprite(key, team_num, variant)
    elif key in COACH_KEYS:
        expression = key.replace("coach_", "")
        generate_coach_sprite(key, expression)
    elif key in BACKGROUND_KEYS:
        scene = key.replace("bg_", "")
        generate_background_sprite(key, scene)
    elif key in EFFECT_KEYS:
        generate_effect_sprite(key, key)
    elif key in UI_KEYS:
        generate_ui_sprite(key, key)
    else:
        print(f"  [SKIP] Unknown key: {key}")


# ── Manifest Writer ────────────────────────────────────────────────────────


def write_manifest() -> None:
    """Write assets/manifest.json with entries for all generated sprites."""
    manifest: dict[str, dict] = {}

    prompts: dict[str, str] = {
        "team1_cell": (
            "Chunky Kawaii kitten sprite, round pink head, pointy ears, "
            "4px outline, sitting pose on transparent background"
        ),
        "team1_wiggle": (
            "Chunky Kawaii kitten sprite, round pink head, pointy ears "
            "slightly tilted, ear wiggle animation frame, 4px outline"
        ),
        "team1_celebrate": (
            "Chunky Kawaii kitten sprite, paws raised in celebration, "
            "wide happy eyes, big smile, 4px outline"
        ),
        "team2_cell": (
            "Chunky Kawaii puppy sprite, round mint head, floppy ears, "
            "4px outline, sitting pose on transparent background"
        ),
        "team2_wiggle": (
            "Chunky Kawaii puppy sprite, round mint head, tail wagging, "
            "4px outline, idle animation frame"
        ),
        "team2_celebrate": (
            "Chunky Kawaii puppy sprite, excited play-bow pose, "
            "wide eyes, big smile, 4px outline"
        ),
        "coach_wave": (
            "Chunky Kawaii coach critter sprite, lavender base, one paw "
            "raised waving, welcoming expression, 4px outline"
        ),
        "coach_point": (
            "Chunky Kawaii coach critter sprite, lavender base, paw "
            "pointing forward, thinking squinted-eye expression, 4px outline"
        ),
        "coach_cheer_small": (
            "Chunky Kawaii coach critter sprite, lavender base, soft "
            "encouraging smile, slight paw raise, 4px outline"
        ),
        "coach_cheer": (
            "Chunky Kawaii coach critter sprite, lavender base, both paws "
            "raised celebrating, wide eyes, big grin, 4px outline"
        ),
        "coach_aww": (
            "Chunky Kawaii coach critter sprite, lavender base, tilted "
            "head, sympathetic soft eyes, consoling expression, 4px outline"
        ),
        "coach_idle": (
            "Chunky Kawaii coach critter sprite, lavender base, neutral "
            "expression, hands at sides, small smile, 4px outline"
        ),
        "bg_team_select": (
            "Chunky Kawaii team select background, lavender and butter "
            "gradient bands, decorative circles, 960x720"
        ),
        "bg_game": (
            "Chunky Kawaii game scene background, sky blue and mint "
            "gradient bands, grass strip at bottom, 960x720"
        ),
        "bg_celebration": (
            "Chunky Kawaii celebration background, pink and butter "
            "gradient bands, sparkle star accents everywhere, 960x720"
        ),
        "sparkle": (
            "Chunky Kawaii sparkle particle, 4-point star with rounded "
            "tips, periwinkle base, 32x32"
        ),
        "confetti": (
            "Chunky Kawaii confetti particle, rounded rectangle, "
            "butter base, 16x16"
        ),
        "heart": (
            "Chunky Kawaii heart shape, primary pink, two circles "
            "with triangle point, 24x24"
        ),
        "star": (
            "Chunky Kawaii star shape, 5-point star, butter base, 24x24"
        ),
        "btn_start": (
            "Chunky Kawaii pill-shaped start button, periwinkle base, "
            "lighter inner area for text, 200x60"
        ),
        "btn_play_again": (
            "Chunky Kawaii pill-shaped play again button, primary pink "
            "base, lighter inner area for text, 200x60"
        ),
        "board_frame": (
            "Chunky Kawaii garden fence board frame, periwinkle pickets, "
            "two horizontal rails, rounded tops, 440x440"
        ),
    }

    all_keys = TEAM_KEYS + COACH_KEYS + BACKGROUND_KEYS + EFFECT_KEYS + UI_KEYS

    for key in all_keys:
        spec = SPRITE_SPECS[key]
        manifest[key] = {
            "key": key,
            "file": f"sprites/{key}.png",
            "prompt": prompts.get(key, f"Chunky Kawaii sprite: {key}"),
            "width": int(spec["width"]),
            "height": int(spec["height"]),
        }

    # Preserve existing POC entry
    manifest["poc"] = {
        "key": "poc",
        "file": "sprites/poc.png",
        "prompt": (
            "5-point gold star on transparent background, "
            "star shape drawn with golden-ratio polygon, "
            "inner highlight in lighter gold"
        ),
        "width": 120,
        "height": 120,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"[OK] Wrote {MANIFEST_PATH} ({len(manifest)} entries)")


# ── Main Pipeline ──────────────────────────────────────────────────────────


def _file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    """Run the full generation pipeline: all sprites then manifest."""
    print("=== Favur Tic-Tac-Toe: Asset Generation Pipeline ===")
    print(f"[..] Generating {len(TEAM_KEYS)} team sprites...")
    for key in TEAM_KEYS:
        _generate_sprite_for_key(key)

    print(f"[..] Generating {len(COACH_KEYS)} coach expression sprites...")
    for key in COACH_KEYS:
        _generate_sprite_for_key(key)

    print(f"[..] Generating {len(BACKGROUND_KEYS)} background sprites...")
    for key in BACKGROUND_KEYS:
        _generate_sprite_for_key(key)

    print(f"[..] Generating {len(EFFECT_KEYS)} effect sprites...")
    for key in EFFECT_KEYS:
        _generate_sprite_for_key(key)

    print(f"[..] Generating {len(UI_KEYS)} UI chrome sprites...")
    for key in UI_KEYS:
        _generate_sprite_for_key(key)

    # Preserved POC sprite
    print("[..] Generating proof-of-concept sprite (preserved)...")
    generate_poc_sprite()

    write_manifest()

    sprite_files = list(SPRITES_DIR.glob("*.png"))
    print(f"[OK] {len(sprite_files)} sprite files in {SPRITES_DIR}/")

    all_hashes: list[str] = []
    for f in sorted(sprite_files):
        all_hashes.append(_file_hash(f))
    combined = hashlib.sha256("".join(all_hashes).encode()).hexdigest()
    print(f"[OK] Run fingerprint: {combined}")
    print("[DONE] Generation complete.")


# CHANGELOG: Sprint 3, Task 2 — Full pipeline: 22 sprites + manifest

if __name__ == "__main__":
    main()