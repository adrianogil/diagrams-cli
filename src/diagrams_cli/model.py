"""Renderer-independent diagram domain model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

DiagramDirection = Literal["top-to-bottom", "left-to-right"]
NodeType = Literal["actor", "service", "database", "queue", "generic"]


@dataclass(frozen=True)
class Node:
    """A named element in a diagram."""

    id: str
    label: str
    type: NodeType = "generic"


@dataclass(frozen=True)
class Edge:
    """A directed relationship between two nodes."""

    source: str
    target: str
    label: Optional[str] = None


@dataclass(frozen=True)
class Diagram:
    """A validated diagram that can be passed to any renderer."""

    nodes: Tuple[Node, ...]
    edges: Tuple[Edge, ...] = ()
    title: Optional[str] = None
    direction: DiagramDirection = "top-to-bottom"
