"""Manifest handling for package index management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ManifestEntry:
    """An entry in the package manifest."""
    id: str
    name: str
    version: str
    category: str
    download: str = ""
    sha256: str = ""
    size: int = 0


def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """
    Load and return packages from a manifest JSON file.

    Args:
        manifest_path: Path to packages.json

    Returns:
        List of package dictionaries, empty list if file doesn't exist.
    """
    if not manifest_path.exists():
        return []
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("packages", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_manifest(manifest_path: Path, packages: List[Dict[str, Any]]) -> None:
    """
    Save a list of packages to a manifest JSON file.

    Args:
        manifest_path: Path to packages.json
        packages: List of package dictionaries
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"packages": packages}
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_manifest_entry(id: str, name: str, version: str, category: str,
                          download: str, sha256: str, size: int) -> ManifestEntry:
    """Create a new manifest entry."""
    return ManifestEntry(
        id=id,
        name=name,
        version=version,
        category=category,
        download=download,
        sha256=sha256,
        size=size,
    )


def generate_download_url(repo_full: str, tag: str, asset_name: str) -> str:
    """
    Generate a GitHub download URL for an asset.

    Args:
        repo_full: Full repository name (e.g., 'owner/repo')
        tag: Release tag (e.g., 'v1.0.0')
        asset_name: Name of the asset file

    Returns:
        Full download URL
    """
    owner, repo = repo_full.split("/", 1)
    return f"https://github.com/{owner}/{repo}/releases/download/{tag}/{asset_name}"


def find_package_in_manifest(packages: List[Dict[str, Any]], package_id: str) -> Optional[Dict[str, Any]]:
    """Find a package in a list by its ID."""
    for pkg in packages:
        if pkg.get("id") == package_id:
            return pkg
    return None


def update_package_in_manifest(packages: List[Dict[str, Any]], entry: ManifestEntry) -> List[Dict[str, Any]]:
    """Update or add a package entry in the manifest list."""
    for i, pkg in enumerate(packages):
        if pkg.get("id") == entry.id:
            packages[i] = {
                "id": entry.id,
                "name": entry.name,
                "version": entry.version,
                "category": entry.category,
                "download": entry.download,
                "sha256": entry.sha256,
                "size": entry.size,
            }
            return packages

    # New package, add to list
    packages.append({
        "id": entry.id,
        "name": entry.name,
        "version": entry.version,
        "category": entry.category,
        "download": entry.download,
        "sha256": entry.sha256,
        "size": entry.size,
    })
    return packages
