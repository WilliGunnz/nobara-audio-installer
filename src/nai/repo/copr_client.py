"""
COPR repository client for fetching package listings from audinux.

Talks directly to the COPR v3 REST API (no python-copr dependency).
Designed for the ycollet/audinux COPR project but works with any public COPR.
"""

from __future__ import annotations

import logging
import platform
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

from .models import RepoPackage, PackageSource

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

COPR_BASE_URL = "https://copr.fedorainfracloud.org/api_3"
DEFAULT_OWNER = "ycollet"
DEFAULT_PROJECT = "audinux"
DEFAULT_CACHE_TTL = 600  # 10 minutes
PAGE_SIZE = 100

# ── Exceptions ────────────────────────────────────────────────────────────────

class CoprError(Exception):
    """Base error for COPR client operations."""

class CoprConnectionError(CoprError):
    """Could not reach the COPR API (network / DNS / timeout)."""

class CoprAPIError(CoprError):
    """COPR API responded with a non-200 status."""
    def __init__(self, status_code: int, message: str = ""):
        self.status_code = status_code
        super().__init__(f"COPR API error {status_code}: {message}")

# ── Chroot detection ──────────────────────────────────────────────────────────

def detect_chroot() -> Optional[str]:
    """
    Detect the appropriate COPR chroot for the running system.
    Returns something like 'fedora-43-x86_64' or None if detection fails.
    """
    arch = platform.machine()

    try:
        os_release = _read_os_release()
        version = os_release.get("VERSION_ID")
        base_id = os_release.get("ID", "")

        if base_id in ("nobara", "fedora"):
            if version and version.isdigit():
                return f"fedora-{version}-{arch}"
    except Exception as e:
        logger.warning("Could not detect Fedora version from /etc/os-release: %s", e)

    try:
        result = subprocess.run(
            ["rpm", "-q", "--qf", "%{version}", "fedora-release"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            ver = result.stdout.strip()
            return f"fedora-{ver}-{arch}"
    except Exception:
        pass

    logger.warning("Could not auto-detect chroot; caller must specify one.")
    return None

def _read_os_release(path: str = "/etc/os-release") -> dict[str, str]:
    """Parse /etc/os-release into a dict."""
    data: dict[str, str] = {}
    release_file = Path(path)
    if not release_file.exists():
        release_file = Path("/usr/lib/os-release")
    if not release_file.exists():
        return data

    for line in release_file.read_text().splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            data[key.strip()] = value
    return data

# ── Cache ─────────────────────────────────────────────────────────────────────

@dataclass
class _Cache:
    packages: list[RepoPackage] = field(default_factory=list)
    fetched_at: float = 0.0

    @property
    def is_empty(self) -> bool:
        return len(self.packages) == 0

    def age(self) -> float:
        return time.time() - self.fetched_at if self.fetched_at else float("inf")

# ── Client ────────────────────────────────────────────────────────────────────

class CoprRepoClient:
    """
    Fetches and caches package listings from a COPR repository.

    Usage:
        client = CoprRepoClient()  # defaults to ycollet/audinux
        packages = client.list_packages()  # auto-detects chroot
        results = client.search("cardinal")
    """

    def __init__(
        self,
        owner: str = DEFAULT_OWNER,
        project: str = DEFAULT_PROJECT,
        timeout: int = 30,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        chroot: Optional[str] = None,
    ):
        self.owner = owner
        self.project = project
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._chroot_override = chroot
        self._cache = _Cache()
        self._repo_id = f"{owner}/{project}"

    @property
    def chroot(self) -> Optional[str]:
        if self._chroot_override:
            return self._chroot_override
        return detect_chroot()

    @property
    def repo_id(self) -> str:
        return self._repo_id

    # ── Public API ──────────────────────────────────────────────────────────

    def list_packages(
        self,
        *,
        chroot: Optional[str] = None,
        state: str = "succeeded",
        arch: Optional[str] = None,
        use_cache: bool = True,
    ) -> list[RepoPackage]:
        """
        Fetch all packages from the COPR project.

        Args:
            chroot: Filter by chroot. If None, uses auto-detected chroot.
                    Pass empty string '' to disable chroot filtering.
            state: Filter by build state. Default: 'succeeded'.
            arch: Filter by architecture. None = all.
            use_cache: If True and cache is fresh, reuse cached results.
        """
        effective_chroot = chroot if chroot is not None else self.chroot
        if effective_chroot == "":
            effective_chroot = None

        if use_cache and self._cache_is_fresh():
            results = self._cache.packages
        else:
            results = self._fetch_all_pages()
            self._cache = _Cache(packages=results, fetched_at=time.time())

        # Only filter by chroot if packages actually have chroot info
        if effective_chroot:
            filtered = [p for p in results if p.chroot == effective_chroot]
            if not filtered and results:
                logger.info(
                    "Chroot filter '%s' removed all %d packages; "
                    "COPR API doesn't provide chroot on package level, keeping all",
                    effective_chroot, len(results),
                )
            else:
                results = filtered

        # Only filter by state if packages have state info
        if state:
            filtered = [p for p in results if p.state == state]
            if not filtered and results:
                logger.info(
                    "State filter '%s' removed all %d packages; keeping all",
                    state, len(results),
                )
            else:
                results = filtered

        if arch:
            filtered = [p for p in results if p.arch == arch]
            if not filtered and results:
                logger.info("Arch filter '%s' removed all packages; keeping all", arch)
            else:
                results = filtered

        return results

    def search(
        self,
        query: str,
        *,
        chroot: Optional[str] = None,
        state: str = "succeeded",
    ) -> list[RepoPackage]:
        """Case-insensitive substring search on package name."""
        pkgs = self.list_packages(chroot=chroot, state=state)
        q = query.lower()
        return [p for p in pkgs if q in p.name.lower()]

    def get_package(
        self,
        name: str,
        *,
        chroot: Optional[str] = None,
        state: str = "succeeded",
    ) -> Optional[RepoPackage]:
        """Return the first package with an exact name match, or None."""
        pkgs = self.list_packages(chroot=chroot, state=state)
        for p in pkgs:
            if p.name == name:
                return p
        return None

    def is_repo_enabled(self) -> bool:
        """Check whether the COPR repo is enabled in dnf."""
        repo_dirs = [
            Path("/etc/yum.repos.d"),
            Path.home() / ".config" / "dnf" / "repos.d",
        ]
        repo_pattern = f"{self.owner}-{self.project}"

        for repo_dir in repo_dirs:
            if not repo_dir.is_dir():
                continue
            for repo_file in repo_dir.glob("*.repo"):
                try:
                    if repo_pattern in repo_file.read_text():
                        return True
                except OSError:
                    continue
        return False

    def repo_enable_command(self) -> str:
        return f"sudo dnf copr enable {self.owner}/{self.project}"

    def install_command(self, package_name: str) -> str:
        return f"sudo dnf install {package_name}"

    def clear_cache(self) -> None:
        self._cache = _Cache()

    def cache_age(self) -> float:
        return self._cache.age()

    # ── Internal: fetching ───────────────────────────────────────────────────

    def _fetch_all_pages(self) -> list[RepoPackage]:
        """Fetch all packages from COPR, handling pagination."""
        all_packages: list[RepoPackage] = []
        offset = 0

        while True:
            params = {
                "ownername": self.owner,
                "projectname": self.project,
                "limit": PAGE_SIZE,
                "offset": offset,
                "order": "name",
            }

            logger.debug(
                "Fetching COPR packages: %s/%s offset=%d",
                self.owner, self.project, offset,
            )

            try:
                resp = requests.get(
                    f"{COPR_BASE_URL}/package/list",
                    params=params,
                    timeout=self.timeout,
                )
            except requests.exceptions.Timeout:
                raise CoprConnectionError(
                    f"Timed out contacting COPR API after {self.timeout}s"
                )
            except requests.exceptions.ConnectionError as e:
                raise CoprConnectionError(f"Cannot reach COPR API: {e}")

            if resp.status_code != 200:
                raise CoprAPIError(resp.status_code, resp.text[:500])

            body = resp.json()

            # COPR API returns {"items": [...], "meta": {...}}
            if isinstance(body, dict):
                page_packages = body.get("items", body.get("packages", []))
            elif isinstance(body, list):
                page_packages = body
            else:
                page_packages = []

            logger.debug("COPR API returned %d raw items", len(page_packages))

            for raw in page_packages:
                pkg = self._parse_package(raw)
                if pkg:
                    all_packages.append(pkg)

            # Pagination check
            if isinstance(body, dict):
                meta = body.get("meta", {})
                total = 0
                if isinstance(meta, dict):
                    total = meta.get("total", 0)

                if total and offset + len(page_packages) < total:
                    offset += len(page_packages)
                    continue

            break

        logger.info(
            "Fetched %d packages from %s/%s",
            len(all_packages), self.owner, self.project,
        )
        return all_packages

    def _parse_package(self, raw: dict) -> Optional[RepoPackage]:
        """Parse a raw API response dict into a RepoPackage."""
        try:
            if not isinstance(raw, dict):
                return None

            name = raw.get("name", "")
            if not name:
                return None

            # Extract version/state/chroot from builds list if available
            version = ""
            release = ""
            arch = ""
            chroot = ""
            state = "available"

            builds = raw.get("builds", [])
            if isinstance(builds, list) and builds:
                # Find the latest succeeded build
                latest_build = None
                for b in builds:
                    if isinstance(b, dict):
                        b_state = b.get("state", "")
                        if b_state == "succeeded":
                            latest_build = b
                            break
                    elif isinstance(b, int):
                        latest_build = {"id": b}
                        break

                if not latest_build and isinstance(builds[0], dict):
                    latest_build = builds[0]

                if latest_build and isinstance(latest_build, dict):
                    version = latest_build.get("version", "")
                    release = latest_build.get("release", "")
                    arch = latest_build.get("arch", "")
                    chroot = latest_build.get("chroot", latest_build.get("own_chroot", ""))
                    state = latest_build.get("state", "available")

            # Also try source_dict for version info
            if not version:
                source_dict = raw.get("source_dict", {})
                if isinstance(source_dict, dict):
                    version = source_dict.get("version", "")
                    release = source_dict.get("release", "")

            return RepoPackage(
                name=name,
                version=version,
                release=release,
                arch=arch,
                epoch=int(raw.get("epoch", 0) or 0),
                chroot=chroot,
                state=state,
                summary=raw.get("summary", raw.get("description", "")),
                url=raw.get("url", raw.get("rpm_path", "")),
                source=PackageSource.COPR,
                repo_id=self._repo_id,
            )
        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse COPR package entry: %s (keys=%s)",
                e,
                list(raw.keys()) if isinstance(raw, dict) else "N/A",
            )
            return None

    # ── Internal: cache helpers ──────────────────────────────────────────────

    def _cache_is_fresh(self) -> bool:
        return (
            not self._cache.is_empty
            and self._cache.age() < self.cache_ttl
        )
