"""Command line interface for diagrams-cli."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from diagrams_cli import __version__
from diagrams_cli.errors import DiagramError
from diagrams_cli.loader import load_diagram
from diagrams_cli.output import validate_output_path, write_output_file
from diagrams_cli.renderers import render_excalidraw, render_plantuml


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diagrams-cli",
        description="Generate PlantUML and Excalidraw from JSON.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"diagrams-cli {__version__}",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to an input JSON file.",
    )
    parser.add_argument(
        "--format",
        choices=["plantuml", "excalidraw"],
        default="plantuml",
        help="Output format; defaults to plantuml.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write to .puml/.excalidraw instead of stdout.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output file; requires --output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.input:
        parser.print_help()
        return 1
    if args.force and not args.output:
        parser.error("--force requires --output")

    if args.output:
        try:
            validate_output_path(args.output, args.format)
        except DiagramError as error:
            print(f"diagrams-cli: error: {error}", file=sys.stderr)
            return 1

    source_path = Path(args.input)
    if not source_path.exists():
        parser.error(f"input file does not exist: {args.input}")
    if not source_path.is_file():
        parser.error(f"input path is not a file: {args.input}")

    try:
        diagram = load_diagram(source_path)
    except DiagramError as error:
        print(f"diagrams-cli: error: {error}", file=sys.stderr)
        return 1

    renderer = (
        render_plantuml if args.format == "plantuml" else render_excalidraw
    )
    rendered = renderer(diagram)
    if args.output:
        try:
            write_output_file(
                rendered,
                args.output,
                args.format,
                force=args.force,
            )
        except DiagramError as error:
            print(f"diagrams-cli: error: {error}", file=sys.stderr)
            return 1
    else:
        print(rendered, end="", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
