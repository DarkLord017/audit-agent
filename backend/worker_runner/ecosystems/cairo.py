"""Cairo/Starknet audit profile: cairo-auditor then snforge bug-breaker."""

import os

from backend.worker_runner.profiles import (
    AuditProfile,
    Role,
    Toolchain,
    registry,
)

CAIRO_TOOLS = Toolchain(
    key="cairo",
    image=os.getenv("WORKER_IMAGE_CAIRO", "evmbench/worker-cairo:latest"),
    project_markers=("Scarb.toml",),
    scaffold_dirs=("src", "tests"),
    scaffold_files=(
        (
            "Scarb.toml",
            """\
# Fallback project, written only because the upload shipped no
# Scarb.toml of its own. If it had, that one would be used as-is.
[package]
name = "poc"
version = "0.1.0"
edition = "2024_07"

[dependencies]
starknet = ">=2.12.0"

[dev-dependencies]
snforge_std = "0.63.0"

[[target.starknet-contract]]
sierra = true

[scripts]
test = "snforge test"

[tool.scarb]
allow-prebuilt-plugins = ["snforge_std"]
""",
        ),
        (
            "src/lib.cairo",
            """\
// Fallback package. Copy contracts from ../unzipped/ into src/ (never
// modify unzipped/). Tests go in tests/.
""",
        ),
    ),
    briefing="""\
## Compiling and testing

If the upload has its own `Scarb.toml`, **use it**. It carries their
dependencies, edition, `[[target.starknet-contract]]` and
`allow-prebuilt-plugins`, and nothing else will compile their code.
Work inside their project and add your tests to its `tests/` directory.

There is no network. Pass `--offline` on every scarb command:

```
scarb --offline test
snforge test --exact test_your_poc_name
```

`--offline` stops scarb reaching the registry. `snforge_std` 0.63.0 and
OpenZeppelin Cairo contracts are already in this image's cache / `/opt`.
Both flags and the cache are available without editing their `Scarb.toml`.

If the upload has no `Scarb.toml`, use `{poc}/`, where `snforge_std` is
pinned to the version in the cache. Copy (do not rewrite) the contracts
you need from `{source}/` into `{poc}/src/`.

`/work` is a 1g tmpfs. Cairo `target/` directories grow fast — run one
`--exact` test at a time and do not build examples. If the mount fills,
mark remaining findings UNVERIFIED.

## Tools on PATH

- `scarb` -- Cairo package manager and compiler (2.20.1)
- `snforge`, `sncast` -- Starknet Foundry 0.63.0, for tests
- `universal-sierra-compiler` -- required by snforge, already on PATH

Caracal is not in this image (its last binary targets Cairo 2.5). Do not
try to install it.

There is no internet access. `scarb add`, `git clone` and `cargo install`
will fail. Anything not already installed is not available, so do not try
to fetch dependencies. If their lockfile needs a crate this image did not
vendor, mark the finding **UNVERIFIED**.
""",
)

AUDITOR = Role(
    key="auditor",
    label="Auditor",
    skill="cairo-auditor",
    command="/cairo-auditor",
    description="Reads the Cairo contracts and reports suspected vulnerabilities.",
    source="https://github.com/keep-starknet-strange/starknet-skills/tree/main/cairo-auditor",
)

BREAKER = Role(
    key="breaker",
    label="Bug breaker",
    skill="bug-breaker",
    command="/bug-breaker",
    description="Tries to prove each claimed bug with a Starknet Foundry test.",
    max_turns=300,
)

registry.register(
    AuditProfile(
        key="cairo",
        label="Cairo/Starknet smart contracts",
        roles=(AUDITOR, BREAKER),
        toolchain=CAIRO_TOOLS,
        include_globs=("**/*.cairo",),
        exclude_globs=(
            "**/test/**",
            "**/tests/**",
            "**/mock/**",
            "**/mocks/**",
            "**/example/**",
            "**/examples/**",
            "**/preset/**",
            "**/presets/**",
            "**/fixture/**",
            "**/fixtures/**",
            "**/vendor/**",
            "**/vendors/**",
            "**/*_test.cairo",
            "**/*Test*.cairo",
            "**/*Mock*.cairo",
        ),
        description="Loss-of-funds vulnerabilities in Cairo/Starknet contracts, with proofs.",
    )
)
