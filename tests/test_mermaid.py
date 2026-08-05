"""Tests for deterministic Mermaid flowchart generation."""

from __future__ import annotations

import unittest

from diagrams_cli.model import Diagram, Edge, Node
from diagrams_cli.renderers import Renderer, render_mermaid


class MermaidRendererTests(unittest.TestCase):
    def test_render_function_implements_common_renderer_interface(self) -> None:
        renderer: Renderer = render_mermaid

        self.assertEqual(renderer(Diagram(nodes=())), "flowchart TD\n")

    def test_maps_every_portable_node_type(self) -> None:
        diagram = Diagram(
            title="System",
            direction="left-to-right",
            nodes=(
                Node("user", "User", "actor"),
                Node("api", "API", "service"),
                Node("db", "Database", "database"),
                Node("jobs", "Jobs", "queue"),
                Node("note", "Note", "generic"),
            ),
            edges=(
                Edge("user", "api", "Request"),
                Edge("api", "db"),
            ),
        )

        self.assertEqual(
            render_mermaid(diagram),
            "---\n"
            'title: "System"\n'
            "---\n"
            "flowchart LR\n"
            '    node_1(["User"])\n'
            '    node_2["API"]\n'
            '    node_3[("Database")]\n'
            '    node_4[["Jobs"]]\n'
            '    node_5["Note"]\n'
            "\n"
            '    node_1 -->|"Request"| node_2\n'
            "    node_2 --> node_3\n",
        )

    def test_escapes_labels_and_never_uses_source_ids_as_aliases(self) -> None:
        unsafe_id = 'unsafe"]\nclick node callback'
        diagram = Diagram(
            title='A: "quoted" title',
            nodes=(Node(unsafe_id, 'A "quoted"\n<script>|`'),),
            edges=(Edge(unsafe_id, unsafe_id, "Retry\n| stop"),),
        )

        rendered = render_mermaid(diagram)

        self.assertIn('title: "A: \\"quoted\\" title"', rendered)
        self.assertIn(
            'node_1["A &quot;quoted&quot;<br/>&lt;script&gt;&#124;&#96;"]',
            rendered,
        )
        self.assertIn(
            'node_1 -->|"Retry<br/>&#124; stop"| node_1', rendered
        )
        self.assertNotIn("unsafe", rendered)
        self.assertNotIn("\nclick", rendered)

    def test_rendering_is_deterministic(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B")),
            edges=(Edge("a", "b", "calls"),),
        )

        self.assertEqual(render_mermaid(diagram), render_mermaid(diagram))


if __name__ == "__main__":
    unittest.main()
