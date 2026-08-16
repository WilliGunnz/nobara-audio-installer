"""Package uninstallation utilities."""

import shutil
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from ..config import Config

class UninstallError(Exception):
    """Raised when uninstallation fails."""
    pass

@dataclass
class UninstallResult:
    """Result of an uninstall operation."""
    id: str
    name: str
    version: str
    category: str

@dataclass
class InstallResult:
    """Result of an install operation."""
    id: str
    name: str
    version: str
    category: str
    install_path: str
    downloaded_size: int
    checksum_verified: bool

def _get_install_path(config: Config) -> Path:
    """Get the installation prefix as a Path object."""
    install_prefix = config.get("install_path", config.get("install_prefix", ""))

    if not install_prefix:
        install_prefix = str(Path.home() / ".local" / "share" / "nai" / "packages")

    return Path(install_prefix)

def _get_content_path(config: Config) -> Path:
    """Get the content path as a Path object."""
    content_path = config.get("content_path", "")

    if not content_path:
        raise UninstallError("Content path not configured")

    return Path(content_path)

def list_installed() -> List[Dict[str, Any]]:
    """
    List all installed packages.

    Returns:
        List of installed package metadata
    """
    config = Config()
    install_prefix = _get_install_path(config)

    packages = []

    if not install_prefix.exists():
        return packages

    for item in install_prefix.iterdir():
        if item.is_dir():
            # Try to read metadata
            metadata_file = item / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        packages.append({
                            "id": metadata.get("id", item.name),
                            "name": metadata.get("name", item.name),
                            "version": metadata.get("version", "Unknown"),
                            "category": metadata.get("category", "Unknown"),
                            "install_date": metadata.get("_install_date", "Unknown"),
                        })
                except (json.JSONDecodeError, IOError):
                    # Fall back to directory name
                    packages.append({
                        "id": item.name,
                        "name": item.name,
                        "version": "Unknown",
                        "category": "Unknown",
                        "install_date": "Unknown",
                    })

    return packages

def uninstall_package(package_id: str) -> UninstallResult:
    """
    Uninstall a package by ID.

    Args:
        package_id: Package ID to uninstall

    Returns:
        UninstallResult with package information

    Raises:
        UninstallError: If package not found or removal fails
    """
    config = Config()
    install_prefix = _get_install_path(config)

    package_path = install_prefix / package_id

    if not package_path.exists():
        raise UninstallError(f"Package not installed: {package_id}")

    # Read metadata before deletion
    metadata_file = package_path / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Remove the package directory
    try:
        shutil.rmtree(package_path)
    except OSError as e:
        raise UninstallError(f"Failed to remove package directory: {e}")

    return UninstallResult(
        id=package_id,
        name=metadata.get("name", package_id),
        version=metadata.get("version", "Unknown"),
        category=metadata.get("category", "Unknown"),
    )

def find_installed(package_id: str) -> Optional[Path]:
    """Find the installation path for a package."""
    config = Config()
    install_prefix = _get_install_path(config)
    package_path = install_prefix / package_id

    if package_path.exists():
        return package_path
    return None
