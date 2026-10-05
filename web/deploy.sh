#!/bin/bash
# Publish one complete, verified static bundle. Infra retains nginx/DNS ownership.
set -euo pipefail
cd "$(dirname "$0")/.."
SERVER="root@104.131.94.68"
REMOTE_DIR="/var/www/lang"
if [ "${1:-}" != "--prepared" ]; then ./web/build.sh; fi
node web/site_manifest.js --verify
release="$(git rev-parse --short HEAD)-$(shasum -a 256 web/asset-manifest.json | cut -c1-12)"
staging="/var/www/lang-releases/$release"
bundle=$(mktemp -d)
trap 'rm -rf "$bundle"' EXIT
# The manifest is the explicit public asset allowlist; do not ship workspace files.
node - "$bundle" <<'JS'
const fs=require('fs'),path=require('path');
const manifest=JSON.parse(fs.readFileSync('web/asset-manifest.json'));
const output=process.argv[2];
for(const name of [...Object.keys(manifest.assets),'asset-manifest.json']) {
  const destination=path.join(output,name);
  fs.mkdirSync(path.dirname(destination),{recursive:true});
  fs.copyFileSync(path.join('web',name),destination);
}
JS
# Stage without touching the currently served release.
ssh -o BatchMode=yes "$SERVER" "mkdir -p '$staging'"
tar -C "$bundle" -cf - . | ssh -o BatchMode=yes "$SERVER" "tar -xf - -C '$staging'"
# Verify every uploaded asset before the served path changes.
ssh -o BatchMode=yes "$SERVER" python3 - "$staging" "$REMOTE_DIR" "$release" <<'PYREMOTE'
import hashlib,json,os,pathlib,sys
staging,remote,release=map(pathlib.Path,sys.argv[1:])
manifest=json.loads((staging/'asset-manifest.json').read_text())
for name,entry in manifest['assets'].items():
    data=(staging/name).read_bytes()
    if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
        raise SystemExit('uploaded asset differs: '+name)
next_link=pathlib.Path(str(remote)+'.next-'+str(release))
if next_link.exists() or next_link.is_symlink(): next_link.unlink()
next_link.symlink_to(staging)
previous_target=str(remote.resolve()) if remote.exists() else None
legacy=None
try:
    # First release retains the original directory for rollback; later swaps are atomic.
    if remote.is_dir() and not remote.is_symlink():
        legacy=staging.parent/('legacy-'+str(release))
        if legacy.exists(): raise SystemExit('legacy backup already exists')
        remote.rename(legacy)
    os.replace(next_link,remote)
except BaseException:
    if legacy is not None and not remote.exists(): legacy.rename(remote)
    if next_link.is_symlink(): next_link.unlink()
    raise
print(json.dumps({'release':str(staging),'source_commit':manifest['source_commit'],'assets':len(manifest['assets']),'previous_directory':str(legacy) if legacy else None,'previous_target':previous_target}))
PYREMOTE
printf 'Published verified release: https://lang.ehrlich.dev/ (%s)\n' "$release"
