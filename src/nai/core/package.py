"""Package metadata and manifest utilities."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class PackageInfo:
    """Metadata about a package."""
    id: str
    name: str
    version: str
    category: str
    author: str = ""
    license: str = ""
    description: str = ""
    homepage: str = ""
    tags: List[str] = field(default_factory=list)

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """
    Load and return packages from a manifest JSON file.

    Args:
        manifest_path: Path to packages.json

    Returns:
        List of package dictionaries, empty list if file doesn't exist or is invalid.
    """
    if not manifest_path.exists():
        return []
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("packages", [])
    except (json.JSONDecodeError, IOError, OSError):
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

def find_package_by_id(packages: List[Dict[str, Any]], package_id: str) -> Optional[Dict[str, Any]]:
    """Find a package in a list by its ID."""
    for pkg in packages:
        if pkg.get("id") == package_id:
            return pkg
    return None

def validate_package_structure(package_dir: Path) -> tuple[bool, str]:
    """
    Validate that a package directory follows the required structure.

    Args:
        package_dir: Path to package directory

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_files = ["metadata.json", "README.md", "LICENSE"]
    required_dirs = ["artwork", "files"]

    for file in required_files:
        if not (package_dir / file).exists():
            return False, f"Missing required file: {file}"

    for directory in required_dirs:
        if not (package_dir / directory).is_dir():
            return False, f"Missing required directory: {directory}"

    # Validate metadata.json
    metadata_path = package_dir / "metadata.json"
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False, "Invalid metadata.json (not valid JSON)"

    # Check required metadata fields
    required_fields = ["id", "name", "version", "category", "author", "license", "description"]
    for fld in required_fields:
        if fld not in metadata:
            return False, f"Missing required metadata field: {fld}"

    # Validate package ID format (lowercase, hyphens only)
    pkg_id = metadata["id"]
    if pkg_id != pkg_id.lower():
        return False, "Package ID must be lowercase"
    if "_" in pkg_id or any(c in pkg_id for c in "!@#$%^&*()"):
        return False, "Package ID must use hyphens only (no underscores or special chars)"

    return True, ""

def load_package_metadata(package_dir: Path) -> Optional[Dict[str, Any]]:
    """Load metadata from a package directory."""
    metadata_path = package_dir / "metadata.json"
    if not metadata_path.exists():
        return None
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def get_category_path(library_path: Path, category: str) -> Path:
    """Get the filesystem path for a category within the library."""
    return library_path / category
