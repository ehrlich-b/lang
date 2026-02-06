#!/bin/bash
# Apply patches to an upstream compiler and build it
# Usage: ./scripts/apply-patches.sh <target> [--no-build]
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <target> [--no-build]"
    echo "Example: $0 zig"
    exit 1
fi

TARGET="$1"
NO_BUILD="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MANIFEST="$ROOT_DIR/patches/$TARGET/manifest.yaml"

if [ ! -f "$MANIFEST" ]; then
    echo "Error: No manifest at $MANIFEST"
    exit 1
fi

# Parse manifest (basic grep/awk - no yq dependency)
REPO=$(grep 'repo:' "$MANIFEST" | head -1 | awk '{print $2}')
COMMIT=$(grep 'commit:' "$MANIFEST" | head -1 | awk '{print $2}')
VERSION=$(grep 'version:' "$MANIFEST" | head -1 | awk '{print $2}')

echo "==> $TARGET capture (upstream $VERSION @ $COMMIT)"
echo "    Repo: $REPO"

# Create work directory
WORKDIR="/tmp/lang-patches-$TARGET-$$"
echo "==> Cloning to $WORKDIR"

# Shallow clone, then fetch the specific commit
git clone --depth=1 "$REPO" "$WORKDIR" 2>&1 | sed 's/^/    /'

cd "$WORKDIR"

# For a tagged version, fetch the tag
if git fetch --depth=1 origin "refs/tags/$VERSION" 2>/dev/null; then
    git checkout FETCH_HEAD 2>&1 | sed 's/^/    /'
else
    # Fall back to fetching the commit directly
    git fetch --depth=1 origin "$COMMIT" 2>&1 | sed 's/^/    /'
    git checkout FETCH_HEAD 2>&1 | sed 's/^/    /'
fi

# Apply patches (if any exist)
echo "==> Applying patches"
for patch in "$ROOT_DIR/patches/$TARGET"/*.patch; do
    [ -f "$patch" ] || continue
    echo "    $(basename "$patch")"
    git apply "$patch"
done

# Copy new files
echo "==> Copying new files"
if [ -d "$ROOT_DIR/patches/$TARGET/src" ]; then
    cp -r "$ROOT_DIR/patches/$TARGET/src/"* "src/" 2>/dev/null || true
    echo "    Copied src/ files"
fi

# Build (unless --no-build specified)
if [ "$NO_BUILD" != "--no-build" ]; then
    echo "==> Building"
    # Check if host zig is available
    if ! command -v zig &> /dev/null; then
        echo "Error: zig not found in PATH"
        echo "Install Zig 0.14.0+ to build the patched compiler"
        exit 1
    fi

    zig build -Doptimize=Debug 2>&1 | sed 's/^/    /'

    echo "==> Done!"
    echo "    Binary: $WORKDIR/zig-out/bin/zig"
else
    echo "==> Skipped build (--no-build)"
    echo "    Work directory: $WORKDIR"
fi

# Output the work directory for scripts to use
echo "$WORKDIR" > /tmp/lang-patches-$TARGET-latest
