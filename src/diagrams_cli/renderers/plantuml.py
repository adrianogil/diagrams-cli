"""Deterministic PlantUML rendering for the portable diagram model."""

from __future__ import annotations

from typing import Dict, List

from diagrams_cli.model import Diagram, Group, Node, NodeType

NODE_KEYWORDS: Dict[NodeType, str] = {
    "actor": "actor",
    "service": "component",
    "database": "database",
    "queue": "queue",
    "generic": "rectangle",
}


def render_plantuml(diagram: Diagram) -> str:
    """Render a validated diagram as deterministic PlantUML source."""
    lines: List[str] = ["@startuml"]

    if diagram.title is not None:
        lines.append(f"title {_escape_text(diagram.title)}")
    if diagram.direction == "left-to-right":
        lines.append("left to right direction")

    aliases = {
        node.id: f"node_{index}"
        for index, node in enumerate(diagram.nodes, start=1)
    }

    has_header = diagram.title is not None or diagram.direction == "left-to-right"
    if has_header and (diagram.nodes or diagram.edges):
        lines.append("")

    if diagram.groups or diagram.swimlanes:
        lines.extend(_render_boundaries(diagram, aliases))
    else:
        for node in diagram.nodes:
            lines.append(_node_declaration(node, aliases[node.id]))

    if diagram.nodes and diagram.edges:
        lines.append("")

    for edge in diagram.edges:
        relationship = f"{aliases[edge.source]} --> {aliases[edge.target]}"
        if edge.label:
            relationship += f" : {_escape_text(edge.label)}"
        lines.append(relationship)

    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def _render_boundaries(diagram: Diagram, aliases: Dict[str, str]) -> List[str]:
    lines: List[str] = []
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
    group_lanes = {
        group.id: lane_of.get(group.members[0]) for group in diagram.groups
    }
    group_aliases = {
        group.id: f"group_{index}"
        for index, group in enumerate(diagram.groups, start=1)
    }
    group_by_id = {group.id: group for group in diagram.groups}
    lane_aliases = {
        lane.id: f"swimlane_{index}"
        for index, lane in enumerate(diagram.swimlanes, start=1)
    }
    node_by_id = {node.id: node for node in diagram.nodes}

    for lane in diagram.swimlanes:
        lines.append(
            f'frame "{_escape_text(lane.label)}" as {lane_aliases[lane.id]} {{'
        )
        emitted_groups = set()
        for member in lane.members:
            group_id = group_of.get(member)
            if group_id is not None and group_id not in emitted_groups:
                emitted_groups.add(group_id)
                group = group_by_id[group_id]
                lines.extend(
                    _group_declaration(
                        group,
                        group_aliases[group.id],
                        aliases,
                        node_by_id,
                        2,
                    )
                )
            elif group_id is None:
                lines.append(
                    "  " + _node_declaration(node_by_id[member], aliases[member])
                )
        lines.append("}")

    emitted_groups = set()
    for node in diagram.nodes:
        group_id = group_of.get(node.id)
        if (
            group_id is not None
            and group_lanes[group_id] is None
            and group_id not in emitted_groups
        ):
            emitted_groups.add(group_id)
            lines.extend(
                _group_declaration(
                    group_by_id[group_id],
                    group_aliases[group_id],
                    aliases,
                    node_by_id,
                    0,
                )
            )
        elif group_id is None and node.id not in lane_of:
            lines.append(_node_declaration(node, aliases[node.id]))
    return lines


def _group_declaration(
    group: Group,
    alias: str,
    aliases: Dict[str, str],
    node_by_id: Dict[str, Node],
    indentation: int,
) -> List[str]:
    prefix = " " * indentation
    lines = [
        f'{prefix}package "{_escape_text(group.label)}" as {alias} {{'
    ]
    for member in group.members:
        lines.append(
            prefix + "  " + _node_declaration(node_by_id[member], aliases[member])
        )
    lines.append(prefix + "}")
    return lines


def _node_declaration(node: Node, alias: str) -> str:
    keyword = NODE_KEYWORDS[node.type]
    label = _escape_text(node.label)
    return f'{keyword} "{label}" as {alias}'


def _escape_text(value: str) -> str:
    """Keep user text on one PlantUML source line and escape preprocessors."""
    return (
        value.replace("%", "%percent()")
        .replace("$", "%dollar()")
        .replace("\\", "%backslash()")
        .replace("\r\n", "%n()")
        .replace("\r", "%n()")
        .replace("\n", "%n()")
        .replace("\t", "%tab()")
        .replace('"', '\\"')
    )
