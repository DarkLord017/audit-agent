# Scarb and snforge in this container

`scarb` and `snforge` are installed and work. **There is no network.**
That changes two things about every command you run.

## The flag you always need

```
scarb --offline test
```

or, equivalent, from a project that already has snforge configured:

```
snforge test
```

`--offline` on **scarb** stops it reaching the registry. `snforge test`
invokes scarb internally; if a run tries to fetch, wrap it:

```
scarb --offline snforge test
```

There is no compiler download step analogous to solc — Cairo ships inside
this Scarb. If their `Scarb.toml` pins a Cairo/edition this image cannot
satisfy, say so and mark UNVERIFIED. Do not try `scarb upgrade`.

## Use their project, not yours

If `unzipped/` contains a `Scarb.toml`, **work inside their project**. It
carries the dependencies, edition, `[tool.scarb] allow-prebuilt-plugins`,
and `[[target.starknet-contract]]` their code needs. Nothing else will
compile it. Put your tests in their `tests/` directory (create it if
missing). Do not edit their `Scarb.toml` to "fix" remappings; if it will
not build as shipped, that is UNVERIFIED.

Only if they shipped no `Scarb.toml` do you use `poc/`, which is
scaffolded with `snforge_std = "0.63.0"` (already in this image's
`SCARB_CACHE`) and a bare `src/lib.cairo`. Copy the contracts you need
from `unzipped/` into `poc/src/` (read-only on `unzipped/`) and declare
them from tests.

OpenZeppelin Cairo contracts are cloned at `/opt/cairo-contracts`
(v4.0.1). Path-dep a package if their code needs OZ and they did not
vendor a copy, for example:

```
openzeppelin_token = { path = "/opt/cairo-contracts/packages/token" }
```

If the import still will not resolve, mark UNVERIFIED.

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `Could not resolve host` / registry timeout | missing `--offline`, or a dep not in the cache | add `--offline`; never `scarb add` / `git clone` |
| `Package not found` / unresolved dep | their lockfile wants a crate this image did not vendor | cannot compile, mark UNVERIFIED, do not fake it |
| `Failed to get universal-sierra-compiler` | USC not on PATH | it is at `/opt/usc/bin`; `PATH` should already include it |
| Edition / Cairo version mismatch | their `edition` or cairo pin is newer than this Scarb | mark UNVERIFIED |
| Their whole suite fails | pre-existing breakage, not yours | `--exact test_your_poc_name` only |
| `/work` fills up (1g tmpfs) | `target/` from a fat debug build | `--exact` one test; do not build examples |

## Run only your test

Their suite may be broken, slow, or noisy. Scope every run:

```
snforge test --exact test_attacker_drains_other_users_deposit
```

or, if several tests share a prefix:

```
snforge test test_attacker_drains
```

Quote the output. A passing test without the captured run is not evidence.

## Compiling is not proving

`scarb --offline build` succeeding means nothing about the finding. Only a
test that runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).
