"""Tests for format-aware output file handling."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from diagrams_cli.errors import DiagramOutputError
from diagrams_cli.output import validate_output_path, write_output_file


class ValidateOutputPathTests(unittest.TestCase):
    def test_accepts_format_specific_extensions_case_insensitively(self) -> None:
        self.assertEqual(
            validate_output_path("diagram.PUML", "plantuml"),
            Path("diagram.PUML"),
        )
        self.assertEqual(
            validate_output_path("diagram.EXCALIDRAW", "excalidraw"),
            Path("diagram.EXCALIDRAW"),
        )
        self.assertEqual(
            validate_output_path("diagram.MMD", "mermaid"),
            Path("diagram.MMD"),
        )

    def test_rejects_wrong_plantuml_extension(self) -> None:
        with self.assertRaisesRegex(
            DiagramOutputError,
            r"plantuml output path must use the \.puml extension",
        ):
            validate_output_path("diagram.txt", "plantuml")

    def test_rejects_wrong_excalidraw_extension(self) -> None:
        with self.assertRaisesRegex(
            DiagramOutputError,
            r"excalidraw output path must use the \.excalidraw extension",
        ):
            validate_output_path("diagram.puml", "excalidraw")

    def test_rejects_wrong_mermaid_extension(self) -> None:
        with self.assertRaisesRegex(
            DiagramOutputError,
            r"mermaid output path must use the \.mmd extension",
        ):
            validate_output_path("diagram.puml", "mermaid")

    def test_rejects_an_unsupported_output_format(self) -> None:
        with self.assertRaisesRegex(
            DiagramOutputError, "unsupported output format: svg"
        ):
            validate_output_path("diagram.svg", "svg")


class WriteOutputFileTests(unittest.TestCase):
    def test_creates_a_new_utf8_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory, "diagram.puml")

            result = write_output_file(
                "@startuml\n' café\n@enduml\n",
                destination,
                "plantuml",
            )

            self.assertEqual(result, destination)
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "@startuml\n' café\n@enduml\n",
            )

    def test_refuses_to_overwrite_an_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory, "diagram.puml")
            destination.write_text("keep me", encoding="utf-8")

            with self.assertRaisesRegex(
                DiagramOutputError, "output file already exists"
            ):
                write_output_file("replacement", destination, "plantuml")

            self.assertEqual(
                destination.read_text(encoding="utf-8"), "keep me"
            )

    def test_force_overwrites_an_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory, "diagram.puml")
            destination.write_text("old", encoding="utf-8")

            write_output_file(
                "new\n", destination, "plantuml", force=True
            )

            self.assertEqual(destination.read_text(encoding="utf-8"), "new\n")

    def test_rejects_a_directory_output_path(self) -> None:
        with tempfile.TemporaryDirectory(suffix=".puml") as directory:
            with self.assertRaisesRegex(
                DiagramOutputError, "output path is a directory"
            ):
                write_output_file("content", directory, "plantuml")

    def test_reports_a_missing_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory, "missing", "diagram.puml")

            with self.assertRaisesRegex(
                DiagramOutputError, "output directory does not exist"
            ):
                write_output_file("content", destination, "plantuml")


if __name__ == "__main__":
    unittest.main()
