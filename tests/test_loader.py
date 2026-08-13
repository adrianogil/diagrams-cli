"""Tests for JSON loading and diagram schema validation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from diagrams_cli.errors import DiagramLoadError, DiagramValidationError
from diagrams_cli.loader import load_diagram, loads_diagram
from diagrams_cli.model import Diagram, Edge, Group, Node, Swimlane


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
        self.assertEqual(diagram.groups, ())
        self.assertEqual(diagram.swimlanes, ())

    def test_loads_groups_and_swimlanes_in_declared_order(self) -> None:
        diagram = loads_diagram(
            """
            {
              "nodes": [
                {"id": "a", "label": "A"},
                {"id": "b", "label": "B"}
              ],
              "groups": [
                {"id": "g", "label": "Services", "members": ["a", "b"]}
              ],
              "swimlanes": [
                {"id": "l", "label": "Cloud", "members": ["a", "b"]}
              ]
            }
            """
        )

        self.assertEqual(diagram.groups, (Group("g", "Services", ("a", "b")),))
        self.assertEqual(diagram.swimlanes, (Swimlane("l", "Cloud", ("a", "b")),))

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

    def test_rejects_duplicate_boundary_ids_across_types(self) -> None:
        content = """
        {
          "nodes": [{"id": "a", "label": "A"}],
          "groups": [{"id": "boundary", "label": "G", "members": ["a"]}],
          "swimlanes": [{"id": "boundary", "label": "L", "members": ["a"]}]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError, 'duplicates boundary id "boundary"'
        ):
            loads_diagram(content)

    def test_rejects_duplicate_member_within_boundary(self) -> None:
        content = """
        {
          "nodes": [{"id": "a", "label": "A"}],
          "groups": [
            {"id": "g", "label": "Group", "members": ["a", "a"]}
          ]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'document.groups\[0\].members\[1\] duplicates node "a"',
        ):
            loads_diagram(content)

    def test_rejects_dangling_boundary_member(self) -> None:
        content = """
        {
          "nodes": [{"id": "a", "label": "A"}],
          "swimlanes": [
            {"id": "lane", "label": "Lane", "members": ["missing"]}
          ]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'document.swimlanes\[0\].members\[0\] references unknown node "missing"',
        ):
            loads_diagram(content)

    def test_rejects_node_assigned_to_multiple_groups(self) -> None:
        content = """
        {
          "nodes": [{"id": "a", "label": "A"}],
          "groups": [
            {"id": "first", "label": "First", "members": ["a"]},
            {"id": "second", "label": "Second", "members": ["a"]}
          ]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'assigns node "a" to multiple groups: "first" and "second"',
        ):
            loads_diagram(content)

    def test_rejects_node_assigned_to_multiple_swimlanes(self) -> None:
        content = """
        {
          "nodes": [{"id": "a", "label": "A"}],
          "swimlanes": [
            {"id": "first", "label": "First", "members": ["a"]},
            {"id": "second", "label": "Second", "members": ["a"]}
          ]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'assigns node "a" to multiple swimlanes: "first" and "second"',
        ):
            loads_diagram(content)

    def test_rejects_group_spanning_swimlanes(self) -> None:
        content = """
        {
          "nodes": [
            {"id": "a", "label": "A"},
            {"id": "b", "label": "B"}
          ],
          "groups": [
            {"id": "g", "label": "Group", "members": ["a", "b"]}
          ],
          "swimlanes": [
            {"id": "one", "label": "One", "members": ["a"]},
            {"id": "two", "label": "Two", "members": ["b"]}
          ]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'boundary "g" spans multiple swimlanes: "one", "two"',
        ):
            loads_diagram(content)

    def test_rejects_implicit_partial_group_nesting(self) -> None:
        content = """
        {
          "nodes": [
            {"id": "a", "label": "A"},
            {"id": "b", "label": "B"}
          ],
          "groups": [
            {"id": "g", "label": "Group", "members": ["a", "b"]}
          ],
          "swimlanes": [
            {"id": "one", "label": "One", "members": ["a"]}
          ]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'boundary "g" spans multiple swimlanes: no swimlane, "one"',
        ):
            loads_diagram(content)

    def test_rejects_nested_boundary_objects(self) -> None:
        content = """
        {
          "nodes": [{"id": "a", "label": "A"}],
          "groups": [
            {"id": "outer", "label": "Outer", "members": [
              {"id": "inner", "members": ["a"]}
            ]}
          ]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError,
            r'document.groups\[0\].members\[0\] must be a non-empty string',
        ):
            loads_diagram(content)

    def test_rejects_empty_boundary_members(self) -> None:
        content = """
        {
          "nodes": [],
          "groups": [{"id": "g", "label": "Group", "members": []}]
        }
        """

        with self.assertRaisesRegex(
            DiagramValidationError, "members must contain at least one node id"
        ):
            loads_diagram(content)


if __name__ == "__main__":
    unittest.main()
