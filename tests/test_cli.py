"""Tests for the diagrams-cli command-line interface."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

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

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            source.write_text('{"nodes": []}', encoding="utf-8")

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [str(source), "--format", "excalidraw"]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue(),
            f"Placeholder: would generate excalidraw from {source}\n",
        )

    def test_missing_source_reports_cli_error(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "missing.json")

            with contextlib.redirect_stderr(stderr):
                with self.assertRaisesRegex(SystemExit, "2"):
                    main([str(source)])

        message = stderr.getvalue()
        self.assertIn(f"input file does not exist: {source}", message)
        self.assertNotIn("Traceback", message)

    def test_directory_source_reports_cli_error(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stderr(stderr):
                with self.assertRaisesRegex(SystemExit, "2"):
                    main([directory])

        message = stderr.getvalue()
        self.assertIn(f"input path is not a file: {directory}", message)
        self.assertNotIn("Traceback", message)

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

    def test_invalid_json_reports_input_error(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            source.write_text("{", encoding="utf-8")

            with contextlib.redirect_stderr(stderr):
                exit_code = main([str(source)])

        self.assertEqual(exit_code, 1)
        self.assertIn("invalid JSON", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_invalid_schema_reports_validation_error(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            source.write_text('{"edges": []}', encoding="utf-8")

            with contextlib.redirect_stderr(stderr):
                exit_code = main([str(source)])

        self.assertEqual(exit_code, 1)
        self.assertIn("document.nodes is required", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
