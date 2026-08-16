"""Package publishing workflow."""

import shutil
import tempfile
from pathlib import Path
from typing import NamedTuple, Optional

from rich.console import Console
import typer

from ..config import Config
from .checksum import calculate_sha256
from .github import (
    GitHubRelease,
    create_or_update_release,
    upload_release_asset,
)
from .manifest import (
    ManifestEntry,
    generate_download_url,
    load_manifest,
    save_manifest,
    update_package_in_manifest,
)
from .zipper import create_archive

console = Console()

class PublishResult(NamedTuple):
    """Result of a publish operation."""
    id: str
    version: str
    archive_path: Path
    size: int
    sha256: str
    download: str


class PublishError(Exception):
    """Raised when publishing fails."""
    pass


def scan_packages(library_path: Path, category: str) -> list:
    """
    Scan a library directory for valid packages.

    Args:
        library_path: Root path to audio library
        category: Category subdirectory to scan

    Returns:
        List of package metadata dictionaries
    """
    category_path = library_path / category
    packages = []

    if not category_path.exists():
        return packages

    for item in category_path.iterdir():
        if item.is_dir():
            metadata_file = item / "metadata.json"
            if metadata_file.exists():
                import json
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        packages.append({
                            "path": item,
                            "metadata": metadata,
                        })
                except (json.JSONDecodeError, IOError):
                    continue

    return packages


def validate_package(package_dir: Path) -> tuple[bool, str]:
    """
    Validate a package directory structure.

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

    return True, ""


def publish_package(
    package_path: Path,
    dry_run: bool = False,
    no_upload: bool = False,
) -> PublishResult:
    """
    Publish a single package.

    Args:
        package_path: Path to package directory
        dry_run: If True, don't actually upload to GitHub
        no_upload: If True, skip GitHub upload but still create archive

    Returns:
        PublishResult with all relevant information
    """
    from ..config import Config
    config = Config()

    # Load metadata
    import json
    metadata_file = package_path / "metadata.json"
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    pkg_id = metadata["id"]
    name = metadata["name"]
    version = metadata["version"]
    category = metadata["category"]

    console.print(f"\n[dim]Publishing:[/dim] {pkg_id} v{version}")

    # Create archive
    archive_name = f"{pkg_id}-{version}.zip"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        archive_path = tmp_path / archive_name

        console.print(f"[dim]Creating archive...[/dim]")
        create_archive(package_path, archive_path)

        # Calculate checksum
        console.print(f"[dim]Calculating SHA-256...[/dim]")
        sha256 = calculate_sha256(archive_path)
        size = archive_path.stat().st_size

        # Prepare GitHub upload if not dry-run and not no-upload
        github_repo = config.get("github_repo", "")
        github_token = config.get("github_token", "")
        download_url = ""

        if not dry_run and not no_upload:
            if not github_repo:
                raise PublishError("GitHub repository not configured. Run: nai config --set-key github_repo --set-value owner/repo")
            if not github_token:
                raise PublishError("GitHub token not configured. Run: nai config --set-key github_token --set-value ghp_yourtoken")

            tag = f"v{version}"
            release_name = f"{name} v{version}"
            body = f"Automated release of {name} version {version}"

            console.print(f"[dim]Repository:[/dim] {github_repo}")
            console.print(f"[dim]Token present:[/dim] {'*' * 8}{github_token[-4:] if github_token else 'None'}")
            console.print(f"[dim]Tag:[/dim] {tag}")

            # Create or update release
            console.print(f"[dim]Creating/updating GitHub release...[/dim]")
            release: GitHubRelease = create_or_update_release(
                repo_full=github_repo,
                tag=tag,
                name=release_name,
                body=body,
                token=github_token,
            )

            # Upload asset
            console.print(f"[dim]Uploading asset...[/dim]")
            asset = upload_release_asset(
                release_upload_url=release.upload_url,
                asset_path=archive_path,
                asset_name=archive_name,
                token=github_token,
            )

            download_url = asset.browser_download_url

            # Update manifest
            console.print(f"[dim]Updating package manifest...[/dim]")
            content_path = config.get("content_path", "")
            if content_path:
                manifest_path = Path(content_path) / "packages.json"
                manifest_packages = load_manifest(manifest_path)

                entry = ManifestEntry(
                    id=pkg_id,
                    name=name,
                    version=version,
                    category=category,
                    download=download_url,
                    sha256=sha256,
                    size=size,
                )
                updated_packages = update_package_in_manifest(manifest_packages, entry)
                save_manifest(manifest_path, updated_packages)
        elif dry_run:
            download_url = f"https://github.com/{github_repo}/releases/download/v{version}/{archive_name}" if github_repo else ""
        else:
            download_url = ""

    result = PublishResult(
        id=pkg_id,
        version=version,
        archive_path=archive_path,
        size=size,
        sha256=sha256,
        download=download_url,
    )

    return result
