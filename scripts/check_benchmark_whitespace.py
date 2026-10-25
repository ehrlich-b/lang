#!/usr/bin/env python3
"""Verify the sealed, byte-exact reader benchmark whitespace revision."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

BASELINE = "f72bc13de73454f8bf176658d4252f0ab4daa256"
OLD_MANIFEST_SHA256 = "5264e95368289b19a86aff673424390ec4001ef361250dfc287ce7a08835cacb"
BENCHMARK = "benchmark/reader_tasks"
OPERATOR = "operator:corpus.json.gz"
ADDITIONS = {"scripts/check_benchmark_whitespace.py", "test/test_benchmark_whitespace.py"}
SITES = {
    "tasks/R08/starter.lang": (
        59, "bf166f1ff14978492e643ffd691106177f2109df5ca856c90926274a4e33e143",
        "b633169cfb540707a7f36fd6cd0f2eb73a741f7bda67785a2886e36180da3eac"),
    "tasks/R09/starter.lang": (
        59, "e77bd18a6dd82cfb1648a538ad35eb202a4058697ecc6c3362eb0325191e3a50",
        "d6d9456130ad55a2d16de4bb0838c5ff44a2a53d8316b5353423c9310d921f0e"),
    "tasks/R10/starter.lang": (
        59, "bd34d2f5a34a3867c78d81bac41b4a98c678ea2a625f254e3dbe084984f4286e",
        "4208f3321877465137b05bd4f0b167d9cb1ca2185dd3638cae25d965e379067f"),
    "tasks/R11/starter.lang": (
        59, "f90c50e9f544b4d8a52cb42edaf288f7c9df87851fb1170ee3e4e2a4b6998b42",
        "b96c4b6613e7d8ba61c1b0358077722ae26ad0779e5538c24d60bce763015a9b"),
    "tasks/R12/starter.lang": (
        59, "f8e5a50b2d24622d94ea33485455ca110b3181ae653daca7eb5fbf84911a6b91",
        "9ce3346ab1fa7954163af002e4d3cebfb4df5397aa728a08e9268114a7d5e38d"),
    "tasks/R13/starter.lang": (
        59, "56248330c8f190cfec5dc7328fd805c074b309ddc244ce94d3a6c19486dfe3b1",
        "40ae6d41ed3489e4d966cf2b7a5679e5469b5f5dd3e093f171b02cc7ef9b229d"),
    "tasks/R15/starter.lang": (
        59, "c640fe82db50415c1c457ec734ae7db22506bd35e6a0d0d0c61119dc21b228a4",
        "5214dd53bcc9ed9b78c48bcfd3a448fac4b5f1755baa17a9568d3d45768fb7aa"),
    "tasks/R16/starter.lang": (
        59, "790f8831c8775ba3c4739ea6d2cc844b810b889b037f87e53b4b44f351a852d3",
        "f181b843609e60c3ecffb79e3f32d5042ce0a1ac10bae14ab0822aa5c68e817e"),
    "tasks/R17/starter.lang": (
        60, "7247a3d3b0da6a277ff17d88bc0fae84292d44aafe853670ba60bcd083d5b5a2",
        "96b301e8277f2bca60f16a6054ea48f5bece33b14b63721488d6107e82205615"),
    "tasks/R18/starter.lang": (
        59, "bf32599126a81d521f2ec0754c9e21a26fd4e3317c30f450f240f55fdf7c69bf",
        "83afe134c0a5ad029f81e0d4ef4f9ba074dbd3945eb3496bb21df112e8b39580"),
    "tasks/R19/starter.lang": (
        59, "2792efd0768c9412e79ca893028e8d618dddf701ab8ff0bc6072a6bd31bd5f22",
        "2f35abae7952e699c89f83bc5e2cd7ff221b015524eaa9d25e11157815f8d2ae"),
    "tasks/R20/starter.lang": (
        59, "f564ada5022694be2703ea5a1ee6b3f68772e8eab46e65d726b7a6f8f49faa5e",
        "0081e87f67c9667a0b4caf657b905dde3ad80a5b89ce1e6ccb4eaf352529ce00"),
}


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def load_baseline(root, baseline=BASELINE):
    require(baseline == BASELINE, "baseline must be the full sealed source pin")
    require(git(root, "rev-parse", baseline).decode().strip() == BASELINE, "source pin mismatch")
    paths = git(root, "ls-tree", "-r", "--name-only", baseline, "--", BENCHMARK).decode().splitlines()
    return {str(PurePosixPath(p).relative_to(BENCHMARK)):
            git(root, "show", baseline + ":" + p) for p in paths}


def parse_manifest(data):
    entries = {}
    for line in data.decode("ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(match is not None, "malformed checksum entry")
        value, name = match.groups()
        path = PurePosixPath(name)
        require(not path.is_absolute() and ".." not in path.parts and str(path) == name,
                "unsafe checksum path")
        require(name not in entries and name != "SHA256SUMS", "duplicate/self checksum")
        entries[name] = value
    return entries


def verify_checksums(directory, entries, corpus=None):
    for name, expected in entries.items():
        if name == OPERATOR:
            require(corpus is not None, "operator archive required via --corpus or READER_TASK_CORPUS")
            require(not Path(corpus).resolve().is_relative_to(directory.resolve()),
                    "operator archive must stay external")
            path = Path(corpus)
        else:
            path = directory / name
        require(digest(path.read_bytes()) == expected, "checksum mismatch: " + name)


def expected_revision(originals):
    old_manifest = originals["SHA256SUMS"]
    require(digest(old_manifest) == OLD_MANIFEST_SHA256, "forged old manifest")
    entries = parse_manifest(old_manifest)
    require(set(entries) == (set(originals) - {"SHA256SUMS"}) | {OPERATOR}, "old manifest coverage mismatch")
    for name, expected in entries.items():
        if name == OPERATOR:
            continue
        require(digest(originals[name]) == expected, "old checksum mismatch: " + name)
    expected_files = dict(originals)
    manifest = old_manifest
    mapping = []
    for name, (number, old_hash, new_hash) in SITES.items():
        old = originals[name]
        require(digest(old) == old_hash, "old starter hash mismatch: " + name)
        lines = old.splitlines(keepends=True)
        require(lines[number - 1] == b"    \n", "unrecorded blank-line bytes: " + name)
        lines[number - 1] = b"\n"
        new = b"".join(lines)
        require(digest(new) == new_hash, "new starter hash mismatch: " + name)
        require(len(old.splitlines()) == len(new.splitlines()), "line count changed: " + name)
        expected_files[name] = new
        old_entry = (old_hash + "  " + name + "\n").encode()
        new_entry = (new_hash + "  " + name + "\n").encode()
        require(manifest.count(old_entry) == 1, "missing old starter checksum: " + name)
        manifest = manifest.replace(old_entry, new_entry)
        mapping.append({"path": BENCHMARK + "/" + name, "line": number,
                        "old_sha256": old_hash, "new_sha256": new_hash,
                        "old_bytes": len(old), "new_bytes": len(new),
                        "line_count": len(lines), "removed_bytes": 4})
    expected_files["SHA256SUMS"] = manifest
    return expected_files, mapping


def check_benchmark(root, originals):
    directory = Path(root) / BENCHMARK
    expected_files, mapping = expected_revision(originals)
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file() or p.is_symlink()}
    require(actual == set(originals), "extra or missing benchmark files")
    require(all(not (directory / name).is_symlink() for name in actual), "benchmark symlink")
    entries = parse_manifest((directory / "SHA256SUMS").read_bytes())
    require(set(entries) == (set(originals) - {"SHA256SUMS"}) | {OPERATOR}, "manifest coverage mismatch")
    verify_checksums(directory, {name: value for name, value in entries.items() if name != OPERATOR})
    require((directory / "SHA256SUMS").read_bytes() == expected_files["SHA256SUMS"],
            "manifest changes exceed twelve starter digests")
    for name, expected in expected_files.items():
        if name != "SHA256SUMS":
            require((directory / name).read_bytes() == expected, "unexpected byte/semantic delta: " + name)
    return mapping


def check_scope(root):
    changed = set(git(root, "diff", "--name-only", BASELINE, "--").decode().splitlines())
    changed.update(git(root, "ls-files", "--others", "--exclude-standard").decode().splitlines())
    required = {BENCHMARK + "/" + name for name in SITES} | {BENCHMARK + "/SHA256SUMS"} | ADDITIONS
    require(changed == required, "file allowlist mismatch: " + repr(sorted(changed ^ required)))
    modes = git(root, "diff", "--summary", BASELINE, "--", BENCHMARK).decode()
    require(not modes, "benchmark file mode changed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=BASELINE)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--corpus", type=Path, default=os.environ.get("READER_TASK_CORPUS"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        originals = load_baseline(root, args.baseline)
        mapping = check_benchmark(root, originals)
        check_scope(root)
        result = {"baseline": BASELINE, "revision": "blank-line-whitespace-v2",
                  "historical_bytes_preserved": False, "sites": mapping,
                  "repository_checksums_checked": len(originals) - 1,
                  "operator_checksum": parse_manifest(originals["SHA256SUMS"])[OPERATOR],
                  "operator_status": "PASS" if args.corpus else "HOLD: archive unavailable"}
        if args.corpus:
            verify_checksums(root / BENCHMARK, {OPERATOR: result["operator_checksum"]}, args.corpus)
        if args.evidence:
            destination = args.evidence.resolve()
            require(not destination.is_relative_to(root), "evidence must be outside checkout")
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "hash-map.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        require(args.corpus is not None, "operator archive required via --corpus or READER_TASK_CORPUS")
    except (Invalid, OSError, subprocess.CalledProcessError) as error:
        print("benchmark whitespace check FAILED: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
