"""Service orchestrating dashboard fetch and parsing."""

from __future__ import annotations

import logging
from typing import Dict

from ..clients.newrelic_client import NewRelicDashboardClient
from .widget_parser import WidgetParser

logger = logging.getLogger(__name__)


class DashboardService:
    """High-level facade that returns normalized dashboard metrics."""

    def __init__(self, client: NewRelicDashboardClient, parser: WidgetParser | None = None) -> None:
        self._client = client
        self._parser = parser or WidgetParser()

    def get_metrics(self) -> Dict[str, dict]:
        """Fetch widgets and parse into the normalized KPI dictionary."""

        widgets = self._client.fetch_widgets()
        if not widgets:
            logger.warning("No widgets returned from dashboard GUID %s", self._client._dashboard_guid)
        metrics = self._parser.parse(widgets)
        logger.debug("Normalized metrics: %s", metrics)
        return metrics


__all__ = ["DashboardService"]
