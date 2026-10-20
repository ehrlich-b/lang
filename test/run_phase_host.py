#!/usr/bin/env python3
"""Compile and exercise the production host boundary, including failure paths."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
os.chdir(root)
compiler = str(Path(os.environ.get("COMPILER", "out/lang")).resolve())
out = Path(os.environ.get("PHASE_HOST_EVIDENCE", tempfile.mkdtemp(prefix="phase-host-"))).resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, LANGBE="llvm", LANG_CACHE=str(out / "cache"))
results = []

def command(args, data=b"", extra=None):
    return subprocess.run(args, input=data, capture_output=True, env=dict(env, **(extra or {})), timeout=120)

def check(name, proc, code=0, expected=None, error=None):
    (out / (name + ".stdout")).write_bytes(proc.stdout)
    (out / (name + ".stderr")).write_bytes(proc.stderr)
    ok = proc.returncode == code and (expected is None or proc.stdout == expected)
    if error:
        ok = proc.returncode != 0 and not proc.stdout and error.encode() in proc.stderr and b"host-error" in proc.stderr
    results.append({"name": name, "pass": ok, "exit": proc.returncode, "stdout_bytes": len(proc.stdout), "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest()})
    print(("PASS " if ok else "FAIL ") + name, flush=True)
    if not ok:
        print(proc.stderr.decode(errors="replace")[:2000], flush=True)
    return proc.stdout

ir = out / "probe.ll"
check("build-probe", command([compiler, "test/phase_host/probe.lang", "-o", str(ir)]))
probe = out / "probe"
check("link-probe", command(["clang", "-O2", str(ir), "-o", str(probe)]))

def run(mode, data=b"", extra=None, arg=None):
    return command([str(probe), mode] + ([str(arg)] if arg else []), data, extra)

large = b"a" * (5 * 1024 * 1024 + 17)
check("large-source", run("echo", large), expected=large)
check("large-emission", run("emit", large), expected=large)
check("exact-limit", run("echo", b"a" * 256, {"LANG_HOST_MAX_BYTES": "256"}), expected=b"a" * 256)
check("source-limit", run("echo", large, {"LANG_HOST_MAX_BYTES": "4194304"}), error="byte-limit")
check("emission-limit", run("emit", b"a" * 256, {"LANG_HOST_MAX_BYTES": "255"}), error="byte-limit")
check("invalid-limit", run("echo", b"", {"LANG_HOST_MAX_BYTES": "999999999999999999999"}), error="invalid-limit")
check("nul-source", run("echo", b"a\0b"), error="embedded-nul")
for size in [0, 3, 55, 56, 63, 64, 65, 4097]:
    data = b"abc" if size == 3 else b"z" * size
    check("digest-" + str(size), run("digest", data), expected=hashlib.sha256(data).hexdigest().encode() + b"\n")
for name, data, error in [("depth", b"(" * 129 + b")" * 129, "ast-depth"),
                          ("unclosed", b"(program", "ast-shape"),
                          ("trailing", b"(program) (program)", "ast-shape"),
                          ("quote", b'(program "abc)', "ast-shape"),
                          ("root", b"garbage", "ast-root")]:
    check(name, run("shape", data), error=error)
check("nodes", run("shape", b"(program " + b"a " * 1048577 + b")"), error="ast-nodes")
check("origins", run("origin", "éabc".encode()))
check("envelope", run("envelope", "éabc".encode()))
check("identity-fields", run("identity"))
check("invalid-utf8", run("origin", b"\xc0\x80"), error="invalid-utf8")
check("negative-span", run("span-negative"), error="invalid-span-number")
check("utf8-span", run("span", "éabc".encode()), error="invalid-span")
check("forged-parent", run("forged", b"a"), error="forged-include-origin")
check("missing-source", run("missing", b"a"), error="invalid-span")
for mode, error in [("wire-short", "wire-header"), ("wire-length", "wire-length"), ("wire-origin", "wire-origin"), ("wire-version", "wire-version")]:
    check(mode, run(mode, b"(program)"), error=error)
check("wire-valid", run("wire", b"(program)"), expected=b"(program)")
check("wire-comments", run("wire", b"/* trivia ) */ (program) // ( end"), expected=b"/* trivia ) */ (program) // ( end")
check("wire-unclosed-comment", run("wire", b"(program) /*"), error="ast-shape")
check("memory-budget", run("budget", b"abc"), error="memory-budget")
check("work-budget", run("work"), error="work-budget")
# A real source larger than the old 4 MiB capacity takes the normal include,
# parser, emitter and wire-parser paths. Check the complete payload survives.
source = out / "large.lang"
source.write_bytes(b'func main() i64 { var text *u8 = "' + large + b'"; return 0; }\n')
ast = out / "large.ast"
check("large-frontend", command([compiler, str(source), "--emit-expanded-ast", "-o", str(ast)]))
deep_source = out / "deep.lang"
deep_source.write_text("func main() i64 { return " + "(" * 129 + "0" + ")" * 129 + "; }")
check("native-depth", command([compiler, str(deep_source), "--emit-expanded-ast", "-o", str(out / "deep.ast")]), error="source-depth")
ast_bytes = ast.read_bytes()
assert large in ast_bytes
first = check("large-ast-parse", run("roundtrip", ast_bytes))
check("large-ast-fixed-point", run("roundtrip", first), expected=first)
# Native legacy readers are linked without optimization. The host must also
# retain bounded stack use there, rather than depending on LLVM promotion.
optimized_probe = probe
probe = out / "probe-o0"
check("link-probe-o0", command(["clang", "-O0", str(ir), "-o", str(probe)]))
check("large-digest-o0", run("digest", large), expected=hashlib.sha256(large).hexdigest().encode() + b"\n")
check("large-roundtrip-o0", run("roundtrip", first), expected=first)
check("large-origin-o0", run("origin", large))
check("unicode-origin-o0", run("origin", "é".encode() * 1200000))
probe = optimized_probe
# Both sides of the legacy pipes exceed pipe capacity at the same time.
worker = out / "worker.py"
worker.write_text("#!/usr/bin/env python3\nimport sys\nsys.stdout.buffer.write(b'x' * 200000); sys.stdout.flush()\nsys.stdin.buffer.read()\n")
worker.chmod(0o755)
check("duplex-worker", run("worker", large, arg=worker), expected=b"x" * 200000)
# Frozen mtimes, transitive includes and a warm artifact hit.
leaf = out / "leaf.lang"
helper = out / "helper.lang"
reader = out / "reader.lang"
guest = out / "answer.hostprobe"
leaf.write_text("func leaf() i64 { return 41; }\n")
helper.write_text('include "' + str(leaf) + '"\nfunc helper() i64 { return leaf(); }\n')
reader.write_text('include "std/ast.lang"\ninclude "' + str(helper) + '"\nreader hostprobe(text *u8) *u8 { return ast_main_i64(ast_number(emit_number(helper()))); }\n')
guest.write_text("input")
def read():
    return command([compiler, "read", "--compact", str(reader), str(guest)])
cold = check("dependency-cold", read())
artifact = out / "cache/readers/hostprobe"
stat = artifact.stat()
check("dependency-warm", read(), expected=cold)
assert artifact.stat().st_mtime_ns == stat.st_mtime_ns
before = leaf.stat()
leaf.write_text("func leaf() i64 { return 42; }\n")
os.utime(leaf, ns=(before.st_atime_ns, before.st_mtime_ns))
changed = check("dependency-same-mtime", read())
assert changed != cold and b"42" in changed and b"41" in cold
(out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
if not all(row["pass"] for row in results):
    raise SystemExit(1)
print(f"{len(results)} host checks passed; evidence: {out}")
