"""peasy-compress — Zero-dependency archive & compression library.

ZIP, TAR, gzip, bz2, and lzma using only Python stdlib.
"""

from __future__ import annotations

from peasy_compress.engine import (
    ArchiveEntry,
    ArchiveInfo,
    ArchiveInput,
    CompressionLevel,
    bz2_compress,
    bz2_decompress,
    gzip_compress,
    gzip_decompress,
    lzma_compress,
    lzma_decompress,
    tar_create,
    tar_extract,
    tar_list,
    zip_add,
    zip_create,
    zip_extract,
    zip_list,
)

__version__ = "0.1.0"

__all__ = [
    "ArchiveEntry",
    "ArchiveInfo",
    "ArchiveInput",
    "CompressionLevel",
    "bz2_compress",
    "bz2_decompress",
    "gzip_compress",
    "gzip_decompress",
    "lzma_compress",
    "lzma_decompress",
    "tar_create",
    "tar_extract",
    "tar_list",
    "zip_add",
    "zip_create",
    "zip_extract",
    "zip_list",
]
