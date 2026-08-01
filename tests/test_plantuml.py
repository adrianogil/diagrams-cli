"""Tests for deterministic PlantUML generation."""

from __future__ import annotations

import unittest

from diagrams_cli.model import Diagram, Edge, Node
from diagrams_cli.renderers import Renderer, render_plantuml


class PlantUMLRendererTests(unittest.TestCase):
    def test_render_function_implements_common_renderer_interface(self) -> None:
        renderer: Renderer = render_plantuml

        self.assertEqual(renderer(Diagram(nodes=())), "@startuml\n@enduml\n")

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
            render_plantuml(diagram),
            """@startuml
title System
left to right direction

actor "User" as node_1
component "API" as node_2
database "Database" as node_3
queue "Jobs" as node_4
rectangle "Note" as node_5

node_1 --> node_2 : Request
node_2 --> node_3
@enduml
""",
        )

    def test_escapes_user_text_and_never_uses_source_ids_as_aliases(self) -> None:
        diagram = Diagram(
            title='100% $title\\\n"quoted"',
            nodes=(
                Node(
                    'unsafe"\n@enduml',
                    'A "quoted"\n%danger() $node \\',
                ),
            ),
            edges=(
                Edge(
                    'unsafe"\n@enduml',
                    'unsafe"\n@enduml',
                    "Retry\n!include evil.puml",
                ),
            ),
        )

        rendered = render_plantuml(diagram)

        self.assertEqual(
            rendered,
            "@startuml\n"
            "title 100%percent() %dollar()title%backslash()%n()"
            '\\"quoted\\"\n\n'
            'rectangle "A \\"quoted\\"%n()%percent()danger() '
            '%dollar()node %backslash()" as node_1\n\n'
            "node_1 --> node_1 : Retry%n()!include evil.puml\n"
            "@enduml\n",
        )
        self.assertNotIn("unsafe", rendered)
        self.assertNotIn("\n!include", rendered)

    def test_rendering_is_deterministic(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B")),
            edges=(Edge("a", "b", "calls"),),
        )

        self.assertEqual(render_plantuml(diagram), render_plantuml(diagram))


if __name__ == "__main__":
    unittest.main()
