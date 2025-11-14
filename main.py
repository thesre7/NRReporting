"""Command-line entry point for the New Relic TPS automation pipeline."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from src.newrelic_tps_automation.config import AppConfig, load_config
from src.newrelic_tps_automation.delivery import O365EmailDelivery, SlackDelivery
from src.newrelic_tps_automation.pipeline import TPSReportPipeline
from src.newrelic_tps_automation.secrets import (
    SecretsProvider,
    extract_secret_field,
    get_secrets_provider,
)

ROOT_DIR = Path(__file__).parent
TEMPLATES_DIR = ROOT_DIR / "templates"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate TPS/Capacity status reports from New Relic dashboards",
    )
    parser.add_argument("--env-file", type=str, help="Optional path to .env file")
    parser.add_argument(
        "--delivery",
        choices=["console", "slack", "email", "both"],
        default="slack",
        help="Delivery target for the report",
    )
    parser.add_argument("--event-name", type=str, help="Override event name in the report")
    parser.add_argument(
        "--templates-dir",
        type=str,
        default=str(TEMPLATES_DIR),
        help="Directory containing Jinja2 templates",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Python logging level (e.g., INFO, DEBUG)",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def build_secrets_provider(config: AppConfig) -> SecretsProvider:
    provider = config.secrets_provider.lower()
    if provider == "aws":
        return get_secrets_provider("aws", region_name=os.getenv("AWS_REGION"))
    if provider == "vault":
        return get_secrets_provider(
            "vault",
            url=os.getenv("VAULT_ADDR"),
            token=os.getenv("VAULT_TOKEN"),
            mount_point=os.getenv("VAULT_MOUNT", "secret"),
        )
    if provider == "azure":
        return get_secrets_provider("azure", vault_url=os.getenv("AZURE_KEY_VAULT_URL"))
    raise ValueError(f"Unsupported secrets provider: {provider}")


def build_deliveries(config: AppConfig, secrets: SecretsProvider, delivery_mode: str) -> Dict[str, object]:
    deliveries: Dict[str, object] = {}
    if delivery_mode in {"slack", "both"}:
        slack_delivery = _build_slack_delivery(config, secrets)
        if slack_delivery:
            deliveries["slack"] = slack_delivery
    if delivery_mode in {"email", "both"}:
        email_payload = _build_email_delivery(config, secrets)
        if email_payload:
            deliveries["email"] = email_payload
    return deliveries


def _build_slack_delivery(config: AppConfig, secrets: SecretsProvider) -> Optional[SlackDelivery]:
    secret_id = config.secret_refs.slack_webhook
    if not secret_id:
        logging.warning("Slack delivery requested but SECRET_ID_SLACK_WEBHOOK not configured")
        return None
    payload = secrets.get_secret(secret_id)
    webhook = extract_secret_field(payload, "url", "webhook", default=payload if isinstance(payload, str) else None)
    if not webhook:
        logging.warning("Slack secret %s did not contain a webhook URL", secret_id)
        return None
    return SlackDelivery(webhook)


def _build_email_delivery(config: AppConfig, secrets: SecretsProvider) -> Optional[Dict[str, object]]:
    secret_id = config.secret_refs.o365_credentials
    if not secret_id:
        logging.warning("Email delivery requested but SECRET_ID_O365_CREDENTIALS not configured")
        return None
    payload = secrets.get_secret(secret_id)
    tenant_id = extract_secret_field(payload, "tenant_id", "tenant")
    client_id = extract_secret_field(payload, "client_id", "app_id")
    client_secret = extract_secret_field(payload, "client_secret", "secret")
    sender_email = extract_secret_field(payload, "sender_email", "from")
    if not all([tenant_id, client_id, client_secret, sender_email]):
        logging.warning("O365 secret %s missing required fields", secret_id)
        return None
    recipients = _get_email_recipients()
    if not recipients:
        logging.warning("EMAIL_RECIPIENTS not configured; skipping email delivery")
        return None
    client = O365EmailDelivery(tenant_id, client_id, client_secret, sender_email)
    return {"client": client, "recipients": recipients}


def _get_email_recipients() -> List[str]:
    raw = os.getenv("EMAIL_RECIPIENTS", "")
    return [recipient.strip() for recipient in raw.split(",") if recipient.strip()]


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)

    env_path = Path(args.env_file) if args.env_file else None
    config = load_config(env_path)
    secrets_provider = build_secrets_provider(config)

    pipeline = TPSReportPipeline(
        config=config,
        secrets_provider=secrets_provider,
        templates_dir=Path(args.templates_dir),
    )

    deliveries = build_deliveries(config, secrets_provider, args.delivery)
    pipeline.run(deliveries=deliveries, event_name=args.event_name)


if __name__ == "__main__":
    main()
