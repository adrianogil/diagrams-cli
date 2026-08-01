"""Deterministic PlantUML rendering for the portable diagram model."""

from __future__ import annotations

from typing import Dict, List

from diagrams_cli.model import Diagram, NodeType

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

    for node in diagram.nodes:
        keyword = NODE_KEYWORDS[node.type]
        label = _escape_text(node.label)
        lines.append(f'{keyword} "{label}" as {aliases[node.id]}')

    if diagram.nodes and diagram.edges:
        lines.append("")

    for edge in diagram.edges:
        relationship = f"{aliases[edge.source]} --> {aliases[edge.target]}"
        if edge.label:
            relationship += f" : {_escape_text(edge.label)}"
        lines.append(relationship)

    lines.append("@enduml")
    return "\n".join(lines) + "\n"


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
