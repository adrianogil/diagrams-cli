"""Output renderer interfaces and implementations."""

from __future__ import annotations

from typing import Callable

from diagrams_cli.model import Diagram
from diagrams_cli.renderers.plantuml import render_plantuml

Renderer = Callable[[Diagram], str]

__all__ = ["Renderer", "render_plantuml"]
