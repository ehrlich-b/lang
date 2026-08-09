#!/bin/bash
# Deploy the demo site content. Infra owns nginx and DNS; this script only
# builds and ships the static app, then maintains the apex-path symlink.
set -e
cd "$(dirname "$0")"

SERVER="root@104.131.94.68"
REMOTE_DIR="/var/www/lang"

./build.sh

ssh $SERVER "mkdir -p $REMOTE_DIR/examples"
scp index.html readers.html lab.html host.js compiler_host.js program_host.js editor.js stdlib.json compiler.wasm $SERVER:$REMOTE_DIR/
scp examples/*.wasm examples/*.lang $SERVER:$REMOTE_DIR/examples/

# Path on the apex: ehrlich.dev/lang/ (apex root is /var/www/bryan)
ssh $SERVER "ln -sfn $REMOTE_DIR /var/www/bryan/lang"

# Plumbing (lang.ehrlich.dev vhost) is owned by ~/repos/infra — this script
# only ships content and the apex symlink.
echo "Deployed: https://ehrlich.dev/lang/ and https://lang.ehrlich.dev/"
