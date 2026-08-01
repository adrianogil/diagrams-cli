"""Format-aware and overwrite-safe output file handling."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Union

from diagrams_cli.errors import DiagramOutputError

PathInput = Union[str, os.PathLike[str]]

FORMAT_EXTENSIONS: Dict[str, str] = {
    "plantuml": ".puml",
    "excalidraw": ".excalidraw",
}


def validate_output_path(path: PathInput, output_format: str) -> Path:
    """Return a path after checking its extension for the output format."""
    destination = Path(path)
    try:
        expected_extension = FORMAT_EXTENSIONS[output_format]
    except KeyError as error:
        raise DiagramOutputError(
            f"unsupported output format: {output_format}"
        ) from error
    if destination.suffix.lower() != expected_extension:
        raise DiagramOutputError(
            f"{output_format} output path must use the "
            f"{expected_extension} extension: {destination}"
        )
    return destination


def write_output_file(
    content: str,
    path: PathInput,
    output_format: str,
    *,
    force: bool = False,
) -> Path:
    """Write generated text without overwriting unless explicitly allowed."""
    destination = validate_output_path(path, output_format)

    if destination.is_dir():
        raise DiagramOutputError(
            f"output path is a directory: {destination}"
        )
    if destination.exists() and not force:
        raise DiagramOutputError(
            "output file already exists; use --force to overwrite: "
            f"{destination}"
        )

    mode = "w" if force else "x"
    try:
        with destination.open(mode, encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    except FileExistsError as error:
        raise DiagramOutputError(
            "output file already exists; use --force to overwrite: "
            f"{destination}"
        ) from error
    except FileNotFoundError as error:
        raise DiagramOutputError(
            f"output directory does not exist: {destination.parent}"
        ) from error
    except IsADirectoryError as error:
        raise DiagramOutputError(
            f"output path is a directory: {destination}"
        ) from error
    except OSError as error:
        raise DiagramOutputError(
            f"could not write output file {destination}: {error}"
        ) from error

    return destination
