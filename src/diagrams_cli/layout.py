"""Deterministic layered layout for renderer-independent diagrams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from diagrams_cli.model import Diagram, Group, Node, Swimlane

NODE_WIDTH = 220
NODE_HEIGHT = 100
CANVAS_MARGIN = 100
TITLE_SPACE = 60
LAYER_GAP = 160
NODE_GAP = 80
BOUNDARY_GAP = 80
BOUNDARY_PADDING = 40
BOUNDARY_HEADER = 50


@dataclass(frozen=True)
class NodePlacement:
    """The size and canvas position assigned to one diagram node."""

    node: Node
    x: int
    y: int
    width: int
    height: int
    layer: int


@dataclass(frozen=True)
class GroupPlacement:
    """The bounding rectangle assigned to one architectural group."""

    group: Group
    x: int
    y: int
    width: int
    height: int
    swimlane_id: Optional[str] = None


@dataclass(frozen=True)
class SwimlanePlacement:
    """The bounding rectangle assigned to one responsibility swimlane."""

    swimlane: Swimlane
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class LayeredLayout:
    """An immutable, input-ordered collection of node placements."""

    placements: Tuple[NodePlacement, ...]
    groups: Tuple[GroupPlacement, ...] = ()
    swimlanes: Tuple[SwimlanePlacement, ...] = ()


def layout_diagram(diagram: Diagram) -> LayeredLayout:
    """Place nodes in stable graph-depth layers for the requested direction.

    Strongly connected nodes share one layer, turning the graph into a DAG
    before depth is calculated. Nodes within a layer retain input order.
    """
    if diagram.groups or diagram.swimlanes:
        return _layout_boundaries(diagram)
    return _layout_graph(diagram)


def _layout_graph(diagram: Diagram) -> LayeredLayout:
    if not diagram.nodes:
        return LayeredLayout(placements=())

    component_of, components = _strongly_connected_components(diagram)
    component_layers = _component_layers(diagram, component_of, components)
    node_layers = {
        node.id: component_layers[component_of[node.id]]
        for node in diagram.nodes
    }

    nodes_by_layer: Dict[int, List[Node]] = {}
    for node in diagram.nodes:
        nodes_by_layer.setdefault(node_layers[node.id], []).append(node)

    max_layer_size = max(len(nodes) for nodes in nodes_by_layer.values())
    cross_size = (
        NODE_HEIGHT
        if diagram.direction == "left-to-right"
        else NODE_WIDTH
    )
    cross_span = (
        max_layer_size * cross_size + (max_layer_size - 1) * NODE_GAP
    )
    primary_origin = CANVAS_MARGIN + (TITLE_SPACE if diagram.title else 0)

    coordinates: Dict[str, Tuple[int, int]] = {}
    for layer in sorted(nodes_by_layer):
        layer_nodes = nodes_by_layer[layer]
        layer_span = (
            len(layer_nodes) * cross_size
            + (len(layer_nodes) - 1) * NODE_GAP
        )
        cross_origin = CANVAS_MARGIN + (cross_span - layer_span) // 2

        for offset, node in enumerate(layer_nodes):
            cross_position = cross_origin + offset * (cross_size + NODE_GAP)
            if diagram.direction == "left-to-right":
                x = primary_origin + layer * (NODE_WIDTH + LAYER_GAP)
                y = cross_position
            else:
                x = cross_position
                y = primary_origin + layer * (NODE_HEIGHT + LAYER_GAP)
            coordinates[node.id] = (x, y)

    placements = tuple(
        NodePlacement(
            node=node,
            x=coordinates[node.id][0],
            y=coordinates[node.id][1],
            width=NODE_WIDTH,
            height=NODE_HEIGHT,
            layer=node_layers[node.id],
        )
        for node in diagram.nodes
    )
    return LayeredLayout(placements=placements)


@dataclass(frozen=True)
class _LayoutItem:
    kind: str
    item_id: str
    width: int
    height: int


def _layout_boundaries(diagram: Diagram) -> LayeredLayout:
    """Lay out flat lanes with optional, unambiguous nested groups."""
    graph_layout = _layout_graph(diagram)
    layers = {
        placement.node.id: placement.layer
        for placement in graph_layout.placements
    }
    groups = {group.id: group for group in diagram.groups}
    group_of = {
        member: group.id
        for group in diagram.groups
        for member in group.members
    }
    lane_of = {
        member: lane.id
        for lane in diagram.swimlanes
        for member in lane.members
    }
    group_lane = {
        group.id: lane_of.get(group.members[0]) for group in diagram.groups
    }

    node_coordinates: Dict[str, Tuple[int, int]] = {}
    group_coordinates: Dict[str, Tuple[int, int, int, int]] = {}
    lane_coordinates: Dict[str, Tuple[int, int, int, int]] = {}
    primary_origin = CANVAS_MARGIN + (TITLE_SPACE if diagram.title else 0)
    cross_cursor = CANVAS_MARGIN

    lane_specs: List[Tuple[Swimlane, List[_LayoutItem], int, int]] = []
    for lane in diagram.swimlanes:
        items = _boundary_items(
            lane.members,
            group_of,
            groups,
            allowed_lane=lane.id,
            group_lane=group_lane,
            direction=diagram.direction,
        )
        width, height = _container_size(
            items, diagram.direction, lane.label
        )
        lane_specs.append((lane, items, width, height))

    if lane_specs:
        maximum_primary = max(
            width if diagram.direction == "left-to-right" else height
            for _, _, width, height in lane_specs
        )
    else:
        maximum_primary = 0

    for lane, items, width, height in lane_specs:
        if diagram.direction == "left-to-right":
            width = maximum_primary
            lane_x, lane_y = primary_origin, cross_cursor
            cross_cursor += height + BOUNDARY_GAP
        else:
            height = maximum_primary
            lane_x, lane_y = cross_cursor, primary_origin
            cross_cursor += width + BOUNDARY_GAP
        lane_coordinates[lane.id] = (lane_x, lane_y, width, height)
        _place_items(
            items,
            lane_x + BOUNDARY_PADDING,
            lane_y + BOUNDARY_HEADER + BOUNDARY_PADDING,
            diagram.direction,
            groups,
            node_coordinates,
            group_coordinates,
        )

    standalone_members = tuple(
        node.id
        for node in diagram.nodes
        if node.id not in lane_of
    )
    standalone_items = _boundary_items(
        standalone_members,
        group_of,
        groups,
        allowed_lane=None,
        group_lane=group_lane,
        direction=diagram.direction,
    )
    if standalone_items:
        if diagram.direction == "left-to-right":
            standalone_x, standalone_y = primary_origin, cross_cursor
        else:
            standalone_x, standalone_y = cross_cursor, primary_origin
        _place_items(
            standalone_items,
            standalone_x,
            standalone_y,
            diagram.direction,
            groups,
            node_coordinates,
            group_coordinates,
        )

    placements = tuple(
        NodePlacement(
            node=node,
            x=node_coordinates[node.id][0],
            y=node_coordinates[node.id][1],
            width=NODE_WIDTH,
            height=NODE_HEIGHT,
            layer=layers[node.id],
        )
        for node in diagram.nodes
    )
    group_placements = tuple(
        GroupPlacement(
            group=group,
            x=group_coordinates[group.id][0],
            y=group_coordinates[group.id][1],
            width=group_coordinates[group.id][2],
            height=group_coordinates[group.id][3],
            swimlane_id=group_lane[group.id],
        )
        for group in diagram.groups
    )
    swimlane_placements = tuple(
        SwimlanePlacement(
            swimlane=lane,
            x=lane_coordinates[lane.id][0],
            y=lane_coordinates[lane.id][1],
            width=lane_coordinates[lane.id][2],
            height=lane_coordinates[lane.id][3],
        )
        for lane in diagram.swimlanes
    )
    return LayeredLayout(
        placements=placements,
        groups=group_placements,
        swimlanes=swimlane_placements,
    )


def _boundary_items(
    member_ids: Tuple[str, ...],
    group_of: Dict[str, str],
    groups: Dict[str, Group],
    *,
    allowed_lane: Optional[str],
    group_lane: Dict[str, Optional[str]],
    direction: str,
) -> List[_LayoutItem]:
    items: List[_LayoutItem] = []
    emitted_groups: Set[str] = set()
    for node_id in member_ids:
        group_id = group_of.get(node_id)
        if group_id is not None and group_lane[group_id] == allowed_lane:
            if group_id in emitted_groups:
                continue
            emitted_groups.add(group_id)
            width, height = _group_size(groups[group_id], direction)
            items.append(_LayoutItem("group", group_id, width, height))
        elif group_id is None:
            items.append(
                _LayoutItem("node", node_id, NODE_WIDTH, NODE_HEIGHT)
            )
    return items


def _group_size(group: Group, direction: str) -> Tuple[int, int]:
    count = len(group.members)
    if direction == "left-to-right":
        content_width = count * NODE_WIDTH + (count - 1) * NODE_GAP
        content_height = NODE_HEIGHT
    else:
        content_width = NODE_WIDTH
        content_height = count * NODE_HEIGHT + (count - 1) * NODE_GAP
    return (
        max(
            content_width + 2 * BOUNDARY_PADDING,
            _label_width(group.label),
        ),
        content_height + BOUNDARY_HEADER + 2 * BOUNDARY_PADDING,
    )


def _container_size(
    items: List[_LayoutItem], direction: str, label: str
) -> Tuple[int, int]:
    if direction == "left-to-right":
        content_width = sum(item.width for item in items)
        content_width += max(0, len(items) - 1) * BOUNDARY_GAP
        content_height = max(item.height for item in items)
    else:
        content_width = max(item.width for item in items)
        content_height = sum(item.height for item in items)
        content_height += max(0, len(items) - 1) * BOUNDARY_GAP
    return (
        max(content_width + 2 * BOUNDARY_PADDING, _label_width(label)),
        content_height + BOUNDARY_HEADER + 2 * BOUNDARY_PADDING,
    )


def _label_width(label: str) -> int:
    longest_line = max(len(line) for line in label.splitlines() or [""])
    return longest_line * 11 + 2 * BOUNDARY_PADDING


def _place_items(
    items: List[_LayoutItem],
    x: int,
    y: int,
    direction: str,
    groups: Dict[str, Group],
    node_coordinates: Dict[str, Tuple[int, int]],
    group_coordinates: Dict[str, Tuple[int, int, int, int]],
) -> None:
    cursor_x, cursor_y = x, y
    for item in items:
        if item.kind == "group":
            group = groups[item.item_id]
            group_coordinates[group.id] = (
                cursor_x,
                cursor_y,
                item.width,
                item.height,
            )
            node_x = cursor_x + BOUNDARY_PADDING
            node_y = cursor_y + BOUNDARY_HEADER + BOUNDARY_PADDING
            for member in group.members:
                node_coordinates[member] = (node_x, node_y)
                if direction == "left-to-right":
                    node_x += NODE_WIDTH + NODE_GAP
                else:
                    node_y += NODE_HEIGHT + NODE_GAP
        else:
            node_coordinates[item.item_id] = (cursor_x, cursor_y)

        if direction == "left-to-right":
            cursor_x += item.width + BOUNDARY_GAP
        else:
            cursor_y += item.height + BOUNDARY_GAP


def _strongly_connected_components(
    diagram: Diagram,
) -> Tuple[Dict[str, int], Tuple[Tuple[str, ...], ...]]:
    node_order = {node.id: index for index, node in enumerate(diagram.nodes)}
    adjacency: Dict[str, List[str]] = {node.id: [] for node in diagram.nodes}
    for edge in diagram.edges:
        if edge.target not in adjacency[edge.source]:
            adjacency[edge.source].append(edge.target)

    next_index = 0
    indices: Dict[str, int] = {}
    low_links: Dict[str, int] = {}
    stack: List[str] = []
    on_stack: Set[str] = set()
    discovered: List[Tuple[str, ...]] = []

    def visit(node_id: str) -> None:
        nonlocal next_index
        indices[node_id] = next_index
        low_links[node_id] = next_index
        next_index += 1
        stack.append(node_id)
        on_stack.add(node_id)

        for target_id in adjacency[node_id]:
            if target_id not in indices:
                visit(target_id)
                low_links[node_id] = min(
                    low_links[node_id], low_links[target_id]
                )
            elif target_id in on_stack:
                low_links[node_id] = min(
                    low_links[node_id], indices[target_id]
                )

        if low_links[node_id] == indices[node_id]:
            component: List[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node_id:
                    break
            component.sort(key=node_order.__getitem__)
            discovered.append(tuple(component))

    for node in diagram.nodes:
        if node.id not in indices:
            visit(node.id)

    components = tuple(
        sorted(discovered, key=lambda component: node_order[component[0]])
    )
    component_of = {
        node_id: component_index
        for component_index, component in enumerate(components)
        for node_id in component
    }
    return component_of, components


def _component_layers(
    diagram: Diagram,
    component_of: Dict[str, int],
    components: Tuple[Tuple[str, ...], ...],
) -> Dict[int, int]:
    successors: Dict[int, Set[int]] = {
        index: set() for index in range(len(components))
    }
    indegrees = {index: 0 for index in range(len(components))}
    for edge in diagram.edges:
        source = component_of[edge.source]
        target = component_of[edge.target]
        if source != target and target not in successors[source]:
            successors[source].add(target)
            indegrees[target] += 1

    layers = {index: 0 for index in range(len(components))}
    ready = sorted(index for index, degree in indegrees.items() if degree == 0)
    while ready:
        source = ready.pop(0)
        for target in sorted(successors[source]):
            layers[target] = max(layers[target], layers[source] + 1)
            indegrees[target] -= 1
            if indegrees[target] == 0:
                ready.append(target)
                ready.sort()

    return layers
