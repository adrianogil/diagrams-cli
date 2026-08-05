"""End-to-end tests for built and installed command-line entry points."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
import venv
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLES_DIRECTORY = PROJECT_ROOT / "examples"


class InstalledCliTests(unittest.TestCase):
    """Exercise the wheel through its installed script and module entry point."""

    installation_directory: Path
    temporary_directory: tempfile.TemporaryDirectory[str]
    venv_python: Path
    console_script: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        temporary_root = Path(cls.temporary_directory.name)
        wheel_directory = temporary_root / "wheel"
        environment_directory = temporary_root / "venv"
        wheel_directory.mkdir()

        try:
            cls._run_setup_command(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    str(PROJECT_ROOT),
                    "--no-deps",
                    "--no-build-isolation",
                    "--wheel-dir",
                    str(wheel_directory),
                ]
            )
            wheels = list(wheel_directory.glob("diagrams_cli-*.whl"))
            if len(wheels) != 1:
                raise RuntimeError(
                    f"expected one diagrams-cli wheel, found {len(wheels)}"
                )

            venv.EnvBuilder(with_pip=True).create(environment_directory)
            scripts_directory = (
                environment_directory / "Scripts"
                if os.name == "nt"
                else environment_directory / "bin"
            )
            cls.venv_python = scripts_directory / (
                "python.exe" if os.name == "nt" else "python"
            )
            cls.console_script = scripts_directory / (
                "diagrams-cli.exe" if os.name == "nt" else "diagrams-cli"
            )
            cls._run_setup_command(
                [
                    str(cls.venv_python),
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    str(wheels[0]),
                ]
            )
            cls.installation_directory = temporary_root / "runs"
            cls.installation_directory.mkdir()
        except Exception:
            cls.temporary_directory.cleanup()
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    @classmethod
    def _run_setup_command(cls, command: List[str]) -> None:
        result = subprocess.run(
            command,
            cwd=cls.temporary_directory.name,
            env=cls._isolated_environment(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"setup command failed ({result.returncode}): "
                f"{' '.join(command)}\nstdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

    @staticmethod
    def _isolated_environment() -> dict[str, str]:
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"
        return environment

    def _run_console(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return self._run([str(self.console_script), *arguments])

    def _run_module(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return self._run(
            [str(self.venv_python), "-m", "diagrams_cli", *arguments]
        )

    def _run(
        self,
        command: List[str],
        *,
        cwd: Optional[Path] = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd or self.installation_directory,
            env=self._isolated_environment(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_installed_console_script_matches_all_plantuml_goldens(self) -> None:
        for source in sorted(EXAMPLES_DIRECTORY.glob("*.json")):
            with self.subTest(source=source.name):
                expected = (
                    EXAMPLES_DIRECTORY
                    / "plantuml"
                    / f"{source.stem}.puml"
                ).read_text(encoding="utf-8")

                result = self._run_console(str(source), "--format", "plantuml")

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.stderr, "")

    def test_installed_module_matches_all_excalidraw_goldens(self) -> None:
        for source in sorted(EXAMPLES_DIRECTORY.glob("*.json")):
            with self.subTest(source=source.name):
                expected = (
                    EXAMPLES_DIRECTORY
                    / "excalidraw"
                    / f"{source.stem}.excalidraw"
                ).read_text(encoding="utf-8")

                result = self._run_module(str(source), "--format", "excalidraw")

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.stderr, "")

    def test_installed_console_generates_mermaid(self) -> None:
        source = EXAMPLES_DIRECTORY / "01-empty-diagram.json"

        result = self._run_console(str(source), "--format", "mermaid")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "flowchart TD\n")
        self.assertEqual(result.stderr, "")

    def test_both_installed_entry_points_write_golden_files(self) -> None:
        source = EXAMPLES_DIRECTORY / "04-database-flow.json"
        cases = (
            (self._run_console, "plantuml", ".puml"),
            (self._run_module, "excalidraw", ".excalidraw"),
        )

        for run_command, output_format, extension in cases:
            with self.subTest(entry_point=run_command.__name__):
                destination = (
                    self.installation_directory
                    / f"{run_command.__name__}{extension}"
                )
                expected = (
                    EXAMPLES_DIRECTORY
                    / output_format
                    / f"{source.stem}{extension}"
                ).read_text(encoding="utf-8")

                result = run_command(
                    str(source),
                    "--format",
                    output_format,
                    "--output",
                    str(destination),
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")
                self.assertEqual(destination.read_text(encoding="utf-8"), expected)

    def test_installed_console_preserves_existing_output_until_forced(self) -> None:
        source = EXAMPLES_DIRECTORY / "02-single-node.json"
        destination = self.installation_directory / "protected.puml"
        destination.write_text("original", encoding="utf-8")

        refused = self._run_console(str(source), "--output", str(destination))

        self.assertEqual(refused.returncode, 1)
        self.assertEqual(destination.read_text(encoding="utf-8"), "original")
        self.assertIn("use --force to overwrite", refused.stderr)
        self.assertNotIn("Traceback", refused.stderr)

        forced = self._run_console(
            str(source), "--output", str(destination), "--force"
        )
        expected = (
            EXAMPLES_DIRECTORY / "plantuml" / "02-single-node.puml"
        ).read_text(encoding="utf-8")

        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertEqual(destination.read_text(encoding="utf-8"), expected)

    def test_installed_module_reports_input_and_output_errors(self) -> None:
        invalid_source = self.installation_directory / "invalid.json"
        invalid_source.write_text("{", encoding="utf-8")

        invalid_json = self._run_module(str(invalid_source))

        self.assertEqual(invalid_json.returncode, 1)
        self.assertIn("invalid JSON", invalid_json.stderr)
        self.assertNotIn("Traceback", invalid_json.stderr)

        valid_source = EXAMPLES_DIRECTORY / "01-empty-diagram.json"
        wrong_extension = self._run_module(
            str(valid_source), "--output", "diagram.txt"
        )

        self.assertEqual(wrong_extension.returncode, 1)
        self.assertIn("must use the .puml extension", wrong_extension.stderr)
        self.assertNotIn("Traceback", wrong_extension.stderr)

    def test_help_and_version_work_from_both_installed_entry_points(self) -> None:
        for run_command in (self._run_console, self._run_module):
            with self.subTest(entry_point=run_command.__name__):
                help_result = run_command("--help")
                version_result = run_command("--version")

                self.assertEqual(help_result.returncode, 0, help_result.stderr)
                self.assertIn("usage: diagrams-cli", help_result.stdout)
                self.assertEqual(version_result.returncode, 0, version_result.stderr)
                self.assertEqual(version_result.stdout, "diagrams-cli 0.1.0\n")


if __name__ == "__main__":
    unittest.main()
