"""Audit profiles and the roles inside them.

A profile is one kind of review: solidity here, other ecosystems in
ecosystems/. Each profile is a pipeline of roles that run in order,
handing their report to the next one.

Today that is two roles:

    auditor  reads the code and claims bugs
    breaker  tries to prove those claims with a toolchain-specific PoC

Splitting them is the point. An agent that both finds and judges its own
bugs grades its own homework; a second role that has to produce a
passing test cannot wave a claim through.

Adding a new kind of audit means dropping a module in ecosystems/ that
registers a profile, plus skills under skills/<toolchain.key>/.
"""

import importlib
import os
from dataclasses import dataclass, field
from pathlib import Path

# Tools every role needs. Agent is here because skills that fan out to
# specialist subagents cannot work without it.
DEFAULT_TOOLS: tuple[str, ...] = (
    "Read", "Grep", "Glob", "Bash", "Write", "Agent", "Skill",
)


@dataclass(frozen=True)
class Toolchain:
    """Everything about a profile that changes with the ecosystem.

    The generic worker code knows none of this. Solidity means Foundry
    and Slither; Solana would mean cargo and Anchor. Rather than teach
    workspace.py about either, both are described here as data.

    Adding an ecosystem is a Toolchain, a Dockerfile and the skills. No
    changes to workspace.py, runner.py, docker_backend.py or consumer.py.

    Strings may use {source}, {poc} and {reports} for the workspace dirs.
    """

    key: str
    image: str                                      # worker image with these tools
    briefing: str                                   # markdown, injected into AGENTS.md
    # Files that mean "they brought their own project, leave it alone".
    project_markers: tuple[str, ...] = ()
    # Used only when no marker is found: a bare project to work in.
    scaffold_dirs: tuple[str, ...] = ()
    scaffold_files: tuple[tuple[str, str], ...] = ()
    scaffold_links: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Role:
    """One stage of the pipeline."""

    key: str                        # short name, also the report filename
    label: str                      # what a human calls it
    skill: str                      # directory name under skills/<toolchain.key>/
    command: str                    # what we send the agent to start it
    allowed_tools: tuple[str, ...] = DEFAULT_TOOLS
    max_turns: int = 200
    source: str = ""                # where the skill came from, for updates
    description: str = ""


@dataclass(frozen=True)
class AuditProfile:
    key: str                        # what the API and UI call it
    label: str                      # what a human calls it
    roles: tuple[Role, ...]         # run in order, first to last
    toolchain: Toolchain            # image, tools and how to build
    include_globs: tuple[str, ...]  # files worth showing the agent
    exclude_globs: tuple[str, ...] = ()
    description: str = ""
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.roles:
            raise ValueError(f"profile {self.key} has no roles")
        keys = [r.key for r in self.roles]
        if len(keys) != len(set(keys)):
            raise ValueError(f"profile {self.key} has duplicate role keys: {keys}")

    @property
    def skills(self) -> tuple[str, ...]:
        """Every skill this profile needs installed in the workspace."""
        return tuple(dict.fromkeys(r.skill for r in self.roles))


class ProfileRegistry:
    """Holds every audit profile the system knows about."""

    def __init__(self):
        self._profiles: dict[str, AuditProfile] = {}

    def register(self, profile: AuditProfile) -> AuditProfile:
        if profile.key in self._profiles:
            raise ValueError(f"profile already registered: {profile.key}")
        self._profiles[profile.key] = profile
        return profile

    def get(self, key: str) -> AuditProfile:
        try:
            return self._profiles[key]
        except KeyError:
            raise KeyError(f"unknown profile: {key}") from None

    def keys(self) -> list[str]:
        return sorted(self._profiles)

    def all(self) -> list[AuditProfile]:
        return [self._profiles[k] for k in self.keys()]


registry = ProfileRegistry()

# --- solidity ---------------------------------------------------------
#
# Paths baked into the solidity worker image. They live here, next to the
# toolchain that needs them, rather than as constants in the generic code.

FORGE_STD = os.getenv("FORGE_STD_DIR", "/opt/forge-std")
SOLC_BIN = os.getenv(
    "SOLC_BIN", "/opt/solc/.solc-select/artifacts/solc-0.8.28/solc-0.8.28"
)

SOLIDITY_TOOLS = Toolchain(
    key="solidity",
    image=os.getenv("WORKER_IMAGE_SOLIDITY", "evmbench/worker-solidity:latest"),
    project_markers=("foundry.toml",),
    scaffold_dirs=("src", "test", "lib"),
    scaffold_links=(("lib/forge-std", FORGE_STD),),
    scaffold_files=((
        "foundry.toml",
        f"""\
# Fallback project, written only because the upload shipped no
# foundry.toml of its own. If it had, that one would be used as-is.
[profile.default]
src = "src"
test = "test"
out = "out"
libs = ["lib"]

allow_paths = ["../{{source}}"]
remappings = [
    "forge-std/={FORGE_STD}/src/",
    "{{source}}/=../{{source}}/",
]
""",
    ),),
    briefing=f"""\
## Compiling and testing

If the upload has its own `foundry.toml`, **use it**. It carries their
remappings, `lib/`, solc version and optimizer settings, and nothing else
will compile their code. Work inside their project and add your tests to
its test directory.

There is no network, so two flags are needed on every forge command:

```
forge test --offline --use {SOLC_BIN} -vv
```

`--offline` stops forge reaching for a compiler list, and `--use` points it
at the solc already in this image. Both are command-line flags, so they
override the project config without editing a single file of theirs.

If the upload has no `foundry.toml`, use `{{poc}}/`, where `forge-std` is
linked and the contracts are reachable as `{{source}}/Whatever.sol`.

## Tools on PATH

- `forge`, `cast`, `anvil` -- Foundry, for compiling and running tests
- `slither` -- static analysis, a fast second opinion
- `solc` -- the Solidity compiler (0.8.28)

There is no internet access. `forge install` and `git clone` will fail.
Anything not already installed is not available, so do not try to fetch
dependencies.
""",
)

AUDITOR = Role(
    key="auditor",
    label="Auditor",
    skill="solidity-auditor",
    command="/solidity-auditor",
    description="Reads the contracts and reports suspected vulnerabilities.",
    source="https://github.com/pashov/skills/tree/main/solidity-auditor",
)

BREAKER = Role(
    key="breaker",
    label="Bug breaker",
    skill="bug-breaker",
    command="/bug-breaker",
    description="Tries to prove each claimed bug with a Foundry test.",
    # Writing and running tests is slower than reading, but it is bounded
    # work: one test per finding, not open-ended exploration.
    max_turns=300,
)

registry.register(
    AuditProfile(
        key="solidity",
        label="Solidity smart contracts",
        roles=(AUDITOR, BREAKER),
        toolchain=SOLIDITY_TOOLS,
        include_globs=("**/*.sol",),
        exclude_globs=(
            "**/lib/**", "**/node_modules/**", "**/test/**",
            "**/mocks/**", "**/*.t.sol", "**/*Test*.sol", "**/*Mock*.sol",
        ),
        description="Loss-of-funds vulnerabilities in EVM contracts, with proofs.",
    )
)

# Chain-specific Solidity profiles share the Foundry/Slither image and
# the breaker skill. Toolchain.key stays "solidity" so skills still load
# from skills/solidity/<skill>/. Add more as <chain>-auditor + a profile.

OPTIMISM_AUDITOR = Role(
    key="auditor",
    label="Optimism auditor",
    skill="optimism-auditor",
    command="/optimism-auditor",
    description=(
        "Reads the contracts as they run on OP Stack: generic EVM bugs "
        "plus L2 block time, fees, predeploys, aliasing and messenger."
    ),
)

OPTIMISM_BRIEFING = """\

## This job is an OP Stack audit

The first stage is `optimism-auditor`, not the generic Solidity auditor.
Assume OP Mainnet / OP Stack execution: ~2s L2 blocks, `block.number` is
L2, L1 origin lives on `L1Block` at `0x4200…0015`, users pay an L1 data
fee that `tx.gasprice` does not include, and L1 contract deposits arrive
from an aliased `msg.sender`.

Anvil is not OP. For PoCs, mock predeploys at the canonical `0x4200…`
addresses rather than forking (there is no RPC). Deposit transaction type
`0x7e` does not exist here — replay the L2-side call the messenger or
aliased sender would make.
"""

OPTIMISM_TOOLS = Toolchain(
    key="solidity",
    image=SOLIDITY_TOOLS.image,
    briefing=SOLIDITY_TOOLS.briefing + OPTIMISM_BRIEFING,
    project_markers=SOLIDITY_TOOLS.project_markers,
    scaffold_dirs=SOLIDITY_TOOLS.scaffold_dirs,
    scaffold_files=SOLIDITY_TOOLS.scaffold_files,
    scaffold_links=SOLIDITY_TOOLS.scaffold_links,
)

registry.register(
    AuditProfile(
        key="solidity-optimism",
        label="Solidity on Optimism / OP Stack",
        roles=(OPTIMISM_AUDITOR, BREAKER),
        toolchain=OPTIMISM_TOOLS,
        include_globs=("**/*.sol",),
        exclude_globs=(
            "**/lib/**", "**/node_modules/**", "**/test/**",
            "**/mocks/**", "**/*.t.sol", "**/*Test*.sol", "**/*Mock*.sol",
        ),
        description=(
            "Loss-of-funds in Solidity as executed on OP Mainnet and other "
            "OP Stack L2s, with Foundry proofs."
        ),
    )
)

# --- other ecosystems -------------------------------------------------
#
# Language agents drop backend/worker_runner/ecosystems/<lang>.py, which
# calls registry.register(...). Skills live at
# skills/<toolchain.key>/<skill>/. Do not add those profiles here.

_ECOSYSTEMS = Path(__file__).resolve().parent / "ecosystems"
if _ECOSYSTEMS.is_dir():
    for _mod in sorted(_ECOSYSTEMS.glob("*.py")):
        if _mod.stem.startswith("_"):
            continue
        importlib.import_module(f"backend.worker_runner.ecosystems.{_mod.stem}")
