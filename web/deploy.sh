#!/bin/bash
# Deploy the demo site. Serves at https://ehrlich.dev/lang/ (a symlink inside
# the apex's static root - no DNS changes needed), and stages an nginx vhost
# for lang.ehrlich.dev that goes live the moment a Cloudflare DNS record for
# "lang" (proxied, -> this server) is added.
set -e
cd "$(dirname "$0")"

SERVER="root@104.131.94.68"
REMOTE_DIR="/var/www/lang"
NGINX_CONF="/etc/nginx/sites-enabled/lang.ehrlich.dev.conf"

./build.sh

ssh $SERVER "mkdir -p $REMOTE_DIR/examples"
scp index.html host.js $SERVER:$REMOTE_DIR/
scp examples/*.wasm examples/*.lang $SERVER:$REMOTE_DIR/examples/

# Path on the apex: ehrlich.dev/lang/ (apex root is /var/www/bryan)
ssh $SERVER "ln -sfn $REMOTE_DIR /var/www/bryan/lang"

# Subdomain vhost, dormant until DNS exists (pattern: pendulbrot.ehrlich.dev)
ssh $SERVER "cat > $NGINX_CONF << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name lang.ehrlich.dev;
    root $REMOTE_DIR;
    index index.html;
    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF
nginx -t && nginx -s reload"

echo "Deployed: https://ehrlich.dev/lang/ (lang.ehrlich.dev staged, needs DNS)"
