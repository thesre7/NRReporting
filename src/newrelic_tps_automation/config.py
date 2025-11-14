"""Configuration helpers for the New Relic TPS automation service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class MetricThresholds:
    """Thresholds used to classify capacity utilization."""

    capacity_warning: float = 70.0
    capacity_critical: float = 85.0


@dataclass(frozen=True)
class ReportConfig:
    """Human-facing report metadata."""

    timezone: str = "US/Eastern"
    event_name: str = "Weekend Performance Report"
    dashboard_url: str = ""
    user_name: str = "SRE Automation"


@dataclass(frozen=True)
class SecretRefs:
    """Logical secret identifiers in the enterprise vault."""

    new_relic_api_key: str = "prod/newrelic/api-key"
    slack_webhook: Optional[str] = None
    o365_credentials: Optional[str] = None


@dataclass(frozen=True)
class AppConfig:
    """Complete runtime configuration bundle."""

    new_relic_account_id: str
    dashboard_guid: str
    secrets_provider: str
    thresholds: MetricThresholds
    report: ReportConfig
    secret_refs: SecretRefs


def load_config(env_file: Optional[Path] = None) -> AppConfig:
    """Load configuration from environment variables (optionally .env)."""

    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    account_id = _require_env("NEW_RELIC_ACCOUNT_ID")
    dashboard_guid = _require_env("DASHBOARD_GUID")
    secrets_provider = _get_env("SECRETS_PROVIDER", "aws").lower()

    thresholds = MetricThresholds(
        capacity_warning=float(_get_env("THRESHOLD_CAPACITY_WARNING", 70)),
        capacity_critical=float(_get_env("THRESHOLD_CAPACITY_CRITICAL", 85)),
    )

    report = ReportConfig(
        timezone=_get_env("REPORT_TIMEZONE", "US/Eastern"),
        event_name=_get_env("EVENT_NAME", "Weekend Performance Report"),
        dashboard_url=_get_env("DASHBOARD_URL", ""),
        user_name=_get_env("REPORT_USER_NAME", "SRE Automation"),
    )

    secret_refs = SecretRefs(
        new_relic_api_key=_get_env("SECRET_ID_NEW_RELIC_API_KEY", "prod/newrelic/api-key"),
        slack_webhook=_get_env("SECRET_ID_SLACK_WEBHOOK"),
        o365_credentials=_get_env("SECRET_ID_O365_CREDENTIALS"),
    )

    return AppConfig(
        new_relic_account_id=account_id,
        dashboard_guid=dashboard_guid,
        secrets_provider=secrets_provider,
        thresholds=thresholds,
        report=report,
        secret_refs=secret_refs,
    )


def _require_env(key: str) -> str:
    value = _get_env(key)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    import os

    value = os.getenv(key)
    if value is None:
        return default
    return value


__all__ = [
    "AppConfig",
    "MetricThresholds",
    "ReportConfig",
    "SecretRefs",
    "load_config",
]
