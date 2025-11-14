"""Render Slack-friendly reports using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, Template


class TemplateRenderer:
    """Simple Jinja2 renderer that loads templates from disk."""

    def __init__(self, templates_dir: Path):
        self._env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def render(self, template_name: str, context: Mapping[str, Any]) -> str:
        template: Template = self._env.get_template(template_name)
        return template.render(**context)


__all__ = ["TemplateRenderer"]
