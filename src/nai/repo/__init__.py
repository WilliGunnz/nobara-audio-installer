"""Repository integration for NAI.

Provides a unified interface for querying packages from multiple sources:
  - COPR repos (e.g. ycollet/audinux) via REST API
  - Local dnf repos (Nobara base, updates, RPM Fusion, etc.) via `dnf repoquery`
"""

from .models import RepoPackage, PackageSource
from .copr_client import CoprRepoClient, CoprError
from .dnf_client import DnfRepoClient, DnfError
from .source_manager import PackageSourceManager, SourceManagerError

__all__ = [
    "RepoPackage",
    "PackageSource",
    "CoprRepoClient",
    "CoprError",
    "DnfRepoClient",
    "DnfError",
    "PackageSourceManager",
    "SourceManagerError",
]
