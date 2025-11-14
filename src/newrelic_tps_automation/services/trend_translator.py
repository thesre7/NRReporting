"""Translation layer that converts dashboard metrics into narratives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..config import MetricThresholds


@dataclass
class AnalysisResult:
    """Structured analysis payload consumed by the report layer."""

    trends: List[str]
    traffic_status: str
    capacity_status: str


class TrendTranslator:
    """Encapsulates the simple translation rules defined in the design doc."""

    def __init__(self, thresholds: MetricThresholds):
        self._thresholds = thresholds

    def translate(self, metrics: Dict[str, Dict[str, float]]) -> AnalysisResult:
        trends: List[str] = []

        tsys = metrics.get("tsys_tps")
        hpns = metrics.get("hpns_tps")
        ratio = metrics.get("tps_ratio")
        tsys_capacity = metrics.get("tsys_capacity")
        hpns_capacity = metrics.get("hpns_capacity")

        if tsys and hpns:
            trends.append(self._traffic_trend(tsys, hpns))
        if ratio:
            trends.append(self._ratio_trend(ratio))
        if tsys_capacity and hpns_capacity:
            trends.append(self._capacity_trend(tsys_capacity, hpns_capacity))

        traffic_status = self._traffic_status(tsys, hpns)
        capacity_status = self._capacity_status(tsys_capacity, hpns_capacity)

        return AnalysisResult(trends=trends, traffic_status=traffic_status, capacity_status=capacity_status)

    def _traffic_trend(self, tsys: Dict[str, float], hpns: Dict[str, float]) -> str:
        tsys_phrase = self._trend_phrase("TSYS Mainframe", tsys)
        hpns_phrase = self._trend_phrase("HPNS", hpns)
        return f"{tsys_phrase}; {hpns_phrase}."

    def _ratio_trend(self, ratio: Dict[str, float]) -> str:
        comparison = ratio.get("comparison_pct", 0.0)
        direction = "lower" if comparison < 0 else "higher"
        comparison_abs = abs(comparison)
        return (
            f"Requests that require data from HPNS have been approx. {ratio.get('current_value', 0):.1f}% of total, "
            f"which is {comparison_abs:.1f}% {direction} than last week."
        )

    def _capacity_trend(self, tsys_capacity: Dict[str, float], hpns_capacity: Dict[str, float]) -> str:
        tsys_val = tsys_capacity.get("current_value", 0.0)
        hpns_val = hpns_capacity.get("current_value", 0.0)
        max_val = max(tsys_val, hpns_val)
        if max_val >= self._thresholds.capacity_critical:
            service = "TSYS" if tsys_val >= hpns_val else "HPNS"
            return (
                f"⚠️ Capacity utilization is elevated at {max_val:.1f}% for {service}. "
                "Recommend monitoring closely."
            )
        if max_val >= self._thresholds.capacity_warning:
            return (
                "Capacity utilization is elevated but manageable "
                f"(TSYS: {tsys_val:.1f}%, HPNS: {hpns_val:.1f}%). Monitoring trends."
            )
        return "Growth is closely matching last week's behavior. There are no capacity concerns at this time."

    def _trend_phrase(self, service_name: str, metric: Dict[str, float]) -> str:
        comparison = abs(metric.get("comparison_pct", 0.0))
        trend = metric.get("trend", "neutral")
        if trend == "up":
            return f"The TPS is {comparison:.1f}% higher than last week for {service_name}"
        if trend == "down":
            return f"The TPS is {comparison:.1f}% lower than last week for {service_name}"
        return f"The TPS is stable for {service_name}"

    def _traffic_status(self, tsys: Dict[str, float] | None, hpns: Dict[str, float] | None) -> str:
        tsys_val = (tsys or {}).get("current_value", 0.0)
        hpns_val = (hpns or {}).get("current_value", 0.0)
        if tsys_val > 2000 and hpns_val > 800:
            return "🟢"
        if tsys_val > 1000 or hpns_val > 400:
            return "🟡"
        return "🔴"

    def _capacity_status(self, tsys_capacity: Dict[str, float] | None, hpns_capacity: Dict[str, float] | None) -> str:
        tsys_val = (tsys_capacity or {}).get("current_value", 0.0)
        hpns_val = (hpns_capacity or {}).get("current_value", 0.0)
        max_val = max(tsys_val, hpns_val)
        if max_val >= self._thresholds.capacity_critical:
            return "🔴"
        if max_val >= self._thresholds.capacity_warning:
            return "🟡"
        return "🟢"


__all__ = ["TrendTranslator", "AnalysisResult"]
