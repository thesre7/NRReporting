"""Utilities for building report context payloads."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict

import pytz

from ..config import ReportConfig
from ..services.trend_translator import AnalysisResult


@dataclass(frozen=True)
class ReportContext:
    """Serializable payload passed to the template renderer."""

    user_name: str
    timestamp: str
    event_name: str
    report_date: str
    report_time: str
    dashboard_url: str
    traffic_status: str
    capacity_status: str
    trends: str
    tsys_avg_tps: str
    tsys_peak_tps: str
    tsys_peak_time: str
    tsys_avg_capacity: str
    hpns_avg_tps: str
    hpns_peak_tps: str
    hpns_peak_time: str
    hpns_avg_capacity: str

    def as_dict(self) -> Dict[str, str]:  # pragma: no cover - convenience
        return asdict(self)


class ReportContextBuilder:
    """Builds the final template context from metrics and analysis results."""

    def __init__(self, config: ReportConfig):
        self._config = config

    def build(self, metrics: Dict[str, Dict[str, float]], analysis: AnalysisResult, event_name: str | None = None) -> ReportContext:
        tz = pytz.timezone(self._config.timezone)
        now = datetime.now(tz)
        report_date = now.strftime("%B %d, %Y")
        report_time = now.strftime("%-I:%M %p %Z")
        timestamp = now.strftime("%b %d at %-I:%M %p %Z")

        tsys = metrics.get("tsys_tps", {})
        hpns = metrics.get("hpns_tps", {})
        tsys_capacity = metrics.get("tsys_capacity", {})
        hpns_capacity = metrics.get("hpns_capacity", {})

        return ReportContext(
            user_name=self._config.user_name,
            timestamp=timestamp,
            event_name=event_name or self._config.event_name,
            report_date=report_date,
            report_time=report_time,
            dashboard_url=self._config.dashboard_url,
            traffic_status=analysis.traffic_status,
            capacity_status=analysis.capacity_status,
            trends="\n".join(f"• {trend}" for trend in analysis.trends),
            tsys_avg_tps=self._format_metric(tsys.get("current_value")),
            tsys_peak_tps=self._format_metric(tsys.get("peak_value")),
            tsys_peak_time=tsys.get("peak_time", "--"),
            tsys_avg_capacity=self._format_metric(tsys_capacity.get("current_value")),
            hpns_avg_tps=self._format_metric(hpns.get("current_value")),
            hpns_peak_tps=self._format_metric(hpns.get("peak_value")),
            hpns_peak_time=hpns.get("peak_time", "--"),
            hpns_avg_capacity=self._format_metric(hpns_capacity.get("current_value")),
        )

    @staticmethod
    def _format_metric(value: float | None) -> str:
        if value is None:
            return "--"
        if value >= 1000:
            return f"{value/1000:.1f}k"
        return f"{value:.1f}"


__all__ = ["ReportContext", "ReportContextBuilder"]
