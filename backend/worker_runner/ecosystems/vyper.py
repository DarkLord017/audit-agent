"""Vyper audit profile: vyper-auditor then titanoboa bug-breaker."""

import os

from backend.worker_runner.profiles import (
    AuditProfile,
    Role,
    Toolchain,
    registry,
)

VYPER_TOOLS = Toolchain(
    key="vyper",
    image=os.getenv("WORKER_IMAGE_VYPER", "evmbench/worker-vyper:latest"),
    project_markers=("pytest.ini", "pyproject.toml"),
    scaffold_dirs=("tests",),
    scaffold_files=(
        (
            "pytest.ini",
            """\
# Fallback project, written only because the upload shipped no pytest.ini
# or pyproject.toml of its own. If it had, that one would be used as-is.
[pytest]
testpaths = tests
pythonpath = .
""",
        ),
        (
            "conftest.py",
            """\
\"\"\"Titanoboa loads .vy files from unzipped/. Never modify unzipped/.\"\"\"
from pathlib import Path

import pytest

UNZIPPED = Path(__file__).resolve().parents[1] / "unzipped"


@pytest.fixture
def unzipped() -> Path:
    return UNZIPPED
""",
        ),
    ),
    briefing="""\
## Compiling and testing

If the upload has its own `pytest.ini` or `pyproject.toml`, **use it**.
It carries their fixtures, pythonpath and plugin settings, and nothing
else will load their contracts the way they expect. Work inside their
project and add your tests next to theirs.

There is no network. Titanoboa and `vyper` are already in this image.
Run tests in-process from the project directory:

```
pytest tests/test_foo.py -vv
```

If the upload has no pytest project, use `{poc}/`, where `conftest.py`
exposes `UNZIPPED` (and an `unzipped` fixture) pointing at `{source}/`.
Load contracts with `boa.load(str(UNZIPPED / "Whatever.vy"))`.

`/work` is a 1g tmpfs. Titanoboa is an in-process interpreter — keep
PoCs small and do not try to fork a live chain (there is no RPC).

## Tools on PATH

- `vyper` -- the Vyper compiler
- `pytest` -- test runner (Titanoboa's plugin isolates EVM state per test)
- `slither` -- static analysis; it understands `.vy` files
- `python` -- Titanoboa is `import boa`

There is no internet access. `pip install` and `git clone` will fail.
Anything not already installed is not available, so do not try to fetch
dependencies.
""",
)

AUDITOR = Role(
    key="auditor",
    label="Auditor",
    skill="vyper-auditor",
    command="/vyper-auditor",
    description="Reads the Vyper contracts and reports suspected vulnerabilities.",
    source="https://github.com/pashov/skills/tree/main/solidity-auditor",
)

BREAKER = Role(
    key="breaker",
    label="Bug breaker",
    skill="bug-breaker",
    command="/bug-breaker",
    description="Tries to prove each claimed bug with a Titanoboa pytest.",
    max_turns=300,
)

registry.register(
    AuditProfile(
        key="vyper",
        label="Vyper smart contracts",
        roles=(AUDITOR, BREAKER),
        toolchain=VYPER_TOOLS,
        include_globs=("**/*.vy",),
        exclude_globs=(
            "**/test/**",
            "**/tests/**",
            "**/mocks/**",
            "**/*Test*.vy",
            "**/*Mock*.vy",
            "**/test_*.vy",
        ),
        description="Loss-of-funds vulnerabilities in Vyper contracts, with proofs.",
    )
)
