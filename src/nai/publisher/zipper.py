"""Archive creation utilities for publishing."""

import zipfile
from pathlib import Path
from typing import Optional

class ZipError(Exception):
    """Raised when archive operations fail."""
    pass

def create_archive(source_dir: Path, output_path: Path) -> Path:
    """
    Create a ZIP archive from a directory.

    Args:
        source_dir: Directory to archive
        output_path: Output ZIP file path

    Returns:
        Path to created archive
    """
    if not source_dir.exists():
        raise ZipError(f"Source directory not found: {source_dir}")

    # Ensure output path has .zip extension
    if not str(output_path).endswith('.zip'):
        output_path = output_path.with_suffix('.zip')

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                # Compute relative path within archive
                arc_name = file_path.relative_to(source_dir)
                zf.write(file_path, arc_name)

    return output_path

def extract_archive(archive_path: Path, dest_dir: Path) -> Path:
    """
    Extract a ZIP archive to a directory.

    Args:
        archive_path: Path to ZIP file
        dest_dir: Destination directory

    Returns:
        Path to extraction destination
    """
    if not archive_path.exists():
        raise ZipError(f"Archive not found: {archive_path}")

    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, 'r') as zf:
        zf.extractall(dest_dir)

    return dest_dir

def list_archive_contents(archive_path: Path) -> list:
    """
    List all files in a ZIP archive.

    Args:
        archive_path: Path to ZIP file

    Returns:
        List of file paths in archive
    """
    if not archive_path.exists():
        raise ZipError(f"Archive not found: {archive_path}")

    with zipfile.ZipFile(archive_path, 'r') as zf:
        return zf.namelist()

def get_archive_size(archive_path: Path) -> int:
    """Get the size of an archive in bytes."""
    if not archive_path.exists():
        raise ZipError(f"Archive not found: {archive_path}")
    return archive_path.stat().st_size
