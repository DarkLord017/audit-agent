"""Runs one audit inside the container.

The profile decides the stages. Today that is two:

  1. the auditor reads the code and writes a markdown report
  2. the breaker reads that report and tries to prove each claim with a
     Foundry test, writing its own markdown report

then a short final pass turns the last report into the JSON our Report
model accepts.

The stages are separate agents on purpose. One agent that both finds and
judges its own bugs grades its own homework. The conversion is separate
too: the skills are written for humans reading markdown, and asking the
same run to also produce strict JSON tends to degrade both. Splitting it
keeps the audit prompts untouched and makes the conversion cheap to retry.
"""

import json
import logging
import os
import re

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

from backend.utils.utils import Report
from backend.worker_runner.profiles import AuditProfile, Role
from backend.worker_runner.workspace import Workspace

log = logging.getLogger(__name__)

# Reports are handed between stages in memory, never read back off disk.
# A copy is still written to reports/ for humans, but the code under review
# runs during `forge test` and can overwrite anything in the workspace --
# including that copy. If a stage read its input from a file, an upload
# could blank out the findings against it and score itself clean.
MAX_HANDOFF_CHARS = 200_000

HANDOFF_PROMPT = """\
{command} {source}

Below is the previous stage's report, handed to you directly. Work from it.
Your job is the next stage, not a repeat of the last one.

A copy sits at `{path}` for humans to read. Do not load it from there: the
code under review can rewrite that file. The text below is the copy that
counts.

--- previous report ---
{report}
--- end previous report ---
"""

CONVERT_PROMPT = """\
Below is the final report from a security audit pipeline. Convert it into JSON.

Output ONLY a JSON object in a ```json code block. No commentary.

It must match this JSON Schema exactly:

{schema}

Rules:
- one entry in "vulnerabilities" per finding in the report
- "file" must be the real path relative to the audited source, never
  absolute and never containing "..". Strip any leading "unzipped/".
  Use "unknown" ONLY when the report gives no path at all -- never as a
  shortcut, and never invent a plausible-looking one.
- "start_line"/"end_line" come from the report's `path:line` markers
  (any extension: `file.sol:42`, `lib.rs:17`, `contract.cairo:9`,
  `module.move:3`, `msg.rs:10`, `jetton.fc:8`, `vault.vy:12`,
  `app.teal:4`, ...) when it gives them, else null
- map the report's confidence score to "severity":
  90-100 -> critical, 70-89 -> high, 50-69 -> medium, below 50 -> low
- "verified" is true ONLY where the report shows a proof-of-concept test
  that actually ran and demonstrated the bug. If the report is unclear,
  or the test did not pass, use false. Never guess it true.
- "poc" carries the proof-of-concept test source VERBATIM whenever the
  report shows one, copied character for character from the COMPLETE
  fenced code block under that finding's Proof section, whatever the
  language tag (```solidity, ```rust, ```cairo, ```move, ```go,
  ```python, ```func, ```tact, ```vyper, ```teal, ```typescript, ...).
  Never summarise it, never truncate it, never replace it with a
  description, and never leave it null when the report contains a test.
  A finding marked verified with a null poc is a failure of this step:
  the proof is the whole point of the second stage, and this JSON is the
  only place it is kept.
- "verification" carries a one-line note on how it was proven or why it
  could not be, else null
- keep unverified findings. They are not errors, they are unproven.
- if the report found nothing, return {{"vulnerabilities": []}}

--- report ---
{report}
--- end report ---
"""


class AuditFailed(Exception):
    """The pipeline finished without producing a usable report."""


class AuditRunner:
    def __init__(
        self,
        workspace: Workspace,
        profile: AuditProfile,
        model: str = "claude-opus-5",
        max_turns: int | None = None,
    ):
        self.workspace = workspace
        self.profile = profile
        self.model = model
        self.max_turns = max_turns   # None: each role uses its own budget

    # --- options ------------------------------------------------------

    def options(self, role: Role | None = None, max_turns: int | None = None) -> ClaudeAgentOptions:
        """Options for one stage. role=None is the toolless conversion pass."""
        return ClaudeAgentOptions(
            cwd=str(self.workspace.root),
            # Required, or .claude/skills/ is never discovered.
            setting_sources=["project"] if role else [],
            skills=[role.skill] if role else [],
            allowed_tools=list(role.allowed_tools) if role else [],
            # Safe only because this runs inside a locked-down container
            # with no network route out except the proxy.
            permission_mode="bypassPermissions",
            model=self.model,
            max_turns=max_turns or self.max_turns or (role.max_turns if role else 3),
        )

    # --- passes -------------------------------------------------------

    async def run(self) -> Report:
        markdown = await self.run_roles()
        return await self.to_report(markdown)

    async def run_roles(self) -> str:
        """Run every role in order. Returns the last one's markdown."""
        previous: str | None = None
        markdown = ""

        for role in self.profile.roles:
            log.info("stage %s (%s) starting", role.key, role.skill)
            markdown = await self.run_role(role, previous)
            if not markdown.strip():
                raise AuditFailed(f"the {role.key} stage produced no report")

            # Written for humans only. The next stage gets the string.
            path = self.workspace.report_path(role.key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markdown)
            log.info("stage %s wrote %s (%d chars)", role.key, path, len(markdown))
            previous = markdown

        return markdown

    async def run_role(self, role: Role, previous: str | None) -> str:
        """Run one stage. Later stages are handed the previous report text."""
        if previous is None:
            prompt = f"{role.command} {self.workspace.SOURCE_SUBDIR}"
        else:
            prompt = HANDOFF_PROMPT.format(
                command=role.command,
                source=self.workspace.SOURCE_SUBDIR,
                path=self.workspace.report_path(role.key).relative_to(
                    self.workspace.root
                ),
                report=self._trim(previous),
            )
        return await self._collect(prompt, self.options(role))

    @staticmethod
    def _trim(report: str) -> str:
        """Keep a runaway report from blowing up the next stage's prompt."""
        if len(report) <= MAX_HANDOFF_CHARS:
            return report
        log.warning("report is %d chars, trimming to %d", len(report), MAX_HANDOFF_CHARS)
        return report[:MAX_HANDOFF_CHARS] + "\n\n[report truncated]"

    async def to_report(self, markdown: str) -> Report:
        """Final pass: markdown in, validated Report out."""
        prompt = CONVERT_PROMPT.format(
            schema=json.dumps(Report.model_json_schema(), indent=2),
            report=markdown,
        )
        # No skills, no tools, few turns. This is a formatting job.
        # Was 3. Copying several full test sources through verbatim is
        # more work than a one-shot reformat, and a truncated reply loses
        # exactly the proofs the breaker stage existed to produce.
        raw = await self._collect(prompt, self.options(max_turns=8))
        report = Report.model_validate(self._extract_json(raw))

        # Loud, not fatal. A report that reaches here is still worth
        # keeping, but these two gaps make findings unscoreable and are
        # invisible in the JSON itself.
        if report.missing_proofs:
            log.warning(
                "%d of %d verified findings carry no PoC source: %s",
                len(report.missing_proofs), report.verified_count,
                "; ".join(report.missing_proofs),
            )
        if report.unlocated:
            log.warning(
                "%d findings have no file path: %s",
                len(report.unlocated), "; ".join(report.unlocated),
            )
        return report

    # --- plumbing -----------------------------------------------------

    async def _collect(self, prompt: str, options: ClaudeAgentOptions) -> str:
        """Drive one query to completion and return the final text."""
        text: list[str] = []
        result: str | None = None

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.subtype != "success":
                    raise AuditFailed(f"run ended as {message.subtype}")
                result = message.result

        return result or "\n".join(text)

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Pull the JSON out of a ```json fence, or fall back to the
        first {...} block. Models add prose no matter how firmly you ask
        them not to."""
        fenced = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
        candidate = fenced.group(1) if fenced else text

        try:
            return json.loads(candidate)
        except ValueError:
            pass

        start, end = candidate.find("{"), candidate.rfind("}")
        if start == -1 or end <= start:
            raise AuditFailed("no JSON object found in the conversion output")
        try:
            return json.loads(candidate[start : end + 1])
        except ValueError as exc:
            raise AuditFailed(f"conversion output is not valid JSON: {exc}") from exc


def model_for_job() -> str:
    return os.getenv("MODEL", "claude-opus-5")
