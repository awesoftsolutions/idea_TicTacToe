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
    assert (
        actual_width == expected_width
    ), f"Width mismatch: expected {expected_width}, got {actual_width}"
    assert (
        actual_height == expected_height
    ), f"Height mismatch: expected {expected_height}, got {actual_height}"


# === README Validation ===


def test_readme_contains_style_guide() -> None:
    """Verify README.md has a Style Guide section with palette hex codes."""
    readme_path = Path("README.md")

    # Step 1: Assert README exists
    assert readme_path.exists(), "README.md not found"

    # Step 2: Read entire file content as text
    readme_content = readme_path.read_text(encoding="utf-8")

    # Step 3: Assert Style Guide heading exists
    assert "## Style Guide" in readme_content, "README missing '## Style Guide' section"

    # Step 4: Assert at least one palette hex code exists via regex
    hex_pattern = r"#[0-9A-Fa-f]{6}"
    hex_matches = re.findall(hex_pattern, readme_content)
    assert len(hex_matches) >= 1, "README Style Guide section missing palette hex codes"

    # Step 5: Verify the Chunky Kawaii outline color is present
    assert "#5A4A5C" in readme_content, "README missing outline color #5A4A5C"


def test_readme_lists_rejected_alternatives() -> None:
    """Verify README.md documents at least one rejected alternative style."""
    readme_path = Path("README.md")

    # Step 1: Read README
    readme_content = readme_path.read_text(encoding="utf-8")

    # Step 2: Assert presence of rejected alternatives heading
    assert (
        "### Rejected Alternatives" in readme_content
    ), "README missing 'Rejected Alternatives' section"

    # Step 3: Assert at least one "Rejected:" prefix in subheadings
    assert (
        "Rejected:" in readme_content
    ), "README missing any 'Rejected:' alternative entries"


# === AssetManager Tests ===
# Sprint 3, Task 3 — TDD red phase (AssetManager not yet implemented)

import tempfile

from src.assets import AssetLoadError, AssetManager, ManifestMissingError

ALL_MANIFEST_KEYS = [
    "team1_cell",
    "team1_wiggle",
    "team1_celebrate",
    "team2_cell",
    "team2_wiggle",
    "team2_celebrate",
    "coach_wave",
    "coach_point",
    "coach_cheer_small",
    "coach_cheer",
    "coach_aww",
    "coach_idle",
    "bg_team_select",
    "bg_game",
    "bg_celebration",
    "sparkle",
    "confetti",
    "heart",
    "star",
    "btn_start",
    "btn_play_again",
    "board_frame",
    "poc",
]


def test_asset_manager_loads_valid_manifest() -> None:
    """Construct AssetManager with valid manifest — no exception expected."""
    manager = AssetManager("assets/manifest.json")
    assert len(manager._sprites) > 0


def test_asset_manager_get_sprite_returns_surface() -> None:
    """get_sprite('team1_cell') returns pygame.Surface with correct dimensions."""
    manager = AssetManager("assets/manifest.json")
    surface = manager.get_sprite("team1_cell")
    assert isinstance(surface, pygame.Surface)
    assert surface.get_width() == 120
    assert surface.get_height() == 120


def test_asset_manager_get_sprite_size_returns_tuple() -> None:
    """get_sprite_size('team1_cell') returns (120, 120)."""
    manager = AssetManager("assets/manifest.json")
    dimensions = manager.get_sprite_size("team1_cell")
    assert dimensions == (120, 120)


def test_asset_manager_raises_on_missing_key() -> None:
    """get_sprite('nonexistent') raises KeyError with key name."""
    manager = AssetManager("assets/manifest.json")
    with pytest.raises(KeyError, match="nonexistent"):
        manager.get_sprite("nonexistent")


def test_asset_manager_raises_on_missing_manifest() -> None:
    """AssetManager with nonexistent path raises ManifestMissingError."""
    with pytest.raises(ManifestMissingError, match="missing.json"):
        AssetManager("assets/missing.json")


def test_asset_manager_raises_on_missing_file() -> None:
    """AssetManager with manifest to missing PNG raises AssetLoadError with key name."""
    manifest_data = {
        "missing_sprite": {
            "key": "missing_sprite",
            "file": "sprites/does_not_exist.png",
            "width": 120,
            "height": 120,
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(manifest_data, f)
        temp_path = f.name
    try:
        with pytest.raises(AssetLoadError) as excinfo:
            AssetManager(temp_path)
        assert "missing_sprite" in str(excinfo.value)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_asset_manager_raises_on_path_traversal() -> None:
    """AssetManager with '..' in file path raises AssetLoadError."""
    manifest_data = {
        "traversal_try": {
            "key": "traversal_try",
            "file": "sprites/../../etc/passwd",
            "width": 120,
            "height": 120,
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(manifest_data, f)
        temp_path = f.name
    try:
        with pytest.raises(AssetLoadError):
            AssetManager(temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_asset_manager_loads_all_23_keys() -> None:
    """AssetManager loads all 23 manifest keys without exception."""
    manager = AssetManager("assets/manifest.json")
    for key in ALL_MANIFEST_KEYS:
        surface = manager.get_sprite(key)
        assert surface is not None
        assert surface.get_width() > 0
        assert surface.get_height() > 0


# Sprint 3, Task 4 — Milestone 3 Asset Test Suite

import hashlib
import shutil
import subprocess


def test_manifest_contains_required_categories() -> None:
    """Verify manifest has entries for all required asset categories
    with minimum counts."""
    manifest_path = Path("assets/manifest.json")
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Category key lists (from src.sprite_config group constants)
    team_keys = [
        "team1_cell",
        "team1_wiggle",
        "team1_celebrate",
        "team2_cell",
        "team2_wiggle",
        "team2_celebrate",
    ]
    coach_keys = [
        "coach_wave",
        "coach_point",
        "coach_cheer_small",
        "coach_cheer",
        "coach_aww",
        "coach_idle",
    ]
    bg_keys = ["bg_team_select", "bg_game", "bg_celebration"]
    effect_keys = ["sparkle", "confetti", "heart", "star"]
    ui_keys = ["btn_start", "btn_play_again", "board_frame"]

    # Count keys present per category
    team_count = sum(1 for k in team_keys if k in manifest_data)
    coach_count = sum(1 for k in coach_keys if k in manifest_data)
    bg_count = sum(1 for k in bg_keys if k in manifest_data)
    effect_count = sum(1 for k in effect_keys if k in manifest_data)
    ui_count = sum(1 for k in ui_keys if k in manifest_data)

    # Assert each category meets minimum counts
    assert team_count >= 6, f"Expected >=6 team entries, got {team_count}"
    assert coach_count >= 6, f"Expected >=6 coach entries, got {coach_count}"
    assert bg_count >= 3, f"Expected >=3 background entries, got {bg_count}"
    assert effect_count >= 4, f"Expected >=4 effect entries, got {effect_count}"
    assert ui_count >= 3, f"Expected >=3 UI entries, got {ui_count}"

    # Assert total entry count >= 23
    total_count = len(manifest_data)
    assert total_count >= 23, f"Expected >=23 manifest entries, got {total_count}"


def test_manifest_keys_unique() -> None:
    """Verify no duplicate keys exist in the manifest."""
    manifest_path = Path("assets/manifest.json")
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    all_keys = list(manifest_data.keys())
    unique_keys = set(all_keys)

    assert len(all_keys) == len(
        unique_keys
    ), f"Found {len(all_keys) - len(unique_keys)} duplicate keys in manifest"


def test_manifest_files_exist() -> None:
    """For every manifest entry, verify the sprite file exists at the resolved path."""
    manifest_path = Path("assets/manifest.json")
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert len(manifest_data) > 0, "Manifest is empty"

    for key, entry in manifest_data.items():
        file_path_str = entry["file"]
        full_path = Path("assets") / file_path_str
        assert full_path.exists(), f"File not found for key '{key}': {full_path}"


def test_manifest_files_loadable() -> None:
    """For every manifest entry, verify the sprite file loads as
    a valid pygame Surface."""
    manifest_path = Path("assets/manifest.json")
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    for key, entry in manifest_data.items():
        full_path = Path("assets") / entry["file"]
        surface = pygame.image.load(str(full_path))
        assert surface is not None, f"pygame.image.load returned None for '{key}'"
        assert surface.get_width() > 0, f"Zero width for '{key}'"
        assert surface.get_height() > 0, f"Zero height for '{key}'"


def test_manifest_dimensions_match() -> None:
    """For every manifest entry, verify loaded sprite dimensions
    match manifest entry values."""
    manifest_path = Path("assets/manifest.json")
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    for key, entry in manifest_data.items():
        expected_width = entry["width"]
        expected_height = entry["height"]

        full_path = Path("assets") / entry["file"]
        surface = pygame.image.load(str(full_path))

        actual_width = surface.get_width()
        actual_height = surface.get_height()

        assert (
            actual_width == expected_width
        ), f"Width mismatch for '{key}': expected {expected_width}, got {actual_width}"
        assert actual_height == expected_height, (
            f"Height mismatch for '{key}':"
            f" expected {expected_height}, got {actual_height}"
        )


def test_asset_manager_raises_on_missing_file_e2e() -> None:
    """Verify AssetManager raises AssetLoadError when a real sprite
    file is temporarily renamed."""
    manifest_path = Path("assets/manifest.json")
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    victim_key = "sparkle"
    assert victim_key in manifest_data, f"'{victim_key}' not in manifest"

    victim_file_rel = manifest_data[victim_key]["file"]
    victim_file = Path("assets") / victim_file_rel
    assert victim_file.exists(), f"Victim file not found: {victim_file}"

    backup_file = victim_file.with_suffix(".backup.png")

    # Temporarily rename the sprite file
    shutil.move(str(victim_file), str(backup_file))
    assert not victim_file.exists(), "Victim file still exists after rename"

    try:
        with pytest.raises(AssetLoadError) as excinfo:
            AssetManager("assets/manifest.json")
        assert victim_key in str(excinfo.value), (
            f"AssetLoadError message missing key" f" '{victim_key}': {excinfo.value}"
        )
    finally:
        # Restore the renamed file
        if backup_file.exists():
            shutil.move(str(backup_file), str(victim_file))
            assert victim_file.exists(), "Failed to restore victim file in cleanup"


def test_generate_assets_reproducible() -> None:
    """Verify two pipeline runs produce identical SHA-256 hashes
    for all sprite files."""
    sprites_dir = Path("assets/sprites")

    # Compute baseline hashes from current sprite files
    sprite_files = sorted(sprites_dir.glob("*.png"))
    assert len(sprite_files) >= 23, "Expected >=23 sprite files before regeneration"

    baseline_hashes = []
    for file in sprite_files:
        h = hashlib.sha256(file.read_bytes()).hexdigest()
        baseline_hashes.append(h)

    # Run the generation pipeline (first regeneration)
    try:
        result1 = subprocess.run(
            ["poetry", "run", "python", "tools/generate_assets.py"],
            capture_output=True,
            timeout=60,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback if "poetry" approach fails
        result1 = subprocess.run(
            ["python", "tools/generate_assets.py"],
            capture_output=True,
            timeout=60,
            check=True,
        )

    assert result1.returncode == 0, "Generation pipeline failed (run 1)"

    # Compute hashes after first regeneration
    sprite_files_after = sorted(sprites_dir.glob("*.png"))
    assert (
        len(sprite_files_after) >= 23
    ), "Expected >=23 sprite files after regeneration (run 1)"

    run1_hashes = []
    for file in sprite_files_after:
        h = hashlib.sha256(file.read_bytes()).hexdigest()
        run1_hashes.append(h)

    # Run the generation pipeline (second regeneration)
    try:
        result2 = subprocess.run(
            ["poetry", "run", "python", "tools/generate_assets.py"],
            capture_output=True,
            timeout=60,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        result2 = subprocess.run(
            ["python", "tools/generate_assets.py"],
            capture_output=True,
            timeout=60,
            check=True,
        )

    assert result2.returncode == 0, "Generation pipeline failed (run 2)"

    # Compute hashes after second regeneration
    sprite_files_after2 = sorted(sprites_dir.glob("*.png"))
    run2_hashes = []
    for file in sprite_files_after2:
        h = hashlib.sha256(file.read_bytes()).hexdigest()
        run2_hashes.append(h)

    # Assert hashes are identical between the two runs
    assert run1_hashes == run2_hashes, (
        "Sprite file hashes differ between runs 1 and 2"
        " \u2014 generation is not reproducible"
    )
