# Sui Move in this container

`sui` is installed and `sui move test` works. **There is no network.**
That changes two things about every command you run.

`/work` is a 1g tmpfs. Keep PoCs to one filtered test. A full package
`build/` plus extra copies of the framework will blow the disk.

## Detect Sui vs Aptos first

Read every `Move.toml` under `unzipped/`.

| Dialect | Markers in `Move.toml` |
|---|---|
| **Sui** (this image) | `Sui =`, `MystenLabs/sui`, `sui-framework`, `sui = "0x2"` |
| **Aptos** | `AptosFramework`, `AptosStdlib`, `aptos-labs/aptos-core`, `aptos_framework` |

No match → **Sui**. Aptos packages: there is no `aptos` binary here.
Mark those findings **UNVERIFIED**. Do not try to prove them with
`sui move test` — the runtimes are not the same.

## The flags you always need

```
sui move test --skip-fetch-latest-git-deps --filter test_attacker_drains
```

`--skip-fetch-latest-git-deps` stops the package manager reaching GitHub
for `Sui` / `MoveStdlib`. Without it the build dies with a DNS error.

`$SUI_FRAMEWORK_DIR` (default `/opt/sui-framework/packages/sui-framework`)
is the vendored Sui framework, with `MoveStdlib` beside it at
`/opt/sui-framework/packages/move-stdlib`.

These are **command-line flags**. Do not edit the uploader's `Move.toml`
inside `unzipped/` to add them.

## Never modify `unzipped/`

Read it, compile against it, do not write it. Tests, rewritten manifests,
and `build/` go under `poc/` (or `/tmp`), never back into `unzipped/`.

## Use their package, from a copy

If `unzipped/` contains a `Move.toml`, that package is the one that will
compile their modules. **Do not add tests inside it.** Copy the package
tree into `poc/` and work on the copy:

```
# find the package root (the directory that holds Move.toml)
# copy it to poc/pkg/  --  leave unzipped/ untouched
```

If the copy's `Move.toml` pins `Sui` via git, rewrite **the copy** to the
vendored framework:

```toml
[dependencies]
Sui = { local = "/opt/sui-framework/packages/sui-framework" }
```

Then put your test module in `poc/pkg/tests/` and run:

```
cd poc/pkg && sui move test --skip-fetch-latest-git-deps --filter test_foo
```

If their lockfile / git rev needs a framework this image does not have,
mark UNVERIFIED. Do not fake a compile.

Only if they shipped no `Move.toml` do you use the scaffolded `poc/`,
which already points `Sui` at `$SUI_FRAMEWORK_DIR`. Copy the in-scope
`.move` files into `poc/sources/` (a copy, not a move) and put tests in
`poc/tests/`.

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `Could not resolve host` / git fetch failed | missing `--skip-fetch-latest-git-deps`, or git deps | add the flag; retarget a **copy** of Move.toml at `$SUI_FRAMEWORK_DIR` |
| `Unable to resolve packages` | git `Sui` pin, empty vendor | local path on the copy; if that still fails, UNVERIFIED |
| edition / compiler mismatch | their edition is not what this CLI speaks | say so and mark UNVERIFIED |
| abort in their existing tests | pre-existing breakage, not yours | `--filter` your own test only |
| `aptos: not found` | Aptos package | UNVERIFIED; this image is Sui-only |
| no space left on device | `/work` is 1g | delete `build/`, run one `--filter` test, stop copying the framework |

## Run only your test

Their suite may be broken, slow, or noisy. Scope every run:

```
sui move test --skip-fetch-latest-git-deps --filter test_attacker_drains
```

Quote the PASS / FAIL line. That is what you need to show *why* it
failed or that the attacker succeeded.

## Compiling is not proving

`sui move build` succeeding means nothing about the finding. Only a test
that runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).
