"""Audit profiles.

A profile is one kind of review: solidity today, frontend or solana
tomorrow. Each one names the skill that does the work and the files
that are worth looking at. Adding a new kind of audit means registering
a profile and dropping the skill in skills/ -- no other code changes.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuditProfile:
    key: str                        # what the API and UI call it
    label: str                      # what a human calls it
    skill: str                      # directory name under skills/
    command: str                    # what we send the agent to start it
    include_globs: tuple[str, ...]  # files worth showing the agent
    exclude_globs: tuple[str, ...] = ()
    description: str = ""
    allowed_tools: tuple[str, ...] = (
        "Read", "Grep", "Glob", "Bash", "Write", "Agent", "Skill",
    )
    source: str = ""                # where the skill came from, for updates
    extra: dict = field(default_factory=dict)


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

registry.register(
    AuditProfile(
        key="solidity",
        label="Solidity smart contracts",
        skill="solidity-auditor",
        command="/solidity-auditor",
        include_globs=("**/*.sol",),
        exclude_globs=(
            "**/lib/**", "**/node_modules/**", "**/test/**",
            "**/mocks/**", "**/*.t.sol", "**/*Test*.sol", "**/*Mock*.sol",
        ),
        description="Loss-of-funds vulnerabilities in EVM contracts.",
        source="https://github.com/pashov/skills/tree/main/solidity-auditor",
    )
)

# --- to add another kind of audit -------------------------------------
#
# 1. put the skill in  skills/<skill-name>/SKILL.md
# 2. register it here
# 3. add its key to ALLOWED_PROFILES in the API
#
# registry.register(
#     AuditProfile(
#         key="frontend",
#         label="Frontend / web",
#         skill="frontend-auditor",
#         command="/frontend-auditor",
#         include_globs=("**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"),
#         exclude_globs=("**/node_modules/**", "**/dist/**"),
#         description="XSS, CSRF, unsafe rendering, secrets in bundles.",
#     )
# )
