"""
Package source manager — aggregates multiple repository sources
(COPR + local dnf repos) into a unified query interface.

The Plugins tab UI talks to this manager instead of individual clients,
so it doesn't need to know or care where a package comes from.
"""

from __future__ import annotations

import logging
from typing import Optional, Protocol

from .models import RepoPackage, PackageSource

logger = logging.getLogger(__name__)

# ── Exceptions ────────────────────────────────────────────────────────────────

class SourceManagerError(Exception):
    """Base error for source manager operations."""

# ── Protocol ──────────────────────────────────────────────────────────────────

class PackageQueryable(Protocol):
    """Interface that any package source must implement."""

    def search(self, query: str, **kwargs) -> list[RepoPackage]: ...
    def get_package(self, name: str, **kwargs) -> Optional[RepoPackage]: ...

# ── Manager ───────────────────────────────────────────────────────────────────

class PackageSourceManager:
    """
    Aggregates multiple package sources and provides unified search.

    Sources are tried in order; results are merged and deduplicated by name,
    preferring the first source that returns a given package.

    Usage:
        mgr = PackageSourceManager()
        mgr.add_source("audinux", copr_client)
        mgr.add_source("dnf", dnf_client)

        # Search across ALL sources
        results = mgr.search("ardour")
        # → finds Ardour from dnf repos

        results = mgr.search("cardinal")
        # → finds Cardinal from audinux COPR

        # Search a SPECIFIC source only
        results = mgr.search("ardour", source="dnf")
    """

    def __init__(self) -> None:
        self._sources: dict[str, PackageQueryable] = {}
        self._errors: dict[str, str] = {}  # source_name → last error message

    # ── Source management ──────────────────────────────────────────────────

    def add_source(self, name: str, client: PackageQueryable) -> None:
        """Register a package source under a friendly name."""
        self._sources[name] = client
        logger.info("Added package source: %s", name)

    def remove_source(self, name: str) -> None:
        """Remove a registered source."""
        if name in self._sources:
            del self._sources[name]
            self._errors.pop(name, None)
            logger.info("Removed package source: %s", name)

    @property
    def source_names(self) -> list[str]:
        return list(self._sources.keys())

    @property
    def last_errors(self) -> dict[str, str]:
        """Per-source error messages from the last operation."""
        return dict(self._errors)

    # ── Unified queries ─────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        source: Optional[str] = None,
    ) -> list[RepoPackage]:
        """
        Search across all (or one specific) source(s).

        Results from multiple sources are merged. If the same package name
        appears in multiple sources, the first source wins (insertion order).

        Args:
            query: Package name or partial name.
            source: Limit to a specific source name. None = search all.
        """
        if source:
            if source not in self._sources:
                raise SourceManagerError(f"Unknown source: {source}")
            sources_to_query = {source: self._sources[source]}
        else:
            sources_to_query = dict(self._sources)

        all_results: list[RepoPackage] = []
        seen_names: set[str] = set()

        for src_name, client in sources_to_query.items():
            try:
                results = client.search(query)
                self._errors.pop(src_name, None)

                for pkg in results:
                    if pkg.name not in seen_names:
                        seen_names.add(pkg.name)
                        all_results.append(pkg)

            except Exception as e:
                self._errors[src_name] = str(e)
                logger.warning("Source '%s' failed during search: %s", src_name, e)

        # Sort by name for consistent display
        all_results.sort(key=lambda p: p.name.lower())
        return all_results

    def get_package(
        self,
        name: str,
        *,
        source: Optional[str] = None,
    ) -> Optional[RepoPackage]:
        """
        Find a package by exact name across all (or one specific) source(s).

        Returns the first match found, checking sources in insertion order.
        """
        if source:
            if source not in self._sources:
                raise SourceManagerError(f"Unknown source: {source}")
            try:
                return self._sources[source].get_package(name)
            except Exception as e:
                self._errors[source] = str(e)
                return None

        for src_name, client in self._sources.items():
            try:
                pkg = client.get_package(name)
                self._errors.pop(src_name, None)
                if pkg:
                    return pkg
            except Exception as e:
                self._errors[src_name] = str(e)
                logger.warning("Source '%s' failed during get_package: %s", src_name, e)

        return None

    def clear_all_caches(self) -> None:
        """Clear caches on all registered sources that support it."""
        for src_name, client in self._sources.items():
            clear_fn = getattr(client, "clear_cache", None)
            if callable(clear_fn):
                clear_fn()
                logger.debug("Cleared cache for source: %s", src_name)
