#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const cp = require('child_process');
const root = path.resolve(__dirname, '..');
const web = path.join(root, 'web');
const assets = {};
function gather(directory, prefix = '') {
  for (const item of fs.readdirSync(directory, {withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name))) {
    const relative = prefix + item.name;
    if (item.isDirectory() && ['examples','reference'].includes(item.name)) gather(path.join(directory,item.name),relative+'/');
    else if (item.isFile() && /\.(?:html|js|json|wasm|lang|md)$/.test(item.name) && !['site_manifest.js','stdlib.json','asset-manifest.json','build_stdlib.js'].includes(item.name)) {
      const bytes = fs.readFileSync(path.join(directory,item.name));
      assets[relative] = {bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};
    }
  }
}
gather(web);
const stdlib = fs.readFileSync(path.join(web,'stdlib.json'));
assets['stdlib.json']={bytes:stdlib.length,sha256:crypto.createHash('sha256').update(stdlib).digest('hex')};
if (process.argv.includes('--verify')) {
  const manifest=JSON.parse(fs.readFileSync(path.join(web,'asset-manifest.json')));
  const head=cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
  if (manifest.source_commit!==head) throw new Error('site manifest source commit differs from HEAD; regenerate after committing');
  if (JSON.stringify(manifest.assets)!==JSON.stringify(assets)) throw new Error('site assets changed after validation; rebuild the manifest');
  console.log('site asset manifest verified');
} else {
  const git=(...args)=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim();
  const manifest={source_commit:git('rev-parse','HEAD'),source_dirty:!!git('status','--porcelain'),compiler_root:fs.readFileSync(path.join(root,'bootstrap/current/COMMIT'),'utf8').trim(),assets};
  fs.writeFileSync(path.join(web,'asset-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  console.log(`built site manifest (${Object.keys(assets).length} assets)`);
}
