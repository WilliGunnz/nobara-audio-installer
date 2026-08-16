"""Package scanning functionality."""

from pathlib import Path

from nai.core.package import (
    PackageInfo,
    discover_packages,
    filter_packages,
    group_by_category,
)


def scan_packages(
    base_path: str | Path,
    category: str | None = None,
) -> list[PackageInfo]:
    """
    Scan a directory for valid audio packages.

    Args:
        base_path: Directory to scan (library path).
        category: Optional category filter.

    Returns:
        List of PackageInfo objects.
    """
    path = Path(base_path)

    if not path.is_absolute():
        # Try to resolve relative to current working directory
        path = Path.cwd() / path

    if not path.exists():
        raise FileNotFoundError(f"Library path does not exist: {path}")

    packages = discover_packages(path)

    if category:
        packages = filter_packages(packages, category)

    return packages


def scan_with_summary(
    base_path: str | Path,
    category: str | None = None,
) -> dict[str, int]:
    """
    Scan packages and return a summary.

    Returns:
        Dictionary with counts: valid, invalid, total, by_category.
    """
    packages = scan_packages(base_path, category)

    total = len(packages)
    valid = sum(1 for p in packages if p.valid)
    invalid = total - valid

    by_category: dict[str, int] = {}
    for pkg in packages:
        cat = pkg.category
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "by_category": by_category,
    }
