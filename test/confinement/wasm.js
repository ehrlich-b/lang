'use strict';
const assert = require('assert');
const {runLangProgram} = require('../../web/program_host.js');
// Minimal binary modules call the actual program host imports. No mock host.
const str = s => [s.length,...Buffer.from(s)];
const section = (id, data) => [id,data.length,...data];
function moduleFor(name,args) {
  const type = [2,0x60,args.length,...args.map(()=>0x7e),1,0x7e,0x60,0,1,0x7e];
  const code = [0,...args.flatMap(n=>[0x42,n]),0x10,0,0x0b];
  return Uint8Array.from([0,97,115,109,1,0,0,0,
    ...section(1,type),...section(2,[1,...str('lang'),...str(name),0,0]),
    ...section(3,[1,1]),...section(5,[1,1,1,2]),
    ...section(7,[2,...str('main'),0,1,...str('memory'),2,0]),
    ...section(10,[1,code.length,...code])]);
}
(async()=> {
  const rows=[];
  for (const [name,args,expected] of [['open',[0,0,0],-1n],['unlink',[0],-1n],['fork',[],-1n],['execve',[0,0,0],-1n],['read',[9,0,1],0n]]) {
    const r=await runLangProgram(moduleFor(name,args)); assert.strictEqual(r.value,expected);
    rows.push({name,result:String(r.value),pass:true});
  }
  for (const name of ['socket','connect','system','dlopen']) {
    await assert.rejects(()=>runLangProgram(moduleFor(name,[])),WebAssembly.LinkError);
    rows.push({name,result:'unavailable import',pass:true});
  }
  console.log(JSON.stringify({outcome:'supported-Wasm',profile:'direct-wasm32',scope:'authority imports only; production fuel/memory/output supervision remains future work',rows},null,2));
})().catch(e=>{console.error(e);process.exit(1);});
