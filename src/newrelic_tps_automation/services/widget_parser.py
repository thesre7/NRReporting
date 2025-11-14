"""Widget parsing utilities for extracting KPI values from New Relic dashboards."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class WidgetMetric:
    """Normalized representation of a dashboard widget."""

    title: str
    current_value: float
    comparison_pct: float
    trend: str
    display_value: str


class WidgetParser:
    """Parse dashboard widgets into normalized metrics."""

    TREND_ARROWS = {"↗": "up", "▲": "up", "↑": "up", "↘": "down", "▼": "down", "↓": "down"}

    def parse(self, widgets: List[Dict[str, Any]]) -> Dict[str, WidgetMetric]:
        """Parse widgets and map them to TSYS/HPNS metrics."""

        normalized: Dict[str, WidgetMetric] = {}
        for widget in widgets:
            metric = self._parse_widget(widget)
            if not metric:
                continue
            title = metric.title.lower()
            if "total" in title or "tsys" in title and "tps" in title:
                normalized.setdefault("tsys_tps", metric)
            elif "hpns" in title and "tps" in title:
                normalized.setdefault("hpns_tps", metric)
            elif "tsys" in title and "capacity" in title:
                normalized.setdefault("tsys_capacity", metric)
            elif "hpns" in title and "capacity" in title:
                normalized.setdefault("hpns_capacity", metric)
            elif "ratio" in title:
                normalized.setdefault("tps_ratio", metric)
        return normalized

    def _parse_widget(self, widget: Dict[str, Any]) -> Optional[WidgetMetric]:
        title = widget.get("title") or widget.get("layout", {}).get("title", "")
        if not title:
            return None

        visualization_data = widget.get("data", {}).get("visualization") or {}
        raw_value = self._extract_current_value(widget, visualization_data)
        comparison_pct = self._extract_comparison_pct(widget, visualization_data)
        trend = self._extract_trend(widget, visualization_data)

        if raw_value is None:
            return None

        display_value = widget.get("rawConfiguration", {}).get("title") or str(raw_value)
        return WidgetMetric(
            title=title,
            current_value=raw_value,
            comparison_pct=comparison_pct or 0.0,
            trend=trend,
            display_value=display_value,
        )

    def _extract_current_value(self, widget: Dict[str, Any], viz: Dict[str, Any]) -> Optional[float]:
        candidates = [
            viz.get("currentValue"),
            widget.get("rawConfiguration", {}).get("nrqlQueries", [{}])[0].get("value"),
            widget.get("data", {}).get("raw", {}).get("current"),
            widget.get("data", {}).get("raw", {}).get("value"),
        ]
        text = self._first_non_none(candidates) or widget.get("title")
        return self._parse_numeric(text)

    def _extract_comparison_pct(self, widget: Dict[str, Any], viz: Dict[str, Any]) -> Optional[float]:
        candidates = [
            viz.get("comparison"),
            widget.get("data", {}).get("raw", {}).get("comparison"),
            widget.get("rawConfiguration", {}).get("thresholds", [{}])[0].get("value"),
        ]
        text = self._first_non_none(candidates)
        return self._parse_numeric(text)

    def _extract_trend(self, widget: Dict[str, Any], viz: Dict[str, Any]) -> str:
        trend = viz.get("trend") or widget.get("data", {}).get("raw", {}).get("trend")
        if trend:
            return trend.lower()
        title = widget.get("title", "")
        for arrow, name in self.TREND_ARROWS.items():
            if arrow in title:
                return name
        comparison = widget.get("rawConfiguration", {}).get("subtitle", "")
        for arrow, name in self.TREND_ARROWS.items():
            if arrow in comparison:
                return name
        return "neutral"

    @staticmethod
    def _parse_numeric(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip()
            multiplier = 1.0
            if cleaned.endswith("%"):
                cleaned = cleaned[:-1]
            if cleaned.lower().endswith("k"):
                multiplier = 1_000
                cleaned = cleaned[:-1]
            if cleaned.lower().endswith("m"):
                multiplier = 1_000_000
                cleaned = cleaned[:-1]
            match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
            if match:
                return float(match.group()) * multiplier
        return None

    @staticmethod
    def _first_non_none(values: List[Any]) -> Optional[Any]:
        for value in values:
            if value is not None:
                return value
        return None


__all__ = ["WidgetParser", "WidgetMetric"]
