"""Command line interface for diagrams-cli."""

from __future__ import annotations

import argparse
import sys

from diagrams_cli import __version__


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
        help="Output format to generate.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.input:
        parser.print_help()
        return 1

    print(
        "Placeholder: would generate",
        args.format,
        "from",
        args.input,
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
