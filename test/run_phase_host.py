#!/usr/bin/env python3
"""Compile and exercise the production host boundary, including failure paths."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading

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
for name, data, error in [("depth", b"(" * 513 + b")" * 513, "ast-depth"),
                          ("unclosed", b"(program", "ast-shape"),
                          ("trailing", b"(program) (program)", "ast-shape"),
                          ("quote", b'(program "abc)', "ast-shape"),
                          ("root", b"garbage", "ast-root")]:
    check(name, run("shape", data), error=error)
check("configured-depth", run("shape", b"(" * 129 + b")" * 129, {"LANG_HOST_MAX_DEPTH": "128"}), error="ast-depth")
check("raised-depth", run("shape", b"(" * 700 + b")" * 700, {"LANG_HOST_MAX_DEPTH": "1024"}))
check("invalid-depth-limit", run("shape", b"(program)", {"LANG_HOST_MAX_DEPTH": "1025"}), error="invalid-depth-limit")
check("source-register", run("register"))
check("nodes", run("shape", b"(program " + b"a " * 1048577 + b")", {"LANG_HOST_MAX_NODES": "1048576"}), error="ast-nodes")
check("origins", run("origin", "éabc".encode()))
for name, text in [("empty", ""), ("mixed", "é\n\nabc\r\nz\n"), ("no-newline", "hello é")]:
    check("span-index-" + name, run("span-index", text.encode()))
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
deep_source.write_text("func main() i64 { return " + "(" * 513 + "0" + ")" * 513 + "; }")
check("native-depth", command([compiler, str(deep_source), "--emit-expanded-ast", "-o", str(out / "deep.ast")]), error="source-depth")
ast_bytes = ast.read_bytes()
assert large in ast_bytes
first = check("large-ast-parse", run("roundtrip", ast_bytes))
check("large-ast-fixed-point", run("roundtrip", first), expected=first)
# Ordinary left-associative expressions and else-if chains cross the AST boundary.
for name, body, value, setting in [
    ("sum-200", "return " + " + ".join(["1"] * 200) + ";", 200, {}),
    ("sum-700", "return " + " + ".join(["1"] * 700) + ";", 700, {"LANG_HOST_MAX_DEPTH": "1024"}),
    ("else-if-150", "".join("if 0 { return 1; } else " for _ in range(150)) + "{ return 23; }", 23, {}),
]:
    path = out / (name + ".lang")
    path.write_text("func main() i64 { " + body + " }\n")
    emitted = out / (name + ".ast")
    check(name + "-emit", command([compiler, str(path), "--emit-expanded-ast", "-o", str(emitted)], extra=setting))
    llvm = out / (name + ".ll")
    check(name + "-from-ast", command([compiler, "--from-ast", str(emitted), "-o", str(llvm)], extra=setting))
    executable = out / name
    check(name + "-link", command(["clang", "-O0", str(llvm), "-o", str(executable)]))
    check(name + "-run", command([str(executable)]), code=value % 256)
    if name == "sum-200":
        refused = command([compiler, "--from-ast", str(emitted), "-o", str(llvm)], extra={"LANG_HOST_MAX_DEPTH": "128"})
        check("raw-depth-source", refused, error="ast-depth")
        assert str(emitted).encode() in refused.stderr
spanned = out / "unbound.ast"
spanned.write_text('(program (func main () (type_base i64) (block (return (span 7 9 (number 20))))))')
refused = command([compiler, "--from-ast", str(spanned), "-o", str(out / "unbound.ll")])
check("raw-span-source", refused, error="missing-span-source")
assert str(spanned).encode() in refused.stderr
latin = out / "latin.lang"
latin.write_bytes(b"// \xe9\nfunc main() i64 { return 0; }\n")
refused = command([compiler, str(latin), "-o", str(out / "latin.ll")])
check("native-invalid-utf8", refused, error="invalid-utf8")
assert str(latin).encode() in refused.stderr
# A root source supplied once must not be reopened for origins or expansion.
fifo = out / "once.lang"
if fifo.exists():
    fifo.unlink()
os.mkfifo(fifo)
def write_root():
    with fifo.open("w") as pipe:
        pipe.write("func main() i64 { return 7; }\n")
writer = threading.Thread(target=write_root, daemon=True)
writer.start()
check("root-snapshot", command([compiler, str(fifo), "--emit-expanded-ast", "-o", str(out / "once.ast")]))
writer.join(timeout=5)
assert not writer.is_alive() and b"(number 7)" in (out / "once.ast").read_bytes()
fifo.unlink()
# A large first guest followed by many appends must retain allocated capacity.
guest = out / "large.capacityprobe"
guest.write_bytes(large)
empty = out / "empty.lang"
empty.write_text("")
check("combined-capacity", command([compiler, str(guest)] + [str(empty)] * 100 + ["--emit-ast", "-o", str(out / "combined.ast")]))
calc_input = out / "deep.calc"
calc_input.write_text("answer " + " + ".join(["1"] * 150))
check("calc-deep-read", command([compiler, "read", "example/calc/calc.lang", str(calc_input)]))
# Native legacy readers are linked without optimization. The host must also
# retain bounded stack use there, rather than depending on LLVM promotion.
optimized_probe = probe
probe = out / "probe-o0"
check("link-probe-o0", command(["clang", "-O0", str(ir), "-o", str(probe)]))
check("large-digest-o0", run("digest", large), expected=hashlib.sha256(large).hexdigest().encode() + b"\n")
check("large-roundtrip-o0", run("roundtrip", first), expected=first)
check("deep-roundtrip-o0", run("roundtrip", (out / "sum-700.ast").read_bytes(), {"LANG_HOST_MAX_DEPTH": "1024"}))
check("large-origin-o0", run("origin", large))
check("unicode-origin-o0", run("origin", "é".encode() * 1200000))
probe = optimized_probe
# Both sides of the legacy pipes exceed pipe capacity at the same time.
worker = out / "worker.py"
worker.write_text("#!/usr/bin/env python3\nimport sys\nsys.stdout.buffer.write(b'x' * 200000); sys.stdout.flush()\nsys.stdin.buffer.read()\n")
worker.chmod(0o755)
check("duplex-worker", run("worker", large, arg=worker), expected=b"x" * 200000)
# File snapshots must remain distinct from C-reader slices with the same name.
algorithm_ir = out / "algorithms.ll"
for state in ["cold", "warm"]:
    check("c-snapshot-" + state, command([compiler, "example/c/algorithms.lang", "-o", str(algorithm_ir)]))
    if state == "cold":
        cold_ir = algorithm_ir.read_bytes()
    else:
        assert algorithm_ir.read_bytes() == cold_ir
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
