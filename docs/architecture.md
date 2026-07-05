# Architecture

## Repositories

### nobara-audio-installer

Application source code.

Contains:

- CLI
- GUI
- Installer
- Publisher
- Release tools

---

### nobara-audio-content

Package metadata.

Contains:

- packages.json
- manifests
- metadata
- documentation

---

## Local Library

Location:

~/Documents/nobara-audio-library

Structure:

```
drum-packs/
ir-packs/
midi-packs/
plugins/
presets/
soundfonts/
```

This directory is **not** tracked by Git.

It contains the raw audio assets used by the publisher.
