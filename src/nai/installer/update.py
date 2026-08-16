"""Package update functionality."""

from __future__ import annotations

from pathlib import Path

from nai.config import Config
from nai.publisher.manifest import load_manifest


class UpdateError(Exception):
    """Error during update operations."""

    def __init__(self, message: str):
        super().__init__(message)


def _get_manifest(config: Config) -> dict[str, Any]:
    """Load the package manifest."""
    content_path = config.content_path
    if not content_path:
        raise UpdateError("Content path not configured. Run: nai config --set-key content_path --set-value /path/to/content")

    return load_manifest(content_path)


def _find_package_in_manifest(manifest: dict[str, Any], package_id: str) -> dict[str, Any] | None:
    """Find a package entry by ID."""
    for pkg in manifest.get("packages", []):
        if pkg.get("id") == package_id:
            return pkg
    return None


def _parse_version(version: str) -> tuple[int, int, int]:
    """Parse semantic version string into tuple."""
    parts = version.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return major, minor, patch


def _is_newer(new_version: str, old_version: str) -> bool:
    """Check if new version is strictly greater than old version."""
    new = _parse_version(new_version)
    old = _parse_version(old_version)
    return new > old


def check_for_updates() -> list[dict[str, str]]:
    """
    Check all installed packages for updates.

    Returns:
        List of packages with available updates.
    """
    config = Config()

    # Load manifest
    manifest = _get_manifest(config)

    # Get installed packages (from uninstall module!)
    from nai.installer.uninstall import list_installed
    installed_pkgs = list_installed()

    updates_available = []

    for pkg in installed_pkgs:
        package_id = pkg["package_id"]
        current_version = pkg["version"]

        # Find latest in manifest
        manifest_pkg = _find_package_in_manifest(manifest, package_id)

        if not manifest_pkg:
            continue

        latest_version = manifest_pkg["version"]

        if _is_newer(latest_version, current_version):
            updates_available.append({
                "package_id": package_id,
                "current_version": current_version,
                "latest_version": latest_version,
                "name": pkg.get("name", package_id),
                "category": pkg.get("category", ""),
            })

    return updates_available


def update_package(
    package_id: str,
    check_only: bool = False,
) -> dict[str, str]:
    """
    Update a specific package.

    Args:
        package_id: Package to update.
        check_only: Only check for update, don't apply it.

    Returns:
        Updated package metadata.

    Raises:
        UpdateError: If update fails or not applicable.
    """
    from nai.installer.install import install_package
    from nai.installer.uninstall import find_installed

    # First check if package is installed
    result = find_installed(package_id)
    if not result:
        raise UpdateError(f"Package not installed: {package_id}")

    install_path, metadata = result
    current_version = metadata["version"]

    # Check manifest
    config = Config()
    manifest = _get_manifest(config)
    manifest_pkg = _find_package_in_manifest(manifest, package_id)

    if not manifest_pkg:
        raise UpdateError(f"Package not found in manifest: {package_id}")

    latest_version = manifest_pkg["version"]

    if not _is_newer(latest_version, current_version):
        raise UpdateError(f"Already up to date: {package_id} v{current_version}")

    if check_only:
        return {
            "package_id": package_id,
            "current_version": current_version,
            "latest_version": latest_version,
            "available": True,
        }

    # Apply update (reinstall)
    install_package(package_id, force=True)

    # Return new metadata
    result = find_installed(package_id)
    if not result:
        raise UpdateError(f"Update succeeded but package not found after reinstall: {package_id}")

    return result[1]
