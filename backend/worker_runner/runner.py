"""Runs one audit inside the container.

Two passes, on purpose:

  1. the skill does the audit and writes its own markdown report
  2. a short second pass turns that report into the JSON our Report
     model accepts

The skills we use are written for humans reading markdown. Asking the
same run to also produce strict JSON tends to degrade both. Splitting it
keeps the audit prompt untouched and makes the conversion cheap to retry.
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
from backend.worker_runner.profiles import AuditProfile
from backend.worker_runner.workspace import Workspace

log = logging.getLogger(__name__)

CONVERT_PROMPT = """\
Below is a security audit report you just produced. Convert it into JSON.

Output ONLY a JSON object in a ```json code block. No commentary.

It must match this JSON Schema exactly:

{schema}

Rules:
- one entry in "vulnerabilities" per finding in the report
- "file" must be a path relative to the audited source, never absolute
  and never containing ".."
- map the report's confidence score to "severity":
  90-100 -> critical, 70-89 -> high, 50-69 -> medium, below 50 -> low
- if the report found nothing, return {{"vulnerabilities": []}}

--- report ---
{report}
--- end report ---
"""


class AuditFailed(Exception):
    """The agent finished without producing a usable report."""


class AuditRunner:
    def __init__(
        self,
        workspace: Workspace,
        profile: AuditProfile,
        model: str = "claude-opus-5",
        max_turns: int = 200,
    ):
        self.workspace = workspace
        self.profile = profile
        self.model = model
        self.max_turns = max_turns

    # --- options ------------------------------------------------------

    def options(self, max_turns: int | None = None, skills: bool = True) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            cwd=str(self.workspace.root),
            # Required, or .claude/skills/ is never discovered.
            setting_sources=["project"] if skills else [],
            skills=[self.profile.skill] if skills else [],
            allowed_tools=list(self.profile.allowed_tools),
            # Safe only because this runs inside a locked-down container
            # with no network route out except the proxy.
            permission_mode="bypassPermissions",
            model=self.model,
            max_turns=max_turns or self.max_turns,
        )

    # --- passes -------------------------------------------------------

    async def run(self) -> Report:
        markdown = await self.run_audit()
        if not markdown.strip():
            raise AuditFailed("the agent produced no report")
        return await self.to_report(markdown)

    async def run_audit(self) -> str:
        """Pass 1: let the skill do its thing. Returns its markdown."""
        prompt = f"{self.profile.command} {self.workspace.SOURCE_SUBDIR}"
        return await self._collect(prompt, self.options())

    async def to_report(self, markdown: str) -> Report:
        """Pass 2: markdown in, validated Report out."""
        prompt = CONVERT_PROMPT.format(
            schema=json.dumps(Report.model_json_schema(), indent=2),
            report=markdown,
        )
        # No skills, no tools, few turns. This is a formatting job.
        raw = await self._collect(prompt, self.options(max_turns=3, skills=False))
        return Report.model_validate(self._extract_json(raw))

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
