#!/usr/bin/env python3
"""Check frozen independent C manifest identities, nesting and raw denominators."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent/'conformance'
for line in (root/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split();assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
inventory=json.loads((root/'inventory.json').read_text())['cases']
keys=lambda cases:{(r['corpus'],r['path']) for r in cases}
assert len(keys(inventory))==4099
assert sum(r['corpus']=='gcc' and r['kind']=='execute' for r in inventory)==1890
assert sum(r['corpus']=='gcc' and r['kind']=='compile-only' for r in inventory)==1988
assert sum(r['kind']=='unsorted' for r in inventory)==1
previous=set()
for name,counts in [('C1',(55,95,100)),('C2',(176,945,995)),('C3',(220,1607,1690))]:
    manifest=json.loads((root/(name+'.json')).read_text());cases=manifest['cases'];selected=keys(cases)
    actual=(sum(r['corpus']=='c-testsuite' for r in cases),sum(r['corpus']=='gcc' and r['kind']=='execute' for r in cases),sum(r['corpus']=='gcc' and r['kind']=='compile-only' for r in cases))
    assert actual==counts and len(selected)==len(cases),(name,actual)
    assert previous<=selected<=keys(inventory)
    assert all(r['dialect'] and r['reference_flags'] and r['sha256'] for r in cases)
    assert all('directives' in r and 'directive_option_sets' in r for r in cases if r['corpus']=='gcc')
    previous=selected
    print(name+': PASS; execution/compile-only counts '+str(counts))
print('Manifest hashes, independent source inventory and nesting: PASS')
