"""Deterministic Mermaid flowchart rendering for the portable model."""

from __future__ import annotations

import json
from typing import Dict, List

from diagrams_cli.model import Diagram, NodeType

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

    for node in diagram.nodes:
        shape = NODE_SHAPES[node.type].format(label=_escape_text(node.label))
        lines.append(f"    {aliases[node.id]}{shape}")

    if diagram.nodes and diagram.edges:
        lines.append("")

    for edge in diagram.edges:
        relationship = f"    {aliases[edge.source]} -->"
        if edge.label:
            relationship += f'|"{_escape_text(edge.label)}"|'
        relationship += f" {aliases[edge.target]}"
        lines.append(relationship)

    return "\n".join(lines) + "\n"


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
