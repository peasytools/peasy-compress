# peasy-compress

[![PyPI version](https://agentgif.com/badge/pypi/peasy-compress/version.svg)](https://pypi.org/project/peasy-compress/)
[![Python](https://img.shields.io/pypi/pyversions/peasy-compress)](https://pypi.org/project/peasy-compress/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](https://pypi.org/project/peasy-compress/)

Pure Python archive and compression library with zero external dependencies. Create, extract, and inspect ZIP and TAR archives, compress and decompress data with 3 algorithms (gzip, bz2, lzma), and manage 5 archive formats (`.zip`, `.tar`, `.tar.gz`, `.tar.bz2`, `.tar.xz`) -- all using only the Python standard library. Every function works with `bytes`, `Path`, or string paths, operates entirely in memory with no filesystem side effects, and returns clean `bytes` or typed dataclasses.

Built for [Peasy Tools](https://peasytools.com), a free online toolkit with interactive tools for archive creation, file compression, and archive inspection. The library powers 13 functions across 2 archive formats and 3 compression algorithms, providing a consistent, type-safe API for all common compression tasks.

> **Try the interactive tools at [peasytools.com](https://peasytools.com)** -- archive creation, compression, and inspection tools.

<p align="center">
  <img src="demo.gif" alt="peasy-compress demo -- create ZIP archives, compress with gzip bz2 lzma, inspect TAR contents in Python" width="800">
</p>

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start)
- [What You Can Do](#what-you-can-do)
  - [ZIP Archives](#zip-archives)
  - [TAR Archives](#tar-archives)
  - [Single-File Compression](#single-file-compression)
  - [Compression Algorithm Comparison](#compression-algorithm-comparison)
  - [Archive Inspection](#archive-inspection)
- [Command-Line Interface](#command-line-interface)
- [API Reference](#api-reference)
  - [Types](#types)
  - [Functions](#functions)
- [Learn More About Compression](#learn-more-about-compression)
- [Also Available](#also-available)
- [Peasy Developer Tools](#peasy-developer-tools)
- [License](#license)

## Install

```bash
# Core library (zero dependencies, Python 3.10+)
pip install peasy-compress

# With CLI support (adds typer)
pip install "peasy-compress[cli]"
```

## Quick Start

```python
from peasy_compress import zip_create, zip_extract, gzip_compress, gzip_decompress

# Create a ZIP archive entirely in memory -- no temp files, no disk I/O
archive = zip_create({
    "hello.txt": b"Hello, world!",
    "data.csv": b"name,value\nalpha,1\nbravo,2",
})

# Extract all files from the archive
files = zip_extract(archive)
print(files["hello.txt"])  # b'Hello, world!'

# Compress raw bytes with gzip (RFC 1952 compliant)
original = b"Repetitive data " * 1000
compressed = gzip_compress(original)
print(f"Compressed: {len(original)} -> {len(compressed)} bytes")

# Decompress back to original -- lossless round-trip guaranteed
restored = gzip_decompress(compressed)
assert restored == original
```

## What You Can Do

### ZIP Archives

ZIP is the most widely used archive format, supported natively on Windows, macOS, and Linux. It uses per-file [DEFLATE compression](https://peasytools.com/glossary/) (RFC 1951) and supports random access to individual entries without decompressing the entire archive. `peasy-compress` operates entirely in memory -- no temporary files, no filesystem side effects, no `zipfile.ZipFile` context managers to worry about.

| Function | Description |
|----------|-------------|
| `zip_create()` | Create a ZIP archive from a `dict[str, bytes]` file mapping |
| `zip_extract()` | Extract all files from a ZIP archive to `dict[str, bytes]` |
| `zip_list()` | Inspect archive contents and compression ratios without extracting |
| `zip_add()` | Append files to an existing ZIP archive |

The ZIP format stores each file with its own compression stream, allowing tools to extract individual files without processing the entire archive. The `CompressionLevel` parameter (`"fastest"`, `"default"`, `"best"`) maps to DEFLATE levels 1, 6, and 9 respectively:

| Level | DEFLATE Level | Use Case | Speed |
|-------|---------------|----------|-------|
| `"fastest"` | 1 | Quick archiving, CI artifacts, large file counts | Fastest |
| `"default"` | 6 | General purpose, good balance of speed and ratio | Balanced |
| `"best"` | 9 | Distribution packages, long-term storage | Slowest |

```python
from peasy_compress import zip_create, zip_extract, zip_list, zip_add

# Create a ZIP archive with maximum DEFLATE compression
archive = zip_create(
    {"report.txt": b"Q1 results...", "data.json": b'{"sales": 42}'},
    level="best",  # DEFLATE level 9 -- smallest output
)

# List contents without extracting -- inspect compression ratios
info = zip_list(archive)
print(f"Files: {info.file_count}, Total size: {info.total_size} bytes")
for entry in info.entries:
    ratio = entry.compressed_size / entry.size if entry.size else 0
    print(f"  {entry.name}: {entry.size}B -> {entry.compressed_size}B ({ratio:.0%})")

# Add more files to an existing archive without re-creating it
updated = zip_add(archive, {"readme.md": b"# Project Notes"})
print(f"Updated archive has {zip_list(updated).file_count} files")

# Extract from a file path -- accepts bytes, Path, or str
files = zip_extract("/path/to/archive.zip")
```

Learn more: [Peasy Tools](https://peasytools.com/) · [DEFLATE Glossary](https://peasytools.com/glossary/)

### TAR Archives

TAR (Tape Archive) bundles multiple files into a single sequential stream, optionally compressed with gzip, bz2, or xz. Unlike ZIP, TAR separates the archiving step from compression -- the entire archive is compressed as one unit, which typically yields better compression ratios for collections of similar files. TAR is the standard archive format on Unix/Linux systems and is the backbone of software distribution (source tarballs), container images (Docker layers), and system backups.

The `compression` parameter controls the outer compression layer:

| Compression | Extension | Algorithm | Typical Ratio | Speed | Standard |
|-------------|-----------|-----------|---------------|-------|----------|
| `""` (none) | `.tar` | None | 1:1 (no compression) | Instant | POSIX.1-1988 |
| `"gz"` | `.tar.gz` | DEFLATE (RFC 1952) | 3:1 -- 5:1 | Fast | RFC 1952 |
| `"bz2"` | `.tar.bz2` | Burrows-Wheeler | 4:1 -- 7:1 | Moderate | bzip2 spec |
| `"xz"` | `.tar.xz` | LZMA2 | 5:1 -- 10:1 | Slowest | XZ Utils / LZMA SDK |

```python
from peasy_compress import tar_create, tar_extract, tar_list

# Create a gzip-compressed tar archive -- standard .tar.gz format
archive = tar_create(
    {"src/main.py": b"print('hello')", "src/utils.py": b"# utils"},
    compression="gz",  # Options: "", "gz", "bz2", "xz"
)

# Extract all files -- preserves directory structure in keys
files = tar_extract(archive, compression="gz")
print(files["src/main.py"])  # b"print('hello')"

# List contents without extracting -- inspect format and file count
info = tar_list(archive, compression="gz")
print(f"Format: {info.format}")   # "tar.gz"
print(f"Files: {info.file_count}")  # 2

# Create an uncompressed tar for piping to external compressors
raw_tar = tar_create({"data.bin": b"\x00" * 10000})

# Create a tar.xz archive -- maximum compression for distribution
dist = tar_create(
    {"package/setup.py": b"...", "package/README.md": b"..."},
    compression="xz",  # LZMA2 compression -- best ratio
)
```

Learn more: [Peasy Tools](https://peasytools.com/) · [TAR Format Glossary](https://peasytools.com/glossary/tar/)

### Single-File Compression

Compress or decompress individual byte sequences without creating an archive. All three algorithms are included in the Python standard library, and `peasy-compress` provides a consistent, symmetrical API across them -- every `*_compress()` function returns `bytes` and every `*_decompress()` function restores the original data losslessly.

| Algorithm | Module | RFC/Standard | Typical Ratio | Best For |
|-----------|--------|-------------|---------------|----------|
| **gzip** | `gzip` | RFC 1952 | 3:1 -- 5:1 | HTTP `Content-Encoding`, general purpose, web assets |
| **bz2** | `bz2` | bzip2 1.0.6 | 4:1 -- 7:1 | Text-heavy data, source code, log files |
| **lzma** | `lzma` | LZMA SDK / XZ | 5:1 -- 10:1 | Maximum compression, software distribution, `.xz` files |

**Gzip** (GNU zip) is the most widely deployed compression algorithm on the internet. Every web server and browser supports `Content-Encoding: gzip`, and it is the default compression for HTTP/1.1 transfer encoding. Gzip uses DEFLATE internally (LZ77 + Huffman coding) with a 32KB sliding window.

**Bz2** (bzip2) uses the Burrows-Wheeler Transform followed by Move-to-Front and Huffman coding. It achieves 10-15% better compression than gzip on text-heavy data, at the cost of 2-4x slower compression speed. Bz2 uses a block size of 100-900KB (controlled by the `level` parameter).

**LZMA** (Lempel-Ziv-Markov chain Algorithm) provides the best compression ratio of the three. It uses a dictionary size of up to 4GB and sophisticated range coding. LZMA is the algorithm behind `.xz` files and `7z` archives. The `lzma` module does not expose a compression level parameter -- it uses optimal settings by default.

```python
from peasy_compress import (
    gzip_compress, gzip_decompress,
    bz2_compress, bz2_decompress,
    lzma_compress, lzma_decompress,
)

data = b"Hello, compression!" * 500

# gzip -- fast, universally compatible (HTTP Content-Encoding)
gz = gzip_compress(data, level=9)  # Level 1-9, default 9
assert gzip_decompress(gz) == data

# bz2 -- Burrows-Wheeler transform, better ratio for text
bz = bz2_compress(data, level=9)  # Level 1-9, default 9
assert bz2_decompress(bz) == data

# lzma -- maximum compression, LZMA2 algorithm
xz = lzma_compress(data)  # No level parameter -- optimal by default
assert lzma_decompress(xz) == data

# Compare compression ratios across all three algorithms
print(f"Original: {len(data):>6} bytes")
print(f"gzip:     {len(gz):>6} bytes ({len(gz)/len(data):.1%})")
print(f"bz2:      {len(bz):>6} bytes ({len(bz)/len(data):.1%})")
print(f"lzma:     {len(xz):>6} bytes ({len(xz)/len(data):.1%})")
```

Learn more: [Peasy Tools](https://peasytools.com/) · [Compression Glossary](https://peasytools.com/glossary/)

### Compression Algorithm Comparison

Choosing the right compression algorithm depends on your use case. Here is a practical guide based on real-world trade-offs between compression ratio, speed, and compatibility:

| Scenario | Recommended | Why |
|----------|-------------|-----|
| Web server assets (CSS, JS, HTML) | **gzip** | Universal browser support via `Content-Encoding: gzip` |
| CI/CD build artifacts | **gzip** (`level=1`) | Speed matters more than ratio for ephemeral files |
| Log file archival | **bz2** | Logs are text-heavy; bz2 excels at repetitive text |
| Source code distribution | **xz** (LZMA) | Best ratio for `.tar.xz` tarballs, standard on Linux |
| Cross-platform sharing | **ZIP** | Built-in OS support on Windows, macOS, Linux |
| Container image layers | **gzip** | Docker/OCI spec requires gzip-compressed tar layers |
| Database backups | **lzma** | Maximum compression for large SQL dumps |
| Streaming/piping | **gzip** | Supports streaming compression; bz2/lzma are block-based |

**Compression level trade-offs:** Gzip and bz2 accept levels 1-9. Level 1 is fastest with the lowest ratio, level 9 is slowest with the best ratio. In practice, levels 6-9 produce similar ratios -- the speed difference is more significant than the size difference. For most use cases, the default level 9 in `peasy-compress` is the right choice.

```python
from peasy_compress import gzip_compress, bz2_compress, lzma_compress

# Benchmark compression ratios on realistic data
log_data = b"2026-01-15 INFO Request processed in 42ms\n" * 10000
json_data = b'{"id": 1, "name": "example", "active": true}\n' * 5000
binary_data = bytes(range(256)) * 1000

for label, data in [("Log file", log_data), ("JSON", json_data), ("Binary", binary_data)]:
    gz = gzip_compress(data)
    bz = bz2_compress(data)
    xz = lzma_compress(data)
    print(f"{label} ({len(data):,} bytes):")
    print(f"  gzip: {len(gz):>7,} ({len(gz)/len(data):5.1%})")
    print(f"  bz2:  {len(bz):>7,} ({len(bz)/len(data):5.1%})")
    print(f"  lzma: {len(xz):>7,} ({len(xz)/len(data):5.1%})")
```

Learn more: [Peasy Tools](https://peasytools.com/) · [Compression Glossary](https://peasytools.com/glossary/)

### Archive Inspection

The `zip_list()` and `tar_list()` functions return an `ArchiveInfo` dataclass with detailed metadata about every entry in the archive -- sizes, compression ratios, file/directory counts -- without extracting any content. This is useful for validation, auditing, and building archive browsers.

```python
from peasy_compress import zip_create, zip_list, tar_create, tar_list

# Create a ZIP archive and inspect its contents
archive = zip_create({
    "docs/guide.md": b"# User Guide\n" * 100,
    "src/app.py": b"import os\n" * 50,
    "README.md": b"# Project\n",
})

# ArchiveInfo gives you a complete summary without extracting
info = zip_list(archive)
print(f"Format: {info.format}")                  # "zip"
print(f"Files: {info.file_count}")               # 3
print(f"Directories: {info.dir_count}")          # 0
print(f"Total size: {info.total_size} bytes")    # uncompressed total
print(f"Compressed: {info.total_compressed} bytes")

# Each ArchiveEntry has name, size, compressed_size, and is_dir
for entry in info.entries:
    if not entry.is_dir:
        ratio = (1 - entry.compressed_size / entry.size) * 100 if entry.size else 0
        print(f"  {entry.name}: {entry.size}B -> {entry.compressed_size}B ({ratio:.0f}% saved)")

# TAR inspection works the same way
tar_data = tar_create({"config.yaml": b"key: value\n"}, compression="gz")
tar_info = tar_list(tar_data, compression="gz")
print(f"\nTAR format: {tar_info.format}")  # "tar.gz"
```

Learn more: [Peasy Tools](https://peasytools.com/) · [Archive Format Glossary](https://peasytools.com/glossary/archive/)

## Command-Line Interface

Install with CLI support: `pip install "peasy-compress[cli]"`

```bash
# ZIP operations -- create, extract, and inspect ZIP archives
peasy-compress zip-create file1.txt file2.txt -o archive.zip
peasy-compress zip-extract archive.zip -o ./output/
peasy-compress zip-list archive.zip

# TAR operations -- with optional gzip/bz2/xz compression
peasy-compress tar-create src/ docs/ -o backup.tar.gz -c gz
peasy-compress tar-extract backup.tar.gz -o ./restored/ -c gz
peasy-compress tar-list backup.tar.gz -c gz

# Single-file compression and decompression
peasy-compress gzip largefile.txt              # -> largefile.txt.gz
peasy-compress gunzip largefile.txt.gz         # -> largefile.txt
peasy-compress bz2 data.csv                    # -> data.csv.bz2
peasy-compress bunzip2 data.csv.bz2            # -> data.csv
peasy-compress xz database.sql                 # -> database.sql.xz
peasy-compress unxz database.sql.xz            # -> database.sql

# Control compression level (1-9) for gzip and bz2
peasy-compress gzip largefile.txt -l 1         # fastest compression
peasy-compress bz2 data.csv -l 9               # best compression

# Specify custom output path
peasy-compress gzip input.txt -o /tmp/compressed.gz
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `zip-create` | Create a ZIP archive from one or more files |
| `zip-extract` | Extract all files from a ZIP archive |
| `zip-list` | List contents with sizes and compression info |
| `tar-create` | Create a TAR archive with optional compression |
| `tar-extract` | Extract a TAR archive |
| `tar-list` | List TAR archive contents |
| `gzip` / `gunzip` | Compress / decompress with gzip |
| `bz2` / `bunzip2` | Compress / decompress with bz2 |
| `xz` / `unxz` | Compress / decompress with lzma/xz |

## API Reference

### Types

| Type | Description |
|------|-------------|
| `ArchiveInput` | `bytes \| Path \| str` -- flexible input accepted by all archive functions |
| `CompressionLevel` | `Literal["fastest", "default", "best"]` -- maps to DEFLATE levels 1, 6, 9 |
| `ArchiveEntry` | Frozen dataclass: `name: str`, `size: int`, `compressed_size: int`, `is_dir: bool` |
| `ArchiveInfo` | Frozen dataclass: `format: str`, `entries: list[ArchiveEntry]`, `total_size: int`, `total_compressed: int`, `file_count: int`, `dir_count: int` |

### Functions

| Function | Signature | Returns | Description |
|----------|-----------|---------|-------------|
| `zip_create` | `(files: dict[str, bytes], *, level: CompressionLevel = "default")` | `bytes` | Create a ZIP archive in memory |
| `zip_extract` | `(source: ArchiveInput)` | `dict[str, bytes]` | Extract all files from a ZIP archive |
| `zip_list` | `(source: ArchiveInput)` | `ArchiveInfo` | List ZIP contents with compression ratios |
| `zip_add` | `(source: ArchiveInput, files: dict[str, bytes])` | `bytes` | Append files to an existing ZIP archive |
| `tar_create` | `(files: dict[str, bytes], *, compression: str = "")` | `bytes` | Create a TAR archive (plain, gz, bz2, xz) |
| `tar_extract` | `(source: ArchiveInput, *, compression: str = "")` | `dict[str, bytes]` | Extract all files from a TAR archive |
| `tar_list` | `(source: ArchiveInput, *, compression: str = "")` | `ArchiveInfo` | List TAR contents and format |
| `gzip_compress` | `(data: bytes, *, level: int = 9)` | `bytes` | Compress bytes with gzip (RFC 1952) |
| `gzip_decompress` | `(data: bytes)` | `bytes` | Decompress gzip data |
| `bz2_compress` | `(data: bytes, *, level: int = 9)` | `bytes` | Compress bytes with bz2 (Burrows-Wheeler) |
| `bz2_decompress` | `(data: bytes)` | `bytes` | Decompress bz2 data |
| `lzma_compress` | `(data: bytes)` | `bytes` | Compress bytes with LZMA/XZ |
| `lzma_decompress` | `(data: bytes)` | `bytes` | Decompress LZMA/XZ data |

## Learn More About Compression

- **Tools**: [ZIP Creator](https://peasytools.com/tools/zip-creator/) · [File Compressor](https://peasytools.com/tools/file-compressor/) · [Archive Inspector](https://peasytools.com/tools/archive-inspector/) · [All Tools](https://peasytools.com/)
- **Guides**: [Compression Algorithms Guide](https://peasytools.com/guides/compression-algorithms/) · [Archive Formats Guide](https://peasytools.com/guides/archive-formats/) · [All Guides](https://peasytools.com/guides/)
- **Glossary**: [Gzip](https://peasytools.com/glossary/gzip/) · [TAR](https://peasytools.com/glossary/tar/) · [Brotli](https://peasytools.com/glossary/brotli/) · [All Terms](https://peasytools.com/glossary/)
- **Formats**: [ZIP](https://peasytools.com/formats/zip/) · [TAR](https://peasytools.com/formats/tar/) · [All Formats](https://peasytools.com/formats/)
- **API**: [REST API Docs](https://peasytools.com/developers/) · [OpenAPI Spec](https://peasytools.com/api/openapi.json)

## Also Available

| Platform | Install | Link |
|----------|---------|------|
| **TypeScript / npm** | `npm install peasy-compress` | [npm](https://www.npmjs.com/package/peasy-compress) |
| **Go** | `go get github.com/peasytools/peasy-compress-go` | [pkg.go.dev](https://pkg.go.dev/github.com/peasytools/peasy-compress-go) |
| **Rust** | `cargo add peasy-compress` | [crates.io](https://crates.io/crates/peasy-compress) |
| **Ruby** | `gem install peasy-compress` | [RubyGems](https://rubygems.org/gems/peasy-compress) |
| **MCP** | `uvx --from "peasy-compress[mcp]" python -m peasy_compress.mcp_server` | [Config](#mcp-server-claude-cursor-windsurf) |

## Peasy Developer Tools

Part of the [Peasy](https://peasytools.com) open-source developer tools ecosystem.

| Package | PyPI | npm | Description |
|---------|------|-----|-------------|
| peasy-pdf | [PyPI](https://pypi.org/project/peasy-pdf/) | [npm](https://www.npmjs.com/package/peasy-pdf) | PDF merge, split, compress, 21 operations — [peasypdf.com](https://peasypdf.com) |
| peasy-image | [PyPI](https://pypi.org/project/peasy-image/) | [npm](https://www.npmjs.com/package/peasy-image) | Image resize, crop, convert, compress, 20 operations — [peasyimage.com](https://peasyimage.com) |
| peasytext | [PyPI](https://pypi.org/project/peasytext/) | [npm](https://www.npmjs.com/package/peasytext) | Text case, slugify, word count, encoding — [peasytext.com](https://peasytext.com) |
| peasy-css | [PyPI](https://pypi.org/project/peasy-css/) | [npm](https://www.npmjs.com/package/peasy-css) | CSS gradients, shadows, flexbox, grid generators — [peasycss.com](https://peasycss.com) |
| **peasy-compress** | **[PyPI](https://pypi.org/project/peasy-compress/)** | **[npm](https://www.npmjs.com/package/peasy-compress)** | **ZIP, TAR, gzip, brotli archive operations — [peasytools.com](https://peasytools.com)** |
| peasy-document | [PyPI](https://pypi.org/project/peasy-document/) | [npm](https://www.npmjs.com/package/peasy-document) | Markdown, HTML, CSV, JSON conversions — [peasyformats.com](https://peasyformats.com) |
| peasy-audio | [PyPI](https://pypi.org/project/peasy-audio/) | [npm](https://www.npmjs.com/package/peasy-audio) | Audio convert, trim, merge, normalize — [peasyaudio.com](https://peasyaudio.com) |
| peasy-video | [PyPI](https://pypi.org/project/peasy-video/) | [npm](https://www.npmjs.com/package/peasy-video) | Video trim, resize, GIF conversion — [peasyvideo.com](https://peasyvideo.com) |

## License

MIT
