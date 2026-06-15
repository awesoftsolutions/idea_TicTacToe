"""AssetManager: loads, validates, and caches the generated sprite catalog.

Architecture §6.2 interface: __init__(manifest_path), get_sprite(key),
get_sprite_size(key).  Errors: ERR-001 AssetLoadError, ERR-004 ManifestMissingError.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

# Allow pygame.image.load() + convert_alpha() to work without a display
# surface (headless / CI environment).  This must be set before the first
# pygame import on Windows.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

logger = logging.getLogger("src.assets")


class AssetLoadError(Exception):
    """Raised when a specific asset file cannot be loaded (ERR-001)."""


class ManifestMissingError(Exception):
    """Raised when the manifest file is not found at the expected path (ERR-004)."""


# Initialise a minimal hidden display so that ``convert_alpha()`` works in
# headless / CI environments.  ``pygame.image.load()`` can load surfaces
# without a display, but ``Surface.convert_alpha()`` requires an existing
# display mode.
_pygame_display_initialised: bool = False
if not pygame.display.get_init():
    pygame.display.set_mode((1, 1), pygame.NOFRAME)
    _pygame_display_initialised = True


class AssetManager:
    """Loads and validates the generated sprite catalog from manifest.json.

    All sprites are loaded at construction time.  Any missing or unreadable
    asset raises ``AssetLoadError`` with the failing manifest key in the
    message.
    """

    def __init__(self, manifest_path: str = "assets/manifest.json") -> None:
        """Read manifest, validate all assets, cache surfaces.

        Args:
            manifest_path: Path to the asset manifest JSON file.

        Raises:
            ManifestMissingError: The manifest file does not exist.
            AssetLoadError: An asset file is missing, corrupt, or its
                dimensions do not match the manifest entry.
        """
        manifest_path_obj = Path(manifest_path)

        if not manifest_path_obj.exists():
            raise ManifestMissingError(
                f"Manifest file not found at {manifest_path}"
            )

        with manifest_path_obj.open("r", encoding="utf-8") as f:
            manifest_data: dict = json.load(f)

        self._manifest: dict[str, dict] = {}
        self._sprites: dict[str, pygame.Surface] = {}
        loaded_count: int = 0
        total_count: int = len(manifest_data)

        for key, entry in manifest_data.items():
            # Store metadata first (needed by get_sprite_size).
            self._manifest[key] = entry

            file_path_str: str = entry["file"]

            # Path traversal check — reject ".." in asset paths (security).
            if ".." in file_path_str:
                raise AssetLoadError(
                    f"Failed to load asset '{key}': "
                    f"path traversal detected in '{file_path_str}'"
                )

            # Resolve the sprite file path relative to the manifest parent.
            # e.g. manifest at "assets/manifest.json" -> parent is "assets/"
            #   "sprites/team1_cell.png" -> "assets/sprites/team1_cell.png"
            full_path: Path = manifest_path_obj.parent / file_path_str

            if not full_path.exists():
                raise AssetLoadError(
                    f"Failed to load asset '{key}': "
                    f"file not found at {full_path}"
                )

            try:
                raw_surface = pygame.image.load(str(full_path))
                surface = raw_surface.convert_alpha()
            except pygame.error as exc:
                raise AssetLoadError(
                    f"Failed to load asset '{key}' from {file_path_str}: {exc}"
                ) from exc

            loaded_width: int = surface.get_width()
            loaded_height: int = surface.get_height()

            # Reject zero or negative dimensions (corrupt PNG).
            if loaded_width <= 0 or loaded_height <= 0:
                raise AssetLoadError(
                    f"Failed to load asset '{key}': invalid dimensions "
                    f"({loaded_width}x{loaded_height})"
                )

            expected_width: int = entry["width"]
            expected_height: int = entry["height"]

            if loaded_width != expected_width or loaded_height != expected_height:
                raise AssetLoadError(
                    f"Failed to load asset '{key}': dimension mismatch "
                    f"(expected {expected_width}x{expected_height}, "
                    f"got {loaded_width}x{loaded_height})"
                )

            self._sprites[key] = surface
            loaded_count += 1

            logger.debug(
                "Loaded asset '%s' (%sx%s)", key, loaded_width, loaded_height
            )

        logger.info(
            "AssetManager: loaded %s/%s assets", loaded_count, total_count
        )

    def get_sprite(self, key: str) -> pygame.Surface:
        """Retrieve a loaded sprite by manifest key.

        Args:
            key: Manifest key (e.g. ``"team1_cell"``, ``"coach_wave"``).

        Returns:
            The cached :class:`pygame.Surface`.

        Raises:
            KeyError: The key was not found in the loaded manifest.
        """
        if key not in self._sprites:
            raise KeyError(f"Unknown asset key: '{key}'")
        return self._sprites[key]

    def get_sprite_size(self, key: str) -> tuple[int, int]:
        """Return the (width, height) of a sprite from manifest metadata.

        Args:
            key: Manifest key.

        Returns:
            (width, height) in pixels.

        Raises:
            KeyError: The key was not found in the loaded manifest.
        """
        if key not in self._manifest:
            raise KeyError(f"Unknown asset key: '{key}'")
        entry = self._manifest[key]
        return (entry["width"], entry["height"])
