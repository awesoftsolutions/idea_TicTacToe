#!/usr/bin/env python3
"""Reproducible asset generation pipeline -- proof-of-concept sprite + manifest.

Generates one transparent PNG sprite (5-point star) and writes assets/manifest.json.
Idempotent: same output on every run.

Usage: python tools/generate_assets.py
"""

import json
import math
from pathlib import Path

SPRITES_DIR = Path("assets/sprites")
MANIFEST_PATH = Path("assets/manifest.json")
SPRITE_SIZE = 120  # 120x120 pixels, matching CELL_SIZE from architecture


def star_points(
    cx: float, cy: float, outer_r: float, inner_r: float, points: int = 5
) -> list[tuple[float, float]]:
    """Generate vertices of a regular star polygon centered at (cx, cy)."""
    coords: list[tuple[float, float]] = []
    for i in range(points * 2):
        angle = math.pi / 2 + math.pi * i / points  # start from top
        r = outer_r if i % 2 == 0 else inner_r
        coords.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    return coords


def generate_poc_sprite() -> None:
    """Generate the proof-of-concept star sprite using PIL/Pillow."""
    from PIL import Image, ImageDraw

    SPRITES_DIR.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (SPRITE_SIZE, SPRITE_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Compute star polygon -- 5-point star, golden ratio proportions
    cx, cy = SPRITE_SIZE / 2, SPRITE_SIZE / 2
    outer_r = SPRITE_SIZE * 0.42
    inner_r = outer_r * 0.382  # golden ratio inverse
    points = star_points(cx, cy, outer_r, inner_r, 5)

    # Star fill color: warm gold (RGBA)
    fill_color = (255, 215, 0, 255)  # gold, fully opaque
    draw.polygon(points, fill=fill_color, outline=(255, 180, 0, 255))

    # Inner highlight: smaller star in lighter gold
    inner_points = star_points(cx, cy, outer_r * 0.4, inner_r * 0.4, 5)
    draw.polygon(inner_points, fill=(255, 240, 150, 200))

    sprite_path = SPRITES_DIR / "poc.png"
    img.save(str(sprite_path), "PNG")
    print(f"[OK] Generated {sprite_path} ({SPRITE_SIZE}x{SPRITE_SIZE} RGBA)")


def write_manifest() -> None:
    """Write assets/manifest.json with the poc sprite entry."""
    manifest = {
        "poc": {
            "key": "poc",
            "file": "sprites/poc.png",
            "prompt": (
                "5-point gold star on transparent background, "
                "star shape drawn with golden-ratio polygon, "
                "inner highlight in lighter gold"
            ),
            "width": SPRITE_SIZE,
            "height": SPRITE_SIZE,
        }
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"[OK] Wrote {MANIFEST_PATH}")


def main() -> None:
    """Run the generation pipeline: sprite then manifest."""
    print("=== Favur Tic-Tac-Toe: Asset Generation Pipeline ===")
    generate_poc_sprite()
    write_manifest()
    print("[DONE] Generation complete.")


if __name__ == "__main__":
    main()