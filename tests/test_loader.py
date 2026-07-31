"""Tests for JSON loading and diagram schema validation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from diagrams_cli.errors import DiagramLoadError, DiagramValidationError
from diagrams_cli.loader import load_diagram, loads_diagram
from diagrams_cli.model import Diagram, Edge, Node


class LoadDiagramTests(unittest.TestCase):
    def test_loads_valid_diagram_file(self) -> None:
        content = """
        {
          "title": "Order Processing",
          "direction": "left-to-right",
          "nodes": [
            {"id": "client", "label": "Web Client", "type": "actor"},
            {"id": "api", "label": "Orders API", "type": "service"}
          ],
          "edges": [
            {"from": "client", "to": "api", "label": "POST /orders"}
          ]
        }
        """

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "diagram.json")
            source.write_text(content, encoding="utf-8")

            diagram = load_diagram(source)

        self.assertEqual(
            diagram,
            Diagram(
                title="Order Processing",
                direction="left-to-right",
                nodes=(
                    Node("client", "Web Client", "actor"),
                    Node("api", "Orders API", "service"),
                ),
                edges=(Edge("client", "api", "POST /orders"),),
            ),
        )

    def test_applies_optional_field_defaults(self) -> None:
        diagram = loads_diagram(
            '{"nodes": [{"id": "api", "label": "API"}]}'
        )

        self.assertIsNone(diagram.title)
        self.assertEqual(diagram.direction, "top-to-bottom")
        self.assertEqual(diagram.nodes, (Node("api", "API", "generic"),))
        self.assertEqual(diagram.edges, ())

    def test_reports_malformed_json_location(self) -> None:
        with self.assertRaisesRegex(
            DiagramLoadError,
            r"invalid JSON in example.json at line 1, column 12",
        ):
            loads_diagram('{"nodes": [}', source="example.json")

    def test_reports_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "missing.json")

            with self.assertRaisesRegex(
                DiagramLoadError, "input file does not exist"
            ):
                load_diagram(source)


class DiagramValidationTests(unittest.TestCase):
    def test_requires_an_object_document(self) -> None:
        with self.assertRaisesRegex(
            DiagramValidationError, "document must be an object"
        ):
            loads_diagram("[]")

    def test_requires_nodes(self) -> None:
        with self.assertRaisesRegex(
            DiagramValidationError, "document.nodes is required"
        ):
            loads_diagram("{}")

    def test_requires_nodes_to_be_an_array(self) -> None:
        with self.assertRaisesRegex(
            DiagramValidationError, "document.nodes must be an array"
        ):
            loads_diagram('{"nodes": {}}')

    def test_rejects_duplicate_node_ids(self) -> None:
        content = """
        {
          "nodes": [
            {"id": "api", "label": "First"},
            {"id": "api", "label": "Second"}
          ]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError, 'duplicates node id "api"'
        ):
            loads_diagram(content)

    def test_rejects_unsupported_node_type(self) -> None:
        content = """
        {"nodes": [{"id": "api", "label": "API", "type": "server"}]}
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r"document.nodes\[0\].type must be one of",
        ):
            loads_diagram(content)

    def test_rejects_edge_with_unknown_source(self) -> None:
        content = """
        {
          "nodes": [{"id": "api", "label": "API"}],
          "edges": [{"from": "client", "to": "api"}]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'document.edges\[0\].from references unknown node "client"',
        ):
            loads_diagram(content)

    def test_rejects_edge_with_unknown_target(self) -> None:
        content = """
        {
          "nodes": [{"id": "api", "label": "API"}],
          "edges": [{"from": "api", "to": "database"}]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'document.edges\[0\].to references unknown node "database"',
        ):
            loads_diagram(content)

    def test_rejects_unknown_fields(self) -> None:
        content = '{"nodes": [], "node": []}'

        with self.assertRaisesRegex(
            DiagramValidationError,
            r"document contains unknown field\(s\): node",
        ):
            loads_diagram(content)

    def test_rejects_invalid_direction(self) -> None:
        content = '{"nodes": [], "direction": "diagonal"}'

        with self.assertRaisesRegex(
            DiagramValidationError, "document.direction must be one of"
        ):
            loads_diagram(content)


if __name__ == "__main__":
    unittest.main()
