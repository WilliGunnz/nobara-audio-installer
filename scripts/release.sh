#!/usr/bin/env bash
set -euo pipefail

###############################################
# Nobara Audio Installer
# Enterprise Release System v4
###############################################

VERSION_FILE="VERSION"

die() {
    echo "[ERROR] $1"
    exit 1
}

log() {
    echo "[INFO] $1"
}

#---------------------------------------------
# Verify repository
#---------------------------------------------
git rev-parse --git-dir >/dev/null 2>&1 || die "Not inside a git repository"

#---------------------------------------------
# Determine version bump
#---------------------------------------------
BUMP="${1:-patch}"

[[ -f "$VERSION_FILE" ]] || echo "0.1.0" > "$VERSION_FILE"

CURRENT=$(cat "$VERSION_FILE")

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$BUMP" in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    *)
        die "Usage: ./release.sh [patch|minor|major]"
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
TAG="v${NEW_VERSION}"

log "Preparing release ${TAG}"

#---------------------------------------------
# Check for duplicate tag
#---------------------------------------------
if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
    die "Tag ${TAG} already exists"
fi

#---------------------------------------------
# Update VERSION
#---------------------------------------------
echo "$NEW_VERSION" > "$VERSION_FILE"

#---------------------------------------------
# Generate changelog
#---------------------------------------------
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [[ -n "$LAST_TAG" ]]; then
    LOG_RANGE="${LAST_TAG}..HEAD"
else
    LOG_RANGE="HEAD"
fi

{
    echo "# Changelog"
    echo
    echo "## ${TAG} - $(date +%F)"
    echo
    git log "$LOG_RANGE" --pretty=format:"- %s"
} > CHANGELOG.md

#---------------------------------------------
# Commit everything
#---------------------------------------------
git add .

if ! git diff --cached --quiet; then
    git commit -m "release: ${TAG}"
else
    log "Nothing new to commit."
fi

#---------------------------------------------
# Create tag
#---------------------------------------------
git tag -a "${TAG}" -m "Release ${TAG}"

#---------------------------------------------
# Push
#---------------------------------------------
git push origin main
git push origin "${TAG}"

#---------------------------------------------
# GitHub Release
#---------------------------------------------
if command -v gh >/dev/null 2>&1; then
    gh release create "${TAG}" \
        --title "Nobara Audio Installer ${TAG}" \
        --notes-file CHANGELOG.md \
        --latest
else
    log "GitHub CLI not installed. Skipping release creation."
fi

echo
echo "===================================="
echo " Release Complete"
echo "===================================="
echo " Version : ${NEW_VERSION}"
echo " Tag     : ${TAG}"
echo "===================================="
