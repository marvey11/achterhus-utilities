from collections.abc import Generator
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import ClassVar

from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from document_router import app
from document_router import main as app_main
from document_router.core.models import DocumentMetadata, ProcessingJob


class StubProcessor:
    def execute_job(self, _: ProcessingJob) -> str:
        return "MOVE -> archived.pdf"


def _null_context(_: str) -> nullcontext[None]:
    return nullcontext(None)


class StubEngine:
    jobs: ClassVar[list[ProcessingJob]] = []

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        self.processor = StubProcessor()

    def discover_and_plan(self) -> list[ProcessingJob]:
        return self.jobs


def test_cli_reports_empty_source(
    monkeypatch: MonkeyPatch, mocker: MockerFixture, tmp_path: Path
) -> None:
    mocker.patch.object(app_main, "DocumentRouterEngine", StubEngine)
    monkeypatch.setenv("TELEMETRY_API_URL", "http://telemetry:9000")
    mocker.patch("document_router.main.telemetry_context", _null_context)

    StubEngine.jobs = []

    result = CliRunner().invoke(app, [str(tmp_path), str(tmp_path / "target")])

    assert result.exit_code == 0
    assert "No matchable documents found" in result.output


def test_cli_executes_and_displays_routing_job(
    monkeypatch: MonkeyPatch, mocker: MockerFixture, tmp_path: Path
) -> None:
    mocker.patch.object(app_main, "DocumentRouterEngine", StubEngine)
    monkeypatch.setenv("TELEMETRY_API_URL", "http://telemetry:9000")
    mocker.patch("document_router.main.telemetry_context", _null_context)

    source = tmp_path / "provider" / "invoice.pdf"

    StubEngine.jobs = [
        ProcessingJob(
            source_base_path=tmp_path,
            source_file_path=source,
            target_base_path=tmp_path / "target",
            metadata=DocumentMetadata(provider="provider"),
        )
    ]

    result = CliRunner().invoke(app, [str(tmp_path), str(tmp_path / "target")])

    assert result.exit_code == 0
    assert "Routing Execution Summary" in result.output
    assert "archived.pdf" in result.output


def test_cli_returns_error_for_engine_failure(
    monkeypatch: MonkeyPatch, mocker: MockerFixture, tmp_path: Path
) -> None:
    class FailingEngine(StubEngine):
        def discover_and_plan(self) -> list[ProcessingJob]:
            raise OSError("source unavailable")

    monkeypatch.setenv("TELEMETRY_API_URL", "http://telemetry:9000")
    mocker.patch.object(app_main, "DocumentRouterEngine", FailingEngine)
    mocker.patch("document_router.main.telemetry_context", _null_context)

    result = CliRunner().invoke(app, [str(tmp_path), str(tmp_path / "target")])

    assert result.exit_code == 1
    assert "source unavailable" in result.output


def test_cli_reports_action_metrics(
    monkeypatch: MonkeyPatch, mocker: MockerFixture, tmp_path: Path
) -> None:
    class FakeTelemetry:
        def __init__(self) -> None:
            self.metrics: dict[str, object] = {}

        def set_metrics(self, metrics: dict[str, object]) -> None:
            self.metrics = metrics

    telemetry = FakeTelemetry()

    @contextmanager
    def telemetry_scope(_: str) -> Generator[FakeTelemetry, None, None]:
        yield telemetry

    mocker.patch.object(app_main, "DocumentRouterEngine", StubEngine)
    monkeypatch.setenv("TELEMETRY_API_URL", "http://telemetry:9000")
    mocker.patch("document_router.main.telemetry_context", telemetry_scope)

    StubEngine.jobs = [
        ProcessingJob(
            source_base_path=tmp_path,
            source_file_path=tmp_path / "provider" / "invoice.pdf",
            target_base_path=tmp_path / "target",
            metadata=DocumentMetadata(provider="provider"),
        )
    ]

    result = CliRunner().invoke(
        app, [str(tmp_path), str(tmp_path / "target"), "--dry-run"]
    )

    assert result.exit_code == 0
    assert telemetry.metrics == {
        "jobs": 1,
        "moved": 1,
        "copied": 0,
        "ignored": 0,
        "quarantined": 0,
        "dry_run": True,
    }
