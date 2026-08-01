"""Deterministic layered layout for renderer-independent diagrams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from diagrams_cli.model import Diagram, Node

NODE_WIDTH = 220
NODE_HEIGHT = 100
CANVAS_MARGIN = 100
TITLE_SPACE = 60
LAYER_GAP = 160
NODE_GAP = 80


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
class LayeredLayout:
    """An immutable, input-ordered collection of node placements."""

    placements: Tuple[NodePlacement, ...]


def layout_diagram(diagram: Diagram) -> LayeredLayout:
    """Place nodes in stable graph-depth layers for the requested direction.

    Strongly connected nodes share one layer, turning the graph into a DAG
    before depth is calculated. Nodes within a layer retain input order.
    """
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
