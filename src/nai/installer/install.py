"""Package installation with plugin path handling."""

import json
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from ..config import Config
from ..publisher.checksum import calculate_sha256
from .verify import VerifyError

class InstallError(Exception):
    """Raised when installation fails."""
    pass

class InstallResult:
    """Result of an install operation."""
    def __init__(
        self,
        id: str,
        name: str,
        version: str,
        category: str,
        install_path: str,
        downloaded_size: int,
        checksum_verified: bool,
    ):
        self.id = id
        self.name = name
        self.version = version
        self.category = category
        self.install_path = install_path
        self.downloaded_size = downloaded_size
        self.checksum_verified = checksum_verified

# Category-to-path mapping for user-local installation
PLUGIN_PATHS = {
    "lv2": Path.home() / ".lv2",
    "vst3": Path.home() / ".vst3",
    "vst": Path.home() / ".vst",
    "clap": Path.home() / ".clap",
    "plugins": Path.home() / ".vst3",
    "drum-packs": Path.home() / "Audio" / "drum-packs",
    "ir-packs": Path.home() / "Audio" / "ir-packs",
    "midi-packs": Path.home() / "Audio" / "midi-packs",
    "presets": Path.home() / "Audio" / "presets",
    "soundfonts": Path.home() / "Audio" / "soundfonts",
}

def _get_manifest(config: Config) -> list:
    """Load packages from manifest."""
    content_path = config.get("content_path", "")
    if not content_path:
        raise InstallError("Content path not configured")

    manifest_path = Path(content_path) / "packages.json"
    if not manifest_path.exists():
        return []

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("packages", [])
    except (json.JSONDecodeError, IOError):
        return []

def _find_package_in_manifest(packages: list, package_id: str) -> Optional[dict]:
    """Find a package in the manifest by ID."""
    for pkg in packages:
        if pkg.get("id") == package_id:
            return pkg
    return None

def _get_destination(category: str, package_id: str, config: Config) -> Path:
    """Determine the destination path for a package."""
    # Check if category has a known user path
    if category in PLUGIN_PATHS:
        return PLUGIN_PATHS[category] / package_id

    # Fall back to NAI install path
    install_prefix = config.get("install_path", str(Path.home() / ".local" / "share" / "nai" / "packages"))
    return Path(install_prefix) / package_id

def _record_installation(
    package_id: str,
    name: str,
    version: str,
    category: str,
    install_path: Path,
    config: Config,
) -> None:
    """Record installation metadata in the NAI tracking directory."""
    install_prefix = Path(config.get("install_path", str(Path.home() / ".local" / "share" / "nai" / "packages")))
    tracking_dir = install_prefix / package_id
    tracking_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "id": package_id,
        "name": name,
        "version": version,
        "category": category,
        "install_path": str(install_path),
        "install_date": datetime.now().isoformat(),
    }

    metadata_file = tracking_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

def install_package(package_id: str, force: bool = False) -> InstallResult:
    """
    Install a package by ID.

    Downloads the ZIP archive from GitHub Releases, verifies the SHA-256
    checksum, and extracts files to the correct user-local path based
    on the package category.

    Args:
        package_id: Package ID to install
        force: If True, reinstall even if already installed

    Returns:
        InstallResult with installation details

    Raises:
        InstallError: If installation fails
    """
    config = Config()

    # Load manifest and find package
    packages = _get_manifest(config)
    pkg_info = _find_package_in_manifest(packages, package_id)

    if not pkg_info:
        raise InstallError(f"Package not found in manifest: {package_id}")

    # Check if already installed
    install_prefix = Path(config.get("install_path", str(Path.home() / ".local" / "share" / "nai" / "packages")))
    tracking_dir = install_prefix / package_id

    if tracking_dir.exists() and not force:
        raise InstallError(f"Package already installed: {package_id}. Use --force to reinstall.")

    # Get download URL
    download_url = pkg_info.get("download", "")
    if not download_url:
        raise InstallError(f"No download URL for {package_id}")

    # Download to temporary file
    try:
        response = requests.get(download_url, stream=True, timeout=120)
        response.raise_for_status()
    except requests.RequestException as e:
        raise InstallError(f"Download failed: {e}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    downloaded_size = tmp_path.stat().st_size

    # Verify checksum
    expected_sha256 = pkg_info.get("sha256", "")
    checksum_verified = False

    if expected_sha256:
        actual_sha256 = calculate_sha256(tmp_path)
        if actual_sha256.lower() != expected_sha256.lower():
            tmp_path.unlink(missing_ok=True)
            raise InstallError(f"Checksum verification failed for {package_id}")
        checksum_verified = True

    # Determine destination
    category = pkg_info.get("category", "unknown")
    dest = _get_destination(category, package_id, config)

    # Remove existing installation if force-reinstalling
    if dest.exists():
        shutil.rmtree(dest)

    # Create destination directory
    dest.mkdir(parents=True, exist_ok=True)

    # Extract archive to destination
    try:
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(dest)
    except (zipfile.BadZipFile, OSError) as e:
        tmp_path.unlink(missing_ok=True)
        shutil.rmtree(dest, ignore_errors=True)
        raise InstallError(f"Extraction failed: {e}")

    # Clean up temporary file
    tmp_path.unlink(missing_ok=True)

    # Record installation for tracking (list, verify, uninstall)
    _record_installation(
        package_id=package_id,
        name=pkg_info.get("name", package_id),
        version=pkg_info.get("version", "1.0.0"),
        category=category,
        install_path=dest,
        config=config,
    )

    return InstallResult(
        id=package_id,
        name=pkg_info.get("name", package_id),
        version=pkg_info.get("version", "1.0.0"),
        category=category,
        install_path=str(dest),
        downloaded_size=downloaded_size,
        checksum_verified=checksum_verified,
    )
