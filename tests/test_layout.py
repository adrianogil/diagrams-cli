"""Tests for deterministic layered diagram layout."""

from __future__ import annotations

import unittest

from diagrams_cli.layout import layout_diagram
from diagrams_cli.model import Diagram, Edge, Group, Node, Swimlane


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

    def test_groups_are_contained_by_their_shared_swimlane(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B"), Node("c", "C")),
            edges=(Edge("a", "b"), Edge("b", "c")),
            direction="left-to-right",
            groups=(Group("services", "Services", ("a", "b")),),
            swimlanes=(Swimlane("cloud", "Cloud", ("a", "b", "c")),),
        )

        layout = layout_diagram(diagram)
        group = layout.groups[0]
        lane = layout.swimlanes[0]
        placements = {item.node.id: item for item in layout.placements}

        self.assertEqual(group.swimlane_id, "cloud")
        self.assertGreaterEqual(group.x, lane.x)
        self.assertGreaterEqual(group.y, lane.y)
        self.assertLessEqual(group.x + group.width, lane.x + lane.width)
        self.assertLessEqual(group.y + group.height, lane.y + lane.height)
        for node_id in ("a", "b"):
            node = placements[node_id]
            self.assertGreaterEqual(node.x, group.x)
            self.assertGreaterEqual(node.y, group.y)
            self.assertLessEqual(node.x + node.width, group.x + group.width)
            self.assertLessEqual(node.y + node.height, group.y + group.height)

    def test_swimlanes_are_parallel_non_overlapping_bands(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B")),
            direction="left-to-right",
            swimlanes=(
                Swimlane("one", "One", ("a",)),
                Swimlane("two", "Two", ("b",)),
            ),
        )

        first, second = layout_diagram(diagram).swimlanes

        self.assertEqual(first.x, second.x)
        self.assertEqual(first.width, second.width)
        self.assertLessEqual(first.y + first.height, second.y)

    def test_top_to_bottom_swimlanes_are_parallel_columns(self) -> None:
        diagram = Diagram(
            nodes=(Node("a", "A"), Node("b", "B")),
            swimlanes=(
                Swimlane("one", "One", ("a",)),
                Swimlane("two", "Two", ("b",)),
            ),
        )

        first, second = layout_diagram(diagram).swimlanes

        self.assertEqual(first.y, second.y)
        self.assertEqual(first.height, second.height)
        self.assertLessEqual(first.x + first.width, second.x)

    def test_grouped_nodes_and_sibling_boundaries_do_not_overlap(self) -> None:
        diagram = Diagram(
            nodes=tuple(Node(str(index), str(index)) for index in range(6)),
            groups=(
                Group("first", "First", ("0", "1")),
                Group("second", "Second", ("2", "3")),
            ),
            swimlanes=(
                Swimlane("lane-a", "Lane A", ("0", "1", "2", "3")),
                Swimlane("lane-b", "Lane B", ("4", "5")),
            ),
            direction="left-to-right",
        )

        layout = layout_diagram(diagram)

        for index, first in enumerate(layout.placements):
            for second in layout.placements[index + 1 :]:
                self.assertTrue(_separated(first, second))
        self.assertTrue(_separated(layout.groups[0], layout.groups[1]))
        self.assertTrue(_separated(layout.swimlanes[0], layout.swimlanes[1]))
        self.assertEqual(layout, layout_diagram(diagram))


def _separated(first: object, second: object) -> bool:
    return (
        first.x + first.width <= second.x
        or second.x + second.width <= first.x
        or first.y + first.height <= second.y
        or second.y + second.height <= first.y
    )


if __name__ == "__main__":
    unittest.main()
