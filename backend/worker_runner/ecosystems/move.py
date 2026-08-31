"""Move / Sui audit profile: move-auditor then sui move test bug-breaker."""

import os

from backend.worker_runner.profiles import (
    AuditProfile,
    Role,
    Toolchain,
    registry,
)

SUI_FRAMEWORK = os.getenv(
    "SUI_FRAMEWORK_DIR", "/opt/sui-framework/packages/sui-framework"
)

MOVE_TOOLS = Toolchain(
    key="move",
    image=os.getenv("WORKER_IMAGE_MOVE", "evmbench/worker-move:latest"),
    project_markers=("Move.toml",),
    scaffold_dirs=("sources", "tests"),
    scaffold_files=((
        "Move.toml",
        f"""\
# Fallback package, written only because the upload shipped no
# Move.toml of its own. If it had, that one would be used as-is
# (from a copy under poc/ -- never by editing unzipped/).
[package]
name = "poc"
edition = "2024.beta"

[dependencies]
Sui = {{ local = "{SUI_FRAMEWORK}" }}

[addresses]
poc = "0x0"
""",
    ),),
    briefing=f"""\
## Compiling and testing

If the upload has its own `Move.toml`, **use it** — from a copy. It
carries their named addresses, edition and dependency pins, and nothing
else will compile their modules. Copy the package tree to `{{poc}}/` and
add tests there. **Never modify `{{source}}/`.**

There is no network, so every `sui` command needs:

```
sui move test --skip-fetch-latest-git-deps --filter test_foo
```

`--skip-fetch-latest-git-deps` stops the package manager reaching GitHub.
If the copy still pins `Sui` via git, retarget **the copy's** Move.toml
at the framework already in this image:

```
{SUI_FRAMEWORK}
```

If the upload has no `Move.toml`, use `{{poc}}/`, where that path is
already set and you copy in-scope `.move` files into `{{poc}}/sources/`.

Detect Aptos vs Sui from `Move.toml` (`AptosFramework` / `aptos-labs`
vs `Sui` / `MystenLabs/sui`). This image is Sui. Aptos packages cannot
be proved here — mark them UNVERIFIED.

`/work` is a 1g tmpfs. Run one `--filter` test at a time; a full
`build/` of a large package will fill the disk.

## Tools on PATH

- `sui` -- Sui CLI, for `sui move test` / `sui move build`

There is no internet access. `git clone` and framework fetches will fail.
Anything not already installed is not available, so do not try to fetch
dependencies. There is no Aptos CLI.
""",
)

AUDITOR = Role(
    key="auditor",
    label="Auditor",
    skill="move-auditor",
    command="/move-auditor",
    description="Reads the Move packages and reports suspected vulnerabilities.",
    source="https://github.com/sanbir/move-auditor-skills/tree/main/move-auditor",
)

BREAKER = Role(
    key="breaker",
    label="Bug breaker",
    skill="bug-breaker",
    command="/bug-breaker",
    description="Tries to prove each claimed bug with a sui move test.",
    max_turns=300,
)

registry.register(
    AuditProfile(
        key="move",
        label="Move (Sui) smart contracts",
        roles=(AUDITOR, BREAKER),
        toolchain=MOVE_TOOLS,
        include_globs=("**/*.move",),
        exclude_globs=(
            "**/tests/**",
            "**/test/**",
            "**/build/**",
            "**/examples/**",
            "**/node_modules/**",
            "**/*_test.move",
            "**/*_tests.move",
            "**/test_*.move",
        ),
        description="Loss-of-funds vulnerabilities in Sui Move packages, with proofs.",
    )
)
