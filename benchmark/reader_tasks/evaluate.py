#!/usr/bin/env python3
"""Operator-side reader task evaluator. Candidate programs never receive answers."""
import argparse
import gzip
import io
import tarfile
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
LANGUAGES = ('Lang', 'Python')
CORPUS = None


def read(path):
    return json.loads(Path(path).read_text())


def sealed():
    assert CORPUS is not None, 'Supply --corpus or READER_TASK_CORPUS (operator archive outside checkout)'
    path = Path(CORPUS).resolve()
    assert REPO != path and REPO not in path.parents, 'Keep the operator archive outside the checkout'
    expected = dict((name, digest) for digest, name in
                    (line.split('  ') for line in (ROOT/'SHA256SUMS').read_text().splitlines()))
    raw = path.read_bytes()
    assert fingerprint(raw) == expected['operator:corpus.json.gz'], 'Operator corpus hash mismatch'
    return json.loads(gzip.decompress(raw))


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def audit():
    manifest = read(ROOT / 'manifest.json')
    tasks = manifest['tasks']
    assert len(tasks) >= 20 and len({t['id'] for t in tasks}) == len(tasks)
    assert len({t['signature'] for t in tasks}) == len(tasks)
    assert {t['kind'] for t in tasks} == {'create', 'evolve', 'repair'}
    expected_files = set()
    for line in (ROOT / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ')
        if name == 'operator:corpus.json.gz':
            sealed()
            expected_files.add(name)
            continue
        path = (ROOT / name).resolve()
        assert ROOT in path.parents and path.is_file()
        assert fingerprint(path.read_bytes()) == digest, name
        expected_files.add(name)
    required={p.relative_to(ROOT).as_posix() for p in (ROOT/'tasks').rglob('*') if p.is_file()}
    assert required <= expected_files, 'Unfrozen task files'
    assert {'manifest.json','pack_exclusions.json','public/calibration.json'} <= expected_files
    assert {'operator:corpus.json.gz','evaluate.py','PROTOCOL.md','README.md','toolkit.json'} <= expected_files
    answers = sealed()['tasks']
    assert [a['id'] for a in answers] == [t['id'] for t in tasks]
    specs = []
    for task, answer in zip(tasks, answers):
        spec = read(ROOT / task['path'])
        specs.append(spec)
        assert spec['Lang']['specification'] == spec['Python']['specification'] == spec['objective']
        assert spec['grammar'] and len(answer['cases']) >= 18
        assert len({c['source'] for c in answer['cases']}) == len(answer['cases'])
        assert {c['category'] for c in answer['cases']} == {'valid', 'trailing', 'malformed'}
        assert sum(c['expected']['ok'] for c in answer['cases']) > len(answer['cases']) / 2
        assert len({c['source'].rsplit(' ', 2)[-1] for c in answer['cases'] if c['category']=='trailing'}) >= 3
        for case in answer['cases']:
            expected = case['expected']
            assert valid_response(expected)
            if expected['ok']:
                assert 0 <= expected['start'] < expected['end'] <= len(case['source'].encode())
        for language in LANGUAGES:
            assert (ROOT / task['path']).parent.joinpath(spec[language]['starter']).is_file()
            assert language in answer['fixtures']
    # Detect structural renamings: these tasks must differ beyond a keyword.
    import re
    normalized = [re.sub(r"'[A-Za-z_]+'", "'keyword'", s['grammar']) + '\n' + s['objective'] for s in specs]
    assert len(set(normalized)) == len(specs)
    print(json.dumps({'audit':'PASS','tasks':len(tasks),'cases':sum(len(t['cases']) for t in answers),
                      'kinds':{k:sum(t['kind']==k for t in tasks) for k in ('create','evolve','repair')}}))
    return manifest


def freeze():
    audit()
    relative = (ROOT / 'SHA256SUMS').relative_to(REPO).as_posix()
    commit = subprocess.check_output(['git','log','-1','--format=%H','--',relative], cwd=REPO, text=True).strip()
    assert commit, 'Commit the frozen corpus before any trial'
    recorded = subprocess.check_output(['git','show',f'{commit}:{relative}'],cwd=REPO)
    assert recorded == (ROOT/'SHA256SUMS').read_bytes(), 'Uncommitted corpus hashes'
    # All frozen inputs must be present at that same commit, not only the hash list.
    for line in recorded.decode().splitlines():
        digest, name = line.split('  ')
        if name == 'operator:corpus.json.gz':
            assert fingerprint(Path(CORPUS).read_bytes()) == digest
            continue
        blob = subprocess.check_output(['git','show',f'{commit}:{ROOT.relative_to(REPO).as_posix()}/{name}'],cwd=REPO)
        assert fingerprint(blob) == digest
    # No ancestor of a publishable candidate may contain the plaintext answers.
    leaked = subprocess.check_output(['git','log','--format=%H','HEAD','--',
                'benchmark/reader_tasks/sealed'],cwd=REPO,text=True).strip()
    assert not leaked, 'Remove operator answers from unpublished commit history'
    exclusions = read(ROOT/'pack_exclusions.json')
    assert exclusions['baseline'] == '8fdb5a1'
    examples = set()
    for entry in exclusions['files']:
        blob = subprocess.check_output(['git','show',f"8fdb5a1:{entry['path']}"],cwd=REPO)
        assert fingerprint(blob) == entry['sha256']
        examples.add(blob)
    for task in read(ROOT/'manifest.json')['tasks']:
        for path in (ROOT/task['path']).parent.iterdir():
            assert path.read_bytes() not in examples
    assert set(e['path'] for e in exclusions['files']) == set(subprocess.check_output(
        ['git','ls-tree','-r','--name-only','8fdb5a1','example'],cwd=REPO,text=True).splitlines())
    print(json.dumps({'freeze':'PASS','commit':commit,'excluded_pack_files':len(examples),'model_trials':0}))
    return commit


def valid_response(obj):
    if not isinstance(obj, dict) or type(obj.get('ok')) is not bool:
        return False
    if obj['ok']:
        return set(obj) == {'ok','value','start','end'} and all(type(obj[k]) is int for k in ('value','start','end'))
    return set(obj) == {'ok'}


def limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (65536,65536))
    resource.setrlimit(resource.RLIMIT_CPU, (2,2))
    resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0,0))


def execute(argv, source, timeout, directory):
    """Bound output, wall time and child processes; never use a shell."""
    start = time.monotonic()
    with tempfile.TemporaryFile(dir=directory) as output, tempfile.TemporaryFile(dir=directory) as errors:
        try:
            proc = subprocess.Popen([*argv,source],stdout=output,stderr=errors,start_new_session=True,
                                    preexec_fn=limits, cwd=directory,
                                    env={'PATH':os.environ.get('PATH',''),'LANG':'C.UTF-8'})
        except OSError as error:
            return {'status':'launch-failure','seconds':time.monotonic()-start,'detail':str(error)}
        try:
            code = proc.wait(timeout=timeout)
            status = 'ok' if code == 0 else 'runtime-failure'
        except subprocess.TimeoutExpired:
            status = 'timeout'
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        finally:
            # Reap descendants even if the parent exited before the timeout.
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
        output.seek(0); raw=output.read(65537)
        errors.seek(0); stderr=errors.read(65537).decode(errors='replace')
    result={'status':status,'seconds':time.monotonic()-start,'stderr':stderr}
    if status == 'ok':
        try:
            def unique(pairs):
                obj={}
                for k,v in pairs:
                    if k in obj: raise ValueError('duplicate response key')
                    obj[k]=v
                return obj
            obj=json.loads(raw,object_pairs_hook=unique)
            if not valid_response(obj): raise ValueError('response schema')
            result['response']=obj
        except (ValueError,UnicodeError): result['status']='protocol-failure'
    return result


def score(task, argv, directory, timeout=1.0):
    rows=[]
    for index,case in enumerate(task['cases']):
        if argv is None:
            result={'status':'abstention','seconds':0.0}
        else:
            result=execute(argv,case['source'],timeout,directory)
        result.update(case=index, category=case['category'])
        # JSON equality alone would incorrectly equate bool with integer.
        result['correct']=result['status']=='ok' and result['response']==case['expected']
        if not result['correct'] and result['status']=='ok':
            if case['category']=='trailing' and result['response']['ok']:
                result['status']='accepted-trailing-input'
            elif result['response']['ok'] and case['expected']['ok'] and any(
                    result['response'][k]!=case['expected'][k] for k in ('start','end')):
                result['status']='wrong-span'
            else:
                result['status']='wrong-output'
        rows.append(result)
    correct=sum(r['correct'] for r in rows)
    return {'id':task['id'],'correct_cases':correct,'total_cases':len(rows),
            'case_score':correct/len(rows),'task_score':int(correct==len(rows)),'cases':rows}


def schedule(seed, ids):
    # Hash ordering is stable across Python versions; seed is frozen before attempts.
    return [{'id':tid,'languages':sorted(LANGUAGES,key=lambda l:fingerprint(f'{seed}/{tid}/{l}'.encode()))}
            for tid in sorted(ids,key=lambda i:fingerprint(f'{seed}/{i}'.encode()))]


def accounting(events, ids):
    """No success-only denominator; explicit phase intervals for every assigned cell."""
    cells={(tid,lang):{} for tid in ids for lang in LANGUAGES}
    for event in events:
        key=(event['id'],event['language'])
        assert key in cells and event['phase'] in ('authoring','review')
        assert event['phase'] not in cells[key]
        start,end=event['start'],event['end']
        assert type(start) in (int,float) and type(end) in (int,float)
        import math
        assert math.isfinite(start) and math.isfinite(end) and 0 <= start <= end
        cells[key][event['phase']]=(start,end)
    assert all(set(v)=={'authoring','review'} for v in cells.values()), 'Missing time intervals'
    assert all(v['authoring'][1] <= v['review'][0] for v in cells.values()), 'Review precedes authoring'
    intervals=sorted((start,end) for phases in cells.values() for start,end in phases.values() if end>start)
    assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])), 'Overlapping accounting intervals'
    totals={l:sum(end-start for (tid,lang),phases in cells.items() if lang==l for start,end in phases.values()) for l in LANGUAGES}
    return {'total_seconds':totals,'assigned_cells':len(cells),'includes_failed_and_abstained':True}


def toolkit(destination, compiler):
    """Construct the supported toolkit without a checkout, Git history or answers."""
    pin = read(ROOT/'toolkit.json')
    assert fingerprint(compiler.read_bytes()) == pin['compiler_sha256'], 'Wrong pinned compiler'
    destination.mkdir(parents=True)
    # Only public compiler resources/documentation from the pinned baseline.
    archive = subprocess.check_output(['git','archive',pin['source_revision'],'std','src','docs'],cwd=REPO)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        tree.extractall(destination, filter='data')
    (destination/'std/os.lang').write_text(pin['os_layer'])
    (destination/'out').mkdir()
    shutil.copyfile(compiler,destination/'out/lang')
    (destination/'out/lang').chmod(0o755)
    (destination/'toolkit.json').write_text(json.dumps(pin,indent=2)+'\n')
    return destination/'out/lang'


def export(destination, seed, compiler):
    freeze()
    dest=Path(destination).resolve()
    assert not dest.exists(), 'Use a new participant directory'
    dest.mkdir(parents=True)
    manifest=read(ROOT/'manifest.json')
    for task in manifest['tasks']:
        shutil.copytree((ROOT/task['path']).parent,dest/task['id'])
    shutil.copytree(ROOT/'public',dest/'public')
    toolkit(dest/'toolkit',compiler)
    (dest/'order.json').write_text(json.dumps(schedule(seed,[t['id'] for t in manifest['tasks']]),indent=2)+'\n')
    (dest/'PROTOCOL.md').write_text((ROOT/'PROTOCOL.md').read_text())
    assert not any('sealed' in p.parts or p.name=='evaluate.py' for p in dest.rglob('*'))
    print(json.dumps({'export':'PASS','destination':str(dest),'seed':seed,'tasks':len(manifest['tasks'])}))


def controls(directory, compiler):
    task=sealed()['tasks'][0]
    fixture=directory/'control_fixture.py';fixture.write_text(task['fixtures']['Python'])
    lang_source=directory/'control_fixture.lang';lang_source.write_text(task['fixtures']['Lang'])
    binary=build_lang(lang_source,directory,compiler)
    wrapper=directory/'control.py'
    wrapper.write_text('''import json,subprocess,sys,time
mode=sys.argv[1]; source=sys.argv[-1]
if mode=='timeout': time.sleep(5)
x=json.loads(subprocess.check_output([*sys.argv[2:-1],source]))
if x['ok']:
    if mode=='span': x['start']+=1
    if mode=='output': x['value']+=1
elif mode=='trailing': x={'ok':True,'value':0,'start':0,'end':1}
if mode=='schema': x={'ok':True,'value':True,'start':0,'end':1}
print(json.dumps(x))
''')
    outcomes={}
    for mode in ('raw','span','trailing','output','schema','timeout','crash','malformed','abstain'):
        pair={}
        for language,fixture_argv in [('Lang',[str(binary)]),('Python',[sys.executable,str(fixture)])]:
            argv=[sys.executable,str(wrapper),mode,*fixture_argv]
            if mode=='crash': argv=[sys.executable,'-c','raise SystemExit(7)']
            if mode=='malformed': argv=[sys.executable,'-c','print("bad json")']
            if mode=='abstain': argv=None
            result=score(task,argv,directory,0.15 if mode=='timeout' else 1)
            assert result['task_score']==int(mode=='raw'), mode
            wanted={'span':'wrong-span','trailing':'accepted-trailing-input','output':'wrong-output',
                    'schema':'protocol-failure','timeout':'timeout','crash':'runtime-failure',
                    'malformed':'protocol-failure','abstain':'abstention'}.get(mode,'ok')
            assert any(c['status']==wanted for c in result['cases']), (mode,language)
            if mode in ('timeout','crash','malformed','abstain','schema'):
                assert result['correct_cases']==0
            pair[language]=result
        assert [(r['status'],r['correct']) for r in pair['Lang']['cases']] == [
                (r['status'],r['correct']) for r in pair['Python']['cases']], mode
        outcomes[mode]=pair
    assert not valid_response({'ok':False,'extra':1})
    (directory/'negative-controls.json').write_text(json.dumps(outcomes,indent=2)+'\n')
    print(json.dumps({'controls':'PASS','paired_modes':list(outcomes),'identical_case_statuses':True}))


def build_lang(source, folder, compiler):
    ir=folder/'solution.ll';binary=folder/'solution'
    env=dict(os.environ,LANGBE='llvm',LANG_ROOT=str(compiler.parent.parent),LANG_CACHE=str(folder/'cache'))
    with (folder/'build.txt').open('w') as log:
        subprocess.run([str(compiler),str(source),'-o',str(ir)],cwd=compiler.parent.parent,env=env,
                       stdout=log,stderr=log,timeout=60,check=True)
        subprocess.run(['clang','-O0',str(ir),'-o',str(binary)],stdout=log,stderr=log,timeout=60,check=True)
    return binary


def dry_run(directory, compiler):
    freeze()
    directory.mkdir(parents=True,exist_ok=False)
    compiler=toolkit(directory/'toolkit',compiler)
    tasks={t['id']:t for t in sealed()['tasks']}
    order=schedule('fixed-fixture-dry-run-v1',tasks)
    scores={language:[] for language in LANGUAGES}; events=[]; submission={tid:{} for tid in tasks}
    for cell in order:
        tid=cell['id'];task=tasks[tid]
        for language in cell['languages']:
            start=time.monotonic()
            folder=directory/f'{tid}-{language}';folder.mkdir()
            source=folder/('solution.lang' if language=='Lang' else 'solution.py')
            source.write_text(task['fixtures'][language])
            if language=='Lang':
                argv=[str(build_lang(source,folder,compiler))]
            else: argv=[sys.executable,str(source)]
            submission[tid][language]=argv
            result=score(task,argv,folder)
            scores[language].append(result)
            end=time.monotonic()
            events.extend([{'id':tid,'language':language,'phase':'authoring','start':start,'end':end},
                           {'id':tid,'language':language,'phase':'review','start':end,'end':end}])
    (directory/'submission.json').write_text(json.dumps(submission,indent=2)+'\n')
    (directory/'time-ledger.json').write_text(json.dumps(events,indent=2)+'\n')
    totals=accounting(events,tasks)
    report={'kind':'fixed-fixture dry run; no model or human productivity measurement','order':order,
            'scores':scores,'summary':summarize(scores),'events':events,'accounting':totals,'review':'Unattended fixtures: zero human review time.'}
    (directory/'dry-run.json').write_text(json.dumps(report,indent=2)+'\n')
    for tid in tasks:
        pair=[next(s for s in scores[l] if s['id']==tid) for l in LANGUAGES]
        assert all(p['task_score']==1 for p in pair), f'{tid}: '+str([(p['correct_cases'],p['total_cases']) for p in pair])
        assert pair[0]['case_score']==pair[1]['case_score']
    controls(directory,compiler)
    print(json.dumps({'dry_run':'PASS','tasks_per_language':len(tasks),'full_correctness':True,'identical_scores':True,'evidence':str(directory/'dry-run.json')}))


def starters(directory, compiler):
    freeze()
    directory.mkdir(parents=True,exist_ok=False)
    compiler=toolkit(directory/'toolkit',compiler)
    results={language:[] for language in LANGUAGES}
    for task in sealed()['tasks']:
        for language in LANGUAGES:
            folder=directory/f"{task['id']}-{language}";folder.mkdir()
            original=ROOT/'tasks'/task['id']/('starter.lang' if language=='Lang' else 'starter.py')
            source=folder/original.name;source.write_bytes(original.read_bytes())
            if language=='Lang':
                argv=[str(build_lang(source,folder,compiler))]
            else: argv=[sys.executable,str(source)]
            results[language].append(score(task,argv,folder))
    (directory/'starters.json').write_text(json.dumps(results,indent=2)+'\n')
    for language,tasks in results.items():
        assert all(t['task_score']==0 for t in tasks), f'Already solved {language} starter'
        assert all(all(c['status'] not in ('runtime-failure','protocol-failure','launch-failure') for c in t['cases']) for t in tasks)
    print(json.dumps({'starters':'PASS','compilable_cells':40,'unsolved_cells':40,'evidence':str(directory/'starters.json')}))


def protocol_check(directory, compiler):
    directory.mkdir(parents=True,exist_ok=False)
    ids=[t['id'] for t in read(ROOT/'manifest.json')['tasks']]
    assert schedule('a',ids)==schedule('a',ids)
    assert schedule('a',ids)!=schedule('b',ids)
    assert {c['id'] for c in schedule('a',ids)}==set(ids)
    events=[]
    for i,(tid,language) in enumerate((t,l) for t in ids for l in LANGUAGES):
        events.extend([{'id':tid,'language':language,'phase':'authoring','start':i*3,'end':i*3+2},
                       {'id':tid,'language':language,'phase':'review','start':i*3+2,'end':i*3+3}])
    assert accounting(events,ids)['total_seconds']=={'Lang':60,'Python':60}
    for invalid in [events[:-1],events+[events[0]],events[:-1]+[dict(events[-1],end=-1)],
                    events[:-1]+[dict(events[-1],end=float('nan'))],
                    [dict(events[0],end=10)]+events[1:],
                    [dict(events[0],start=True)]+events[1:]]:
        try: accounting(invalid,ids)
        except AssertionError: pass
        else: raise AssertionError('Invalid timing ledger accepted')
    export(directory/'participant','protocol-check-seed',compiler)
    # Operator mistakes fail validation before any scores/output directory exist.
    for argv in [['python3','/tmp/solution.py'],[sys.executable,'solution.py'],['./solution']]:
        try: validate_argv(argv)
        except AssertionError: pass
        else: raise AssertionError('Relative submission path accepted')
    validate_argv([sys.executable,'/tmp/solution.py'])
    validate_argv(None)
    (directory/'protocol.json').write_text(json.dumps({'check':'PASS','synthetic_ledger_only':True,'same_seed_stable':True,'different_seed_changes_order':True,'invalid_ledgers_rejected':True,'relative_paths_rejected':True})+'\n')
    print('Protocol, participant separation, and timing validation: PASS')


def summarize(scores):
    from collections import Counter
    result={}
    for language,tasks in scores.items():
        failed=Counter(c['status'] for t in tasks for c in t['cases'] if not c['correct'])
        result[language]={'full_correct_tasks':sum(t['task_score'] for t in tasks),
                          'assigned_tasks':len(tasks),
                          'correct_cases':sum(t['correct_cases'] for t in tasks),
                          'total_cases':sum(t['total_cases'] for t in tasks),
                          'abstained_tasks':sum(all(c['status']=='abstention' for c in t['cases']) for t in tasks),
                          'failure_cases':dict(failed)}
    return result


def validate_argv(argv):
    if argv is None: return
    assert isinstance(argv,list) and argv and all(isinstance(a,str) and a for a in argv), 'Expected argv or null'
    # This protocol accepts executable/file paths only; use an absolute-path wrapper
    # script for flags or inline code. Existence of candidate files is scored normally.
    assert all(Path(a).is_absolute() for a in argv), 'Every submission argv entry must be an absolute path'


def main():
    global CORPUS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('audit','freeze','controls','protocol','dry-run','starters','export','score'))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--corpus',type=Path,default=os.environ.get('READER_TASK_CORPUS'),
                        help='Operator archive outside checkout; alternatively READER_TASK_CORPUS')
    parser.add_argument('--compiler',type=Path,default=REPO/'out/lang')
    parser.add_argument('--seed',default='reader-study-v1')
    parser.add_argument('--submission',type=Path,help='Operator manifest: {task_id:{Lang:[argv...],Python:[argv...]}}; null means abstention')
    parser.add_argument('--ledger',type=Path,help='Required authoring/review interval list for every assigned task/language')
    args=parser.parse_args()
    CORPUS=args.corpus
    if args.action=='audit': audit()
    elif args.action=='freeze': freeze()
    else:
        assert args.output, '--output outside the checkout is required'
        out=args.output.resolve()
        assert REPO != out and REPO not in out.parents, 'Keep evaluation artifacts outside the checkout'
        if args.action=='dry-run': dry_run(out,args.compiler.resolve())
        elif args.action=='starters': starters(out,args.compiler.resolve())
        elif args.action=='export': export(out,args.seed,args.compiler.resolve())
        elif args.action=='protocol': protocol_check(out,args.compiler.resolve())
        elif args.action=='controls':
            out.mkdir(parents=True,exist_ok=False)
            controls(out,toolkit(out/'toolkit',args.compiler.resolve()))
        elif args.action=='score':
            freeze()
            assert args.submission and args.ledger, '--submission and --ledger are required'
            submission=read(args.submission);tasks=sealed()['tasks'];ids=[t['id'] for t in tasks]
            assert set(submission)==set(ids), 'Every assigned task must appear, including abstentions'
            assert all(set(submission[tid])==set(LANGUAGES) for tid in ids)
            for cell in submission.values():
                for argv in cell.values():
                    validate_argv(argv)
            times=accounting(read(args.ledger),ids)
            out.mkdir(parents=True,exist_ok=False)
            results={l:[score(t,submission[t['id']][l],out) for t in tasks] for l in LANGUAGES}
            (out/'scores.json').write_text(json.dumps({'scores':results,'summary':summarize(results),'accounting':times,'order':schedule(args.seed,ids)},indent=2)+'\n')
            print(json.dumps({'scored':len(tasks),'output':str(out/'scores.json')}))


if __name__=='__main__':
    main()
