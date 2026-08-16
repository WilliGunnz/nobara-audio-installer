"""Version management for the Nobara Audio Installer."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from packaging.version import Version


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VERSION_FILE = PROJECT_ROOT / "VERSION"


class BumpType(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


def current_version() -> str:
    """Read the current version from the VERSION file."""
    if not VERSION_FILE.exists():
        return "0.0.0"
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def write_version(version: str) -> None:
    """Write a version string to the VERSION file."""
    VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")


def bump_version(version: str, bump_type: str = "patch") -> str:
    """
    Bump a semantic version string.

    Args:
        version: A semantic version string like "1.2.3".
        bump_type: One of "major", "minor", or "patch".

    Returns:
        The bumped version string.

    Raises:
        ValueError: If version is invalid or bump_type is unknown.
    """
    parsed = Version(version)

    major = parsed.major
    minor = parsed.minor
    patch = parsed.micro

    bt = BumpType(bump_type)

    if bt is BumpType.MAJOR:
        major += 1
        minor = 0
        patch = 0
    elif bt is BumpType.MINOR:
        minor += 1
        patch = 0
    elif bt is BumpType.PATCH:
        patch += 1

    return f"{major}.{minor}.{patch}"


def parse_version(version: str) -> Version:
    """Parse a version string into a packaging.version.Version object."""
    return Version(version)


def is_newer(a: str, b: str) -> bool:
    """Return True if version `a` is strictly newer than version `b`."""
    return parse_version(a) > parse_version(b)


def compare_versions(a: str, b: str) -> int:
    """
    Compare two version strings.

    Returns:
        -1 if a < b, 0 if a == b, 1 if a > b.
    """
    va = parse_version(a)
    vb = parse_version(b)

    if va < vb:
        return -1
    elif va > vb:
        return 1
    return 0
