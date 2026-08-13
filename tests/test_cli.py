"""Tests for the diagrams-cli command-line interface."""

from __future__ import annotations

import contextlib
import io
import json
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
        self.assertIsNone(args.output)
        self.assertFalse(args.force)

    def test_parses_input_with_explicit_output_format(self) -> None:
        args = build_parser().parse_args(
            ["diagram.json", "--format", "excalidraw"]
        )

        self.assertEqual(args.input, "diagram.json")
        self.assertEqual(args.format, "excalidraw")

        mermaid_args = build_parser().parse_args(
            ["diagram.json", "--format", "mermaid"]
        )
        self.assertEqual(mermaid_args.format, "mermaid")

    def test_parses_output_and_force_arguments(self) -> None:
        args = build_parser().parse_args(
            ["diagram.json", "-o", "diagram.puml", "--force"]
        )

        self.assertEqual(args.output, "diagram.puml")
        self.assertTrue(args.force)

    def test_rejects_invalid_output_format(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaisesRegex(SystemExit, "2"):
                build_parser().parse_args(
                    ["diagram.json", "--format", "svg"]
                )

        message = stderr.getvalue()
        self.assertIn("invalid choice: 'svg'", message)
        self.assertIn(
            "choose from 'plantuml', 'excalidraw', 'mermaid'", message
        )


class MainTests(unittest.TestCase):
    def test_excalidraw_arguments_render_json_to_stdout(self) -> None:
        stdout = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            source.write_text('{"nodes": []}', encoding="utf-8")

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [str(source), "--format", "excalidraw"]
                )

        self.assertEqual(exit_code, 0)
        document = json.loads(stdout.getvalue())
        self.assertEqual(document["type"], "excalidraw")
        self.assertEqual(document["elements"], [])

    def test_plantuml_arguments_render_to_stdout(self) -> None:
        stdout = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            source.write_text(
                """
                {
                  "nodes": [
                    {"id": "user", "label": "User", "type": "actor"},
                    {"id": "api", "label": "API", "type": "service"}
                  ],
                  "edges": [{"from": "user", "to": "api"}]
                }
                """,
                encoding="utf-8",
            )

            with contextlib.redirect_stdout(stdout):
                exit_code = main([str(source)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue(),
            """@startuml
actor "User" as node_1
component "API" as node_2

node_1 --> node_2
@enduml
""",
        )

    def test_mermaid_arguments_render_to_stdout(self) -> None:
        stdout = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            source.write_text(
                '{"nodes": [{"id": "api", "label": "API"}]}',
                encoding="utf-8",
            )

            with contextlib.redirect_stdout(stdout):
                exit_code = main([str(source), "--format", "mermaid"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), 'flowchart TD\n    node_1["API"]\n')

    def test_grouped_input_renders_boundaries_in_every_format(self) -> None:
        content = """
        {
          "nodes": [{"id": "api", "label": "API", "type": "service"}],
          "groups": [
            {"id": "services", "label": "Services", "members": ["api"]}
          ],
          "swimlanes": [
            {"id": "cloud", "label": "Cloud", "members": ["api"]}
          ]
        }
        """
        expectations = {
            "plantuml": 'frame "Cloud" as swimlane_1',
            "mermaid": 'subgraph swimlane_1["Cloud"]',
            "excalidraw": '"id": "swimlane-1-boundary"',
        }

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            source.write_text(content, encoding="utf-8")
            for output_format, expected in expectations.items():
                with self.subTest(output_format=output_format):
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        exit_code = main(
                            [str(source), "--format", output_format]
                        )

                    self.assertEqual(exit_code, 0)
                    self.assertIn(expected, stdout.getvalue())

    def test_mermaid_output_argument_writes_mmd_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            destination = Path(directory, "diagram.mmd")
            source.write_text('{"nodes": []}', encoding="utf-8")

            exit_code = main(
                [
                    str(source),
                    "--format",
                    "mermaid",
                    "--output",
                    str(destination),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "flowchart TD\n",
            )

    def test_plantuml_output_argument_writes_file_without_stdout(self) -> None:
        stdout = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            destination = Path(directory, "diagram.puml")
            source.write_text('{"nodes": []}', encoding="utf-8")

            with contextlib.redirect_stdout(stdout):
                exit_code = main([str(source), "-o", str(destination)])

            generated = destination.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(generated, "@startuml\n@enduml\n")

    def test_existing_output_is_preserved_without_force(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            destination = Path(directory, "diagram.puml")
            source.write_text('{"nodes": []}', encoding="utf-8")
            destination.write_text("original", encoding="utf-8")

            with contextlib.redirect_stderr(stderr):
                exit_code = main([str(source), "-o", str(destination)])

            preserved = destination.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(preserved, "original")
        self.assertIn("use --force to overwrite", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_force_overwrites_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            destination = Path(directory, "diagram.puml")
            source.write_text('{"nodes": []}', encoding="utf-8")
            destination.write_text("original", encoding="utf-8")

            exit_code = main(
                [str(source), "-o", str(destination), "--force"]
            )
            generated = destination.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(generated, "@startuml\n@enduml\n")

    def test_wrong_output_extension_reports_error(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            destination = Path(directory, "diagram.txt")
            source.write_text('{"nodes": []}', encoding="utf-8")

            with contextlib.redirect_stderr(stderr):
                exit_code = main([str(source), "-o", str(destination)])

        self.assertEqual(exit_code, 1)
        self.assertFalse(destination.exists())
        self.assertIn("must use the .puml extension", stderr.getvalue())

    def test_excalidraw_output_argument_writes_generated_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            destination = Path(directory, "diagram.excalidraw")
            source.write_text('{"nodes": []}', encoding="utf-8")

            exit_code = main(
                [
                    str(source),
                    "--format",
                    "excalidraw",
                    "-o",
                    str(destination),
                ]
            )
            document = json.loads(destination.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(document["type"], "excalidraw")

    def test_force_without_output_reports_argument_error(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaisesRegex(SystemExit, "2"):
                main(["diagram.json", "--force"])

        self.assertIn("--force requires --output", stderr.getvalue())

    def test_missing_output_directory_reports_error(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "source.json")
            destination = Path(directory, "missing", "diagram.puml")
            source.write_text('{"nodes": []}', encoding="utf-8")

            with contextlib.redirect_stderr(stderr):
                exit_code = main([str(source), "-o", str(destination)])

        self.assertEqual(exit_code, 1)
        self.assertIn("output directory does not exist", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

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
            "Generate PlantUML, Excalidraw, or Mermaid from JSON.", help_text
        )
        self.assertIn("--output", help_text)
        self.assertIn("--force", help_text)

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
