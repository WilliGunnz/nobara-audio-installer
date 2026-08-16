"""
DNF repository client for querying local system repos.

Uses `dnf repoquery` (or `dnf5 query` on newer systems) to search packages
across all enabled dnf repositories: Nobara base, Fedora updates, RPM Fusion, etc.

This is how we find packages like Ardour that live in the standard repos
rather than in a COPR repo like audinux.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

from .models import RepoPackage, PackageSource

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_CACHE_TTL = 300  # 5 minutes — dnf repoquery is slower than COPR API
QUERY_TIMEOUT = 120       # dnf can be slow, especially first run

# ── Exceptions ────────────────────────────────────────────────────────────────

class DnfError(Exception):
    """Base error for DNF client operations."""

class DnfNotAvailableError(DnfError):
    """dnf is not installed on this system."""

class DnfQueryError(DnfError):
    """dnf repoquery failed or returned unexpected output."""

# ── Cache ─────────────────────────────────────────────────────────────────────

@dataclass
class _DnfCache:
    packages: list[RepoPackage] = field(default_factory=list)
    fetched_at: float = 0.0
    query_key: str = ""  # what was searched for (empty = all)

    @property
    def is_empty(self) -> bool:
        return len(self.packages) == 0

    def age(self) -> float:
        return time.time() - self.fetched_at if self.fetched_at else float("inf")

# ── Client ────────────────────────────────────────────────────────────────────

class DnfRepoClient:
    """
    Queries local dnf repositories for available packages.

    This covers all enabled repos on the system: Nobara base, Fedora updates,
    RPM Fusion, and any COPR repos that are already enabled.

    Unlike CoprRepoClient (which talks to a remote API), this shells out to
    `dnf repoquery` / `dnf5 query` locally.

    Usage:
        client = DnfRepoClient()
        # Search for a specific package
        results = client.search("ardour")
        # Or list all packages from a specific repo
        results = client.list_packages(repo="fedora")
    """

    def __init__(
        self,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        timeout: int = QUERY_TIMEOUT,
    ):
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self._cache = _DnfCache()

        # Detect which dnf binary to use
        self._dnf_bin = self._detect_dnf_binary()

    @staticmethod
    def _detect_dnf_binary() -> str:
        """Detect whether to use dnf or dnf5."""
        for binary in ("dnf5", "dnf"):
            if shutil.which(binary):
                return binary
        raise DnfNotAvailableError(
            "Neither dnf nor dnf5 found. Is this a Fedora/Nobara system?"
        )

    @property
    def dnf_binary(self) -> str:
        return self._dnf_bin

    @property
    def is_dnf5(self) -> bool:
        return self._dnf_bin == "dnf5"

    # ── Public API ──────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        repo: Optional[str] = None,
        use_cache: bool = True,
    ) -> list[RepoPackage]:
        """
        Search for packages by name (substring match).

        Args:
            query: Package name or partial name to search for.
            repo: Limit to a specific repo ID (e.g. 'fedora', 'updates',
                  'rpmfusion-free'). None = search all repos.
            use_cache: Reuse cached results if fresh and query matches.
        """
        cache_key = f"search:{query.lower()}:{repo or 'all'}"

        if use_cache and self._cache_is_fresh(cache_key):
            return self._cache.packages

        results = self._repoquery(
            query=query,
            repo=repo,
        )

        self._cache = _DnfCache(
            packages=results,
            fetched_at=time.time(),
            query_key=cache_key,
        )

        return results

    def get_package(
        self,
        name: str,
        *,
        repo: Optional[str] = None,
    ) -> Optional[RepoPackage]:
        """Find a package by exact name. Returns first match or None."""
        results = self.search(name, repo=repo)
        for pkg in results:
            if pkg.name == name:
                return pkg
        return None

    def list_packages(
        self,
        *,
        repo: Optional[str] = None,
        use_cache: bool = False,  # listing ALL packages is expensive
    ) -> list[RepoPackage]:
        """
        List all available packages (optionally from a specific repo).

        WARNING: This can return tens of thousands of packages and take
        a while. Prefer search() for most use cases.
        """
        cache_key = f"list:{repo or 'all'}"

        if use_cache and self._cache_is_fresh(cache_key):
            return self._cache.packages

        results = self._repoquery(query=None, repo=repo)

        self._cache = _DnfCache(
            packages=results,
            fetched_at=time.time(),
            query_key=cache_key,
        )

        return results

    def is_installed(self, name: str) -> bool:
        """Check whether a package is currently installed."""
        try:
            cmd = [self._dnf_bin, "repoquery", "--installed", "--qf", "%{name}", name]
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=30,
            )
            return result.returncode == 0 and name in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("Failed to check if %s is installed: %s", name, e)
            return False

    def install_command(self, package_name: str) -> str:
        """Return the shell command to install a package."""
        return f"sudo dnf install {package_name}"

    def clear_cache(self) -> None:
        self._cache = _DnfCache()

    def cache_age(self) -> float:
        return self._cache.age()

    # ── Internal: repoquery ─────────────────────────────────────────────────

    def _repoquery(
        self,
        *,
        query: Optional[str],
        repo: Optional[str] = None,
    ) -> list[RepoPackage]:
        """
        Run dnf repoquery and parse the JSON output.

        Uses --json flag (supported by both dnf4 and dnf5) for structured output.
        Falls back to --qf parsing if --json isn't available.
        """
        if self.is_dnf5:
            cmd = [self._dnf_bin, "query", "--json"]
        else:
            cmd = [self._dnf_bin, "repoquery", "--json"]

        if repo:
            cmd.extend(["--repoid", repo])

        if query:
            # Pass query as positional argument (glob matching)
            cmd.append(f"*{query}*")

        logger.debug("Running dnf query: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            raise DnfQueryError(
                f"dnf repoquery timed out after {self.timeout}s. "
                "The metadata may still be downloading."
            )
        except FileNotFoundError:
            raise DnfNotAvailableError(
                f"{self._dnf_bin} not found despite initial detection."
            )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            # --json might not be supported; fall back to --qf parsing
            if "unrecognized" in stderr.lower() or "unknown" in stderr.lower():
                logger.info("--json not supported, falling back to --qf parsing")
                return self._repoquery_qf(query=query, repo=repo)

            raise DnfQueryError(
                f"dnf repoquery failed (exit {result.returncode}): {stderr[:300]}"
            )

        # Parse JSON output
        try:
            raw_packages = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse dnf JSON output: %s", e)
            # Fall back to --qf parsing
            return self._repoquery_qf(query=query, repo=repo)

        if not isinstance(raw_packages, list):
            raw_packages = [raw_packages] if raw_packages else []

        packages: list[RepoPackage] = []
        for raw in raw_packages:
            pkg = self._parse_json_package(raw)
            if pkg:
                packages.append(pkg)

        logger.info("dnf query returned %d packages", len(packages))
        return packages

    def _repoquery_qf(
        self,
        *,
        query: Optional[str],
        repo: Optional[str] = None,
    ) -> list[RepoPackage]:
        """
        Fallback: parse dnf repoquery output using a custom query format.

        Used when --json is not available (older dnf versions).
        """
        # Format: name|epoch|version|release|arch|summary|repo_id
        qf_format = "%{name}|%{epoch}|%{version}|%{release}|%{arch}|%{summary}|%{reponame}"

        cmd = [self._dnf_bin, "repoquery", "--qf", qf_format]

        if repo:
            cmd.extend(["--repoid", repo])

        if query:
            # Pass query as positional argument (glob matching)
            cmd.append(f"*{query}*")

        logger.debug("Running dnf query (qf fallback): %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            raise DnfQueryError(
                f"dnf repoquery timed out after {self.timeout}s"
            )

        if result.returncode != 0:
            raise DnfQueryError(
                f"dnf repoquery failed (exit {result.returncode}): "
                f"{result.stderr.strip()[:300]}"
            )

        packages: list[RepoPackage] = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            pkg = self._parse_qf_line(line)
            if pkg:
                packages.append(pkg)

        logger.info("dnf query (qf) returned %d packages", len(packages))
        return packages

    def _parse_json_package(self, raw: dict) -> Optional[RepoPackage]:
        """Parse a JSON object from `dnf repoquery --json` into a RepoPackage."""
        try:
            # dnf5 JSON field names (may vary slightly between versions)
            name = raw.get("name", "")
            if not name:
                return None

            return RepoPackage(
                name=name,
                version=raw.get("version", ""),
                release=raw.get("release", ""),
                arch=raw.get("arch", ""),
                epoch=int(raw.get("epoch", 0) or 0),
                summary=raw.get("summary", raw.get("description", "")),
                source=PackageSource.DNF,
                repo_id=raw.get("repo_id", raw.get("repo", raw.get("reponame", "unknown"))),
                state="available",
            )
        except (ValueError, TypeError) as e:
            logger.warning("Failed to parse dnf JSON package: %s", e)
            return None

    def _parse_qf_line(self, line: str) -> Optional[RepoPackage]:
        """Parse a pipe-delimited line from --qf output into a RepoPackage."""
        try:
            parts = line.split("|")
            if len(parts) < 7:
                return None

            name, epoch, version, release, arch, summary, repo_id = parts[:7]

            return RepoPackage(
                name=name,
                version=version,
                release=release,
                arch=arch,
                epoch=int(epoch) if epoch.isdigit() else 0,
                summary=summary,
                source=PackageSource.DNF,
                repo_id=repo_id,
                state="available",
            )
        except (ValueError, TypeError) as e:
            logger.warning("Failed to parse dnf qf line '%s': %s", line, e)
            return None

    # ── Internal: cache helpers ──────────────────────────────────────────────

    def _cache_is_fresh(self, cache_key: str) -> bool:
        return (
            not self._cache.is_empty
            and self._cache.query_key == cache_key
            and self._cache.age() < self.cache_ttl
        )
