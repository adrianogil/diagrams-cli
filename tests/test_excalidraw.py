"""Tests for deterministic Excalidraw rendering."""

from __future__ import annotations

import json
import unittest

from diagrams_cli.model import Diagram, Edge, Group, Node, Swimlane
from diagrams_cli.renderers import Renderer, render_excalidraw


class ExcalidrawRendererTests(unittest.TestCase):
    def test_renderer_matches_common_interface(self) -> None:
        renderer: Renderer = render_excalidraw

        self.assertIs(renderer, render_excalidraw)

    def test_empty_diagram_has_required_document_metadata(self) -> None:
        document = json.loads(render_excalidraw(Diagram(nodes=())))

        self.assertEqual(document["type"], "excalidraw")
        self.assertEqual(document["version"], 2)
        self.assertEqual(document["source"], "diagrams-cli")
        self.assertEqual(document["elements"], [])
        self.assertEqual(
            document["appState"],
            {"gridSize": None, "viewBackgroundColor": "#ffffff"},
        )
        self.assertEqual(document["files"], {})

    def test_node_types_map_to_stable_shapes_and_colors(self) -> None:
        diagram = Diagram(
            nodes=(
                Node("actor", "Actor", "actor"),
                Node("service", "Service", "service"),
                Node("database", "Database", "database"),
                Node("queue", "Queue", "queue"),
                Node("generic", "Generic", "generic"),
            )
        )

        document = json.loads(render_excalidraw(diagram))
        shapes = [
            element
            for element in document["elements"]
            if element["id"].endswith("-shape")
        ]

        self.assertEqual(
            [shape["type"] for shape in shapes],
            ["ellipse", "rectangle", "ellipse", "diamond", "rectangle"],
        )
        self.assertEqual(
            [shape["backgroundColor"] for shape in shapes],
            ["#d0ebff", "#dbe4ff", "#d3f9d8", "#fff3bf", "#f1f3f5"],
        )

    def test_arrows_are_bound_and_labels_are_rendered(self) -> None:
        diagram = Diagram(
            nodes=(Node("source", "Source"), Node("target", "Target")),
            edges=(Edge("source", "target", "Calls"),),
            title="Bound graph",
            direction="left-to-right",
        )

        document = json.loads(render_excalidraw(diagram))
        elements = {element["id"]: element for element in document["elements"]}

        self.assertEqual(elements["diagram-title"]["text"], "Bound graph")
        self.assertEqual(
            elements["edge-1"]["startBinding"]["elementId"],
            "node-1-shape",
        )
        self.assertEqual(
            elements["edge-1"]["endBinding"]["elementId"],
            "node-2-shape",
        )
        self.assertIn(
            {"id": "edge-1", "type": "arrow"},
            elements["node-1-shape"]["boundElements"],
        )
        self.assertEqual(elements["edge-1-label"]["text"], "Calls")
        self.assertEqual(
            elements["node-1-label"]["containerId"], "node-1-shape"
        )

    def test_self_edge_has_visible_loop_geometry(self) -> None:
        diagram = Diagram(
            nodes=(Node("node", "Node"),),
            edges=(Edge("node", "node"),),
        )

        document = json.loads(render_excalidraw(diagram))
        arrow = next(
            element
            for element in document["elements"]
            if element["type"] == "arrow"
        )

        self.assertGreater(len(arrow["points"]), 2)
        self.assertGreater(arrow["width"], 0)
        self.assertGreater(arrow["height"], 0)

    def test_ids_seeds_versions_and_timestamps_are_deterministic(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B")),
            edges=(Edge("a", "b"),),
        )

        first = render_excalidraw(diagram)
        second = render_excalidraw(diagram)
        elements = json.loads(first)["elements"]

        self.assertEqual(first, second)
        self.assertEqual(
            [element["id"] for element in elements],
            [
                "edge-1",
                "node-1-shape",
                "node-1-label",
                "node-2-shape",
                "node-2-label",
            ],
        )
        self.assertTrue(all(element["updated"] == 1 for element in elements))
        self.assertTrue(all(element["version"] == 1 for element in elements))
        self.assertTrue(all(element["seed"] > 0 for element in elements))
        self.assertTrue(all(element["versionNonce"] > 0 for element in elements))
        self.assertTrue(first.endswith("\n"))

    def test_renders_readable_group_and_swimlane_boundaries(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B"), Node("c", "C")),
            edges=(Edge("a", "b"), Edge("b", "c")),
            groups=(Group("services", "Services", ("a", "b")),),
            swimlanes=(Swimlane("cloud", "Cloud", ("a", "b", "c")),),
            direction="left-to-right",
        )

        document = json.loads(render_excalidraw(diagram))
        elements = {element["id"]: element for element in document["elements"]}
        element_ids = [element["id"] for element in document["elements"]]
        lane = elements["swimlane-1-boundary"]
        group = elements["group-1-boundary"]

        self.assertLess(
            element_ids.index("swimlane-1-boundary"),
            element_ids.index("edge-1"),
        )
        self.assertLess(
            element_ids.index("group-1-boundary"),
            element_ids.index("node-1-shape"),
        )
        self.assertEqual(elements["swimlane-1-label"]["text"], "Cloud")
        self.assertEqual(elements["group-1-label"]["text"], "Services")
        self.assertEqual(group["strokeStyle"], "dashed")
        self.assertGreaterEqual(group["x"], lane["x"])
        self.assertGreaterEqual(group["y"], lane["y"])
        self.assertLessEqual(
            group["x"] + group["width"], lane["x"] + lane["width"]
        )
        self.assertLessEqual(
            group["y"] + group["height"], lane["y"] + lane["height"]
        )

    def test_boundary_text_is_preserved_as_json_data(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"),),
            groups=(Group("g", 'Group "one"\n<script>', ("a",)),),
        )

        document = json.loads(render_excalidraw(diagram))
        label = next(
            element
            for element in document["elements"]
            if element["id"] == "group-1-label"
        )

        self.assertEqual(label["text"], 'Group "one"\n<script>')


if __name__ == "__main__":
    unittest.main()
