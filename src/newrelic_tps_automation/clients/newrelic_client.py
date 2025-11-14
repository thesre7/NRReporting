"""Client for retrieving New Relic dashboard widget data via NerdGraph."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


class NewRelicDashboardClient:
    """Thin wrapper around the NerdGraph API for dashboard widgets."""

    GRAPHQL_URL = "https://api.newrelic.com/graphql"

    def __init__(self, api_key: str, dashboard_guid: str) -> None:
        self._dashboard_guid = dashboard_guid
        self._session = requests.Session()
        self._session.headers.update(
            {
                "API-Key": api_key,
                "Content-Type": "application/json",
            }
        )

    def fetch_widgets(self) -> List[Dict[str, Any]]:
        """Return all widgets for the configured dashboard."""

        logger.info("Fetching dashboard widgets for %s", self._dashboard_guid)
        payload = {"query": self._widgets_query(self._dashboard_guid)}
        response = self._session.post(self.GRAPHQL_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        errors = data.get("errors")
        if errors:
            logger.error("NerdGraph returned errors: %s", errors)
            raise RuntimeError(f"Dashboard query failed: {errors}")

        pages = (
            data.get("data", {})
            .get("actor", {})
            .get("entity", {})
            .get("pages", [])
        )

        widgets: List[Dict[str, Any]] = []
        for page in pages:
            widgets.extend(page.get("widgets", []))
        logger.debug("Fetched %d widgets", len(widgets))
        return widgets

    @staticmethod
    def _widgets_query(guid: str) -> str:
        return f"""
        {{
          actor {{
            entity(guid: \"{guid}\") {{
              ... on DashboardEntity {{
                pages {{
                  widgets {{
                    id
                    title
                    visualization {{ id }}
                    rawConfiguration
                    layout {{ column row width height }}
                    data {{
                      raw
                      visualization
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """


__all__ = ["NewRelicDashboardClient"]
