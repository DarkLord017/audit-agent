# Cargo tests in this container

`cargo` and `rustc` are installed and work. **There is no network.**
Crate downloads die with `--offline`.

## The flags you always need

```
cargo test --offline -- --nocapture
```

`--offline` stops cargo reaching crates.io. `CARGO_HOME` is `/opt/cargo`
and already holds `cosmwasm-std` (1.5 and 2.x), `cw-storage-plus`,
`cw-multi-test`, `cw2`, `cw20`, and their graphs as of image build. If
their `Cargo.lock` wants a crate or version that is not there, the build
will fail with `can't find crate` or `failed to get … from registry`.
That is UNVERIFIED — do not fake it.

## Use their project, not yours

If `unzipped/` contains a `Cargo.toml`, **work inside their crate**. It
carries the `cosmwasm-std` version, features and workspace members their
code needs. Put your tests in `src/` as `#[cfg(test)]` or in a `tests/`
file *you create under `poc/cw/` that depends on their package* — but
**never modify anything already in `unzipped/`** except adding a new
test file if you must. Prefer `poc/cw/` with a path dependency:

```toml
[dependencies]
the-contract = { path = "../../unzipped" }
cosmwasm-std = { version = "2", features = ["testing"] }
```

Only if they shipped no `Cargo.toml` do you use the stub `poc/cw/` crate
as-is. You will almost certainly still be UNVERIFIED without their
package — say so.

## /work is 1g

Rust debug builds of a CosmWasm workspace with `target/` under `/work`
will fill the tmpfs. Mitigations, in order:

1. Prefer `cosmwasm_std::testing` (no host, no wasm).
2. Then `cw-multi-test` (in-process, still no wasm32).
3. Set `CARGO_TARGET_DIR=/tmp/target` so objects land off the tmpfs if
   `/tmp` has room — if that also fills, stop.
4. Never `cargo wasm`, never `--release` unless a debug build already
   proved the disk is fine.
5. If the compile is killed with `No space left on device`, mark
   UNVERIFIED and quote that.

## Failures you will actually hit

| Symptom | Cause | Do this |
|---|---|---|
| `can't find crate` / registry error | missing cache entry | mark UNVERIFIED; never `cargo fetch` |
| `error: no matching package named …` | their lockfile vs image | UNVERIFIED |
| `can't find crate for 'std'` with `--target wasm32` | you targeted wasm | drop the target; tests run on host |
| `No space left on device` | 1g tmpfs | UNVERIFIED, quote it |
| Their whole suite fails | pre-existing breakage, not yours | `cargo test --offline --test your_poc -- --nocapture` |

## Run only your test

```
cargo test --offline attacker_drains_other_users_deposit -- --nocapture
```

`--nocapture` prints `println!` and assertion messages, which is what
you need to show *why* it failed.

## Compiling is not proving

`cargo check --offline` succeeding means nothing about the finding. Only
a test that runs and demonstrates the claimed behaviour counts. See
[poc.md](poc.md).

## Never modify unzipped/

Do not `cargo update`. Do not edit `Cargo.toml` / `Cargo.lock` in
`unzipped/`. Do not change contract source to make a test compile.
