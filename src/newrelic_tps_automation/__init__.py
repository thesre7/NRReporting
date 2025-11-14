"""Enterprise-ready New Relic TPS automation package."""

from importlib import metadata


def get_version() -> str:
    """Return the installed package version or the dev fallback."""
    try:
        return metadata.version("newrelic_tps_automation")
    except metadata.PackageNotFoundError:  # pragma: no cover - local dev only
        return "0.1.0-dev"


__all__ = ["get_version"]
