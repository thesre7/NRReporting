"""Widget parsing utilities for extracting KPI values from New Relic dashboards."""

from __future__ import annotations

from datetime import datetime
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytz


@dataclass
class WidgetMetric:
    """Normalized representation of a dashboard widget."""

    title: str
    current_value: float
    comparison_pct: float
    trend: str
    display_value: str
    peak_value: Optional[float] = None
    peak_time: Optional[str] = None


class WidgetParser:
    """Parse dashboard widgets into normalized metrics."""

    TREND_ARROWS = {"↗": "up", "▲": "up", "↑": "up", "↘": "down", "▼": "down", "↓": "down"}

    def parse(self, widgets: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Parse widgets and map them to TSYS/HPNS metrics.

        Returns a mapping where each value is a plain dict to remain compatible
        with downstream translator and context code that expect dict access.
        """

        normalized: Dict[str, Dict[str, Any]] = {}
        for widget in widgets:
            metric = self._parse_widget(widget)
            if not metric:
                continue
            title = (metric.get("title") or "").lower()
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

    def _parse_widget(self, widget: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        title = widget.get("title") or widget.get("layout", {}).get("title", "")
        if not title:
            return None

        visualization_data = widget.get("data", {}).get("visualization") or {}
        raw_value = self._extract_current_value(widget, visualization_data)
        comparison_pct = self._extract_comparison_pct(widget, visualization_data)
        trend = self._extract_trend(widget, visualization_data)
        peak_value, peak_time = self._extract_peak(widget)

        if raw_value is None:
            return None

        display_value = widget.get("rawConfiguration", {}).get("title") or str(raw_value)
        metric: Dict[str, Any] = {
            "title": title,
            "current_value": raw_value,
            "comparison_pct": comparison_pct or 0.0,
            "trend": trend,
            "display_value": display_value,
        }
        if peak_value is not None:
            metric["peak_value"] = peak_value
        if peak_time is not None:
            metric["peak_time"] = peak_time
        return metric

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

    def _extract_peak(self, widget: Dict[str, Any]) -> tuple[Optional[float], Optional[str]]:
        """Derive peak value and timestamp from any embedded time-series data.

        Searches common locations in dashboard widget data and attempts to
        interpret heterogeneous point schemas robustly.
        """
        raw = (widget.get("data", {}) or {}).get("raw")
        viz = (widget.get("data", {}) or {}).get("visualization")
        points: List[tuple[float, int]] = []
        points.extend(self._gather_points(raw))
        points.extend(self._gather_points(viz))

        if not points:
            return None, None

        # Choose the point with the highest value
        peak_val, peak_ts = max(points, key=lambda p: p[0])
        # Format timestamp in US/Eastern as per reporting convention
        try:
            tz_et = pytz.timezone("US/Eastern")
            dt = datetime.fromtimestamp(peak_ts, tz=pytz.utc).astimezone(tz_et)
            peak_time_str = dt.strftime("%-I:%M %p ET on %b %d, %Y")
        except Exception:
            peak_time_str = str(peak_ts)
        return float(peak_val), peak_time_str

    def _gather_points(self, obj: Any) -> List[tuple[float, int]]:
        """Recursively traverse an arbitrary object to collect (value, epoch_s) points."""
        results: List[tuple[float, int]] = []
        if obj is None:
            return results
        if isinstance(obj, list):
            for item in obj:
                results.extend(self._gather_points(item))
            return results
        if isinstance(obj, dict):
            # Attempt to treat this dict as a point first
            value = self._first_numeric(
                [
                    obj.get("tps"),
                    obj.get("y"),
                    obj.get("value"),
                    obj.get("rate"),
                    obj.get("count"),
                ]
            )
            ts = self._first_non_none(
                [
                    obj.get("endTimeSeconds"),
                    obj.get("beginTimeSeconds"),
                    obj.get("x"),
                    obj.get("timestamp"),
                    obj.get("endTime"),
                    obj.get("time"),
                ]
            )
            ts_epoch = self._to_epoch_seconds(ts)
            if value is not None and ts_epoch is not None:
                results.append((float(value), ts_epoch))

            # Recurse into children
            for v in obj.values():
                results.extend(self._gather_points(v))
            return results
        return results

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

    @staticmethod
    def _first_numeric(values: List[Any]) -> Optional[float]:
        for v in values:
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                parsed = WidgetParser._parse_numeric(v)
                if parsed is not None:
                    return parsed
        return None

    @staticmethod
    def _to_epoch_seconds(ts: Any) -> Optional[int]:
        if ts is None:
            return None
        # Numeric seconds or milliseconds
        if isinstance(ts, (int, float)):
            t = float(ts)
            # Heuristic: treat large numbers as milliseconds
            if t > 1e12:
                t /= 1000.0
            return int(t)
        if isinstance(ts, str):
            s = ts.strip()
            # Try ISO8601 parsing
            try:
                s2 = s.replace("Z", "+00:00")
                dt = datetime.fromisoformat(s2)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=pytz.utc)
                return int(dt.timestamp())
            except Exception:
                # Fallback: numeric string
                try:
                    t = float(s)
                    if t > 1e12:
                        t /= 1000.0
                    return int(t)
                except Exception:
                    return None
        return None


__all__ = ["WidgetParser", "WidgetMetric"]
