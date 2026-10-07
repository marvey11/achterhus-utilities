"""Shared telemetry context for Achterhus worker applications."""

import os
from collections.abc import Iterator
from contextlib import contextmanager

from telemetry.client import TelemetryClient


@contextmanager
def telemetry_context(service_name: str) -> Iterator[TelemetryClient | None]:
    """Create a telemetry client when the orchestrator supplied a run ID."""
    if not os.getenv("SERVICE_RUN_ID"):
        yield None
        return

    api_url = os.getenv("TELEMETRY_API_URL", "http://localhost:8000")
    with TelemetryClient(api_url, service_name=service_name) as telemetry:
        yield telemetry
