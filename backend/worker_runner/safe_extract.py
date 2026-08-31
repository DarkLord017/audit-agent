"""Unpack an untrusted zip.

A zip decides where its own files land, and an attacker wrote the zip.
So every entry is checked before anything is written, and the whole
archive is refused if any single entry misbehaves.
"""

import logging
import stat
import zipfile
from pathlib import Path

log = logging.getLogger(__name__)

MAX_FILES = 5_000
MAX_TOTAL_BYTES = 200 * 1024 * 1024   # 200 MB uncompressed
MAX_FILE_BYTES = 10 * 1024 * 1024     # 10 MB per file
_CHUNK = 64 * 1024

SKIP_DIRS = {".claude", ".git", ".github", ".cursor", "node_modules"}
SKIP_FILES = {
    "CLAUDE.md", "CLAUDE.local.md",     # Claude Code
    "AGENTS.md",                        # Codex and others
    ".mcp.json",                        # MCP servers
    ".cursorrules", ".windsurfrules",   # other agent runtimes
    ".aider.conf.yml",
}


class UnsafeZip(Exception):
    """The zip tried to do something it is not allowed to do."""


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    return stat.S_ISLNK(info.external_attr >> 16)


def _should_skip(name: str) -> bool:
    path = Path(name)
    if SKIP_DIRS.intersection(path.parts):
        return True
    return path.name in SKIP_FILES


def _copy_capped(
    src,
    out,
    *,
    name: str,
    max_file_bytes: int,
    max_total_bytes: int,
    running_total: int,
) -> int:
    """Stream src → out. Return the new running total of bytes written.

    Caps are enforced on bytes actually copied, not ZipInfo.file_size.
    The overflowing chunk is not written.
    """
    file_bytes = 0
    while True:
        chunk = src.read(_CHUNK)
        if not chunk:
            break
        n = len(chunk)
        file_bytes += n
        if file_bytes > max_file_bytes:
            raise UnsafeZip(f"file too large: {name}")
        running_total += n
        if running_total > max_total_bytes:
            raise UnsafeZip(f"uncompressed size too large: {running_total} bytes")
        out.write(chunk)
    return running_total


def safe_extract(
    zip_path: Path,
    dest: Path,
    *,
    max_files: int = MAX_FILES,
    max_file_bytes: int = MAX_FILE_BYTES,
    max_total_bytes: int = MAX_TOTAL_BYTES,
) -> int:
    """Extract zip_path into dest. Returns the number of files written.

    Raises UnsafeZip if the archive is hostile.
    """
    dest = Path(dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()

        # --- pass 1: check everything, write nothing ---
        #
        # Two passes, because checking and writing in one loop leaves a
        # half-extracted hostile archive on disk when you abort.
        if len(infos) > max_files:
            raise UnsafeZip(f"too many entries: {len(infos)}")

        total = sum(i.file_size for i in infos)
        if total > max_total_bytes:
            raise UnsafeZip(f"uncompressed size too large: {total} bytes")

        for info in infos:
            name = info.filename

            if info.file_size > max_file_bytes:
                raise UnsafeZip(f"file too large: {name}")

            # A symlink pointing at / lets later entries write through it.
            if _is_symlink(info):
                raise UnsafeZip(f"symlink not allowed: {name}")

            # Absolute paths ignore dest entirely.
            if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
                raise UnsafeZip(f"absolute path not allowed: {name}")

            # resolve() flattens every "..". If the real landing spot is
            # outside dest, the entry is trying to escape.
            target = (dest / name).resolve()
            if target != dest and not target.is_relative_to(dest):
                raise UnsafeZip(f"entry escapes destination: {name}")

        # --- pass 2: safe, so write ---
        written = skipped = 0
        running_total = 0
        for info in infos:
            if info.is_dir():
                continue
            if _should_skip(info.filename):
                skipped += 1
                continue

            target = (dest / info.filename).resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with zf.open(info) as src, target.open("wb") as out:
                    running_total = _copy_capped(
                        src,
                        out,
                        name=info.filename,
                        max_file_bytes=max_file_bytes,
                        max_total_bytes=max_total_bytes,
                        running_total=running_total,
                    )
            except UnsafeZip:
                target.unlink(missing_ok=True)
                raise
            written += 1

    log.info("extracted %d files into %s (%d skipped)", written, dest, skipped)
    return written
