from pathlib import Path

from document_router.core.models import ActionType, DocumentMetadata, ProcessingJob
from document_router.core.processor import DocumentProcessor


def test_move_uses_atomic_move_and_preserves_file_content(tmp_path: Path) -> None:
    source_base = tmp_path / "source"
    source = source_base / "provider" / "invoice.pdf"
    target_base = tmp_path / "target"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"invoice content")
    job = ProcessingJob(
        source_base_path=source_base,
        source_file_path=source,
        target_base_path=target_base,
        metadata=DocumentMetadata(provider="provider", action=ActionType.MOVE),
    )

    result = DocumentProcessor().execute_job(job)

    assert result == "MOVE -> invoice.pdf"
    assert not source.exists()
    assert (target_base / "invoice.pdf").read_bytes() == b"invoice content"


def test_processor_ignores_without_moving_source(tmp_path: Path) -> None:
    source, job = _job(tmp_path, ActionType.IGNORE, ignore_reason="unsupported")

    result = DocumentProcessor().execute_job(job)

    assert result == "IGNORE (unsupported)"
    assert source.exists()


def test_processor_dry_run_does_not_move_source(tmp_path: Path) -> None:
    source, job = _job(tmp_path, ActionType.MOVE)

    result = DocumentProcessor(dry_run=True).execute_job(job)

    assert result == "MOVE -> invoice.pdf"
    assert source.exists()


def test_processor_quarantines_file(tmp_path: Path) -> None:
    source, job = _job(
        tmp_path, ActionType.QUARANTINE, quarantine_reason="invalid document"
    )

    result = DocumentProcessor().execute_job(job)

    assert result == "QUARANTINED (invalid document)"
    assert not source.exists()
    assert (tmp_path / "source" / ".quarantine" / "provider" / "invoice.pdf").exists()


def test_processor_avoids_overwriting_different_content(tmp_path: Path) -> None:
    _, job = _job(tmp_path, ActionType.MOVE)
    target = tmp_path / "target" / "invoice.pdf"
    target.parent.mkdir()
    target.write_bytes(b"existing")

    result = DocumentProcessor().execute_job(job)

    assert result == "MOVE -> invoice_001.pdf"
    assert target.read_bytes() == b"existing"
    assert (target.parent / "invoice_001.pdf").read_bytes() == b"invoice content"


def _job(
    tmp_path: Path,
    action: ActionType,
    ignore_reason: str | None = None,
    quarantine_reason: str | None = None,
) -> tuple[Path, ProcessingJob]:
    source_base = tmp_path / "source"
    source = source_base / "provider" / "invoice.pdf"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"invoice content")
    job = ProcessingJob(
        source_base_path=source_base,
        source_file_path=source,
        target_base_path=tmp_path / "target",
        metadata=DocumentMetadata(
            provider="provider",
            action=action,
            ignore_reason=ignore_reason,
            quarantine_reason=quarantine_reason,
        ),
    )
    return source, job
