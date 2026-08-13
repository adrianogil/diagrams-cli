"""Validation and conversion for decoded diagram JSON values."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Set, Tuple, Type, TypeVar, cast

from diagrams_cli.errors import DiagramValidationError
from diagrams_cli.model import (
    Diagram,
    DiagramDirection,
    Edge,
    Group,
    Node,
    NodeType,
    Swimlane,
)

SUPPORTED_DIRECTIONS = frozenset({"top-to-bottom", "left-to-right"})
SUPPORTED_NODE_TYPES = frozenset(
    {"actor", "service", "database", "queue", "generic"}
)
BoundaryType = TypeVar("BoundaryType", Group, Swimlane)


def parse_diagram(value: object) -> Diagram:
    """Validate a decoded JSON value and build an immutable diagram model."""
    root = _require_object(value, "document")
    _reject_unknown_fields(
        root,
        {"title", "direction", "nodes", "edges", "groups", "swimlanes"},
        "document",
    )

    title = _optional_string(root, "title", "document", allow_empty=False)
    direction_value = _optional_string(
        root, "direction", "document", allow_empty=False
    )
    direction = direction_value or "top-to-bottom"
    if direction not in SUPPORTED_DIRECTIONS:
        choices = ", ".join(sorted(SUPPORTED_DIRECTIONS))
        raise DiagramValidationError(
            f"document.direction must be one of: {choices}"
        )

    if "nodes" not in root:
        raise DiagramValidationError("document.nodes is required")
    nodes_value = _require_array(root["nodes"], "document.nodes")
    nodes, node_ids = _parse_nodes(nodes_value)

    boundary_ids: Set[str] = set()
    group_memberships: Dict[str, str] = {}
    groups = _parse_boundaries(
        _require_array(root.get("groups", []), "document.groups"),
        "groups",
        node_ids,
        boundary_ids,
        group_memberships,
        Group,
    )
    swimlane_memberships: Dict[str, str] = {}
    swimlanes = _parse_boundaries(
        _require_array(root.get("swimlanes", []), "document.swimlanes"),
        "swimlanes",
        node_ids,
        boundary_ids,
        swimlane_memberships,
        Swimlane,
    )
    _validate_group_swimlane_nesting(
        groups, swimlane_memberships
    )

    edges_value = _require_array(
        root.get("edges", []), "document.edges"
    )
    edges = _parse_edges(edges_value, node_ids)

    return Diagram(
        title=title,
        direction=cast(DiagramDirection, direction),
        nodes=tuple(nodes),
        edges=tuple(edges),
        groups=tuple(groups),
        swimlanes=tuple(swimlanes),
    )


def _parse_nodes(values: List[object]) -> Tuple[List[Node], Set[str]]:
    nodes: List[Node] = []
    node_ids: Set[str] = set()

    for index, value in enumerate(values):
        path = f"document.nodes[{index}]"
        node = _require_object(value, path)
        _reject_unknown_fields(node, {"id", "label", "type"}, path)

        node_id = _required_string(node, "id", path)
        if node_id in node_ids:
            raise DiagramValidationError(
                f'{path}.id duplicates node id "{node_id}"'
            )

        label = _required_string(node, "label", path)
        node_type_value = _optional_string(
            node, "type", path, allow_empty=False
        )
        node_type = node_type_value or "generic"
        if node_type not in SUPPORTED_NODE_TYPES:
            choices = ", ".join(sorted(SUPPORTED_NODE_TYPES))
            raise DiagramValidationError(
                f"{path}.type must be one of: {choices}"
            )

        node_ids.add(node_id)
        nodes.append(
            Node(
                id=node_id,
                label=label,
                type=cast(NodeType, node_type),
            )
        )

    return nodes, node_ids


def _parse_edges(values: List[object], node_ids: Set[str]) -> List[Edge]:
    edges: List[Edge] = []

    for index, value in enumerate(values):
        path = f"document.edges[{index}]"
        edge = _require_object(value, path)
        _reject_unknown_fields(edge, {"from", "to", "label"}, path)

        source = _required_string(edge, "from", path)
        target = _required_string(edge, "to", path)
        label = _optional_string(edge, "label", path, allow_empty=True)

        if source not in node_ids:
            raise DiagramValidationError(
                f'{path}.from references unknown node "{source}"'
            )
        if target not in node_ids:
            raise DiagramValidationError(
                f'{path}.to references unknown node "{target}"'
            )

        edges.append(Edge(source=source, target=target, label=label))

    return edges


def _parse_boundaries(
    values: List[object],
    field: str,
    node_ids: Set[str],
    boundary_ids: Set[str],
    memberships: Dict[str, str],
    boundary_type: Type[BoundaryType],
) -> List[BoundaryType]:
    boundaries: List[BoundaryType] = []

    for index, value in enumerate(values):
        path = f"document.{field}[{index}]"
        boundary = _require_object(value, path)
        _reject_unknown_fields(boundary, {"id", "label", "members"}, path)

        boundary_id = _required_string(boundary, "id", path)
        if boundary_id in boundary_ids:
            raise DiagramValidationError(
                f'{path}.id duplicates boundary id "{boundary_id}"'
            )
        label = _required_string(boundary, "label", path)
        if "members" not in boundary:
            raise DiagramValidationError(f"{path}.members is required")
        member_values = _require_array(boundary["members"], f"{path}.members")
        if not member_values:
            raise DiagramValidationError(
                f"{path}.members must contain at least one node id"
            )

        members: List[str] = []
        local_members: Set[str] = set()
        for member_index, member_value in enumerate(member_values):
            member_path = f"{path}.members[{member_index}]"
            if not isinstance(member_value, str) or not member_value.strip():
                raise DiagramValidationError(
                    f"{member_path} must be a non-empty string"
                )
            if member_value not in node_ids:
                raise DiagramValidationError(
                    f'{member_path} references unknown node "{member_value}"'
                )
            if member_value in local_members:
                raise DiagramValidationError(
                    f'{member_path} duplicates node "{member_value}" in '
                    f'boundary "{boundary_id}"'
                )
            if member_value in memberships:
                previous_id = memberships[member_value]
                singular = "group" if field == "groups" else "swimlane"
                raise DiagramValidationError(
                    f'{member_path} assigns node "{member_value}" to '
                    f'multiple {singular}s: "{previous_id}" and '
                    f'"{boundary_id}"'
                )
            local_members.add(member_value)
            memberships[member_value] = boundary_id
            members.append(member_value)

        boundary_ids.add(boundary_id)
        boundaries.append(boundary_type(boundary_id, label, tuple(members)))

    return boundaries


def _validate_group_swimlane_nesting(
    groups: List[Group],
    swimlane_memberships: Dict[str, str],
) -> None:
    for index, group in enumerate(groups):
        lanes = {swimlane_memberships.get(member) for member in group.members}
        if len(lanes) > 1:
            rendered_lanes = ", ".join(
                'no swimlane' if lane is None else f'"{lane}"'
                for lane in sorted(lanes, key=lambda item: item or "")
            )
            raise DiagramValidationError(
                f'document.groups[{index}] boundary "{group.id}" spans '
                f"multiple swimlanes: {rendered_lanes}"
            )


def _require_object(value: object, path: str) -> Dict[str, object]:
    if not isinstance(value, dict):
        raise DiagramValidationError(f"{path} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise DiagramValidationError(f"{path} must use string field names")
    return cast(Dict[str, object], value)


def _require_array(value: object, path: str) -> List[object]:
    if not isinstance(value, list):
        raise DiagramValidationError(f"{path} must be an array")
    return cast(List[object], value)


def _required_string(
    value: Mapping[str, object], field: str, path: str
) -> str:
    if field not in value:
        raise DiagramValidationError(f"{path}.{field} is required")
    result = value[field]
    if not isinstance(result, str) or not result.strip():
        raise DiagramValidationError(
            f"{path}.{field} must be a non-empty string"
        )
    return result


def _optional_string(
    value: Mapping[str, object],
    field: str,
    path: str,
    *,
    allow_empty: bool,
) -> Optional[str]:
    if field not in value:
        return None
    result = value[field]
    if not isinstance(result, str):
        raise DiagramValidationError(f"{path}.{field} must be a string")
    if not allow_empty and not result.strip():
        raise DiagramValidationError(
            f"{path}.{field} must be a non-empty string"
        )
    return result


def _reject_unknown_fields(
    value: Mapping[str, object], allowed: Set[str], path: str
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        fields = ", ".join(unknown)
        raise DiagramValidationError(
            f"{path} contains unknown field(s): {fields}"
        )
