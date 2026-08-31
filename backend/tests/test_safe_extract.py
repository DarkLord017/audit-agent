"""Zip-slip / symlink / size tests for worker_runner.safe_extract."""

import io
import stat
import zipfile
from pathlib import Path

import pytest

from backend.worker_runner.safe_extract import UnsafeZip, _copy_capped, safe_extract


def _write_zip(path: Path, entries: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return path


def test_extracts_plain_file(tmp_path: Path) -> None:
    zpath = _write_zip(tmp_path / "ok.zip", {"hello.txt": b"hi"})
    dest = tmp_path / "out"
    assert safe_extract(zpath, dest) == 1
    assert (dest / "hello.txt").read_bytes() == b"hi"


def test_zip_slip_dotdot_is_rejected(tmp_path: Path) -> None:
    zpath = _write_zip(tmp_path / "slip.zip", {"../pwn.txt": b"escaped"})
    dest = tmp_path / "out"
    with pytest.raises(UnsafeZip, match="escapes destination"):
        safe_extract(zpath, dest)
    assert not (tmp_path / "pwn.txt").exists()
    assert not (dest / "pwn.txt").exists()


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    zpath = _write_zip(tmp_path / "abs.zip", {"/tmp/evil.txt": b"nope"})
    dest = tmp_path / "out"
    with pytest.raises(UnsafeZip, match="absolute path"):
        safe_extract(zpath, dest)
    assert not (dest / "tmp" / "evil.txt").exists()


def test_symlink_is_rejected(tmp_path: Path) -> None:
    zpath = tmp_path / "link.zip"
    info = zipfile.ZipInfo("link")
    info.create_system = 3  # Unix
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr(info, "/etc/passwd")

    dest = tmp_path / "out"
    with pytest.raises(UnsafeZip, match="symlink"):
        safe_extract(zpath, dest)
    assert not (dest / "link").exists()


def test_oversize_file_is_rejected(tmp_path: Path) -> None:
    zpath = _write_zip(tmp_path / "big.zip", {"blob.bin": b"x" * 200})
    dest = tmp_path / "out"
    with pytest.raises(UnsafeZip, match="file too large"):
        safe_extract(zpath, dest, max_file_bytes=100, max_total_bytes=10_000)
    assert not (dest / "blob.bin").exists()


def test_copy_capped_uses_actual_bytes_not_headers() -> None:
    src = io.BytesIO(b"x" * 250)
    out = io.BytesIO()
    with pytest.raises(UnsafeZip, match="file too large"):
        _copy_capped(
            src,
            out,
            name="blob.bin",
            max_file_bytes=100,
            max_total_bytes=10_000,
            running_total=0,
        )
    assert out.tell() == 0


def test_copy_capped_running_total() -> None:
    src = io.BytesIO(b"x" * 80)
    out = io.BytesIO()
    with pytest.raises(UnsafeZip, match="uncompressed size too large"):
        _copy_capped(
            src,
            out,
            name="blob.bin",
            max_file_bytes=1_000,
            max_total_bytes=100,
            running_total=50,
        )
    assert out.tell() == 0


def test_lying_zipinfo_file_size_is_caught(tmp_path: Path, monkeypatch) -> None:
    """Pass 1 trusts ZipInfo.file_size; pass 2 must still cap actual bytes.

    zipfile.ZipExtFile stops at the header size, so a header lie is
    simulated by handing extract a stream longer than ZipInfo.file_size.
    """
    zpath = _write_zip(tmp_path / "lie.zip", {"blob.bin": b"x"})
    dest = tmp_path / "out"
    orig_open = zipfile.ZipFile.open

    def fake_open(self, info, mode="r", pwd=None):
        if getattr(info, "filename", None) == "blob.bin":
            return io.BytesIO(b"x" * 500)
        return orig_open(self, info, mode, pwd=pwd)

    monkeypatch.setattr(zipfile.ZipFile, "open", fake_open)

    with pytest.raises(UnsafeZip, match="file too large"):
        safe_extract(zpath, dest, max_file_bytes=100, max_total_bytes=10_000)
    assert not (dest / "blob.bin").exists()
