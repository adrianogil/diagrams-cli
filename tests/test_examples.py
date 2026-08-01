"""Regression tests for the documented JSON examples."""

from __future__ import annotations

import unittest
from pathlib import Path

from diagrams_cli.loader import load_diagram


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


if __name__ == "__main__":
    unittest.main()
