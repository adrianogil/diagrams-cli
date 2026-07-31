"""Load diagram descriptions from JSON files or strings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Union

from diagrams_cli.errors import DiagramLoadError
from diagrams_cli.model import Diagram
from diagrams_cli.validation import parse_diagram

PathInput = Union[str, os.PathLike[str]]


def load_diagram(path: PathInput) -> Diagram:
    """Read, decode, validate, and return a diagram from a UTF-8 JSON file."""
    source_path = Path(path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise DiagramLoadError(
            f"input file does not exist: {source_path}"
        ) from error
    except IsADirectoryError as error:
        raise DiagramLoadError(
            f"input path is not a file: {source_path}"
        ) from error
    except UnicodeDecodeError as error:
        raise DiagramLoadError(
            f"input file is not valid UTF-8: {source_path}"
        ) from error
    except OSError as error:
        raise DiagramLoadError(
            f"could not read input file {source_path}: {error}"
        ) from error

    return loads_diagram(text, source=str(source_path))


def loads_diagram(text: str, *, source: str = "<string>") -> Diagram:
    """Decode and validate a diagram from a JSON string."""
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise DiagramLoadError(
            f"invalid JSON in {source} at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    return parse_diagram(value)
