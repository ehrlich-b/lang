#!/usr/bin/env python3
"""Exercise shadowed bindings on native LLVM and LLVM wasm32."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
compiler = os.environ.get("COMPILER", "./out/lang")
cases = {
    "294_shadow_parameter.lang": "43\n",
    "295_shadow_nested_lets.lang": "40\n",
    "296_shadow_sibling_blocks.lang": "42\n",
    "297_shadow_lambda_capture.lang": "44\n",
    "298_shadow_loop.lang": "16\n",
    "299_shadow_minilisp.lang": "42\n",
    "300_shadow_global.lang": "42\n",
}
with tempfile.TemporaryDirectory() as tmp:
    for name, expected in cases.items():
        for target in ("linux", "wasm"):
            env = dict(os.environ, LANGBE="llvm", LANGOS=target, LANG_CACHE=tmp + "/cache")
            ll, binary = Path(tmp) / "test.ll", Path(tmp) / "test.bin"
            subprocess.run([compiler, "test/suite/" + name, "-o", str(ll)], cwd=root, env=env, check=True)
            command = ["clang", str(ll), "-o", str(binary)]
            if target == "wasm":
                command = ["clang", "--target=wasm32-unknown-unknown", "-nostdlib", "-Wl,--no-entry", "-Wl,--export-all", "-Wl,--allow-undefined", "-Wl,-z,stack-size=8388608", str(ll), "-o", str(binary)]
            subprocess.run(command, cwd=root, check=True)
            run = [str(binary)] if target == "linux" else ["node", "test/wasm_host.js", str(binary)]
            result = subprocess.run(run, cwd=root, capture_output=True, text=True, check=True)
            if result.stdout != expected:
                raise AssertionError(f"{name} {target}: {result.stdout!r} != {expected!r}")
            print(f"PASS {name} {target}: {result.stdout!r}", flush=True)
