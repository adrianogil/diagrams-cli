"""Tests for deterministic layered diagram layout."""

from __future__ import annotations

import unittest

from diagrams_cli.layout import layout_diagram
from diagrams_cli.model import Diagram, Edge, Node


class LayeredLayoutTests(unittest.TestCase):
    def test_left_to_right_places_successive_depths_on_x_axis(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B"), Node("c", "C")),
            edges=(Edge("a", "b"), Edge("b", "c")),
            direction="left-to-right",
        )

        placements = layout_diagram(diagram).placements

        self.assertEqual([item.layer for item in placements], [0, 1, 2])
        self.assertLess(placements[0].x, placements[1].x)
        self.assertLess(placements[1].x, placements[2].x)
        self.assertEqual(len({item.y for item in placements}), 1)

    def test_top_to_bottom_places_successive_depths_on_y_axis(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B"), Node("c", "C")),
            edges=(Edge("a", "b"), Edge("b", "c")),
        )

        placements = layout_diagram(diagram).placements

        self.assertLess(placements[0].y, placements[1].y)
        self.assertLess(placements[1].y, placements[2].y)
        self.assertEqual(len({item.x for item in placements}), 1)

    def test_disconnected_nodes_share_first_layer_in_input_order(self) -> None:
        diagram = Diagram(
            nodes=(Node("first", "First"), Node("second", "Second")),
            direction="left-to-right",
        )

        placements = layout_diagram(diagram).placements

        self.assertEqual(
            [item.node.id for item in placements], ["first", "second"]
        )
        self.assertEqual([item.layer for item in placements], [0, 0])
        self.assertLess(placements[0].y, placements[1].y)

    def test_cycle_members_share_a_layer_and_successor_advances(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B"), Node("c", "C")),
            edges=(Edge("a", "b"), Edge("b", "a"), Edge("b", "c")),
        )

        placements = layout_diagram(diagram).placements
        layers = {item.node.id: item.layer for item in placements}

        self.assertEqual(layers["a"], layers["b"])
        self.assertEqual(layers["c"], layers["a"] + 1)

    def test_nodes_never_overlap_in_mixed_fixture(self) -> None:
        diagram = Diagram(
            nodes=tuple(Node(str(index), str(index)) for index in range(6)),
            edges=(Edge("0", "2"), Edge("1", "2"), Edge("2", "3")),
        )

        placements = layout_diagram(diagram).placements

        for index, first in enumerate(placements):
            for second in placements[index + 1 :]:
                separated = (
                    first.x + first.width <= second.x
                    or second.x + second.width <= first.x
                    or first.y + first.height <= second.y
                    or second.y + second.height <= first.y
                )
                self.assertTrue(
                    separated,
                    f"{first.node.id} overlaps {second.node.id}",
                )

    def test_repeated_layouts_are_equal(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B")),
            edges=(Edge("a", "b"),),
        )

        self.assertEqual(layout_diagram(diagram), layout_diagram(diagram))


if __name__ == "__main__":
    unittest.main()
