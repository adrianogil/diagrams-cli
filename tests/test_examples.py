"""Regression tests for the documented JSON examples."""

from __future__ import annotations

import unittest
from pathlib import Path

from diagrams_cli.loader import load_diagram
from diagrams_cli.renderers import render_plantuml


class ExampleTests(unittest.TestCase):
    def test_all_ten_examples_are_valid_and_increase_in_size(self) -> None:
        examples_directory = Path(__file__).parents[1] / "examples"
        examples = sorted(examples_directory.glob("*.json"))

        self.assertEqual(len(examples), 10)

        previous_size = (-1, -1)
        for example in examples:
            with self.subTest(example=example.name):
                diagram = load_diagram(example)
                size = (len(diagram.nodes), len(diagram.edges))
                self.assertGreater(size, previous_size)
                previous_size = size

    def test_every_example_matches_its_plantuml_golden_file(self) -> None:
        examples_directory = Path(__file__).parents[1] / "examples"
        examples = sorted(examples_directory.glob("*.json"))
        golden_directory = examples_directory / "plantuml"
        golden_files = sorted(golden_directory.glob("*.puml"))

        self.assertEqual(len(golden_files), len(examples))

        for example in examples:
            with self.subTest(example=example.name):
                expected_path = golden_directory / f"{example.stem}.puml"
                expected = expected_path.read_text(encoding="utf-8")
                self.assertEqual(
                    render_plantuml(load_diagram(example)), expected
                )


if __name__ == "__main__":
    unittest.main()
