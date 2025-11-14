"""Delivery channels for the TPS automation report."""

from __future__ import annotations

import logging
from typing import Iterable, Optional

import requests
from msal import ConfidentialClientApplication

logger = logging.getLogger(__name__)


class SlackDelivery:
    """Send messages via Slack incoming webhooks."""

    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url

    def send(self, message: str) -> bool:
        try:
            response = requests.post(
                self._webhook_url,
                json={"text": message, "mrkdwn": True},
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Report sent to Slack")
            return True
        except requests.RequestException as exc:  # pragma: no cover - network
            logger.error("Failed to send Slack message: %s", exc)
            return False


class O365EmailDelivery:
    """Send HTML emails via Microsoft Graph using OAuth 2.0."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, sender_email: str):
        self._sender_email = sender_email
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self._app = ConfidentialClientApplication(
            client_id=client_id,
            authority=authority,
            client_credential=client_secret,
        )
        self._scope = ["https://graph.microsoft.com/.default"]

    def _get_token(self) -> str:
        result = self._app.acquire_token_silent(self._scope, account=None)
        if not result:
            result = self._app.acquire_token_for_client(scopes=self._scope)
        if "access_token" not in result:
            raise RuntimeError(f"Failed to acquire access token: {result}")
        return result["access_token"]

    def send(self, subject: str, body: str, recipients: Iterable[str]) -> bool:
        token = self._get_token()
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body},
                "toRecipients": [
                    {"emailAddress": {"address": recipient.strip()}}
                    for recipient in recipients
                    if recipient.strip()
                ],
            },
            "saveToSentItems": "true",
        }
        try:
            response = requests.post(
                f"https://graph.microsoft.com/v1.0/users/{self._sender_email}/sendMail",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Report email sent via Microsoft Graph")
            return True
        except requests.RequestException as exc:  # pragma: no cover - network
            logger.error("Failed to send email: %s", exc)
            return False


__all__ = ["SlackDelivery", "O365EmailDelivery"]
