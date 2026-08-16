"""Update checking utilities."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ..config import Config, get_config

@dataclass
class UpdateInfo:
    """Information about an available update."""
    package_id: str
    current_version: str
    latest_version: str
    download_url: str = ""
    size: int = 0
    changelog: str = ""

class UpdateError(Exception):
    """Raised when update operations fail."""
    pass

def _get_manifest_path(config: Config) -> Path:
    """Get the path to the packages.json manifest."""
    content_path = config.get("content_path", "")

    if not content_path:
        raise UpdateError("Content path not configured")

    content_path_obj = Path(content_path)
    return content_path_obj / "packages.json"

def _get_install_path(config: Config) -> Path:
    """Get the installation prefix as a Path object."""
    install_prefix = config.get("install_path", config.get("install_prefix", ""))

    if not install_prefix:
        install_prefix = str(Path.home() / ".local" / "share" / "nai" / "packages")

    return Path(install_prefix)

def get_available_updates() -> List[UpdateInfo]:
    """
    Check for available updates for all installed packages.

    Returns:
        List of UpdateInfo for packages with available updates
    """
    config = get_config()

    # Get installed packages
    from .uninstall import list_installed
    installed = list_installed()

    if not installed:
        return []

    # Load manifest
    manifest_path = _get_manifest_path(config)

    if not manifest_path.exists():
        return []

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            manifest_packages = data.get("packages", [])
    except (json.JSONDecodeError, IOError):
        return []

    updates = []

    for installed_pkg in installed:
        pkg_id = installed_pkg.get("id", "")
        current_version = installed_pkg.get("version", "0.0.0")

        # Find in manifest
        manifest_pkg = None
        for mp in manifest_packages:
            if mp.get("id") == pkg_id:
                manifest_pkg = mp
                break

        if not manifest_pkg:
            continue

        latest_version = manifest_pkg.get("version", current_version)

        if _version_lt(current_version, latest_version):
            updates.append(UpdateInfo(
                package_id=pkg_id,
                current_version=current_version,
                latest_version=latest_version,
                download_url=manifest_pkg.get("download", ""),
                size=manifest_pkg.get("size", 0),
            ))

    return updates

def check_for_updates(package_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Check for updates for a specific package or all packages.

    Args:
        package_id: Specific package ID, or None for all packages

    Returns:
        List of dictionaries with update information
    """
    updates = get_available_updates()

    if package_id:
        updates = [u for u in updates if u.package_id == package_id]

    return [
        {
            "id": u.package_id,
            "current_version": u.current_version,
            "latest_version": u.latest_version,
            "download_url": u.download_url,
            "size": u.size,
        }
        for u in updates
    ]

def _version_lt(v1: str, v2: str) -> bool:
    """Compare two semantic version strings, return True if v1 < v2."""
    def normalize(v):
        return [int(x) for x in v.split(".")[:3]]  # major, minor, patch

    n1 = normalize(v1)
    n2 = normalize(v2)

    return n1 < n2

def apply_update(package_id: str) -> bool:
    """
    Apply an update for a specific package.

    Args:
        package_id: Package ID to update

    Returns:
        True if successful

    Raises:
        UpdateError: If update fails
    """
    from .install import install_package

    try:
        result = install_package(package_id, force=True)
        return True
    except Exception as e:
        raise UpdateError(f"Failed to update {package_id}: {e}")

def fetch_manifest_from_github(repo_full: str, token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the packages.json manifest directly from GitHub releases.

    Args:
        repo_full: Full repository name (owner/repo)
        token: GitHub API token

    Returns:
        Manifest data dictionary or None
    """
    import requests

    owner, repo = repo_full.split("/", 1)
    releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.get(releases_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Look for manifest asset
        for asset in data.get("assets", []):
            if asset["name"] == "packages.json":
                # Download manifest
                manifest_url = asset["browser_download_url"]
                manifest_response = requests.get(manifest_url, timeout=30)
                manifest_response.raise_for_status()
                return manifest_response.json()

        return None
    except (requests.RequestException, KeyError, json.JSONDecodeError):
        return None
