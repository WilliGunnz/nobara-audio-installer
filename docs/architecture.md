# Nobara Audio Installer Architecture

**Last Updated:** July 5, 2026

---

# Project Overview

Nobara Audio Installer is an open-source package management ecosystem for audio production software and content on Nobara Linux.

The project consists of two Git repositories and one local asset library.

---

# Project Components

## Repository: nobara-audio-installer

Purpose:

* Desktop application
* Command-line interface (`nai`)
* Publisher
* Installer
* Release system
* Packaging (RPM/COPR)
* GitHub Actions

Location:

```
~/Documents/nobara-audio-installer
```

---

## Repository: nobara-audio-content

Purpose:

* Package metadata
* Package manifests
* Documentation
* Future community package index

Location:

```
~/Documents/nobara-audio-content
```

---

## Local Library

Purpose:

Contains the original audio assets.

This directory is **not** tracked by Git.

Location:

```
~/Documents/nobara-audio-library
```

Structure:

```
nobara-audio-library/
├── .cache/
├── .staging/
├── drum-packs/
├── ir-packs/
├── midi-packs/
├── plugins/
├── presets/
└── soundfonts/
```

---

# Installer Repository Layout

```
nobara-audio-installer/
├── .github/
├── assets/
├── docs/
├── scripts/
├── src/
│   └── nai/
│       ├── cli/
│       ├── core/
│       ├── gui/
│       ├── installer/
│       ├── publisher/
│       └── utils/
├── tests/
├── CHANGELOG.md
├── LICENSE
├── README.md
├── VERSION
└── pyproject.toml
```

---

# Python Package Layout

All new Python code lives under:

```
src/nai/
```

Modules:

```
cli/
```

Command-line interface.

```
core/
```

Shared business logic.

Examples:

* configuration
* version handling
* manifests

```
gui/
```

Desktop application.

```
installer/
```

Package installation and removal.

```
publisher/
```

Publishing tools.

Responsibilities:

* scan packages
* create ZIP archives
* calculate SHA-256
* upload releases
* update manifests

```
utils/
```

Shared helper functions.

---

# Release Workflow

```
Developer
      │
      ▼
nai release
      │
      ▼
Update VERSION
      │
      ▼
Generate CHANGELOG
      │
      ▼
Commit
      │
      ▼
Create Git Tag
      │
      ▼
Push
      │
      ▼
GitHub Release
```

---

# Publishing Workflow

```
Developer

↓

nobara-audio-library

↓

nai publish

↓

Scan Packages

↓

Validate Metadata

↓

Create ZIP

↓

Generate SHA-256

↓

Upload Release Asset

↓

Update packages.json

↓

Commit

↓

Push
```

---

# Package Structure

Every package should follow this layout:

```
package-name/
├── metadata.json
├── README.md
├── LICENSE
├── artwork/
└── files/
```

Example:

```
drum-packs/
└── metal-essentials/
    ├── metadata.json
    ├── README.md
    ├── LICENSE
    ├── artwork/
    └── files/
```

---

# Command-Line Interface

Planned commands:

```
nai doctor
nai config
nai scan
nai init-package
nai publish
nai release
nai install
nai uninstall
nai update
nai search
nai list
nai verify
```

---

# Design Principles

* Single responsibility for each module.
* No large binary assets committed to Git.
* Keep repositories lightweight.
* Use GitHub Releases for downloadable content.
* Share business logic between the CLI and GUI.
* Prefer automation over manual release steps.
* Keep the project modular and testable.

---

# Long-Term Goals

* RPM packages
* COPR repository
* Automatic updates
* Community package repository
* Package ratings
* Screenshots
* Dependency management
* Multiple download mirrors
* Flatpak support
* Plugin validation
* Digital signatures for published packages

---

# Development Guidelines

* Use lowercase directory names with hyphens.
* Keep Python code inside `src/nai/`.
* Add tests for new functionality where practical.
* Document architectural changes in this file.
* Never store large audio libraries in Git repositories.
