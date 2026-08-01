"""Deterministic Excalidraw JSON rendering."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from diagrams_cli.layout import NodePlacement, layout_diagram
from diagrams_cli.model import Diagram, NodeType

Element = Dict[str, Any]

NODE_STYLES: Dict[NodeType, Tuple[str, str]] = {
    "actor": ("ellipse", "#d0ebff"),
    "service": ("rectangle", "#dbe4ff"),
    "database": ("ellipse", "#d3f9d8"),
    "queue": ("diamond", "#fff3bf"),
    "generic": ("rectangle", "#f1f3f5"),
}


def render_excalidraw(diagram: Diagram) -> str:
    """Render a validated diagram as byte-stable Excalidraw JSON."""
    layout = layout_diagram(diagram)
    placements = {
        placement.node.id: placement for placement in layout.placements
    }
    shape_ids = {
        placement.node.id: f"node-{index}-shape"
        for index, placement in enumerate(layout.placements, start=1)
    }

    arrows = [
        _arrow_element(index, edge.source, edge.target, placements, shape_ids)
        for index, edge in enumerate(diagram.edges, start=1)
    ]
    edge_labels = [
        _edge_label_element(index, edge.label, arrows[index - 1])
        for index, edge in enumerate(diagram.edges, start=1)
        if edge.label
    ]

    elements: List[Element] = []
    if diagram.title:
        elements.append(_title_element(diagram.title))
    elements.extend(arrows)
    for index, placement in enumerate(layout.placements, start=1):
        related_arrows = [
            f"edge-{edge_index}"
            for edge_index, edge in enumerate(diagram.edges, start=1)
            if edge.source == placement.node.id
            or edge.target == placement.node.id
        ]
        elements.append(_shape_element(index, placement, related_arrows))
        elements.append(_node_label_element(index, placement))
    elements.extend(edge_labels)

    document = {
        "type": "excalidraw",
        "version": 2,
        "source": "diagrams-cli",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff",
        },
        "files": {},
    }
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def _base_element(
    element_id: str,
    element_type: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    stroke_color: str = "#1b1b1f",
    background_color: str = "transparent",
    roughness: int = 1,
    roundness: Optional[Dict[str, int]] = None,
) -> Element:
    return {
        "id": element_id,
        "type": element_type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": stroke_color,
        "backgroundColor": background_color,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": roughness,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": None,
        "roundness": roundness,
        "seed": _stable_integer(f"{element_id}:seed"),
        "version": 1,
        "versionNonce": _stable_integer(f"{element_id}:nonce"),
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
    }


def _shape_element(
    index: int,
    placement: NodePlacement,
    related_arrows: List[str],
) -> Element:
    shape_type, background_color = NODE_STYLES[placement.node.type]
    element = _base_element(
        f"node-{index}-shape",
        shape_type,
        placement.x,
        placement.y,
        placement.width,
        placement.height,
        background_color=background_color,
        roundness={"type": 3} if shape_type == "rectangle" else None,
    )
    element["boundElements"] = [
        {"id": f"node-{index}-label", "type": "text"},
        *({"id": arrow_id, "type": "arrow"} for arrow_id in related_arrows),
    ]
    return element


def _node_label_element(index: int, placement: NodePlacement) -> Element:
    width, height = _text_dimensions(placement.node.label, 20)
    element = _base_element(
        f"node-{index}-label",
        "text",
        placement.x + (placement.width - width) / 2,
        placement.y + (placement.height - height) / 2,
        width,
        height,
        stroke_color="#1b1b1f",
        roughness=0,
    )
    element.update(
        {
            "fontSize": 20,
            "fontFamily": 1,
            "text": placement.node.label,
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": f"node-{index}-shape",
            "originalText": placement.node.label,
            "autoResize": True,
            "lineHeight": 1.25,
        }
    )
    return element


def _title_element(title: str) -> Element:
    width, height = _text_dimensions(title, 28)
    element = _base_element(
        "diagram-title",
        "text",
        100,
        50,
        width,
        height,
        roughness=0,
    )
    element.update(
        {
            "fontSize": 28,
            "fontFamily": 1,
            "text": title,
            "textAlign": "left",
            "verticalAlign": "top",
            "containerId": None,
            "originalText": title,
            "autoResize": True,
            "lineHeight": 1.25,
        }
    )
    return element


def _arrow_element(
    index: int,
    source_id: str,
    target_id: str,
    placements: Dict[str, NodePlacement],
    shape_ids: Dict[str, str],
) -> Element:
    source = placements[source_id]
    target = placements[target_id]
    start, end, start_fixed, end_fixed, points = _arrow_geometry(source, target)
    element = _base_element(
        f"edge-{index}",
        "arrow",
        start[0],
        start[1],
        abs(end[0] - start[0]) if len(points) == 2 else 80,
        abs(end[1] - start[1]) if len(points) == 2 else 30,
        stroke_color="#495057",
        roughness=1,
        roundness={"type": 2},
    )
    element.update(
        {
            "points": points,
            "lastCommittedPoint": None,
            "startBinding": {
                "elementId": shape_ids[source_id],
                "mode": "orbit",
                "fixedPoint": start_fixed,
            },
            "endBinding": {
                "elementId": shape_ids[target_id],
                "mode": "orbit",
                "fixedPoint": end_fixed,
            },
            "startArrowhead": None,
            "endArrowhead": "arrow",
            "elbowed": False,
        }
    )
    return element


def _arrow_geometry(
    source: NodePlacement,
    target: NodePlacement,
) -> Tuple[
    Tuple[float, float],
    Tuple[float, float],
    List[float],
    List[float],
    List[List[float]],
]:
    if source.node.id == target.node.id:
        start = (source.x + source.width, source.y + source.height * 0.35)
        end = (source.x + source.width, source.y + source.height * 0.65)
        return (
            start,
            end,
            [1, 0.35],
            [1, 0.65],
            [[0, 0], [80, 0], [80, 30], [0, 30]],
        )

    source_center = (
        source.x + source.width / 2,
        source.y + source.height / 2,
    )
    target_center = (
        target.x + target.width / 2,
        target.y + target.height / 2,
    )
    delta_x = target_center[0] - source_center[0]
    delta_y = target_center[1] - source_center[1]

    if abs(delta_x) >= abs(delta_y):
        if delta_x >= 0:
            start = (source.x + source.width, source_center[1])
            end = (target.x, target_center[1])
            start_fixed, end_fixed = [1, 0.5], [0, 0.5]
        else:
            start = (source.x, source_center[1])
            end = (target.x + target.width, target_center[1])
            start_fixed, end_fixed = [0, 0.5], [1, 0.5]
    elif delta_y >= 0:
        start = (source_center[0], source.y + source.height)
        end = (target_center[0], target.y)
        start_fixed, end_fixed = [0.5, 1], [0.5, 0]
    else:
        start = (source_center[0], source.y)
        end = (target_center[0], target.y + target.height)
        start_fixed, end_fixed = [0.5, 0], [0.5, 1]

    points = [[0, 0], [end[0] - start[0], end[1] - start[1]]]
    return start, end, start_fixed, end_fixed, points


def _edge_label_element(index: int, label: str, arrow: Element) -> Element:
    width, height = _text_dimensions(label, 16)
    points = arrow["points"]
    halfway = points[len(points) // 2]
    x = arrow["x"] + halfway[0] / 2 - width / 2
    y = arrow["y"] + halfway[1] / 2 - height - 6
    element = _base_element(
        f"edge-{index}-label",
        "text",
        x,
        y,
        width,
        height,
        stroke_color="#495057",
        roughness=0,
    )
    element.update(
        {
            "fontSize": 16,
            "fontFamily": 1,
            "text": label,
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": None,
            "originalText": label,
            "autoResize": True,
            "lineHeight": 1.25,
        }
    )
    return element


def _text_dimensions(text: str, font_size: int) -> Tuple[float, float]:
    lines = text.splitlines() or [""]
    width = max(1.0, max(len(line) for line in lines) * font_size * 0.55)
    height = max(1.0, len(lines) * font_size * 1.25)
    return round(width, 2), round(height, 2)


def _stable_integer(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % 2_147_483_646 + 1
