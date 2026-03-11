"""Command-line interface for peasy-compress.

Provides archive and compression commands for ZIP, TAR, gzip, bz2, and lzma.
Requires the ``cli`` extra: ``pip install peasy-compress[cli]``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from peasy_compress.engine import (
    bz2_compress,
    bz2_decompress,
    gzip_compress,
    gzip_decompress,
    lzma_compress,
    lzma_decompress,
    tar_create,
    tar_extract,
    tar_list,
    zip_create,
    zip_extract,
    zip_list,
)

app = typer.Typer(
    name="compress",
    help="Archive & compression tools -- zip, tar, gzip, bz2, lzma.",
    no_args_is_help=True,
)

# ---------------------------------------------------------------------------
# Annotated type aliases (avoids B008 — no function calls in defaults)
# ---------------------------------------------------------------------------

FilesArg = Annotated[list[Path], typer.Argument(help="Files to add to the archive.")]
ArchiveArg = Annotated[Path, typer.Argument(help="Archive file to operate on.")]
FileArg = Annotated[Path, typer.Argument(help="File to process.")]
ZipOutputOpt = Annotated[Path, typer.Option("-o", "--output", help="Output ZIP file path.")]
TarOutputOpt = Annotated[Path, typer.Option("-o", "--output", help="Output TAR file path.")]
OutputDirOpt = Annotated[
    Path, typer.Option("-o", "--output-dir", help="Directory to extract into.")
]
CompressionOpt = Annotated[
    str, typer.Option("-c", "--compression", help="Compression: '', 'gz', 'bz2', 'xz'.")
]
OutputPathOpt = Annotated[Path | None, typer.Option("-o", "--output", help="Output path.")]
LevelOpt = Annotated[
    int, typer.Option("-l", "--level", min=1, max=9, help="Compression level (1-9).")
]


# ---------------------------------------------------------------------------
# ZIP commands
# ---------------------------------------------------------------------------


@app.command("zip-create")
def cmd_zip_create(
    files: FilesArg,
    output: ZipOutputOpt = Path("archive.zip"),
) -> None:
    """Create a ZIP archive from one or more files."""
    contents: dict[str, bytes] = {}
    for f in files:
        if not f.exists():
            typer.echo(f"Error: {f} not found.", err=True)
            raise typer.Exit(1)
        contents[f.name] = f.read_bytes()

    data = zip_create(contents)
    output.write_bytes(data)
    typer.echo(f"Created {output} ({len(contents)} file(s), {len(data)} bytes)")


@app.command("zip-extract")
def cmd_zip_extract(
    archive: ArchiveArg,
    output_dir: OutputDirOpt = Path("."),
) -> None:
    """Extract all files from a ZIP archive."""
    if not archive.exists():
        typer.echo(f"Error: {archive} not found.", err=True)
        raise typer.Exit(1)

    extracted = zip_extract(archive)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, content in extracted.items():
        dest = output_dir / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        typer.echo(f"  {name} ({len(content)} bytes)")

    typer.echo(f"Extracted {len(extracted)} file(s) to {output_dir}")


@app.command("zip-list")
def cmd_zip_list(archive: ArchiveArg) -> None:
    """List contents of a ZIP archive."""
    if not archive.exists():
        typer.echo(f"Error: {archive} not found.", err=True)
        raise typer.Exit(1)

    info = zip_list(archive)
    typer.echo(f"Archive: {archive} ({info.format})")
    typer.echo(f"Files: {info.file_count}, Directories: {info.dir_count}")
    typer.echo(f"Total size: {info.total_size} bytes, Compressed: {info.total_compressed} bytes")
    typer.echo("")
    for entry in info.entries:
        kind = "DIR " if entry.is_dir else "FILE"
        typer.echo(f"  {kind}  {entry.name}  ({entry.size} -> {entry.compressed_size} bytes)")


# ---------------------------------------------------------------------------
# TAR commands
# ---------------------------------------------------------------------------


@app.command("tar-create")
def cmd_tar_create(
    files: FilesArg,
    output: TarOutputOpt = Path("archive.tar"),
    compression: CompressionOpt = "",
) -> None:
    """Create a TAR archive (optionally compressed) from one or more files."""
    contents: dict[str, bytes] = {}
    for f in files:
        if not f.exists():
            typer.echo(f"Error: {f} not found.", err=True)
            raise typer.Exit(1)
        contents[f.name] = f.read_bytes()

    data = tar_create(contents, compression=compression)
    output.write_bytes(data)
    typer.echo(f"Created {output} ({len(contents)} file(s), {len(data)} bytes)")


@app.command("tar-extract")
def cmd_tar_extract(
    archive: ArchiveArg,
    output_dir: OutputDirOpt = Path("."),
    compression: CompressionOpt = "",
) -> None:
    """Extract all files from a TAR archive."""
    if not archive.exists():
        typer.echo(f"Error: {archive} not found.", err=True)
        raise typer.Exit(1)

    extracted = tar_extract(archive, compression=compression)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, content in extracted.items():
        dest = output_dir / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        typer.echo(f"  {name} ({len(content)} bytes)")

    typer.echo(f"Extracted {len(extracted)} file(s) to {output_dir}")


@app.command("tar-list")
def cmd_tar_list(
    archive: ArchiveArg,
    compression: CompressionOpt = "",
) -> None:
    """List contents of a TAR archive."""
    if not archive.exists():
        typer.echo(f"Error: {archive} not found.", err=True)
        raise typer.Exit(1)

    info = tar_list(archive, compression=compression)
    typer.echo(f"Archive: {archive} ({info.format})")
    typer.echo(f"Files: {info.file_count}, Directories: {info.dir_count}")
    typer.echo(f"Total size: {info.total_size} bytes")
    typer.echo("")
    for entry in info.entries:
        kind = "DIR " if entry.is_dir else "FILE"
        typer.echo(f"  {kind}  {entry.name}  ({entry.size} bytes)")


# ---------------------------------------------------------------------------
# Single-file compression commands
# ---------------------------------------------------------------------------


@app.command("gzip")
def cmd_gzip(
    file: FileArg,
    output: OutputPathOpt = None,
    level: LevelOpt = 9,
) -> None:
    """Compress a file with gzip."""
    if not file.exists():
        typer.echo(f"Error: {file} not found.", err=True)
        raise typer.Exit(1)

    dest = output or file.with_suffix(file.suffix + ".gz")
    data = gzip_compress(file.read_bytes(), level=level)
    dest.write_bytes(data)
    typer.echo(f"Compressed {file} -> {dest} ({len(data)} bytes)")


@app.command("gunzip")
def cmd_gunzip(
    file: FileArg,
    output: OutputPathOpt = None,
) -> None:
    """Decompress a gzip file."""
    if not file.exists():
        typer.echo(f"Error: {file} not found.", err=True)
        raise typer.Exit(1)

    if output is None:
        # Strip .gz suffix if present
        dest = file.with_suffix("") if file.suffix == ".gz" else file.with_suffix(".out")
    else:
        dest = output
    data = gzip_decompress(file.read_bytes())
    dest.write_bytes(data)
    typer.echo(f"Decompressed {file} -> {dest} ({len(data)} bytes)")


@app.command("bz2")
def cmd_bz2(
    file: FileArg,
    output: OutputPathOpt = None,
    level: LevelOpt = 9,
) -> None:
    """Compress a file with bz2."""
    if not file.exists():
        typer.echo(f"Error: {file} not found.", err=True)
        raise typer.Exit(1)

    dest = output or file.with_suffix(file.suffix + ".bz2")
    data = bz2_compress(file.read_bytes(), level=level)
    dest.write_bytes(data)
    typer.echo(f"Compressed {file} -> {dest} ({len(data)} bytes)")


@app.command("bunzip2")
def cmd_bunzip2(
    file: FileArg,
    output: OutputPathOpt = None,
) -> None:
    """Decompress a bz2 file."""
    if not file.exists():
        typer.echo(f"Error: {file} not found.", err=True)
        raise typer.Exit(1)

    if output is None:
        dest = file.with_suffix("") if file.suffix == ".bz2" else file.with_suffix(".out")
    else:
        dest = output
    data = bz2_decompress(file.read_bytes())
    dest.write_bytes(data)
    typer.echo(f"Decompressed {file} -> {dest} ({len(data)} bytes)")


@app.command("xz")
def cmd_xz(
    file: FileArg,
    output: OutputPathOpt = None,
) -> None:
    """Compress a file with lzma/xz."""
    if not file.exists():
        typer.echo(f"Error: {file} not found.", err=True)
        raise typer.Exit(1)

    dest = output or file.with_suffix(file.suffix + ".xz")
    data = lzma_compress(file.read_bytes())
    dest.write_bytes(data)
    typer.echo(f"Compressed {file} -> {dest} ({len(data)} bytes)")


@app.command("unxz")
def cmd_unxz(
    file: FileArg,
    output: OutputPathOpt = None,
) -> None:
    """Decompress an xz/lzma file."""
    if not file.exists():
        typer.echo(f"Error: {file} not found.", err=True)
        raise typer.Exit(1)

    if output is None:
        dest = file.with_suffix("") if file.suffix == ".xz" else file.with_suffix(".out")
    else:
        dest = output
    data = lzma_decompress(file.read_bytes())
    dest.write_bytes(data)
    typer.echo(f"Decompressed {file} -> {dest} ({len(data)} bytes)")


if __name__ == "__main__":
    app()
