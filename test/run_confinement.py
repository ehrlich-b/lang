#!/usr/bin/env python3
"""Feasibility spike, never a launcher authorizing native source execution."""
import argparse, json, os, platform, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
a=p.parse_args(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=False)
rows=[]
def run(name,cmd,**kwargs):
    r=subprocess.run(cmd,capture_output=True,timeout=60,**kwargs)
    (out/(name+'.stdout')).write_bytes(r.stdout); (out/(name+'.stderr')).write_bytes(r.stderr)
    rows.append(dict(name=name,command=cmd,exit=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')))
    return r
binary=out/'probe'
run('build',['clang','-O0',str(ROOT/'test/confinement/probe.c'),'-o',str(binary)]).check_returncode()
secret=out/'undeclared'; secret.write_text('private fixture\n')
scratch=out/'scratch'; scratch.mkdir()
# Controls demonstrate each attack is live, against disposable fixtures only.
fd=os.open(secret,os.O_RDONLY)
try:
    for mode,arg in [('read',str(secret)),('write',str(secret)),('socket','0'),('child','0'),('descriptor',str(fd))]:
        r=run('control-'+mode,[str(binary),mode,arg],pass_fds=(fd,))
        if r.returncode!=1: raise RuntimeError('invalid attack control: '+mode)
    os.lseek(fd,0,0)
    if platform.system()=='Linux' and shutil.which('bwrap'):
        base=['bwrap','--unshare-all','--die-with-parent','--new-session','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/etc','--ro-bind',str(binary),'/probe','--bind',str(scratch),'/scratch','--chdir','/scratch','--clearenv','--setenv','PATH','/usr/bin:/bin']
        for mode,arg in [('read',str(secret)),('write',str(secret)),('socket','0'),('child','0'),('descriptor',str(fd))]:
            run('linux-'+mode,base+['--','/probe',mode,arg],pass_fds=(fd,))
        # The compiler and the linker are descendants of the same boundary.
        # The resulting program attempts the same escape after tool execution.
        source=scratch/'child.c'; source.write_text((ROOT/'test/confinement/probe.c').read_text())
        for driver in ['clang','gcc']:
            cmd=' '.join([driver,'-O0 /scratch/child.c -o /scratch/child-'+driver,'&& /scratch/child-'+driver,'socket 0'])
            run('linux-compiler-child-'+driver,base+['--','/bin/sh','-c',cmd])
        linux='unavailable'  # Namespace-only policy permits fork/socket creation.
        reason='Namespace isolation alone is insufficient; inspect attack rows, including tool-child results. No production native launcher is qualified.'
    else:
        linux='unavailable'; reason='Linux bubblewrap unavailable on this execution host.'
    mac='unavailable'
    if platform.system()=='Darwin':
        # Actual Mac runs exercise sandbox-exec as a feasibility candidate only.
        # Deprecated sandbox-exec is not treated as a signed-helper qualification.
        profile='(version 1)(deny default)(allow process-exec)(allow file-read* (subpath "/usr") (subpath "/System") (subpath "/Library") (literal "'+str(binary)+'"))'
        if shutil.which('sandbox-exec'):
            for mode,arg in [('read',str(secret)),('write',str(secret)),('socket','0'),('child','0'),('descriptor',str(fd))]:
                run('macos-'+mode,['sandbox-exec','-p',profile,str(binary),mode,arg],pass_fds=(fd,))
        reason+=' Signed helper/toolchain qualification is still required on macOS.'
    receipt=dict(schema=1,host=dict(system=platform.system(),machine=platform.machine()),linux_native=linux,macos_native=mac,macos_executed=platform.system()=='Darwin',trusted_native_auto=False,reason=reason,rows=rows)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
finally: os.close(fd)
print(json.dumps({k:v for k,v in receipt.items() if k!='rows'},indent=2))
