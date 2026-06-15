"""Test docs/screenshots/ exists for Sprint 4 Demo Carrier verification."""

import pathlib


def test_verification_dir_exists() -> None:
    """Assert that the docs/screenshots/ directory exists."""
    screenshots_dir = pathlib.Path("docs/screenshots/")
    assert screenshots_dir.is_dir(), (
        f"Screenshots directory not found: {screenshots_dir.resolve()}"
    )