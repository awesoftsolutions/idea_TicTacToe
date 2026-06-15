# tests/test_assets.py
# Sprint 1, Task 5 — POC Sprite Validation Tests
# Verifies: manifest, proof-of-concept sprite, README style guide

import json
import re
from pathlib import Path

import pygame
import pytest  # noqa: F401  # imported for pytest framework availability


# === Manifest Validation ===


def test_manifest_exists() -> None:
    """Verify assets/manifest.json exists and parses as valid JSON dict."""
    manifest_path = Path("assets/manifest.json")

    # Step 1: Assert file exists
    assert manifest_path.exists(), "assets/manifest.json not found"

    # Step 2: Open and parse as JSON
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Step 3: Verify it parsed as a dict (valid JSON)
    assert isinstance(manifest, dict), "assets/manifest.json is not a valid JSON object"


# === Sprite Validation ===


def test_proof_of_concept_sprite_exists() -> None:
    """Verify the sprite file exists at the path listed in the manifest."""
    manifest_path = Path("assets/manifest.json")

    # Step 1: Load manifest
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Step 2: Extract sprite path from manifest
    assert "poc" in manifest_data, "manifest missing 'poc' key"
    sprite_filename = manifest_data["poc"]["file"]

    # Step 3: Build full path (relative to project root)
    sprite_path = Path("assets") / sprite_filename

    # Step 4: Assert file exists
    assert sprite_path.exists(), f"Sprite not found: {sprite_path}"


def test_proof_of_concept_sprite_loadable() -> None:
    """Verify the PNG loads without corruption via pygame.image.load."""
    manifest_path = Path("assets/manifest.json")

    # Step 1: Load manifest to get sprite path
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    sprite_filename = manifest_data["poc"]["file"]
    sprite_path = Path("assets") / sprite_filename

    # Step 2: Load PNG via pygame.image.load
    loaded_surface = pygame.image.load(str(sprite_path))

    # Step 3: Assert surface is valid (non-zero dimensions)
    assert loaded_surface is not None, "pygame.image.load returned None"
    assert loaded_surface.get_width() > 0, "Sprite has zero width (corrupt PNG)"
    assert loaded_surface.get_height() > 0, "Sprite has zero height (corrupt PNG)"


def test_proof_of_concept_has_transparency() -> None:
    """Verify the PNG has an alpha channel via SRCALPHA flag."""
    manifest_path = Path("assets/manifest.json")

    # Step 1: Load manifest and sprite
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    sprite_filename = manifest_data["poc"]["file"]
    sprite_path = Path("assets") / sprite_filename

    # Step 2: Load PNG via pygame.image.load
    loaded_surface = pygame.image.load(str(sprite_path))

    # Step 3: Check for alpha channel using SRCALPHA flag
    has_alpha = (loaded_surface.get_flags() & pygame.SRCALPHA) != 0

    # Step 4: Assert alpha is present
    assert has_alpha, "Sprite does not have alpha channel (SRCALPHA flag not set)"


def test_proof_of_concept_size() -> None:
    """Verify sprite dimensions match manifest entry (120x120)."""
    manifest_path = Path("assets/manifest.json")

    # Step 1: Load manifest
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    expected_width = manifest_data["poc"]["width"]
    expected_height = manifest_data["poc"]["height"]

    # Step 2: Load sprite and get actual dimensions
    sprite_filename = manifest_data["poc"]["file"]
    sprite_path = Path("assets") / sprite_filename
    loaded_surface = pygame.image.load(str(sprite_path))
    actual_width = loaded_surface.get_width()
    actual_height = loaded_surface.get_height()

    # Step 3: Assert dimensions match
    assert actual_width == expected_width, (
        f"Width mismatch: expected {expected_width}, got {actual_width}"
    )
    assert actual_height == expected_height, (
        f"Height mismatch: expected {expected_height}, got {actual_height}"
    )


# === README Validation ===


def test_readme_contains_style_guide() -> None:
    """Verify README.md has a Style Guide section with palette hex codes."""
    readme_path = Path("README.md")

    # Step 1: Assert README exists
    assert readme_path.exists(), "README.md not found"

    # Step 2: Read entire file content as text
    readme_content = readme_path.read_text(encoding="utf-8")

    # Step 3: Assert Style Guide heading exists
    assert "## Style Guide" in readme_content, (
        "README missing '## Style Guide' section"
    )

    # Step 4: Assert at least one palette hex code exists via regex
    hex_pattern = r"#[0-9A-Fa-f]{6}"
    hex_matches = re.findall(hex_pattern, readme_content)
    assert len(hex_matches) >= 1, (
        "README Style Guide section missing palette hex codes"
    )

    # Step 5: Verify the Chunky Kawaii outline color is present
    assert "#5A4A5C" in readme_content, (
        "README missing outline color #5A4A5C"
    )


def test_readme_lists_rejected_alternatives() -> None:
    """Verify README.md documents at least one rejected alternative style."""
    readme_path = Path("README.md")

    # Step 1: Read README
    readme_content = readme_path.read_text(encoding="utf-8")

    # Step 2: Assert presence of rejected alternatives heading
    assert "### Rejected Alternatives" in readme_content, (
        "README missing 'Rejected Alternatives' section"
    )

    # Step 3: Assert at least one "Rejected:" prefix in subheadings
    assert "Rejected:" in readme_content, (
        "README missing any 'Rejected:' alternative entries"
    )