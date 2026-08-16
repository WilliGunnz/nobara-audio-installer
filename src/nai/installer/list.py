"""Package listing functionality."""

from __future__ import annotations

from pathlib import Path

from nai.config import Config


def _get_installed_packages() -> list[dict[str, str]]:
    """Get list of installed packages with metadata."""
    config = Config()
    install_prefix = config.install_prefix or Path.home() / ".local" / "share" / "nai" / "packages"

    installed = []

    if not install_prefix.exists():
        return installed

    for pkg_dir in install_prefix.iterdir():
        if not pkg_dir.is_dir():
            continue

        metadata_path = pkg_dir / "installed.json"
        if not metadata_path.exists():
            continue

        try:
            with metadata_path.open("r", encoding="utf-8") as fh:
                metadata = __import__("json").load(fh)
                installed.append(metadata)
        except Exception:
            continue

    # Sort by package ID
    installed.sort(key=lambda x: x.get("package_id", ""))

    return installed


def list_installed(
    show_path: bool = False,
) -> list[dict[str, str]]:
    """
    List all installed packages.

    Args:
        show_path: Include installation path in results.

    Returns:
        List of installed package metadata dictionaries.
    """
    config = Config()
    install_prefix = config.install_prefix or Path.home() / ".local" / "share" / "nai" / "packages"

    installed = _get_installed_packages()

    if show_path:
        for pkg in installed:
            pkg["install_path"] = str(install_prefix / pkg["package_id"])

    return installed
