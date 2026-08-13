"""Deterministic Mermaid flowchart rendering for the portable model."""

from __future__ import annotations

import json
from typing import Dict, List

from diagrams_cli.model import Diagram, Group, Node, NodeType

NODE_SHAPES: Dict[NodeType, str] = {
    "actor": '(["{label}"])',
    "service": '["{label}"]',
    "database": '[("{label}")]',
    "queue": '[["{label}"]]',
    "generic": '["{label}"]',
}


def render_mermaid(diagram: Diagram) -> str:
    """Render a validated diagram as deterministic Mermaid flowchart text."""

    lines: List[str] = []
    if diagram.title is not None:
        lines.extend(
            (
                "---",
                "title: " + json.dumps(diagram.title, ensure_ascii=False),
                "---",
            )
        )

    direction = "LR" if diagram.direction == "left-to-right" else "TD"
    lines.append(f"flowchart {direction}")

    aliases = {
        node.id: f"node_{index}"
        for index, node in enumerate(diagram.nodes, start=1)
    }

    if diagram.groups or diagram.swimlanes:
        lines.extend(_render_boundaries(diagram, aliases, direction))
    else:
        for node in diagram.nodes:
            lines.append("    " + _node_declaration(node, aliases[node.id]))

    if diagram.nodes and diagram.edges:
        lines.append("")

    for edge in diagram.edges:
        relationship = f"    {aliases[edge.source]} -->"
        if edge.label:
            relationship += f'|"{_escape_text(edge.label)}"|'
        relationship += f" {aliases[edge.target]}"
        lines.append(relationship)

    return "\n".join(lines) + "\n"


def _render_boundaries(
    diagram: Diagram, aliases: Dict[str, str], direction: str
) -> List[str]:
    lines: List[str] = []
    node_by_id = {node.id: node for node in diagram.nodes}
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

    for lane in diagram.swimlanes:
        lines.append(
            f'    subgraph {lane_aliases[lane.id]}["{_escape_text(lane.label)}"]'
        )
        lines.append(f"        direction {direction}")
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
                        direction,
                        8,
                    )
                )
            elif group_id is None:
                lines.append(
                    "        "
                    + _node_declaration(node_by_id[member], aliases[member])
                )
        lines.append("    end")

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
                    direction,
                    4,
                )
            )
        elif group_id is None and node.id not in lane_of:
            lines.append("    " + _node_declaration(node, aliases[node.id]))
    return lines


def _group_declaration(
    group: Group,
    alias: str,
    aliases: Dict[str, str],
    node_by_id: Dict[str, Node],
    direction: str,
    indentation: int,
) -> List[str]:
    prefix = " " * indentation
    lines = [f'{prefix}subgraph {alias}["{_escape_text(group.label)}"]']
    lines.append(f"{prefix}    direction {direction}")
    for member in group.members:
        lines.append(
            prefix
            + "    "
            + _node_declaration(node_by_id[member], aliases[member])
        )
    lines.append(prefix + "end")
    return lines


def _node_declaration(node: Node, alias: str) -> str:
    shape = NODE_SHAPES[node.type].format(label=_escape_text(node.label))
    return f"{alias}{shape}"


def _escape_text(value: str) -> str:
    """Encode characters that could terminate a quoted Mermaid label."""

    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "&#124;")
        .replace("`", "&#96;")
        .replace("\r\n", "<br/>")
        .replace("\r", "<br/>")
        .replace("\n", "<br/>")
    )
