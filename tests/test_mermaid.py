"""Tests for deterministic Mermaid flowchart generation."""

from __future__ import annotations

import unittest

from diagrams_cli.model import Diagram, Edge, Group, Node, Swimlane
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

    def test_renders_groups_nested_in_swimlanes(self) -> None:
        diagram = Diagram(
            nodes=(
                Node("api", "API", "service"),
                Node("db", "Database", "database"),
                Node("user", "User", "actor"),
            ),
            edges=(Edge("user", "api", "Calls"), Edge("api", "db")),
            groups=(Group("backend", "Backend", ("api", "db")),),
            swimlanes=(Swimlane("cloud", "Cloud", ("api", "db")),),
        )

        self.assertEqual(
            render_mermaid(diagram),
            """flowchart TD
    subgraph swimlane_1["Cloud"]
        direction TD
        subgraph group_1["Backend"]
            direction TD
            node_1["API"]
            node_2[("Database")]
        end
    end
    node_3(["User"])

    node_3 -->|"Calls"| node_1
    node_1 --> node_2
""",
        )

    def test_escapes_boundary_labels_and_hides_boundary_ids(self) -> None:
        diagram = Diagram(
            nodes=(Node("node", "Node"),),
            swimlanes=(
                Swimlane(
                    'unsafe"]\nend',
                    'Ops "Lane"\n|<team>',
                    ("node",),
                ),
            ),
        )

        rendered = render_mermaid(diagram)

        self.assertIn(
            'subgraph swimlane_1["Ops &quot;Lane&quot;<br/>'
            '&#124;&lt;team&gt;"]',
            rendered,
        )
        self.assertNotIn("unsafe", rendered)


if __name__ == "__main__":
    unittest.main()
