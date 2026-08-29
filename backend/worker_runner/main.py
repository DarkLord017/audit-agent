"""Entrypoint inside the worker container.

    /input/upload.zip     their zip, mounted read-only
    /opt/evmbench/skills  our skills, baked into the image
    /work                 tmpfs, the only writable place

Steps: unpack, build the workspace, run the agent, write the report.
Exit code tells the instancer what happened.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from backend.worker_runner.profiles import registry
from backend.worker_runner.runner import AuditFailed, AuditRunner
from backend.worker_runner.safe_extract import UnsafeZip, safe_extract
from backend.worker_runner.workspace import Workspace

log = logging.getLogger("worker")

UPLOAD_PATH = Path(os.getenv("UPLOAD_PATH", "/input/upload.zip"))
WORK_DIR = Path(os.getenv("WORK_DIR", "/work"))
REPORT_PATH = Path(os.getenv("REPORT_PATH", "/work/report.json"))

# Exit codes the instancer reads.
OK = 0
BAD_INPUT = 2      # their zip was hostile or unusable
AUDIT_ERROR = 3    # the agent could not produce a report
CONFIG_ERROR = 4   # we misconfigured the container


async def run() -> int:
    profile_key = os.getenv("PROFILE", "solidity")
    model = os.getenv("MODEL", "claude-opus-5")

    try:
        profile = registry.get(profile_key)
    except KeyError as exc:
        log.error("%s", exc)
        return CONFIG_ERROR

    if not UPLOAD_PATH.is_file():
        log.error("no upload at %s", UPLOAD_PATH)
        return CONFIG_ERROR

    workspace = Workspace(WORK_DIR, profile)
    try:
        workspace.prepare()
    except Exception:
        log.exception("could not build the workspace")
        return CONFIG_ERROR

    # Their zip decides where its files land, so every entry is checked
    # before anything is written. Nothing it contains can reach .claude.
    try:
        count = safe_extract(UPLOAD_PATH, workspace.source_dir)
    except UnsafeZip as exc:
        log.error("refusing the upload: %s", exc)
        return BAD_INPUT
    except Exception:
        log.exception("could not unpack the upload")
        return BAD_INPUT

    in_scope = workspace.in_scope_files()
    log.info("unpacked %d files, %d in scope for %s", count, len(in_scope), profile.key)
    if not in_scope:
        log.error("nothing to audit: no files matched %s", profile.include_globs)
        return BAD_INPUT

    try:
        report = await AuditRunner(workspace, profile, model=model).run()
    except AuditFailed:
        log.exception("the audit did not produce a report")
        return AUDIT_ERROR
    except Exception:
        log.exception("the audit blew up")
        return AUDIT_ERROR

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report.model_dump(mode="json"), indent=2))
    log.info("wrote %s with %d findings", REPORT_PATH, len(report.vulnerabilities))
    return OK


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    sys.exit(asyncio.run(run()))


if __name__ == "__main__":
    main()
