# peasy-compress

[![PyPI](https://img.shields.io/pypi/v/peasy-compress)](https://pypi.org/project/peasy-compress/)
[![Python](https://img.shields.io/pypi/pyversions/peasy-compress)](https://pypi.org/project/peasy-compress/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](https://pypi.org/project/peasy-compress/)

Zero-dependency archive and compression library for Python. Create, extract, and inspect ZIP and TAR archives, and compress or decompress data with gzip, bz2, and lzma -- all using only the Python standard library. Every function works with `bytes`, `Path`, or string paths, making it easy to integrate into any workflow without filesystem side effects.

Built for [Peasy Tools](https://peasytools.com), a collection of developer utilities that prioritize simplicity and zero external dependencies.

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start)
- [What You Can Do](#what-you-can-do)
  - [ZIP Archives](#zip-archives)
  - [TAR Archives](#tar-archives)
  - [Single-File Compression](#single-file-compression)
- [Command-Line Interface](#command-line-interface)
- [API Reference](#api-reference)
- [Peasy Developer Tools](#peasy-developer-tools)
- [License](#license)

## Install

```bash
# Core library (zero dependencies)
pip install peasy-compress

# With CLI support
pip install peasy-compress[cli]
```

Requires Python 3.10+.

## Quick Start

```python
from peasy_compress import zip_create, zip_extract, gzip_compress, gzip_decompress

# Create a ZIP archive in memory
archive = zip_create({
    "hello.txt": b"Hello, world!",
    "data.csv": b"name,value\nalpha,1\nbravo,2",
})

# Extract all files
files = zip_extract(archive)
print(files["hello.txt"])  # b'Hello, world!'

# Compress raw bytes with gzip
original = b"Repetitive data " * 1000
compressed = gzip_compress(original)
print(f"Compressed: {len(original)} -> {len(compressed)} bytes")

# Decompress back to original
restored = gzip_decompress(compressed)
assert restored == original
```

## What You Can Do

### ZIP Archives

ZIP is the most widely used archive format, supported natively on Windows, macOS, and Linux. `peasy-compress` operates entirely in memory -- no temporary files, no filesystem side effects.

| Function | Description |
|----------|-------------|
| `zip_create()` | Create a ZIP archive from a name-to-content mapping |
| `zip_extract()` | Extract all files from a ZIP archive |
| `zip_list()` | Inspect archive contents without extracting |
| `zip_add()` | Add files to an existing ZIP archive |

```python
from peasy_compress import zip_create, zip_extract, zip_list, zip_add

# Create an archive with compression control
archive = zip_create(
    {"report.txt": b"Q1 results...", "data.json": b'{"sales": 42}'},
    level="best",  # "fastest", "default", or "best"
)

# List contents without extracting
info = zip_list(archive)
print(f"Files: {info.file_count}, Total size: {info.total_size} bytes")
for entry in info.entries:
    ratio = entry.compressed_size / entry.size if entry.size else 0
    print(f"  {entry.name}: {entry.size}B -> {entry.compressed_size}B ({ratio:.0%})")

# Add more files to an existing archive
updated = zip_add(archive, {"readme.md": b"# Project Notes"})
print(f"Updated archive has {zip_list(updated).file_count} files")

# Extract from a file path
files = zip_extract("/path/to/archive.zip")
```

### TAR Archives

TAR archives bundle files into a single stream, optionally compressed with gzip, bz2, or xz. TAR is the standard archive format on Unix/Linux systems and is widely used for source distribution and backups.

| Compression | Extension | Speed | Ratio |
|-------------|-----------|-------|-------|
| None | `.tar` | Fastest | No compression |
| gzip | `.tar.gz` | Fast | Good |
| bz2 | `.tar.bz2` | Moderate | Better |
| xz | `.tar.xz` | Slowest | Best |

```python
from peasy_compress import tar_create, tar_extract, tar_list

# Create a gzip-compressed tar archive
archive = tar_create(
    {"src/main.py": b"print('hello')", "src/utils.py": b"# utils"},
    compression="gz",  # "", "gz", "bz2", or "xz"
)

# Extract all files
files = tar_extract(archive, compression="gz")
print(files["src/main.py"])  # b"print('hello')"

# List contents
info = tar_list(archive, compression="gz")
print(f"Format: {info.format}")  # "tar.gz"
print(f"Files: {info.file_count}")
```

### Single-File Compression

Compress or decompress individual byte sequences. All three algorithms are available in the Python standard library, and `peasy-compress` provides a consistent interface across them.

| Algorithm | Use Case | Compression Ratio | Speed |
|-----------|----------|-------------------|-------|
| **gzip** | Web content, HTTP compression, general purpose | Good | Fast |
| **bz2** | Text-heavy data, better ratio than gzip | Better | Moderate |
| **lzma** | Maximum compression, `.xz` files | Best | Slowest |

```python
from peasy_compress import (
    gzip_compress, gzip_decompress,
    bz2_compress, bz2_decompress,
    lzma_compress, lzma_decompress,
)

data = b"Hello, compression!" * 500

# gzip -- fast, widely compatible
gz = gzip_compress(data, level=9)
assert gzip_decompress(gz) == data

# bz2 -- better compression for text
bz = bz2_compress(data, level=9)
assert bz2_decompress(bz) == data

# lzma -- maximum compression
xz = lzma_compress(data)
assert lzma_decompress(xz) == data

# Compare sizes
print(f"Original: {len(data)} bytes")
print(f"gzip:     {len(gz)} bytes ({len(gz)/len(data):.1%})")
print(f"bz2:      {len(bz)} bytes ({len(bz)/len(data):.1%})")
print(f"lzma:     {len(xz)} bytes ({len(xz)/len(data):.1%})")
```

## Command-Line Interface

Install with CLI support: `pip install peasy-compress[cli]`

```bash
# ZIP operations
peasy-compress zip-create file1.txt file2.txt -o archive.zip
peasy-compress zip-extract archive.zip -o ./output/
peasy-compress zip-list archive.zip

# TAR operations
peasy-compress tar-create src/ docs/ -o backup.tar.gz -c gz
peasy-compress tar-extract backup.tar.gz -o ./restored/ -c gz

# Single-file compression
peasy-compress gzip largefile.txt
peasy-compress gunzip largefile.txt.gz
peasy-compress bz2 data.csv
peasy-compress bunzip2 data.csv.bz2
peasy-compress xz database.sql
peasy-compress unxz database.sql.xz
```

## API Reference

### Archive Types

| Type | Description |
|------|-------------|
| `ArchiveInput` | `bytes \| Path \| str` -- flexible input for all functions |
| `CompressionLevel` | `"fastest" \| "default" \| "best"` -- ZIP compression level |
| `ArchiveEntry` | Frozen dataclass: `name`, `size`, `compressed_size`, `is_dir` |
| `ArchiveInfo` | Frozen dataclass: `format`, `entries`, `total_size`, `total_compressed`, `file_count`, `dir_count` |

### Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `zip_create` | `files: dict[str, bytes]`, `level` | `bytes` | Create ZIP archive |
| `zip_extract` | `source: ArchiveInput` | `dict[str, bytes]` | Extract ZIP archive |
| `zip_list` | `source: ArchiveInput` | `ArchiveInfo` | List ZIP contents |
| `zip_add` | `source: ArchiveInput`, `files: dict[str, bytes]` | `bytes` | Add files to ZIP |
| `tar_create` | `files: dict[str, bytes]`, `compression` | `bytes` | Create TAR archive |
| `tar_extract` | `source: ArchiveInput`, `compression` | `dict[str, bytes]` | Extract TAR archive |
| `tar_list` | `source: ArchiveInput`, `compression` | `ArchiveInfo` | List TAR contents |
| `gzip_compress` | `data: bytes`, `level: int` | `bytes` | Gzip compress |
| `gzip_decompress` | `data: bytes` | `bytes` | Gzip decompress |
| `bz2_compress` | `data: bytes`, `level: int` | `bytes` | Bz2 compress |
| `bz2_decompress` | `data: bytes` | `bytes` | Bz2 decompress |
| `lzma_compress` | `data: bytes` | `bytes` | LZMA/XZ compress |
| `lzma_decompress` | `data: bytes` | `bytes` | LZMA/XZ decompress |

## Peasy Developer Tools

Part of the [Peasy Tools](https://peasytools.com) open-source developer utilities ecosystem.

| Package | PyPI | Description |
|---------|------|-------------|
| peasytext | [PyPI](https://pypi.org/project/peasytext/) | Text manipulation, slug generation, encoding -- [peasytools.com](https://peasytools.com) |
| peasy-pdf | [PyPI](https://pypi.org/project/peasy-pdf/) | PDF text extraction and page manipulation -- [peasytools.com](https://peasytools.com) |
| peasy-image | [PyPI](https://pypi.org/project/peasy-image/) | Image format conversion and metadata -- [peasytools.com](https://peasytools.com) |
| peasy-css | [PyPI](https://pypi.org/project/peasy-css/) | CSS minification, formatting, analysis -- [peasytools.com](https://peasytools.com) |
| **peasy-compress** | [PyPI](https://pypi.org/project/peasy-compress/) | **Archive & compression -- ZIP, TAR, gzip, bz2, lzma -- [peasytools.com](https://peasytools.com)** |
| peasy-convert | [PyPI](https://pypi.org/project/peasy-convert/) | Unified CLI for all Peasy tools -- [peasytools.com](https://peasytools.com) |

## License

MIT
