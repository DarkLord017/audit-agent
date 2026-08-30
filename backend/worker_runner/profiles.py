"""Audit profiles and the roles inside them.

A profile is one kind of review: solidity today, others later. Each
profile is a pipeline of roles that run in order, handing their report
to the next one.

Today that is two roles:

    auditor  reads the code and claims bugs
    breaker  tries to prove those claims with Foundry and Slither

Splitting them is the point. An agent that both finds and judges its own
bugs grades its own homework; a second role that has to produce a
passing test cannot wave a claim through.

Adding a new kind of audit means registering a profile and dropping its
skills in skills/ -- no other code changes.
"""

import os
from dataclasses import dataclass, field

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
    skill: str                      # directory name under skills/
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

# --- to add another kind of audit -------------------------------------
#
# 1. put each role's skill in  skills/<skill-name>/SKILL.md
# 2. describe the roles and register the profile here
#
# The pipeline shape is not fixed at two. A profile can be a single role
# if there is nothing to verify, or three if a triage step earns its
# keep.
