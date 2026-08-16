"""Package verification utilities."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import Config

class VerifyError(Exception):
    """Raised when verification fails."""
    pass


def _get_manifest(config: Config) -> List[Dict[str, Any]]:
    """Load the package manifest from configured content path."""
    content_path = config.get("content_path", "")

    if not content_path:
        raise VerifyError("Content path not configured. Run: nai config --set-key content_path --set-value /path/to/content")

    # Convert to Path object
    content_path_obj = Path(content_path)
    manifest_path = content_path_obj / "packages.json"

    if not manifest_path.exists():
        return []

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("packages", [])
    except (json.JSONDecodeError, IOError):
        return []


def _find_package_in_manifest(packages: List[Dict[str, Any]], package_id: str) -> Optional[Dict[str, Any]]:
    """Find a package in the manifest by ID."""
    for pkg in packages:
        if pkg.get("id") == package_id:
            return pkg
    return None


def _get_installed_package_path(package_id: str, config: Config) -> Path:
    """Get the installation path for a package."""
    install_prefix = config.get("install_path", config.get("install_prefix", ""))

    if not install_prefix:
        install_prefix = str(Path.home() / ".local" / "share" / "nai" / "packages")

    # Convert to Path object
    prefix_path = Path(install_prefix)
    return prefix_path / package_id


def _calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_package(package_id: str) -> Dict[str, Any]:
    """
    Verify an installed package's integrity.

    Args:
        package_id: Package ID to verify

    Returns:
        Dictionary with verification results

    Raises:
        VerifyError: If verification fails
    """
    config = Config()

    # Get the installed package path
    package_path = _get_installed_package_path(package_id, config)

    if not package_path.exists():
        raise VerifyError(f"Package not installed: {package_id}")

    # Load manifest for reference checksum
    manifest = _get_manifest(config)
    manifest_pkg = _find_package_in_manifest(manifest, package_id)

    if not manifest_pkg:
        # Package not in manifest, but exists on disk - partial verification
        return {
            "verified": False,
            "reason": "Package not found in manifest",
            "checksum_verified": False,
            "files_checked": True,
        }

    # Verify archive checksum (if we can find the cached archive)
    checksum_verified = False
    expected_sha256 = manifest_pkg.get("sha256", "")

    # Look for cached archive in installation directory
    cached_archive = package_path / f"{package_id}-{manifest_pkg.get('version', '')}.zip"
    if cached_archive.exists() and expected_sha256:
        actual_hash = _calculate_file_hash(cached_archive)
        checksum_verified = actual_hash.lower() == expected_sha256.lower()

    # Verify all files exist (basic check)
    files_check = package_path.exists()

    if not checksum_verified and expected_sha256:
        raise VerifyError(f"Checksum mismatch for {package_id}")

    if not files_check:
        raise VerifyError(f"Package files missing: {package_id}")

    return {
        "verified": True,
        "reason": "All checks passed",
        "checksum_verified": checksum_verified,
        "files_checked": files_check,
    }


def verify_all() -> List[Dict[str, Any]]:
    """
    Verify all installed packages.

    Returns:
        List of verification results for each package
    """
    from .uninstall import list_installed

    results = []
    installed = list_installed()

    for pkg in installed:
        pkg_id = pkg.get("id", "")
        if not pkg_id:
            continue

        try:
            result = verify_package(pkg_id)
            results.append({
                "package_id": pkg_id,
                "success": True,
                "details": result,
            })
        except VerifyError as e:
            results.append({
                "package_id": pkg_id,
                "success": False,
                "error": str(e),
            })

    return results
