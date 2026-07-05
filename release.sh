#!/usr/bin/env bash
set -euo pipefail

# =====================================================
# Nobara Audio Production Installer
# Enterprise Release System v3.0
# Author: Willi Gunnz
# =====================================================

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VERSION_INPUT="${1:-}"
DRY_RUN="${DRY_RUN:-0}"

# -----------------------------
# Helpers
# -----------------------------

die() {
    echo "[ERROR] $1"
    exit 1
}

log() {
    echo "[INFO] $1"
}

# -----------------------------
# Validate version
# -----------------------------

if [[ -z "$VERSION_INPUT" ]]; then
    echo "Usage: ./release.sh vX.Y.Z"
    exit 1
fi

if ! [[ "$VERSION_INPUT" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    die "Invalid version format. Use vX.Y.Z"
fi

VERSION="$VERSION_INPUT"

log "Starting enterprise release: $VERSION"

# -----------------------------
# Ensure git repo
# -----------------------------
git rev-parse --git-dir >/dev/null 2>&1 || die "Not a git repo"

# -----------------------------
# Prevent duplicate tags
# -----------------------------
git rev-parse "$VERSION" >/dev/null 2>&1 && die "Tag already exists"

# -----------------------------
# Stage changes
# -----------------------------
if [[ -n "$(git status --porcelain)" ]]; then
    log "Staging changes..."
    git add .
fi

# -----------------------------
# Commit changes
# -----------------------------
if ! git diff --cached --quiet; then
    git commit -m "release: $VERSION"
else
    log "No changes to commit"
fi

# -----------------------------
# Sync VERSION file
# -----------------------------
echo "${VERSION#v}" > VERSION
git add VERSION
git commit -m "chore: bump version to $VERSION" || true

# -----------------------------
# Generate structured changelog
# -----------------------------

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

RANGE=""
[[ -n "$LAST_TAG" ]] && RANGE="$LAST_TAG..HEAD"

log "Generating structured changelog..."

FEATURES=$(git log $RANGE --pretty=format:"%s" | grep -i "^feat" || true)
FIXES=$(git log $RANGE --pretty=format:"%s" | grep -i "^fix" || true)
CHORE=$(git log $RANGE --pretty=format:"%s" | grep -i "^chore" || true)
OTHER=$(git log $RANGE --pretty=format:"%s" | grep -viE "^(feat|fix|chore)" || true)

cat > CHANGELOG.md <<EOF
# Changelog

## [$VERSION] - $(date +%Y-%m-%d)

### 🚀 Features
$FEATURES

### 🐛 Fixes
$FIXES

### 🔧 Maintenance
$CHORE

### 📦 Other
$OTHER
EOF

git add CHANGELOG.md
git commit -m "docs: update changelog for $VERSION" || true

# -----------------------------
# Dry run mode
# -----------------------------
if [[ "$DRY_RUN" == "1" ]]; then
    log "DRY RUN active - stopping before push"
    exit 0
fi

# -----------------------------
# Push main
# -----------------------------
log "Pushing main branch..."
git push origin main

# -----------------------------
# Create tag
# -----------------------------
log "Creating tag $VERSION"
git tag "$VERSION"

# Optional GPG signing hook (if configured)
git tag -s "$VERSION" -m "Release $VERSION"

# -----------------------------
# Push tag
# -----------------------------
log "Pushing tag..."
git push origin "$VERSION"

# -----------------------------
# GitHub Release (enterprise feature)
# -----------------------------

log "Creating GitHub release..."

if command -v gh >/dev/null 2>&1; then

    gh release create "$VERSION" \
        --title "Nobara Audio Installer $VERSION" \
        --notes-file CHANGELOG.md \
        --latest

else
    log "GitHub CLI not installed (skipping release creation)"
    log "Install with: sudo dnf install gh"
fi

# -----------------------------
# Done
# -----------------------------
echo
echo "======================================="
echo " ENTERPRISE RELEASE COMPLETE"
echo "======================================="
echo "Version: $VERSION"
echo "Tag: $VERSION"
echo "GitHub Release: created (if gh installed)"
echo "======================================="
