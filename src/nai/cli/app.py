"""Main CLI application for Nobara Audio Installer."""

from pathlib import Path
from typing import Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table

from nai.config import Config, get_my_plugins
from nai.publisher.publish import publish_package, scan_packages
from nai.installer.install import install_package
from nai.installer.uninstall import uninstall_package, list_installed
from nai.installer.verify import verify_package
from nai.installer.update import check_for_updates

app = typer.Typer(
    name="nai",
    help="Nobara Audio Installer — manage audio packages on Nobara Linux.",
    add_completion=False,
)

console = Console()


# =============================================================================
# Doctor Command
# =============================================================================

@app.command()
def doctor():
    """Run diagnostics on the system environment."""
    from nai.config import Config

    console.print("[bold cyan]Running diagnostics...[/bold cyan]\n")

    cfg = Config()

    checks = [
        ("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", True),
        ("Configuration", str(Path.home() / ".config" / "nai" / "config.json"), cfg.get("github_repo") != "", False),
        ("Library Path", cfg.get("library_path", "(not set)"), bool(cfg.get("library_path")), False),
        ("Content Repo", cfg.get("content_path", "(not set)"), bool(cfg.get("content_path")), False),
    ]

    table = Table(title="System Checks")
    table.add_column("Check", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", justify="center")

    passed = 0
    failed = 0

    for name, value, success, _ in checks:
        status = "[bold green]✓[/bold green]" if success else "[bold red]✗[/bold red]"
        table.add_row(name, str(value), status)
        if success:
            passed += 1
        else:
            failed += 1

    console.print(table)
    console.print()

    if failed > 0:
        console.print("[yellow]Some checks failed. Configure missing items.[/yellow]")
    else:
        console.print("[bold green]All checks passed![/bold green]")


# =============================================================================
# Config Command
# =============================================================================

@app.command()
def config(
    init: bool = typer.Option(False, "--init", help="Initialize a default config file."),
    get: Optional[str] = typer.Option(None, "--get", help="Get a configuration value."),
    set_key: Optional[str] = typer.Option(None, "--set-key", help="Set a configuration key."),
    set_value: Optional[str] = typer.Option(None, "--set-value", help="Set a configuration value."),
    unset: bool = typer.Option(False, "--unset", help="Unset a configuration key."),
    list_: bool = typer.Option(False, "--list", "-l", help="List all configuration values."),
):
    """View and manage NAI configuration."""
    from nai.config import Config

    cfg = Config()

    if init:
        cfg.save()
        console.print(f"[green]✓ Configuration initialized:[/green] {cfg._cache}")
        return

    if list_:
        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        for key, value in cfg._cache.items():
            table.add_row(key, str(value))

        console.print(table)
        return

    if get:
        value = cfg.get(get, "(not set)")
        console.print(f"{value}")
        return

    if set_key and set_value:
        cfg.set(set_key, set_value)
        cfg.save()
        console.print(f"[green]✓ Set {set_key} = {set_value}[/green]")
        return

    if unset:
        console.print("[yellow]--unset not yet implemented[/yellow]")
        return

    # Show current config if no arguments
    table = Table(title="Current Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    for key, value in cfg._cache.items():
        table.add_row(key, str(value))

    console.print(table)


# =============================================================================
# Scan Command
# =============================================================================

@app.command()
def scan(
    path: Path = typer.Argument(..., help="Directory to scan for packages"),
):
    """Scan a directory for valid audio packages."""
    from nai.core.package import load_package_metadata, validate_package_structure

    console.print(f"[cyan]Scanning:[/cyan] {path}\n")

    packages = []

    for item in path.iterdir():
        if item.is_dir():
            is_valid, error = validate_package_structure(item)
            if is_valid:
                metadata = load_package_metadata(item)
                if metadata:
                    packages.append({
                        "path": item,
                        "metadata": metadata,
                    })
                    console.print(f"[green]✓ Found[/green] {metadata.get('id')} v{metadata.get('version')}")
            else:
                console.print(f"[red]✗ Invalid:[/red] {item.name} - {error}")

    console.print()
    console.print(f"[bold]Total packages found:[/bold] {len(packages)}")


# =============================================================================
# Init-Package Command
# =============================================================================

@app.command()
def init_package(
    name: str = typer.Argument(..., help="Package name (will be used as ID)"),
    category: str = typer.Option(..., "--category", "-c", help="Package category"),
    output: Path = typer.Option(".", "--output", "-o", help="Output directory"),
):
    """Scaffold a new package directory with metadata.json."""
    import json

    package_dir = output / name
    package_dir.mkdir(parents=True, exist_ok=True)

    # Create required directories
    (package_dir / "artwork").mkdir(exist_ok=True)
    (package_dir / "files").mkdir(exist_ok=True)

    # Create metadata.json
    metadata = {
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "version": "1.0.0",
        "category": category,
        "author": "",
        "license": "CC-BY-4.0",
        "description": "",
        "tags": [],
    }

    metadata_file = package_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    # Create README.md
    readme = package_dir / "README.md"
    readme.write_text(f"# {name}\n\nDescription goes here.\n")

    # Create LICENSE
    license_file = package_dir / "LICENSE"
    license_file.write_text("License text goes here.\n")

    console.print(f"[green]✓ Created package scaffold:[/green] {package_dir}")


# =============================================================================
# Publish Command
# =============================================================================

@app.command()
def publish(
    package_id: str = typer.Argument(..., help="Package ID to publish"),
    library_path: Optional[Path] = typer.Option(None, "--library", "-l", help="Audio library path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't actually upload to GitHub"),
    no_upload: bool = typer.Option(False, "--no-upload", help="Skip GitHub upload"),
):
    """Publish a package to GitHub Releases and update the manifest."""
    from nai.config import Config
    from nai.core.package import find_package_by_id

    cfg = Config()

    if not library_path:
        library_path = Path(cfg.get("library_path", "~/Documents/nobara-audio-library"))

    # Find package in library
    target = None
    for category_dir in library_path.iterdir():
        if category_dir.is_dir():
            for pkg_dir in category_dir.iterdir():
                if pkg_dir.is_dir() and pkg_dir.name == package_id:
                    target = pkg_dir
                    break

    if not target:
        console.print(f"[red]✗ Package not found:[/red] {package_id}")
        raise typer.Exit(1)

    console.print(f"\n[dim]Publishing:[/dim] {package_id}")

    try:
        result = publish_package(target, dry_run=dry_run, no_upload=no_upload)

        console.print()
        console.print(f"[bold green]✓ Published:[/bold green] {result.id} v{result.version}")
        console.print(f"  [dim]Archive:[/dim]      {result.id}-{result.version}.zip")
        console.print(f"  [dim]Size:[/dim]         {format_size(result.size)}")
        console.print(f"  [dim]SHA-256:[/dim]     {result.sha256[:16]}...")
        console.print(f"  [dim]Download:[/dim]    {result.download if result.download else '(not uploaded)'}")

    except Exception as e:
        console.print(f"[red]Publish failed:[/red] {e}")
        raise typer.Exit(1)


def format_size(size_bytes: int) -> str:
    """Format byte count to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# =============================================================================
# Release Command
# =============================================================================

@app.command()
def release(
    bump: str = typer.Option("patch", "--bump", "-b", help="Version bump type (major/minor/patch)"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Release message"),
):
    """Create a new project release (version bump, tag, push)."""
    import subprocess
    import re

    version_file = Path("VERSION")

    if not version_file.exists():
        console.print("[red]✗ VERSION file not found[/red]")
        raise typer.Exit(1)

    current_version = version_file.read_text().strip()
    major, minor, patch = map(int, current_version.split("."))

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    version_file.write_text(new_version + "\n")

    console.print(f"[green]✓ Bumped version:[/green] {current_version} → {new_version}")

    # Commit changes
    subprocess.run(["git", "add", "VERSION"])
    commit_msg = message or f"Release v{new_version}"
    subprocess.run(["git", "commit", "-m", commit_msg])

    # Create tag
    tag_name = f"v{new_version}"
    subprocess.run(["git", "tag", tag_name])

    console.print(f"[green]✓ Created tag:[/green] {tag_name}")

    # Push
    subprocess.run(["git", "push"])
    subprocess.run(["git", "push", "--tags"])

    console.print("[green]✓ Pushed to remote[/green]")


# =============================================================================
# Install Command
# =============================================================================

@app.command()
def install(
    package_id: str = typer.Argument(..., help="Package ID to install"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install a package by ID."""
    console.print(f"[cyan]Installing:[/cyan] {package_id}\n")

    try:
        result = install_package(package_id, force=force)

        console.print(f"[green]✓ Installed:[/green] {result.name} v{result.version}")
        console.print(f"  [dim]Package:[/dim]        {result.id}")
        console.print(f"  [dim]Category:[/dim]      {result.category}")
        console.print(f"  [dim]Downloaded:[/dim]    {format_size(result.downloaded_size)}")
        console.print(f"  [dim]Checksum:[/dim]      {'✓ verified' if result.checksum_verified else '✗ failed'}")
        console.print(f"  [dim]Location:[/dim]      {result.install_path}")

    except Exception as e:
        console.print(f"[red]✗ Installation failed:[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# Uninstall Command
# =============================================================================

@app.command()
def uninstall(
    package_id: str = typer.Argument(..., help="Package ID to uninstall"),
):
    """Uninstall a package by ID."""
    console.print(f"[cyan]Uninstalling:[/cyan] {package_id}\n")

    try:
        result = uninstall_package(package_id)

        console.print(f"[green]✓ Package removed:[/green] {package_id}")
        console.print(f"  [dim]Name:[/dim]       {result.name}")
        console.print(f"  [dim]Version:[/dim]    {result.version}")
        console.print(f"  [dim]Category:[/dim]   {result.category}")

    except Exception as e:
        console.print(f"[red]✗ Uninstallation failed:[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# Update Command
# =============================================================================

@app.command()
def update(
    package_id: Optional[str] = typer.Argument(None, help="Package ID to update (all if not specified)"),
):
    """Check for and apply package updates."""
    console.print("[cyan]Checking for updates...[/cyan]\n")

    try:
        updates = check_for_updates(package_id)

        if not updates:
            console.print("[green]✓ No updates available[/green]")
            return

        table = Table(title="Available Updates")
        table.add_column("Package", style="cyan")
        table.add_column("Current", style="yellow")
        table.add_column("Latest", style="green")
        table.add_column("Category", style="white")

        for pkg in updates:
            table.add_row(
                pkg["id"],
                pkg["current_version"],
                pkg["latest_version"],
                pkg["category"],
            )

        console.print(table)
        console.print()
        console.print("[bold]Run 'nai install <package>' to update.[/bold]")

    except Exception as e:
        console.print(f"[red]✗ Update check failed:[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# Search Command
# =============================================================================

@app.command()
def search(
    query: str = typer.Argument(..., help="Search term"),
):
    """Search the package index."""
    from nai.core.package import load_manifest

    cfg = Config()
    content_path = cfg.get("content_path", "")

    if not content_path:
        console.print("[red]✗ Content path not configured[/red]")
        console.print("[dim]Run: nai config --set-key content_path --set-value /path/to/content[/dim]")
        raise typer.Exit(1)

    manifest_path = Path(content_path) / "packages.json"
    packages = load_manifest(manifest_path)

    results = []
    query_lower = query.lower()

    for pkg in packages:
        if (query_lower in pkg.get("id", "").lower() or
            query_lower in pkg.get("name", "").lower() or
            query_lower in " ".join(pkg.get("tags", [])).lower()):
            results.append(pkg)

    if not results:
        console.print(f"[yellow]No packages found matching '[/yellow][bold]{query}[/bold][yellow]'[/yellow]")
        return

    table = Table(title=f"Search Results ({len(results)} found)")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Version", style="yellow")
    table.add_column("Category", style="magenta")

    for pkg in results:
        table.add_row(
            pkg["id"],
            pkg["name"],
            pkg["version"],
            pkg["category"],
        )

    console.print(table)


# =============================================================================
# List Command
# =============================================================================

@app.command()
def list(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
):
    """List installed packages."""
    from nai.installer.uninstall import list_installed

    installed = list_installed()

    if not installed:
        console.print("[yellow]No packages installed[/yellow]")
        return

    # Filter if category specified
    if category:
        installed = [p for p in installed if p.get("category") == category]

    table = Table(title=f"Installed Packages ({len(installed)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Version", style="yellow")
    table.add_column("Category", style="magenta")
    table.add_column("Install Date", style="blue")

    for pkg in installed:
        table.add_row(
            pkg.get("id", "Unknown"),
            pkg.get("name", "Unknown"),
            pkg.get("version", "Unknown"),
            pkg.get("category", "Unknown"),
            pkg.get("install_date", "Unknown"),
        )

    console.print(table)


# =============================================================================
# Verify Command
# =============================================================================

@app.command()
def verify(
    package_id: str = typer.Argument(..., help="Package ID to verify"),
):
    """Verify the integrity of installed packages."""
    console.print(f"[cyan]Verifying:[/cyan] {package_id}\n")

    try:
        result = verify_package(package_id)

        console.print(f"[green]✓ Verification passed:[/green] {package_id}")
        console.print(f"  [dim]Checksum:[/dim]      ✓ verified")
        console.print(f"  [dim]Files intact:[/dim]  ✓")

    except Exception as e:
        console.print(f"[red]✗ Verification failed:[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# Favorites Command (NEW - for your plugins list feature)
# =============================================================================

@app.command()
def favorite(
    package_id: str = typer.Argument(..., help="Package ID to add to favorites"),
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove from favorites instead"),
):
    """Manage your favorite plugins list."""
    from nai.config import get_my_plugins, set_my_plugins

    current = get_my_plugins()

    if remove:
        if package_id in current:
            current.remove(package_id)
            set_my_plugins(current)
            console.print(f"[green]✓ Removed[/green] '{package_id}' from favorites")
        else:
            console.print(f"[yellow]'{package_id}' was not in favorites[/yellow]")
    else:
        if package_id not in current:
            current.append(package_id)
            set_my_plugins(current)
            console.print(f"[green]✓ Added[/green] '{package_id}' to favorites")
        else:
            console.print(f"[yellow]'{package_id}' is already in favorites[/yellow]")

# Add imports for sys module
import sys
