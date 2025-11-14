"""Enterprise secrets management helpers."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, Optional

import boto3
import hvac
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)


class SecretsProvider(ABC):
    """Abstract secrets provider interface."""

    @abstractmethod
    def get_secret(self, secret_id: str) -> Any:  # pragma: no cover - interface
        """Return the secret payload identified by *secret_id*."""


class AWSSecretsProvider(SecretsProvider):
    """AWS Secrets Manager implementation."""

    def __init__(self, region_name: Optional[str] = None):
        self._client = boto3.client("secretsmanager", region_name=region_name)

    def get_secret(self, secret_id: str) -> Any:
        logger.debug("Fetching secret %s from AWS Secrets Manager", secret_id)
        response = self._client.get_secret_value(SecretId=secret_id)
        secret = response.get("SecretString") or response.get("SecretBinary")
        return _maybe_parse_json(secret)


class VaultSecretsProvider(SecretsProvider):
    """HashiCorp Vault implementation."""

    def __init__(self, url: str, token: str, mount_point: str = "secret"):
        self._client = hvac.Client(url=url, token=token)
        self._mount_point = mount_point

    def get_secret(self, secret_id: str) -> Any:
        logger.debug("Fetching secret %s from Vault", secret_id)
        response = self._client.secrets.kv.v2.read_secret_version(
            path=secret_id, mount_point=self._mount_point
        )
        data = response.get("data", {}).get("data", {})
        return data


class AzureKeyVaultProvider(SecretsProvider):
    """Azure Key Vault implementation."""

    def __init__(self, vault_url: str, credential: Optional[DefaultAzureCredential] = None):
        self._credential = credential or DefaultAzureCredential()
        self._client = SecretClient(vault_url=vault_url, credential=self._credential)

    def get_secret(self, secret_id: str) -> Any:
        logger.debug("Fetching secret %s from Azure Key Vault", secret_id)
        secret = self._client.get_secret(secret_id)
        return _maybe_parse_json(secret.value)


def _maybe_parse_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not value:
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def extract_secret_field(secret_payload: Any, *keys: str, default: Optional[str] = None) -> Optional[str]:
    """Extract a single string field from a secret payload, trying multiple keys."""

    if secret_payload is None:
        return default
    if isinstance(secret_payload, str):
        return secret_payload
    if isinstance(secret_payload, dict):
        for key in keys:
            if key in secret_payload:
                return secret_payload[key]
    return default


@lru_cache(maxsize=1)
def get_secrets_provider(name: str, **kwargs: Any) -> SecretsProvider:
    """Factory returning the configured secrets provider."""

    normalized = name.lower()
    if normalized == "aws":
        return AWSSecretsProvider(region_name=kwargs.get("region_name"))
    if normalized == "vault":
        url = kwargs.get("url")
        token = kwargs.get("token")
        if not url or not token:
            raise RuntimeError("Vault provider requires url and token")
        return VaultSecretsProvider(url=url, token=token, mount_point=kwargs.get("mount_point", "secret"))
    if normalized == "azure":
        vault_url = kwargs.get("vault_url")
        if not vault_url:
            raise RuntimeError("Azure provider requires vault_url")
        return AzureKeyVaultProvider(vault_url=vault_url)
    raise ValueError(f"Unsupported secrets provider: {name}")


__all__ = [
    "SecretsProvider",
    "AWSSecretsProvider",
    "VaultSecretsProvider",
    "AzureKeyVaultProvider",
    "get_secrets_provider",
    "extract_secret_field",
]
