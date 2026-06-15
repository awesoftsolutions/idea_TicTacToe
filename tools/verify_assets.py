#!/usr/bin/env python3
"""End-to-end verification script for the Sprint 3 asset generation pipeline.

Exercises the full pipeline:
  1. Generation pipeline exits 0 and produces 23+ PNGs
  2. Pytest suite exits 0
  3. Manifest JSON structure is valid
  4. AssetManager loads all 23 sprites
  5. Sample from each category returns valid Surface
  6. Unknown key raises KeyError
  7. Missing sprite file raises AssetLoadError naming the key

Every check prints a structured ``[PASS]`` or ``[FAIL]`` line.  The script
exits 0 when all 7 checks pass, 1 otherwise.
"""

from __future__ import annotations

import os

# Set SDL_VIDEODRIVER to "dummy" BEFORE any pygame import so that
# pygame.image.load() and convert_alpha() work in a headless environment.
os.environ["SDL_VIDEODRIVER"] = "dummy"

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from src.assets import AssetLoadError, AssetManager, ManifestMissingError

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
MANIFEST_PATH: Path = PROJECT_ROOT / "assets" / "manifest.json"
SPRITES_DIR: Path = PROJECT_ROOT / "assets" / "sprites"
GENERATE_SCRIPT: str = "tools/generate_assets.py"

# ── Expected Keys ────────────────────────────────────────────────────────────

ALL_EXPECTED_KEYS: list[str] = [
    # Team 1 — Kittens (3)
    "team1_cell",
    "team1_wiggle",
    "team1_celebrate",
    # Team 2 — Puppies (3)
    "team2_cell",
    "team2_wiggle",
    "team2_celebrate",
    # Coach expressions (6)
    "coach_wave",
    "coach_point",
    "coach_cheer_small",
    "coach_cheer",
    "coach_aww",
    "coach_idle",
    # Backgrounds (3)
    "bg_team_select",
    "bg_game",
    "bg_celebration",
    # Effects (4)
    "sparkle",
    "confetti",
    "heart",
    "star",
    # UI Chrome (3)
    "btn_start",
    "btn_play_again",
    "board_frame",
    # Preserved POC (1)
    "poc",
]
# Total: 23


# ── Helper ───────────────────────────────────────────────────────────────────


def print_result(
    check_num: int,
    passed: bool,
    description: str,
    detail: str | None = None,
) -> None:
    """Print a single check result line.

    Format::

        <N> [PASS] <description>
        <N> [FAIL] <description> — <detail>

    Args:
        check_num: 1-based check index.
        passed: True for PASS, False for FAIL.
        description: Human-readable check name.
        detail: Optional failure reason (only printed on FAIL).
    """
    prefix = "[PASS]" if passed else "[FAIL]"
    line = f"{check_num} {prefix} {description}"
    if not passed and detail is not None:
        line += f" — {detail}"
    print(line)
    sys.stdout.flush()


# ── Main Verification ────────────────────────────────────────────────────────


def main() -> None:
    """Run all 7 verification checks and print a structured report."""
    passed_count: int = 0
    total_checks: int = 7
    asset_mgr: AssetManager | None = None

    # ═══════════════════════════════════════════════════════════════════════
    # Check 1 — Generation Pipeline (AC-1)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        generation_result = subprocess.run(
            ["poetry", "run", "python", GENERATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        pipeline_ok = generation_result.returncode == 0

        png_files = list(SPRITES_DIR.glob("*.png"))
        file_count_ok = len(png_files) >= 23

        check1_ok = pipeline_ok and file_count_ok
        if not check1_ok:
            detail_parts: list[str] = []
            if not pipeline_ok:
                detail_parts.append(
                    f"exit code {generation_result.returncode}"
                )
            if not file_count_ok:
                detail_parts.append(
                    f"only {len(png_files)} PNGs found (expected 23+)"
                )
            check1_detail = "; ".join(detail_parts)
        else:
            check1_detail = None
    except FileNotFoundError as exc:
        check1_ok = False
        check1_detail = f"Command not found: {exc}"

    print_result(1, check1_ok, "Generation pipeline exits 0 and produces 23+ PNG files", check1_detail)  # noqa: E501
    if check1_ok:
        passed_count += 1

    # ═══════════════════════════════════════════════════════════════════════
    # Check 2 — Pytest Suite (AC-2)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        pytest_result = subprocess.run(
            ["poetry", "run", "pytest", "tests/test_assets.py", "-v"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        check2_ok = pytest_result.returncode == 0
        if not check2_ok:
            check2_detail = f"exit code {pytest_result.returncode}"
        else:
            check2_detail = None
    except FileNotFoundError as exc:
        check2_ok = False
        check2_detail = f"Command not found: {exc}"

    print_result(2, check2_ok, "Pytest test_assets.py exits 0 (all tests pass)", check2_detail)  # noqa: E501
    if check2_ok:
        passed_count += 1

    # ═══════════════════════════════════════════════════════════════════════
    # Check 3 — Manifest JSON Structure (AC-4)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
        manifest_data: dict = json.loads(manifest_text)

        entry_count_ok = len(manifest_data) >= 23

        all_fields_valid = True
        first_invalid_key: str | None = None
        for entry_key, entry in manifest_data.items():
            if not (
                isinstance(entry.get("key"), str)
                and isinstance(entry.get("file"), str)
                and isinstance(entry.get("width"), int)
                and isinstance(entry.get("height"), int)
            ):
                all_fields_valid = False
                first_invalid_key = entry_key
                break

        check3_ok = entry_count_ok and all_fields_valid
        if not check3_ok:
            detail_parts = []
            if not entry_count_ok:
                detail_parts.append(
                    f"only {len(manifest_data)} entries (expected 23+)"
                )
            if not all_fields_valid and first_invalid_key is not None:
                detail_parts.append(
                    f"invalid field types in entry '{first_invalid_key}'"
                )
            check3_detail = "; ".join(detail_parts)
        else:
            check3_detail = None
    except FileNotFoundError:
        check3_ok = False
        check3_detail = "manifest.json not found"
    except json.JSONDecodeError as exc:
        check3_ok = False
        check3_detail = f"Invalid JSON: {exc}"

    print_result(
        3,
        check3_ok,
        "manifest.json has 23+ entries with valid key/file/width/height fields",
        check3_detail,
    )
    if check3_ok:
        passed_count += 1

    # ═══════════════════════════════════════════════════════════════════════
    # Check 4 — AssetManager Loads All Sprites (AC-3)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        asset_mgr = AssetManager(str(MANIFEST_PATH))
        asset_mgr_ok = True
        check4_detail = None
    except (AssetLoadError, ManifestMissingError) as exc:
        asset_mgr_ok = False
        check4_detail = str(exc)

    all_sprites_ok = False
    if asset_mgr_ok and asset_mgr is not None:
        all_sprites_ok = True
        failing_key: str | None = None
        for key in ALL_EXPECTED_KEYS:
            try:
                surface = asset_mgr.get_sprite(key)
                if surface is None or surface.get_width() <= 0 or surface.get_height() <= 0:  # noqa: E501
                    all_sprites_ok = False
                    failing_key = key
                    break
            except (KeyError, AssetLoadError) as exc:
                all_sprites_ok = False
                failing_key = key
                check4_detail = f"Key '{key}': {exc}"
                break

        if not all_sprites_ok and failing_key is not None:
            if check4_detail is None:
                check4_detail = f"Invalid surface for key '{failing_key}'"

    check4_ok = asset_mgr_ok and all_sprites_ok
    print_result(
        4,
        check4_ok,
        "AssetManager loads all 23 sprites, get_sprite returns valid Surface for each",  # noqa: E501
        check4_detail,
    )
    if check4_ok:
        passed_count += 1

    # ═══════════════════════════════════════════════════════════════════════
    # Checks 5, 6, 7 — depend on a working AssetManager.
    # If Check 4 failed, mark them as FAIL with a skip message.
    # ═══════════════════════════════════════════════════════════════════════
    if not check4_ok:
        # Check 5
        print_result(
            5,
            False,
            "Sample from each category (team, coach, background, effect, UI, POC) returns valid Surface",  # noqa: E501
            "Skipped — AssetManager unavailable",
        )
        # Check 6
        print_result(
            6,
            False,
            "get_sprite('nonexistent') raises KeyError",
            "Skipped — AssetManager unavailable",
        )
        # Check 7
        print_result(
            7,
            False,
            "Missing sprite file raises AssetLoadError naming the exact key",
            "Skipped — AssetManager unavailable",
        )

        print(f"{passed_count}/{total_checks} checks passed.")
        sys.exit(1)

    # ═══════════════════════════════════════════════════════════════════════
    # Check 5 — Sample from Each Category
    # ═══════════════════════════════════════════════════════════════════════
    assert asset_mgr is not None  # Guaranteed by check4_ok guard above.

    category_samples: dict[str, str] = {
        "team": "team1_cell",
        "coach": "coach_wave",
        "background": "bg_team_select",
        "effect": "sparkle",
        "ui": "btn_start",
        "poc": "poc",
    }

    check5_ok = True
    check5_failing_category: str | None = None
    for cat_name, sample_key in category_samples.items():
        try:
            sample_surface = asset_mgr.get_sprite(sample_key)
            if sample_surface is None or sample_surface.get_width() <= 0 or sample_surface.get_height() <= 0:  # noqa: E501
                check5_ok = False
                check5_failing_category = cat_name
                break
        except (KeyError, AssetLoadError) as exc:
            check5_ok = False
            check5_failing_category = cat_name
            check5_detail = f"Category '{cat_name}' ({sample_key}): {exc}"
            break

    if not check5_ok:
        if check5_failing_category is not None:
            check5_detail = f"Category '{check5_failing_category}' returned invalid surface"  # noqa: E501
    else:
        check5_detail = None

    print_result(
        5,
        check5_ok,
        "Sample from each category (team, coach, background, effect, UI, POC) returns valid Surface",  # noqa: E501
        check5_detail,
    )
    if check5_ok:
        passed_count += 1

    # ═══════════════════════════════════════════════════════════════════════
    # Check 6 — KeyError for Unknown Key
    # ═══════════════════════════════════════════════════════════════════════
    try:
        asset_mgr.get_sprite("nonexistent")
        # If we reach here, no exception was raised.
        check6_ok = False
        check6_detail = "No exception raised"
    except KeyError:
        check6_ok = True
        check6_detail = None
    except Exception as exc:  # noqa: BLE001
        check6_ok = False
        check6_detail = f"Wrong exception type: {type(exc).__name__}: {exc}"

    print_result(
        6,
        check6_ok,
        "get_sprite('nonexistent') raises KeyError",
        check6_detail,
    )
    if check6_ok:
        passed_count += 1

    # ═══════════════════════════════════════════════════════════════════════
    # Check 7 — AssetLoadError for Missing File / Milestone 3 DoD (AC-5c)
    # ═══════════════════════════════════════════════════════════════════════
    temp_manifest_path: str | None = None
    check7_ok = False
    check7_detail: str | None = None

    try:
        # Create a temporary manifest pointing to a nonexistent sprite file.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            temp_manifest_path = tmp.name
            json.dump(
                {
                    "test_missing": {
                        "key": "test_missing",
                        "file": "sprites/_does_not_exist.png",
                        "width": 32,
                        "height": 32,
                    }
                },
                tmp,
            )

        # Attempt to construct AssetManager with the bad manifest.
        try:
            AssetManager(temp_manifest_path)
            # No exception raised — fail the check.
            check7_ok = False
            check7_detail = "No exception raised"
        except AssetLoadError as exc:
            error_msg = str(exc)
            if "test_missing" in error_msg:
                check7_ok = True
                check7_detail = None
            else:
                check7_ok = False
                check7_detail = (
                    f"AssetLoadError raised but key 'test_missing' "
                    f"not mentioned in message: {error_msg}"
                )
        except ManifestMissingError:
            check7_ok = False
            check7_detail = (
                "ManifestMissingError raised instead of AssetLoadError"
            )
    except Exception as exc:  # noqa: BLE001
        check7_ok = False
        check7_detail = f"Unexpected error during Check 7 setup: {exc}"
    finally:
        # Clean up temporary file.
        if temp_manifest_path is not None:
            try:
                os.unlink(temp_manifest_path)
            except OSError:
                pass  # Non-fatal — cleanup failure does not affect result.

    print_result(
        7,
        check7_ok,
        "Missing sprite file raises AssetLoadError naming the exact key",
        check7_detail,
    )
    if check7_ok:
        passed_count += 1

    # ═══════════════════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════════════════
    print(f"{passed_count}/{total_checks} checks passed.")

    if passed_count == total_checks:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)
