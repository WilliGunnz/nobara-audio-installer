"""Checksum calculation and verification utilities."""

import hashlib
from pathlib import Path
from typing import Optional


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to file to hash

    Returns:
        Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """
    Verify a file's SHA-256 matches an expected value.

    Args:
        file_path: Path to file to verify
        expected_hash: Expected SHA-256 hex string

    Returns:
        True if hashes match
    """
    actual_hash = calculate_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower()


def format_size(size_bytes: int) -> str:
    """
    Format a byte count into human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
