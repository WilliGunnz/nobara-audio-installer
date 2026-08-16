"""GitHub API integration for package publishing."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ..config import Config


MANIFEST_FILENAME = "packages.json"


@dataclass
class GitHubRelease:
    """Representation of a GitHub release."""
    tag_name: str
    name: str
    body: str
    draft: bool = False
    prerelease: bool = False
    upload_url: str = ""


@dataclass
class GitHubAsset:
    """Representation of a GitHub release asset."""
    id: int
    name: str
    size: int
    download_count: int
    browser_download_url: str


class GitHubAPIError(Exception):
    """Raised when GitHub API operations fail."""
    pass


def _get_auth_headers(token: str) -> Dict[str, str]:
    """Build authentication headers for GitHub API."""
    if not token:
        raise GitHubAPIError("GitHub token is required")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Nobara-Audio-Installer",
    }


def _api_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> requests.Response:
    """Make a request to the GitHub API with error handling."""
    try:
        response = requests.request(method, url, headers=headers, json=json_data, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.HTTPError as e:
        raise GitHubAPIError(f"HTTP {e.response.status_code}: {e.response.text}") from e
    except requests.RequestException as e:
        raise GitHubAPIError(f"Network error: {e}") from e


def get_repository_owner_and_name(repo_full: str) -> tuple[str, str]:
    """
    Parse a full repository name like 'owner/repo' into components.

    Args:
        repo_full: Full repository name (e.g., 'WilliGunnz/nobara-audio-installer')

    Returns:
        Tuple of (owner, repo)
    """
    if "/" not in repo_full:
        raise ValueError(f"Invalid repository format: {repo_full}. Expected 'owner/repo'")
    owner, repo = repo_full.split("/", 1)
    return owner, repo


def create_or_update_release(
    repo_full: str,
    tag: str,
    name: str,
    body: str,
    draft: bool = False,
    prerelease: bool = False,
    token: str = "",
) -> GitHubRelease:
    """
    Create a new GitHub release or update an existing one.

    Args:
        repo_full: Full repository name (e.g., 'owner/repo')
        tag: Git tag name (e.g., 'v1.0.0')
        name: Release title
        body: Release notes/description
        draft: Whether to create as draft
        prerelease: Whether to mark as pre-release
        token: GitHub API token

    Returns:
        GitHubRelease object with upload_url
    """
    owner, repo = get_repository_owner_and_name(repo_full)
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = _get_auth_headers(token)

    # Try to find existing release by tag
    existing_url = f"{base_url}/releases/tags/{tag}"
    try:
        response = _api_request("GET", existing_url, headers)
        data = response.json()
        # Release exists, update it
        update_url = f"{base_url}/releases/{data['id']}"
        payload = {
            "tag_name": tag,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease,
        }
        response = _api_request("PATCH", update_url, headers, json_data=payload)
        result = response.json()
        return GitHubRelease(
            tag_name=result["tag_name"],
            name=result["name"],
            body=result.get("body", ""),
            draft=result.get("draft", False),
            prerelease=result.get("prerelease", False),
            upload_url=result.get("upload_url", ""),
        )
    except GitHubAPIError as e:
        if "404" in str(e):
            # Release doesn't exist, create new one
            releases_url = f"{base_url}/releases"
            payload = {
                "tag_name": tag,
                "name": name,
                "body": body,
                "draft": draft,
                "prerelease": prerelease,
            }
            response = _api_request("POST", releases_url, headers, json_data=payload)
            result = response.json()
            return GitHubRelease(
                tag_name=result["tag_name"],
                name=result["name"],
                body=result.get("body", ""),
                draft=result.get("draft", False),
                prerelease=result.get("prerelease", False),
                upload_url=result.get("upload_url", ""),
            )
        raise


def get_latest_release(repo_full: str, token: str = "") -> Optional[GitHubRelease]:
    """
    Get the latest release for a repository.

    Args:
        repo_full: Full repository name
        token: GitHub API token

    Returns:
        GitHubRelease object or None if no release exists
    """
    owner, repo = get_repository_owner_and_name(repo_full)
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = _get_auth_headers(token)

    try:
        releases_url = f"{base_url}/releases/latest"
        response = _api_request("GET", releases_url, headers)
        data = response.json()
        return GitHubRelease(
            tag_name=data["tag_name"],
            name=data["name"],
            body=data.get("body", ""),
            draft=data.get("draft", False),
            prerelease=data.get("prerelease", False),
            upload_url="",
        )
    except GitHubAPIError:
        return None


def upload_release_asset(
    release_upload_url: str,
    asset_path: Path,
    asset_name: str,
    token: str,
    mime_type: str = "application/zip",
) -> GitHubAsset:
    """
    Upload an asset to a GitHub release.

    Args:
        release_upload_url: The upload_url from the release object
        asset_path: Path to the file to upload
        asset_name: Name the asset should have
        token: GitHub API token
        mime_type: MIME type of the asset

    Returns:
        GitHubAsset object with download URL
    """
    if not asset_path.exists():
        raise FileNotFoundError(f"Asset file not found: {asset_path}")

    # Clean up the upload URL (remove template parts)
    clean_url = release_upload_url.replace("{?name,label}", "")
    headers = _get_auth_headers(token)
    headers["Content-Type"] = mime_type

    params = {"name": asset_name}

    with open(asset_path, "rb") as f:
        response = _api_request("POST", clean_url, headers, json_data=None)

    # Actually we need multipart form data for uploads
    headers.pop("Content-Type")
    response = requests.post(
        clean_url,
        params=params,
        headers=headers,
        data=f.read(),
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()

    return GitHubAsset(
        id=data["id"],
        name=data["name"],
        size=data["size"],
        download_count=data["download_count"],
        browser_download_url=data["browser_download_url"],
    )


def delete_release_asset(repo_full: str, asset_id: int, token: str) -> bool:
    """
    Delete an asset from a GitHub release.

    Args:
        repo_full: Full repository name
        asset_id: The asset ID to delete
        token: GitHub API token

    Returns:
        True if successful
    """
    owner, repo = get_repository_owner_and_name(repo_full)
    delete_url = f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{asset_id}"
    headers = _get_auth_headers(token)

    try:
        response = _api_request("DELETE", delete_url, headers)
        return response.status_code == 204
    except GitHubAPIError:
        return False


def validate_github_credentials(repo_full: str, token: str) -> bool:
    """
    Validate that the GitHub token has access to the repository.

    Args:
        repo_full: Full repository name
        token: GitHub API token

    Returns:
        True if credentials are valid, False otherwise
    """
    if not token:
        return False
    try:
        owner, repo = get_repository_owner_and_name(repo_full)
        test_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = _get_auth_headers(token)
        _api_request("GET", test_url, headers)
        return True
    except GitHubAPIError:
        return False


def get_release_by_tag(repo_full: str, tag: str, token: str) -> Optional[GitHubRelease]:
    """
    Get a specific release by its tag name.

    Args:
        repo_full: Full repository name
        tag: Tag name (e.g., 'v1.0.0')
        token: GitHub API token

    Returns:
        GitHubRelease object or None if not found
    """
    owner, repo = get_repository_owner_and_name(repo_full)
    release_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    headers = _get_auth_headers(token)

    try:
        response = _api_request("GET", release_url, headers)
        data = response.json()
        return GitHubRelease(
            tag_name=data["tag_name"],
            name=data["name"],
            body=data.get("body", ""),
            draft=data.get("draft", False),
            prerelease=data.get("prerelease", False),
            upload_url=data.get("upload_url", ""),
        )
    except GitHubAPIError:
        return None
