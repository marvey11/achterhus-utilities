from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast

from core import telemetry

if TYPE_CHECKING:
    import pytest


def test_telemetry_context_is_disabled_without_run_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SERVICE_RUN_ID", raising=False)

    with telemetry.telemetry_context("test-service") as client:
        assert client is None


def test_telemetry_context_uses_configured_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def __init__(self, api_url: str, *, service_name: str) -> None:
            self.api_url = api_url
            self.service_name = service_name

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_: object) -> None:
            return None

    monkeypatch.setenv("SERVICE_RUN_ID", "run-123")
    monkeypatch.setenv("TELEMETRY_API_URL", "http://telemetry:9000")
    monkeypatch.setattr(telemetry, "TelemetryClient", FakeClient)

    with telemetry.telemetry_context("test-service") as client:
        assert client is not None
        fake_client = cast("FakeClient", client)
        assert fake_client.api_url == "http://telemetry:9000"
        assert fake_client.service_name == "test-service"
