# Changelog

All notable changes to the Nobara Audio Production Installer will be documented here.

---

## [5.0.0] - 2026-07-04

### Added
- Modular plugin system using `.list` files
- GUI installer using Zenity
- Plugin categories (synths, FX, drums, mastering)
- GitHub release workflow
- Realtime audio setup module
- Logging system

### Changed
- Refactored installer into modular structure (`lib/`)
- Improved error handling and sudo checks
- Replaced hardcoded packages with plugin lists

### Fixed
- Broken if/elif logic from early versions
- Duplicate sysctl entries prevention

---

## [4.0.0]
- Initial modular CLI version

## [3.0.0]
- Added GUI installer (Zenity)

## [2.0.0]
- Plugin grouping system introduced

## [1.0.0]
- Basic installer script
