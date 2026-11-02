#!/bin/bash
# Ship a prebuilt, verified site archive.
set -euo pipefail
if [ "$#" -ne 2 ] || [ "$1" != ship ]; then
    echo "usage: $0 ship archive.tar.gz" >&2
    exit 2
fi
archive=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
python3 "$(dirname "$0")/verify_archive.py" "$archive" "$tmp"
SERVER="root@104.131.94.68"
REMOTE_DIR="/var/www/lang"
ssh "$SERVER" "mkdir -p $REMOTE_DIR/examples"
while IFS= read -r path; do
    scp "$tmp/$path" "$SERVER:$REMOTE_DIR/$path"
done < "$tmp/.files"
ssh "$SERVER" "ln -sfn $REMOTE_DIR /var/www/bryan/lang"
echo "Deployed: https://ehrlich.dev/lang/ and https://lang.ehrlich.dev/"
