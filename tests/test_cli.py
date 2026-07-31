"""Tests for the diagrams-cli command-line interface."""

from __future__ import annotations

import contextlib
import io
import unittest

from diagrams_cli import __version__
from diagrams_cli.cli import build_parser, main


class BuildParserTests(unittest.TestCase):
    def test_parses_input_with_default_output_format(self) -> None:
        args = build_parser().parse_args(["diagram.json"])

        self.assertEqual(args.input, "diagram.json")
        self.assertEqual(args.format, "plantuml")

    def test_parses_input_with_explicit_output_format(self) -> None:
        args = build_parser().parse_args(
            ["diagram.json", "--format", "excalidraw"]
        )

        self.assertEqual(args.input, "diagram.json")
        self.assertEqual(args.format, "excalidraw")

    def test_rejects_invalid_output_format(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaisesRegex(SystemExit, "2"):
                build_parser().parse_args(
                    ["diagram.json", "--format", "svg"]
                )

        message = stderr.getvalue()
        self.assertIn("invalid choice: 'svg'", message)
        self.assertIn("choose from 'plantuml', 'excalidraw'", message)


class MainTests(unittest.TestCase):
    def test_valid_arguments_report_input_and_output_format(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["source.json", "--format", "excalidraw"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue(),
            "Placeholder: would generate excalidraw from source.json\n",
        )

    def test_missing_input_prints_help_and_returns_error(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([])

        self.assertEqual(exit_code, 1)
        help_text = stdout.getvalue()
        self.assertIn("usage: diagrams-cli", help_text)
        self.assertIn("Path to an input JSON file.", help_text)

    def test_help_prints_usage_and_exits_successfully(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            with self.assertRaisesRegex(SystemExit, "0"):
                main(["--help"])

        help_text = stdout.getvalue()
        self.assertIn("usage: diagrams-cli", help_text)
        self.assertIn(
            "Generate PlantUML and Excalidraw from JSON.", help_text
        )

    def test_version_prints_version_and_exits_successfully(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            with self.assertRaisesRegex(SystemExit, "0"):
                main(["--version"])

        self.assertEqual(
            stdout.getvalue(), f"diagrams-cli {__version__}\n"
        )


if __name__ == "__main__":
    unittest.main()
