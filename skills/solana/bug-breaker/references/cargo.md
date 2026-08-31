# Cargo in this container

`rustc` and `cargo` are installed. **There is no network.** Every test
run must be offline. Crates that were not vendored at image build time
cannot be fetched.

## The flags you always need

```
cargo test --offline -- --nocapture
```

`--offline` stops cargo reaching crates.io. If the lockfile wants a
crate version that is not in `$CARGO_HOME`, the command fails. That is
**UNVERIFIED**, not a reason to retry without `--offline`.

Scope a single test:

```
cargo test --offline --test withdraw_unsigned -- --nocapture
```

or, inside their package:

```
cargo test --offline --manifest-path unzipped/programs/vault/Cargo.toml \
    --test withdraw_unsigned -- --nocapture
```

These are **command-line flags**. Do not edit their `Cargo.toml` or
`Cargo.lock` to add them.

## Use their project, not yours

If `unzipped/` contains a `Cargo.toml` or `Anchor.toml`, **compile
against it** — it carries the crate graph, features and `[patch]` tables
their code needs. Nothing else will compile it.

**Never modify anything in `unzipped/`.** Do not edit their manifests,
source, or lockfile. Put new tests in `poc/` and, if you must depend on
their package, add a path dependency from `poc/Cargo.toml` to
`../unzipped/...` — that file lives in `poc/`, not in their tree.

If they shipped no `Cargo.toml` / `Anchor.toml`, `poc/` is already
scaffolded with LiteSVM as a dev-dependency.

## Prefer LiteSVM; mind `/work`

`/work` is a **1g tmpfs**. A full Solana debug build will fill it and
fail. Prefer in-process LiteSVM tests. Set, if needed:

```
export CARGO_INCREMENTAL=0
export CARGO_PROFILE_DEV_DEBUG=0
```

Do not start `solana-test-validator`. There is no validator in this
image, and no RAM budget for one.

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `can't download from crates.io` / `network disabled` | missing `--offline`, or crate not cached | add `--offline`; if still failing, **UNVERIFIED** |
| `no matching package named X` | their lockfile wants a crate/version not vendored | **UNVERIFIED** — do not cargo add |
| `target/` disk full / No space left | 1g tmpfs | drop debug info; if still too big, **UNVERIFIED** |
| `unresolved import` inside unzipped | their path deps | run inside their workspace |
| Their whole suite fails | pre-existing breakage | `--test your_poc` / `-- --exact your_fn` only |

## Compiling is not proving

`cargo build --offline` succeeding means nothing about the finding. Only
a test that runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).
