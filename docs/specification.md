# Nobara Audio Installer Package Specification

**Version:** 1.0
**Status:** Draft

---

# Purpose

This document defines the official package specification for the Nobara Audio Installer ecosystem.

It serves as the contract between:

* `nai publish`
* `nai install`
* `nai update`
* `nai verify`
* `nobara-audio-content`

---

# Package Directory

Every package must follow this structure:

```text
package-name/
├── metadata.json
├── README.md
├── LICENSE
├── artwork/
│   └── cover.png
└── files/
```

The `files/` directory contains the package contents.

Examples:

* WAV samples
* SoundFonts
* Plugin presets
* MIDI files
* Impulse responses

---

# Categories

Current supported categories:

```text
drum-packs
ir-packs
midi-packs
plugins
presets
soundfonts
```

Future categories may be added without changing the package format.

---

# metadata.json

Every package **must** contain a `metadata.json`.

Example:

```json
{
  "id": "metal-essentials",
  "name": "Metal Essentials",
  "version": "1.0.0",
  "category": "drum-packs",
  "author": "Willi Gunnz",
  "license": "CC-BY-4.0",
  "description": "High quality metal drum samples",
  "homepage": "",
  "tags": [
    "metal",
    "rock",
    "drums"
  ]
}
```

Required fields:

| Field       | Required | Description               |
| ----------- | -------- | ------------------------- |
| id          | Yes      | Unique package identifier |
| name        | Yes      | Display name              |
| version     | Yes      | Semantic version          |
| category    | Yes      | Package category          |
| author      | Yes      | Package author            |
| license     | Yes      | License                   |
| description | Yes      | Short description         |

Optional fields:

* homepage
* tags
* screenshots
* dependencies
* changelog

---

# Package Archive

Published packages are ZIP archives.

Example:

```text
metal-essentials-1.0.0.zip
```

---

# SHA-256

Every published archive must have a SHA-256 checksum.

Example:

```text
5e884898da28047151d0e56f8dc629...
```

The installer verifies this checksum before installation.

---

# packages.json

The content repository contains a master package index.

Example:

```json
{
  "packages": [
    {
      "id": "metal-essentials",
      "name": "Metal Essentials",
      "version": "1.0.0",
      "category": "drum-packs",
      "download": "https://...",
      "sha256": "...",
      "size": 123456789
    }
  ]
}
```

This file is generated automatically by `nai publish`.

It should **not** be edited manually.

---

# Package IDs

Rules:

* lowercase
* hyphens only
* unique

Valid:

```text
metal-essentials
classic-rock-kit
generaluser-gs
```

Invalid:

```text
Metal Essentials
metal_essentials
MetalEssentials
```

---

# Versioning

Semantic Versioning is used.

Examples:

```text
1.0.0
1.1.0
1.2.4
2.0.0
```

---

# Installer Rules

The installer must:

* validate metadata
* verify SHA-256 checksums
* reject invalid packages
* install only supported categories
* preserve user files where appropriate

---

# Publisher Rules

The publisher must:

* validate metadata
* build ZIP archives
* calculate SHA-256
* upload release assets
* update `packages.json`
* create reproducible archives when possible

---

# Compatibility

Future versions of the installer should remain backward compatible with older package metadata whenever practical.

Breaking changes should require a new specification version.
