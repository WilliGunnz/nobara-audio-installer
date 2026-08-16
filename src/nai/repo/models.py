"""Shared data models for package sources."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PackageSource(Enum):
    """Where a package originates from."""
    COPR = "copr"
    DNF = "dnf"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RepoPackage:
    """
    A unified package representation across all repository types.

    Both COPR API responses and dnf repoquery output map into this struct,
    so the UI layer never needs to know the source.
    """
    name: str
    version: str
    release: str
    arch: str
    epoch: int
    summary: str
    source: PackageSource
    repo_id: str           # e.g. "ycollet/audinux" or "fedora" or "rpmfusion-free"
    chroot: str = ""       # COPR-specific (empty for dnf)
    state: str = "available"
    url: str = ""

    @property
    def full_version(self) -> str:
        return f"{self.version}-{self.release}"

    @property
    def nevra(self) -> str:
        """Standard RPM identifier: name-[epoch:]version-release.arch"""
        if self.epoch:
            return f"{self.name}-{self.epoch}:{self.version}-{self.release}.{self.arch}"
        return f"{self.name}-{self.version}-{self.release}.{self.arch}"

    @property
    def is_copr(self) -> bool:
        return self.source == PackageSource.COPR

    @property
    def is_dnf(self) -> bool:
        return self.source == PackageSource.DNF

    def __repr__(self) -> str:
        return f"<RepoPackage {self.name}-{self.full_version} [{self.repo_id}]>"
