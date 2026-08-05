"""Output renderer interfaces and implementations."""

from __future__ import annotations

from typing import Callable

from diagrams_cli.model import Diagram
from diagrams_cli.renderers.excalidraw import render_excalidraw
from diagrams_cli.renderers.mermaid import render_mermaid
from diagrams_cli.renderers.plantuml import render_plantuml

Renderer = Callable[[Diagram], str]

__all__ = [
    "Renderer",
    "render_excalidraw",
    "render_mermaid",
    "render_plantuml",
]
