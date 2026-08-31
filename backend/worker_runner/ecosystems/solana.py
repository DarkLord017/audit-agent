"""Solana audit profile: solana-auditor then LiteSVM bug-breaker."""

import os

from backend.worker_runner.profiles import (
    AuditProfile,
    Role,
    Toolchain,
    registry,
)

SOLANA_TOOLS = Toolchain(
    key="solana",
    image=os.getenv("WORKER_IMAGE_SOLANA", "evmbench/worker-solana:latest"),
    project_markers=("Cargo.toml", "Anchor.toml"),
    scaffold_dirs=("src", "tests"),
    scaffold_files=(
        (
            "Cargo.toml",
            """\
# Fallback project, written only because the upload shipped no
# Cargo.toml / Anchor.toml of its own. If it had, that one would be
# used as-is — never rewrite theirs.
[package]
name = "poc"
version = "0.1.0"
edition = "2021"

[lib]
path = "src/lib.rs"

[dev-dependencies]
litesvm = "0.6"
solana-sdk = "2.2"
solana-program = "2.2"
""",
        ),
        (
            "src/lib.rs",
            """\
//! Empty library crate so `poc/` is a valid cargo package.
//! Tests live in tests/. Never modify unzipped/.
""",
        ),
    ),
    briefing="""\
## Compiling and testing

If the upload has its own `Cargo.toml` or `Anchor.toml`, **use it**.
It carries their crate graph, features and patches, and nothing else
will compile their programs. Depend on their package from `{poc}/` via
a path dependency if you need to. **Never modify `{source}/`.**

There is no network. Every cargo command must be offline:

```
cargo test --offline -- --nocapture
```

`--offline` stops cargo reaching crates.io. If their lockfile wants a
crate that is not in this image's `$CARGO_HOME`, mark the finding
**UNVERIFIED**. Do not `cargo add`, `cargo fetch`, or `cargo install`.

If the upload has no `Cargo.toml` / `Anchor.toml`, use `{poc}/`, which
is scaffolded with LiteSVM as a dev-dependency.

Prefer **LiteSVM** (in-process). Do not start `solana-test-validator`.
`solana-program-test` is cached for graphs that already use it.

`/work` is a **1g tmpfs**. A Solana debug build can fill it. Prefer
small LiteSVM tests; `CARGO_INCREMENTAL=0` and
`CARGO_PROFILE_DEV_DEBUG=0` are already set. If the build still OOM's,
mark **UNVERIFIED**.

## Tools on PATH

- `cargo`, `rustc` -- host toolchain for compiling and running tests
- LiteSVM crates -- vendored in `$CARGO_HOME` at image build
- `solana-program-test` -- vendored for 1.18 and 2.2 graphs

There is no internet access. `cargo fetch` and `git clone` will fail.
Anything not already in the crate cache is not available.
""",
)

AUDITOR = Role(
    key="auditor",
    label="Auditor",
    skill="solana-auditor",
    command="/solana-auditor",
    max_turns=200,
    description="Reads the Solana/Anchor programs and reports suspected vulnerabilities.",
    source="https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/solana-vulnerability-scanner",
)

BREAKER = Role(
    key="breaker",
    label="Bug breaker",
    skill="bug-breaker",
    command="/bug-breaker",
    description="Tries to prove each claimed bug with a LiteSVM or cargo test.",
    max_turns=300,
)

registry.register(
    AuditProfile(
        key="solana",
        label="Solana programs",
        roles=(AUDITOR, BREAKER),
        toolchain=SOLANA_TOOLS,
        include_globs=("**/*.rs",),
        exclude_globs=(
            "**/target/**",
            "**/test/**",
            "**/tests/**",
            "**/mocks/**",
            "**/*test*.rs",
            "**/*Test*.rs",
            "**/*Mock*.rs",
        ),
        description="Loss-of-funds vulnerabilities in Solana/Anchor programs, with proofs.",
    )
)
