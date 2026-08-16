"""Configuration management for Nobara Audio Installer."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
CONFIG_DIR = Path.home() / ".config" / "nobara-audio-installer"
USER_CONFIG_FILE = CONFIG_DIR / "config.json"
MY_PLUGINS_LIST = PLUGINS_DIR / "my-plugins.list"

class Config:
    """Application configuration handler."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if USER_CONFIG_FILE.exists():
            try:
                with open(USER_CONFIG_FILE, "r") as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache = self._defaults()
        else:
            self._cache = self._defaults()

    def _defaults(self) -> Dict[str, Any]:
        return {
            "github_repo": "",
            "github_token": "",
            "install_path": str(Path.home() / ".local" / "share" / "nai" / "packages"),
            "auto_update": True,
            "theme": "dark",
            "language": "en",
            "content_path": str(Path.home() / "Documents" / "nobara-audio-content"),
            "library_path": str(Path.home() / "Documents" / "nobara-audio-library"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(self._cache, f, indent=2)

    # --- GitHub settings ---
    @property
    def github_repo(self) -> str:
        return self.get("github_repo", "")

    @github_repo.setter
    def github_repo(self, value: str) -> None:
        self.set("github_repo", value)

    @property
    def github_token(self) -> str:
        return self.get("github_token", "")

    @github_token.setter
    def github_token(self, value: str) -> None:
        self.set("github_token", value)

    # --- Install path (with alias for install_prefix) ---
    @property
    def install_path(self) -> str:
        return self.get("install_path", str(Path.home() / ".local" / "share" / "nai" / "packages"))

    @install_path.setter
    def install_path(self, value: str) -> None:
        self.set("install_path", value)

    @property
    def install_prefix(self) -> str:
        """Alias for install_path - used by installer modules."""
        return self.install_path

    @install_prefix.setter
    def install_prefix(self, value: str) -> None:
        self.install_path = value

    # --- Content and library paths ---
    @property
    def content_path(self) -> str:
        return self.get("content_path", "")

    @content_path.setter
    def content_path(self, value: str) -> None:
        self.set("content_path", value)

    @property
    def library_path(self) -> str:
        return self.get("library_path", "")

    @library_path.setter
    def library_path(self, value: str) -> None:
        self.set("library_path", value)

    # --- Other settings ---
    @property
    def auto_update(self) -> bool:
        return self.get("auto_update", True)

    @auto_update.setter
    def auto_update(self, value: bool) -> None:
        self.set("auto_update", value)

    @property
    def theme(self) -> str:
        return self.get("theme", "dark")

    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)

    @property
    def language(self) -> str:
        return self.get("language", "en")

    @language.setter
    def language(self, value: str) -> None:
        self.set("language", value)

def get_my_plugins() -> list:
    """Read plugin IDs from my-plugins.list, one per line."""
    if not MY_PLUGINS_LIST.exists():
        return []
    lines = MY_PLUGINS_LIST.read_text().strip().splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]

def set_my_plugins(plugin_ids: list) -> None:
    """Write plugin IDs to my-plugins.list, one per line."""
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    content = "\n".join(str(pid) for pid in plugin_ids)
    MY_PLUGINS_LIST.write_text(content + "\n")

def init_default_config() -> Config:
    """Create a new default configuration file if none exists."""
    if not USER_CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cfg = Config()
        cfg.save()
    return Config()

def get_config() -> Config:
    """Factory function to get a Config instance."""
    return Config()
