#!/usr/bin/env python3
"""Select bounded regression tests from changed paths; never build a compiler."""
from concurrent.futures import ThreadPoolExecutor
import fnmatch
import json
import os
from pathlib import Path
import re
import resource
import shlex
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "test/fragment-map.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def changed_paths():
    if os.environ.get("FRAGMENT_EXPLICIT") == "1":
        return shlex.split(os.environ.get("FILES", "")), "FILES"
    commit = os.environ.get("FRAGMENT_COMMIT")
    if commit:
        # Measure a historical change's footprint with today's candidate compiler.
        return git("diff", "--name-only", "--no-renames", "-z", commit + "^", commit).split("\0"), commit
    base = os.environ.get("FRAGMENT_BASE") or "origin/main"
    merge_base = git("merge-base", "HEAD", base)
    paths = git("diff", "--name-only", "--no-renames", "-z", merge_base).split("\0")
    paths += git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    return paths, "merge-base " + merge_base


def select(paths, mapping):
    selected, notices = set(), []
    for raw in paths:
        if not raw:
            continue
        path = Path(raw)
        if path.is_absolute():
            path = path.relative_to(ROOT)
        if ".." in path.parts:
            raise ValueError("FILES must stay inside the repository")
        path = path.as_posix()
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in mapping["no_tests"]):
            continue
        matched = False
        for rule in mapping["paths"]:
            if fnmatch.fnmatchcase(path, rule["glob"]):
                selected.update(rule["tests"])
                matched = True
        if matched:
            continue
        if path.startswith("test/suite/") and path.endswith(".lang") and (ROOT / path).is_file():
            selected.add(path)
        else:
            selected.update(mapping["groups"]["compiler-smoke"])
            notices.append(f"unmapped {path}: falling back to compiler-smoke")
    # Rules may refer to named groups or directly to a fixture.
    expanded = set()
    for name in selected:
        expanded.update(mapping["groups"].get(name, [name]))
    return sorted(expanded), notices


def invoke(command, env, timeout=30):
    # Readers and helper compilers inherit this group, even when the immediate
    # child exits or a descendant closes the captured output pipes.
    with subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # The whole group already exited.
            process.communicate()  # Drain pipes and reap the immediate child.
            raise
        return process.returncode, (stdout + stderr).decode("utf-8", "replace")


def run_test(name, compiler, mapping, scratch):
    case = mapping.get("cases", {}).get(name, {"source": name})
    with tempfile.TemporaryDirectory(prefix="case-", dir=scratch) as tmp:
        env = dict(os.environ, COMPILER=str(compiler), LANGBE="llvm",
                   LANGOS="macos" if sys.platform == "darwin" else "linux",
                   LANG_CACHE=tmp + "/cache", TMPDIR=tmp)
        try:
            if "command" in case:
                status, detail = invoke(case["command"], env)
                return {"test": name, "status": "PASS" if status == 0 else "FAIL", "detail": detail}
            source = ROOT / case["source"]
            lines = source.read_text().splitlines()
            if lines[0].startswith("//ignore"):
                return {"test": name, "status": "SKIP", "detail": "ignored by suite"}
            if ("//linux" in "\n".join(lines[:3]) and env["LANGOS"] != "linux") or (
                    "//macos" in "\n".join(lines[:3]) and env["LANGOS"] != "macos"):
                return {"test": name, "status": "SKIP", "detail": "platform marker"}
            ir, binary = tmp + "/test.ll", tmp + "/test"
            status, detail = invoke([str(compiler), str(source), "-o", ir], env)
            if lines[0].startswith("// reject: "):
                expected = lines[0][len("// reject: "):]
                ok = status != 0 and expected in detail
            else:
                # Suite headers also use Expected, expect:0 and trailing //clang.
                marker = re.fullmatch(r"// expect(?:ed)?:\s*(\d+)(?:\s+//.*)?", lines[0], re.IGNORECASE)
                expected = case.get("exit", int(marker[1]) if marker else None)
                if expected is None:
                    raise ValueError("fixture needs // expect: N or an explicit exit oracle")
                if status != 0:
                    return {"test": name, "status": "FAIL", "detail": "compile failed\n" + detail}
                # These oracles exercise semantics, not LLVM optimization.
                status, detail = invoke(["clang", "-O0", ir, "-o", binary], env)
                if status != 0:
                    return {"test": name, "status": "FAIL", "detail": "link failed\n" + detail}
                status, detail = invoke([binary], env, timeout=5)
                ok = status == expected
                if "stdout" in case:
                    ok = ok and detail == case["stdout"]
                detail = f"expected exit {expected}, got {status}\n" + detail
            return {"test": name, "status": "PASS" if ok else "FAIL", "detail": detail}
        except subprocess.TimeoutExpired as exc:
            return {"test": name, "status": "FAIL",
                    "detail": f"{exc}; command process group killed; "
                              "CPU time for orphaned descendants may be unavailable"}
        except (OSError, ValueError) as exc:
            return {"test": name, "status": "FAIL", "detail": str(exc)}


def cpu_seconds():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def main():
    start = time.monotonic()
    mapping = json.loads(MAP.read_text())
    paths, basis = changed_paths()
    tests, notices = select(paths, mapping)
    jobs = max(1, min(4, int(os.environ.get("JOBS") or "4")))
    print(f"fragment: {basis}; {len(tests)} tests; JOBS={jobs}", flush=True)
    for notice in notices:
        print("fragment: " + notice, flush=True)
    results = []
    compiler = None
    if tests:
        requested = os.environ.get("COMPILER")
        compiler = ROOT / (requested or ("out/lang_next" if (ROOT / "out/lang_next").is_file() else "out/lang"))
        compiler = compiler.resolve()
        if not os.access(compiler, os.X_OK):
            raise ValueError(f"already-built compiler required: {compiler}; run make build first")
        print(f"fragment: compiler={compiler} (reused; no build)", flush=True)
        # One shared OS selection, before workers start; never rewrite it per test.
        (ROOT / "std/os.lang").write_text('include "std/os/' + ("libc_macos.lang" if sys.platform == "darwin" else "libc.lang") + '"\n')
        with tempfile.TemporaryDirectory(prefix="lang-fragment-") as scratch:
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                results = list(pool.map(lambda name: run_test(name, compiler, mapping, scratch), tests))
        for result in results:
            print(f"{result['status']} {result['test']}")
            if result["status"] == "FAIL":
                print(result["detail"])
    failures = sum(result["status"] == "FAIL" for result in results)
    report = {"basis": basis, "paths": sorted(set(filter(None, paths))), "tests": results,
              "test_count": len(tests), "failures": failures, "jobs": jobs,
              "compiler": str(compiler) if compiler else None,
              "cpu_seconds": round(cpu_seconds(), 6), "wall_seconds": round(time.monotonic() - start, 6)}
    print(f"fragment: {len(tests)} tests, {failures} failed; CPU seconds={report['cpu_seconds']:.3f}; wall seconds={report['wall_seconds']:.3f}")
    if os.environ.get("FRAGMENT_REPORT"):
        Path(os.environ["FRAGMENT_REPORT"]).write_text(json.dumps(report, indent=2) + "\n")
    return bool(failures)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"fragment: ERROR: {error}", file=sys.stderr)
        sys.exit(2)
