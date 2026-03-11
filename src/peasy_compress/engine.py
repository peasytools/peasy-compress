"""Archive & compression engine — pure functions using only Python stdlib.

Supports ZIP, TAR (plain, gz, bz2, xz), gzip, bz2, and lzma compression.
Zero external dependencies — built entirely on zipfile, tarfile, gzip, bz2, lzma.
"""

from __future__ import annotations

import bz2
import gzip
import io
import lzma
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

ArchiveInput = bytes | Path | str
CompressionLevel = Literal["fastest", "default", "best"]


@dataclass(frozen=True)
class ArchiveEntry:
    """Metadata for a single entry inside an archive."""

    name: str
    size: int
    compressed_size: int
    is_dir: bool


@dataclass(frozen=True)
class ArchiveInfo:
    """Summary of an archive's contents."""

    format: str  # "zip", "tar", "tar.gz", "tar.bz2", "tar.xz"
    entries: list[ArchiveEntry]
    total_size: int
    total_compressed: int
    file_count: int
    dir_count: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_bytes(source: ArchiveInput) -> bytes:
    """Normalize *source* (bytes, Path, or str path) to raw bytes."""
    if isinstance(source, bytes):
        return source
    path = Path(source) if isinstance(source, str) else source
    return path.read_bytes()


def _level_to_int(level: CompressionLevel) -> int:
    """Map a human-readable compression level to an integer (1-9)."""
    mapping: dict[CompressionLevel, int] = {
        "fastest": 1,
        "default": 6,
        "best": 9,
    }
    return mapping[level]


def _tar_format_label(compression: str) -> str:
    """Return a display label for the tar compression variant."""
    if compression == "":
        return "tar"
    return f"tar.{compression}"


def _tar_mode(base: str, compression: str) -> str:
    """Build the tarfile open-mode string (e.g. ``'w:gz'``, ``'r:xz'``)."""
    if compression:
        return f"{base}:{compression}"
    return f"{base}:"


# ---------------------------------------------------------------------------
# ZIP operations
# ---------------------------------------------------------------------------


def zip_create(
    files: dict[str, bytes],
    *,
    level: CompressionLevel = "default",
) -> bytes:
    """Create a ZIP archive in memory from a name-to-content mapping.

    >>> data = zip_create({"hello.txt": b"world"})
    >>> isinstance(data, bytes)
    True
    """
    buf = io.BytesIO()
    comp_level = _level_to_int(level)
    with zipfile.ZipFile(
        buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=comp_level
    ) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def zip_extract(source: ArchiveInput) -> dict[str, bytes]:
    """Extract all files from a ZIP archive, returning name-to-content mapping.

    Directories are skipped — only file entries are returned.

    >>> data = zip_create({"a.txt": b"aaa"})
    >>> zip_extract(data)
    {'a.txt': b'aaa'}
    """
    raw = _read_bytes(source)
    result: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
        for info in zf.infolist():
            if not info.is_dir():
                result[info.filename] = zf.read(info.filename)
    return result


def zip_list(source: ArchiveInput) -> ArchiveInfo:
    """List the contents of a ZIP archive without extracting.

    >>> info = zip_list(zip_create({"f.txt": b"x"}))
    >>> info.file_count
    1
    """
    raw = _read_bytes(source)
    entries: list[ArchiveEntry] = []
    with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
        for info in zf.infolist():
            entries.append(
                ArchiveEntry(
                    name=info.filename,
                    size=info.file_size,
                    compressed_size=info.compress_size,
                    is_dir=info.is_dir(),
                )
            )
    total_size = sum(e.size for e in entries)
    total_compressed = sum(e.compressed_size for e in entries)
    file_count = sum(1 for e in entries if not e.is_dir)
    dir_count = sum(1 for e in entries if e.is_dir)
    return ArchiveInfo(
        format="zip",
        entries=entries,
        total_size=total_size,
        total_compressed=total_compressed,
        file_count=file_count,
        dir_count=dir_count,
    )


def zip_add(source: ArchiveInput, files: dict[str, bytes]) -> bytes:
    """Add files to an existing ZIP archive, returning the updated archive bytes.

    If a filename already exists in the archive it will be overwritten (the old
    entry remains in the underlying data but the new one takes precedence on
    extraction).

    >>> base = zip_create({"a.txt": b"a"})
    >>> updated = zip_add(base, {"b.txt": b"b"})
    >>> sorted(zip_extract(updated).keys())
    ['a.txt', 'b.txt']
    """
    raw = _read_bytes(source)
    buf = io.BytesIO(raw)
    with zipfile.ZipFile(buf, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# TAR operations
# ---------------------------------------------------------------------------


def tar_create(
    files: dict[str, bytes],
    *,
    compression: str = "",
) -> bytes:
    """Create a TAR archive (optionally compressed) from a name-to-content mapping.

    *compression* can be ``""`` (plain), ``"gz"``, ``"bz2"``, or ``"xz"``.

    >>> data = tar_create({"note.txt": b"hello"}, compression="gz")
    >>> isinstance(data, bytes)
    True
    """
    buf = io.BytesIO()
    mode = _tar_mode("w", compression)
    with tarfile.open(fileobj=buf, mode=mode) as tf:  # type: ignore[call-overload]
        for name, content in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def tar_extract(
    source: ArchiveInput,
    *,
    compression: str = "",
) -> dict[str, bytes]:
    """Extract all files from a TAR archive, returning name-to-content mapping.

    *compression* can be ``""`` (plain), ``"gz"``, ``"bz2"``, or ``"xz"``.

    >>> data = tar_create({"a.txt": b"aaa"}, compression="gz")
    >>> tar_extract(data, compression="gz")
    {'a.txt': b'aaa'}
    """
    raw = _read_bytes(source)
    result: dict[str, bytes] = {}
    mode = _tar_mode("r", compression)
    with tarfile.open(fileobj=io.BytesIO(raw), mode=mode) as tf:  # type: ignore[call-overload]
        for member in tf.getmembers():
            if member.isfile():
                f = tf.extractfile(member)
                if f is not None:
                    result[member.name] = f.read()
    return result


def tar_list(
    source: ArchiveInput,
    *,
    compression: str = "",
) -> ArchiveInfo:
    """List the contents of a TAR archive without extracting.

    >>> info = tar_list(tar_create({"f.txt": b"x"}))
    >>> info.file_count
    1
    """
    raw = _read_bytes(source)
    entries: list[ArchiveEntry] = []
    mode = _tar_mode("r", compression)
    fmt = _tar_format_label(compression)
    with tarfile.open(fileobj=io.BytesIO(raw), mode=mode) as tf:  # type: ignore[call-overload]
        for member in tf.getmembers():
            entries.append(
                ArchiveEntry(
                    name=member.name,
                    size=member.size,
                    compressed_size=member.size,  # TAR doesn't track per-entry compression
                    is_dir=member.isdir(),
                )
            )
    total_size = sum(e.size for e in entries)
    file_count = sum(1 for e in entries if not e.is_dir)
    dir_count = sum(1 for e in entries if e.is_dir)
    return ArchiveInfo(
        format=fmt,
        entries=entries,
        total_size=total_size,
        total_compressed=total_size,  # TAR doesn't provide per-entry compressed sizes
        file_count=file_count,
        dir_count=dir_count,
    )


# ---------------------------------------------------------------------------
# Single-file compression: gzip
# ---------------------------------------------------------------------------


def gzip_compress(data: bytes, *, level: int = 9) -> bytes:
    """Compress *data* using gzip.

    >>> compressed = gzip_compress(b"hello world")
    >>> len(compressed) < len(b"hello world" * 100)
    True
    """
    return gzip.compress(data, compresslevel=level)


def gzip_decompress(data: bytes) -> bytes:
    """Decompress gzip-compressed *data*.

    >>> gzip_decompress(gzip_compress(b"roundtrip"))
    b'roundtrip'
    """
    return gzip.decompress(data)


# ---------------------------------------------------------------------------
# Single-file compression: bz2
# ---------------------------------------------------------------------------


def bz2_compress(data: bytes, *, level: int = 9) -> bytes:
    """Compress *data* using bz2.

    >>> compressed = bz2_compress(b"hello world")
    >>> isinstance(compressed, bytes)
    True
    """
    return bz2.compress(data, compresslevel=level)


def bz2_decompress(data: bytes) -> bytes:
    """Decompress bz2-compressed *data*.

    >>> bz2_decompress(bz2_compress(b"roundtrip"))
    b'roundtrip'
    """
    return bz2.decompress(data)


# ---------------------------------------------------------------------------
# Single-file compression: lzma / xz
# ---------------------------------------------------------------------------


def lzma_compress(data: bytes) -> bytes:
    """Compress *data* using lzma (xz format).

    >>> compressed = lzma_compress(b"hello world")
    >>> isinstance(compressed, bytes)
    True
    """
    return lzma.compress(data)


def lzma_decompress(data: bytes) -> bytes:
    """Decompress lzma/xz-compressed *data*.

    >>> lzma_decompress(lzma_compress(b"roundtrip"))
    b'roundtrip'
    """
    return lzma.decompress(data)
