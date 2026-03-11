"""Comprehensive tests for peasy_compress.engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from peasy_compress.engine import (
    ArchiveInfo,
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

# ---------------------------------------------------------------------------
# ZIP tests
# ---------------------------------------------------------------------------


class TestZipCreate:
    def test_creates_valid_zip(self) -> None:
        data = zip_create({"hello.txt": b"world"})
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_empty_archive(self) -> None:
        data = zip_create({})
        assert isinstance(data, bytes)
        info = zip_list(data)
        assert info.file_count == 0

    def test_multiple_files(self) -> None:
        files = {
            "a.txt": b"alpha",
            "b.txt": b"bravo",
            "c.txt": b"charlie",
        }
        data = zip_create(files)
        info = zip_list(data)
        assert info.file_count == 3

    def test_compression_levels(self) -> None:
        content = b"x" * 10_000
        fastest = zip_create({"f.txt": content}, level="fastest")
        best = zip_create({"f.txt": content}, level="best")
        # Both should be valid ZIPs
        assert zip_extract(fastest) == {"f.txt": content}
        assert zip_extract(best) == {"f.txt": content}
        # Best compression should be smaller or equal
        assert len(best) <= len(fastest)

    def test_binary_content(self) -> None:
        binary = bytes(range(256))
        data = zip_create({"binary.bin": binary})
        extracted = zip_extract(data)
        assert extracted["binary.bin"] == binary

    def test_nested_paths(self) -> None:
        files = {
            "dir/sub/file.txt": b"nested",
            "root.txt": b"root",
        }
        data = zip_create(files)
        extracted = zip_extract(data)
        assert extracted["dir/sub/file.txt"] == b"nested"
        assert extracted["root.txt"] == b"root"


class TestZipExtract:
    def test_roundtrip(self) -> None:
        files = {"a.txt": b"aaa", "b.txt": b"bbb"}
        data = zip_create(files)
        result = zip_extract(data)
        assert result == files

    def test_from_path(self, tmp_path: Path) -> None:
        files = {"test.txt": b"path-test"}
        archive_path = tmp_path / "test.zip"
        archive_path.write_bytes(zip_create(files))
        result = zip_extract(archive_path)
        assert result == files

    def test_from_string_path(self, tmp_path: Path) -> None:
        files = {"test.txt": b"string-path"}
        archive_path = tmp_path / "test.zip"
        archive_path.write_bytes(zip_create(files))
        result = zip_extract(str(archive_path))
        assert result == files

    def test_empty_file_content(self) -> None:
        files = {"empty.txt": b""}
        data = zip_create(files)
        result = zip_extract(data)
        assert result == files


class TestZipList:
    def test_file_count(self) -> None:
        files = {"a.txt": b"a", "b.txt": b"bb", "c.txt": b"ccc"}
        info = zip_list(zip_create(files))
        assert info.file_count == 3
        assert info.dir_count == 0
        assert info.format == "zip"

    def test_entry_sizes(self) -> None:
        content = b"hello world"
        info = zip_list(zip_create({"f.txt": content}))
        assert len(info.entries) == 1
        assert info.entries[0].name == "f.txt"
        assert info.entries[0].size == len(content)
        assert info.entries[0].is_dir is False

    def test_total_size(self) -> None:
        files = {"a.txt": b"aaaa", "b.txt": b"bb"}
        info = zip_list(zip_create(files))
        assert info.total_size == 6  # 4 + 2


class TestZipAdd:
    def test_add_to_existing(self) -> None:
        base = zip_create({"a.txt": b"a"})
        updated = zip_add(base, {"b.txt": b"b"})
        result = zip_extract(updated)
        assert "a.txt" in result
        assert "b.txt" in result

    def test_add_multiple_files(self) -> None:
        base = zip_create({"a.txt": b"a"})
        updated = zip_add(base, {"b.txt": b"b", "c.txt": b"c"})
        info = zip_list(updated)
        assert info.file_count == 3

    def test_overwrite_existing(self) -> None:
        base = zip_create({"a.txt": b"old"})
        updated = zip_add(base, {"a.txt": b"new"})
        result = zip_extract(updated)
        assert result["a.txt"] == b"new"


# ---------------------------------------------------------------------------
# TAR tests
# ---------------------------------------------------------------------------


class TestTarCreate:
    def test_plain_tar(self) -> None:
        data = tar_create({"hello.txt": b"world"})
        assert isinstance(data, bytes)

    def test_tar_gz(self) -> None:
        data = tar_create({"hello.txt": b"world"}, compression="gz")
        assert isinstance(data, bytes)

    def test_tar_bz2(self) -> None:
        data = tar_create({"hello.txt": b"world"}, compression="bz2")
        assert isinstance(data, bytes)

    def test_tar_xz(self) -> None:
        data = tar_create({"hello.txt": b"world"}, compression="xz")
        assert isinstance(data, bytes)

    def test_empty_tar(self) -> None:
        data = tar_create({})
        info = tar_list(data)
        assert info.file_count == 0

    def test_multiple_files(self) -> None:
        files = {"a.txt": b"alpha", "b.txt": b"bravo"}
        data = tar_create(files, compression="gz")
        info = tar_list(data, compression="gz")
        assert info.file_count == 2


class TestTarExtract:
    @pytest.mark.parametrize("compression", ["", "gz", "bz2", "xz"])
    def test_roundtrip(self, compression: str) -> None:
        files = {"a.txt": b"aaa", "b.txt": b"bbb"}
        data = tar_create(files, compression=compression)
        result = tar_extract(data, compression=compression)
        assert result == files

    def test_from_path(self, tmp_path: Path) -> None:
        files = {"test.txt": b"tar-path"}
        archive_path = tmp_path / "test.tar"
        archive_path.write_bytes(tar_create(files))
        result = tar_extract(archive_path)
        assert result == files

    def test_binary_content(self) -> None:
        binary = bytes(range(256))
        data = tar_create({"bin.dat": binary}, compression="gz")
        result = tar_extract(data, compression="gz")
        assert result["bin.dat"] == binary


class TestTarList:
    def test_plain_tar_format(self) -> None:
        info = tar_list(tar_create({"f.txt": b"x"}))
        assert info.format == "tar"

    def test_gz_format(self) -> None:
        info = tar_list(tar_create({"f.txt": b"x"}, compression="gz"), compression="gz")
        assert info.format == "tar.gz"

    def test_bz2_format(self) -> None:
        info = tar_list(tar_create({"f.txt": b"x"}, compression="bz2"), compression="bz2")
        assert info.format == "tar.bz2"

    def test_xz_format(self) -> None:
        info = tar_list(tar_create({"f.txt": b"x"}, compression="xz"), compression="xz")
        assert info.format == "tar.xz"

    def test_entry_details(self) -> None:
        content = b"hello world"
        info = tar_list(tar_create({"f.txt": content}))
        assert len(info.entries) == 1
        assert info.entries[0].name == "f.txt"
        assert info.entries[0].size == len(content)
        assert info.entries[0].is_dir is False


# ---------------------------------------------------------------------------
# Gzip tests
# ---------------------------------------------------------------------------


class TestGzip:
    def test_roundtrip(self) -> None:
        original = b"hello world, this is a gzip test"
        compressed = gzip_compress(original)
        decompressed = gzip_decompress(compressed)
        assert decompressed == original

    def test_empty_data(self) -> None:
        compressed = gzip_compress(b"")
        assert gzip_decompress(compressed) == b""

    def test_compression_reduces_size(self) -> None:
        # Repetitive data compresses well
        data = b"abcdefgh" * 1000
        compressed = gzip_compress(data)
        assert len(compressed) < len(data)

    def test_compression_levels(self) -> None:
        data = b"x" * 10_000
        fast = gzip_compress(data, level=1)
        best = gzip_compress(data, level=9)
        # Both decompress correctly
        assert gzip_decompress(fast) == data
        assert gzip_decompress(best) == data

    def test_binary_data(self) -> None:
        data = bytes(range(256)) * 100
        assert gzip_decompress(gzip_compress(data)) == data


# ---------------------------------------------------------------------------
# Bz2 tests
# ---------------------------------------------------------------------------


class TestBz2:
    def test_roundtrip(self) -> None:
        original = b"hello world, this is a bz2 test"
        compressed = bz2_compress(original)
        decompressed = bz2_decompress(compressed)
        assert decompressed == original

    def test_empty_data(self) -> None:
        compressed = bz2_compress(b"")
        assert bz2_decompress(compressed) == b""

    def test_compression_reduces_size(self) -> None:
        data = b"abcdefgh" * 1000
        compressed = bz2_compress(data)
        assert len(compressed) < len(data)

    def test_compression_levels(self) -> None:
        data = b"y" * 10_000
        fast = bz2_compress(data, level=1)
        best = bz2_compress(data, level=9)
        assert bz2_decompress(fast) == data
        assert bz2_decompress(best) == data


# ---------------------------------------------------------------------------
# LZMA tests
# ---------------------------------------------------------------------------


class TestLzma:
    def test_roundtrip(self) -> None:
        original = b"hello world, this is an lzma test"
        compressed = lzma_compress(original)
        decompressed = lzma_decompress(compressed)
        assert decompressed == original

    def test_empty_data(self) -> None:
        compressed = lzma_compress(b"")
        assert lzma_decompress(compressed) == b""

    def test_compression_reduces_size(self) -> None:
        data = b"abcdefgh" * 1000
        compressed = lzma_compress(data)
        assert len(compressed) < len(data)

    def test_binary_data(self) -> None:
        data = bytes(range(256)) * 100
        assert lzma_decompress(lzma_compress(data)) == data


# ---------------------------------------------------------------------------
# Cross-format tests
# ---------------------------------------------------------------------------


class TestCrossFormat:
    def test_large_data_all_compressors(self) -> None:
        """All three single-file compressors handle 1MB of data."""
        data = b"The quick brown fox jumps over the lazy dog. " * 25_000
        assert gzip_decompress(gzip_compress(data)) == data
        assert bz2_decompress(bz2_compress(data)) == data
        assert lzma_decompress(lzma_compress(data)) == data

    def test_zip_and_tar_same_content(self) -> None:
        """ZIP and TAR archives with the same input produce identical extraction."""
        files = {"readme.txt": b"Hello!", "data.bin": bytes(range(128))}
        zip_result = zip_extract(zip_create(files))
        tar_result = tar_extract(tar_create(files))
        assert zip_result == tar_result == files

    def test_archive_info_type(self) -> None:
        data = zip_create({"f.txt": b"content"})
        info = zip_list(data)
        assert isinstance(info, ArchiveInfo)
        assert info.format == "zip"
