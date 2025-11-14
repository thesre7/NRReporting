"""End-to-end pipeline for generating and delivering TPS reports."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, Optional

from .config import AppConfig
from .reporting.context import ReportContextBuilder
from .reporting.renderer import TemplateRenderer
from .services.dashboard_service import DashboardService
from .services.trend_translator import TrendTranslator
from .services.widget_parser import WidgetParser
from .clients.newrelic_client import NewRelicDashboardClient
from .secrets import SecretsProvider, extract_secret_field

logger = logging.getLogger(__name__)


class TPSReportPipeline:
    """Coordinates data retrieval, translation, rendering, and delivery."""

    def __init__(
        self,
        config: AppConfig,
        secrets_provider: SecretsProvider,
        templates_dir: Path,
    ) -> None:
        self._config = config
        self._secrets = secrets_provider
        self._renderer = TemplateRenderer(templates_dir)
        self._context_builder = ReportContextBuilder(config.report)
        self._translator = TrendTranslator(config.thresholds)

    def run(
        self,
        deliveries: Dict[str, object],
        event_name: Optional[str] = None,
    ) -> str:
        """Execute the report generation pipeline. Returns rendered report."""

        api_key = self._get_new_relic_api_key()
        client = NewRelicDashboardClient(api_key=api_key, dashboard_guid=self._config.dashboard_guid)
        dashboard_service = DashboardService(client, parser=WidgetParser())
        metrics = dashboard_service.get_metrics()
        if not metrics:
            raise RuntimeError("No metrics could be parsed from the dashboard response")

        analysis = self._translator.translate(metrics)
        context = self._context_builder.build(metrics, analysis, event_name=event_name)
        report = self._renderer.render("tps_report.j2", context.as_dict())

        self._deliver(report, deliveries, context)
        return report

    def _get_new_relic_api_key(self) -> str:
        secret_id = self._config.secret_refs.new_relic_api_key
        payload = self._secrets.get_secret(secret_id)
        api_key = extract_secret_field(payload, "api_key", "key", default=None)
        if not api_key:
            raise RuntimeError(f"Secret {secret_id} did not contain a New Relic API key")
        return api_key

    def _deliver(self, report: str, deliveries: Dict[str, object], context) -> None:
        if not deliveries:
            logger.info("No delivery channels configured; printing to stdout")
            print(report)
            return

        for name, delivery in deliveries.items():
            if name == "slack":
                delivery.send(report)
            elif name == "email":
                recipients = delivery.get("recipients")  # type: ignore[assignment]
                client = delivery.get("client")
                if client and recipients:
                    subject = f"TPS Report: {context.event_name}"
                    html_body = report.replace("\n", "<br>")
                    client.send(subject, html_body, recipients)
            else:
                logger.warning("Unsupported delivery channel: %s", name)


__all__ = ["TPSReportPipeline"]
