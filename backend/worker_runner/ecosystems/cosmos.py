"""Cosmos SDK + CosmWasm audit profile."""

import os

from backend.worker_runner.profiles import (
    AuditProfile,
    Role,
    Toolchain,
    registry,
)

COSMOS_TOOLS = Toolchain(
    key="cosmos",
    image=os.getenv("WORKER_IMAGE_COSMOS", "evmbench/worker-cosmos:latest"),
    project_markers=("go.mod", "Cargo.toml"),
    scaffold_dirs=("go", "cw", "cw/src"),
    scaffold_files=(
        (
            "go/go.mod",
            """\
module poc

go 1.23
""",
        ),
        (
            "cw/Cargo.toml",
            """\
[package]
name = "poc"
version = "0.1.0"
edition = "2021"

[dependencies]
cosmwasm-std = { version = "2.2", features = ["std"] }
""",
        ),
        (
            "cw/src/lib.rs",
            "// Fallback CosmWasm crate, written only because the upload shipped no Cargo.toml.\n",
        ),
    ),
    briefing="""\
## Compiling and testing

If the upload has its own `go.mod` or `Cargo.toml`, **use it**. It carries
their SDK / `cosmwasm-std` version, replace directives, workspace members
and features, and nothing else will compile their code. Work inside their
project and add your tests next to theirs (a new `*_test.go` or a new
`#[cfg(test)]` module). Prefer writing tests under `{poc}/` with a module
`replace` / path dependency so you never have to edit their tree.

There is no network. Two rules on every command:

```
GOPROXY=off GOSUMDB=off go test ./... -count=1 -v
cargo test --offline -- --nocapture
```

`GOPROXY=off` and `CARGO_NET_OFFLINE=true` are already in the environment.
Do not set them back. Do not run `go get`, `go mod download`, `go mod tidy`,
`cargo fetch`, or `cargo update`.

- Cosmos SDK modules (`.go`) — `go test`. The module cache at
  `$GOMODCACHE` (`/opt/go/pkg/mod`) already holds cosmos-sdk v0.50 and
  v0.53, ibc-go v8 and v10, cometbft, and testify.
- CosmWasm contracts (`.rs`) — `cargo test --offline`. `$CARGO_HOME`
  (`/opt/cargo`) already holds cosmwasm-std 1.5 and 2.2, cw-storage-plus,
  cw-multi-test, cw2, and cw20. Prefer in-process
  `cosmwasm_std::testing` or `cw-multi-test`. Never `cargo wasm`.

If the upload has neither `go.mod` nor `Cargo.toml`, use `{poc}/go/` for
SDK tests and `{poc}/cw/` for CosmWasm tests. If their lockfile needs a
dep that is not in the image cache, mark the finding **UNVERIFIED**.

## /work is a 1g tmpfs

Rust debug builds can fill it and kill the job. `CARGO_TARGET_DIR` is
`/tmp/target` so objects land off `/work`. Still keep crates small. If
you see `No space left on device`, stop and mark UNVERIFIED.

## Tools on PATH

- `go` — Go 1.23, for compiling and running SDK module tests
- `cargo`, `rustc` — Rust 1.81, for CosmWasm tests

There is no internet access. `go get`, `cargo fetch` and `git clone` will
fail. Anything not already installed is not available, so do not try to
fetch dependencies.
""",
)

AUDITOR = Role(
    key="auditor",
    label="Auditor",
    skill="cosmos-auditor",
    command="/cosmos-auditor",
    max_turns=200,
    description="Reads Cosmos SDK modules and CosmWasm contracts and reports suspected vulnerabilities.",
    source="https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/cosmos-vulnerability-scanner",
)

BREAKER = Role(
    key="breaker",
    label="Bug breaker",
    skill="bug-breaker",
    command="/bug-breaker",
    description="Tries to prove each claimed bug with go test or cargo test --offline.",
    max_turns=300,
)

registry.register(
    AuditProfile(
        key="cosmos",
        label="Cosmos SDK + CosmWasm",
        roles=(AUDITOR, BREAKER),
        toolchain=COSMOS_TOOLS,
        include_globs=("**/*.go", "**/*.rs"),
        exclude_globs=(
            "**/vendor/**",
            "**/testdata/**",
            "**/test/**",
            "**/tests/**",
            "**/mocks/**",
            "**/target/**",
            "**/*_test.go",
            "**/*_test.rs",
            "**/*Mock*",
            "**/*mock*",
        ),
        description="Loss-of-funds and consensus-critical bugs in Cosmos SDK modules and CosmWasm contracts, with proofs.",
    )
)
