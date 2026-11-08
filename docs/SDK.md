# Local native SDK

There is no public download yet. A maintainer creates a local archive from a
clean, committed Linux x86-64 checkout:

```sh
nice -n 10 python3 scripts/package_sdk.py --output ../release
```

Packaging requires Python 3.11+, Git, GNU make, Clang and the system C development
toolchain (headers, libc, startup objects, assembler and linker). It builds the
current compiler once from the preserved seed at `-O2`. The archive contains the
native compiler, standard library, compiler-builder resources, embedded reader
starter generator, Tariff sources, documentation and license. It contains no Git
checkout, bootstrap seed, reader cache or dependency downloads. The packaged
`src/` files are compiler-builder resources; creating a reader does not rebuild
the Lang compiler.

The default version is `0.1.0+<12-digit commit>`; `--version` may assign a release
version. The adjacent `.receipt.json` identifies the full commit, tool versions,
file sizes and SHA-256 hashes, archive bytes and SHA-256. `sdk.json` inside the
archive describes its inputs. Two runs with the same commit and toolchain produce
byte-identical archives; output directories must be fresh. Build logs and source
build directories remain beside the output for inspection. Packaging does not
upload, tag or publish anything.

## First language from the archive

Users need Linux x86-64 with glibc, `/bin/sh`, Clang, and the system C development
toolchain. Unpacking needs an XZ-capable tar. No Python, make, Git, bootstrap seed
or Lang checkout is needed to use the SDK. This is a native build for the producer's
glibc/toolchain baseline, not a portable static binary: inspect `ldd libexec/lang`
on the extracted SDK and use an equal or newer glibc (the recorded build uses
Debian glibc 2.41). On Debian/Ubuntu, provision `clang build-essential xz-utils`
with your administrator before starting. Clang 19.1.7 and 23.1.5 are exercised;
other versions are unverified. Clang must be executable on PATH, or select its
absolute executable with `LANG_CLANG`. Keep the extracted directory intact;
`bin/lang` locates resources relative to itself. Work in a separate empty directory.

```sh
# Substitute the actual version printed by the packaging command.
tar -xJf /absolute/path/release/lang-<version>-x86_64-linux.tar.xz
export SDK="$PWD/lang-<version>-x86_64-linux"
export PATH="$SDK/bin:$PATH"
mkdir my-language
cd my-language
lang new reader tiny
lang compiler tiny tiny.lang -o tinyc
./tinyc answer.tiny -o answer.ll
clang -O2 answer.ll -o answer
./answer
echo $?  # 42
```

The starter accepts `answer NUMBER`; edit `tiny.lang` to evolve it. The minted
compiler embeds the reader and native backend. It can emit LLVM without Clang;
linking LLVM into an executable requires Clang and the system C toolchain.
SDK build commands check for Clang before expanding readers, and report one
plain prerequisite message with installation advice if it is missing. `new`,
`help`, `version` and `doctor` need no Clang. `LANG_ROOT` is an optional resource
override; leave it unset for the archive journey.

For the larger Tariff DSL, copy `examples/dsl-compare/lang/tariff.lang` and the
fixtures from the SDK, compile the frontend with `lang "$SDK/std/core.lang" tariff.lang
-o tariff.ll`, then `clang -O2 tariff.ll -o tariff`. That frontend emits shared AST;
`lang --from-ast program.ast --ast-source program.tariff -o program.ll` lowers it.
Link `program.ll` with the supplied `harness.c` using `clang -O2`.
The comparison runner's `--sdk` arm measures this same pipeline and excludes
archive building and extraction as tool provisioning, just like parser installs.
The [comparison](compare-yacc-antlr.md) retains the source-build arm alongside it.
