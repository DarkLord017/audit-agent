"""Algorand audit profile: algorand-auditor then pytest/Tealer bug-breaker."""

import os

from backend.worker_runner.profiles import (
    AuditProfile,
    Role,
    Toolchain,
    registry,
)

ALGORAND_TOOLS = Toolchain(
    key="algorand",
    image=os.getenv("WORKER_IMAGE_ALGORAND", "evmbench/worker-algorand:latest"),
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
\"\"\"PyTeal compile + Tealer read programs from unzipped/. Never modify unzipped/.\"\"\"
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
It carries their fixtures, pythonpath and plugin settings. Work inside
their project and add your tests next to theirs.

There is no network and no algod. PyTeal, `algosdk`, Tealer and pytest
are already in this image. Compile PyTeal to TEAL in-process, write the
`.teal` under `{poc}/` (never into `{source}/`), then run Tealer and
pytest:

```
python -c "from pyteal import compileTeal, Mode; ..."
tealer detect --contracts poc/approval.teal 2>&1
pytest tests/test_foo.py -vv
```

If the upload has no pytest project, use `{poc}/`, where `conftest.py`
exposes `UNZIPPED` (and an `unzipped` fixture) pointing at `{source}/`.

`/work` is a 1g tmpfs. Keep generated TEAL and tests small. Do not try
to run `algod`, `goal`, or a sandbox — they are not in this image.

In-scope programs are `*.teal` and PyTeal `*.py` (files that import
`pyteal` or `beaker`). Client scripts that only import `algosdk` are
not programs; do not treat them as the thing under test.

## Tools on PATH

- `python` -- PyTeal (`compileTeal`) and py-algorand-sdk
- `pytest` -- test runner for proofs
- `tealer` -- static analysis on compiled TEAL (`tealer detect --contracts FILE`)

There is no internet access. `pip install` and `git clone` will fail.
Anything not already installed is not available, so do not try to fetch
dependencies. Beaker is not in this image; if the upload needs it, mark
the finding UNVERIFIED.
""",
)

AUDITOR = Role(
    key="auditor",
    label="Auditor",
    skill="algorand-auditor",
    command="/algorand-auditor",
    description="Reads TEAL/PyTeal programs and reports suspected vulnerabilities.",
    source="https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts/skills/algorand-vulnerability-scanner",
)

BREAKER = Role(
    key="breaker",
    label="Bug breaker",
    skill="bug-breaker",
    command="/bug-breaker",
    description="Tries to prove each claimed bug with pytest and Tealer.",
    max_turns=300,
)

registry.register(
    AuditProfile(
        key="algorand",
        label="Algorand TEAL/PyTeal",
        roles=(AUDITOR, BREAKER),
        toolchain=ALGORAND_TOOLS,
        include_globs=("**/*.teal", "**/*.py"),
        exclude_globs=(
            "**/test/**",
            "**/tests/**",
            "**/mocks/**",
            "**/__pycache__/**",
            "**/.venv/**",
            "**/venv/**",
            "**/*_test.py",
            "**/test_*.py",
        ),
        description="Loss-of-funds vulnerabilities in Algorand programs, with proofs.",
    )
)
