#\!/bin/bash
set -e

cd bootstrap

# Get current commit
CURRENT=$(readlink current 2>/dev/null || echo "")

for dir in */; do
    commit=$(basename "$dir")
    
    # Skip current symlink, recovery, and non-commit folders
    if [ "$commit" = "current" ] || [ "$commit" = "recovery" ]; then
        continue
    fi
    
    # Skip if not a directory with expected files
    if [ \! -f "$dir/compiler_macos.ll" ] && [ \! -f "$dir/compiler.s" ]; then
        echo "Skipping $commit (no compiler files)"
        continue
    fi
    
    echo "Archiving $commit..."
    
    # Create tarball
    tar -czf /tmp/bootstrap-${commit}.tar.gz "$commit"/
    
    # Upload to GitHub release
    if gh release view "bootstrap-${commit}" >/dev/null 2>&1; then
        echo "  Release already exists, skipping"
    else
        gh release create "bootstrap-${commit}" \
            /tmp/bootstrap-${commit}.tar.gz \
            --title "Bootstrap ${commit}" \
            --notes "Historical bootstrap from commit ${commit}" \
            --latest=false
        echo "  Created release bootstrap-${commit}"
    fi
    
    rm /tmp/bootstrap-${commit}.tar.gz
done

echo "Done\! All bootstraps archived to GitHub Releases."
