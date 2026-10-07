from pathlib import Path

import pytest

from document_router.core.engine import DocumentRouterEngine
from document_router.core.models import ActionType, DocumentMetadata
from document_router.core.utils import calculate_sha256
from document_router.parsers.base import BaseDocumentParser
from document_router.parsers.naturstrom import NaturstromParser


class FixedParser(BaseDocumentParser):
    @property
    def provider_id(self) -> str:
        return "sample"

    def parse(self, file_path: Path) -> DocumentMetadata | None:
        if file_path.name == "broken.pdf":
            raise ValueError("bad document")
        if file_path.name == "unknown.pdf":
            return None
        return DocumentMetadata(provider=self.provider_id)


def test_register_parser_rejects_duplicate_provider(tmp_path: Path) -> None:
    engine = DocumentRouterEngine(tmp_path, tmp_path / "target")

    with pytest.raises(ValueError, match="already registered"):
        engine.register_parser(NaturstromParser())


def test_engine_registers_built_in_parsers(tmp_path: Path) -> None:
    engine = DocumentRouterEngine(tmp_path, tmp_path / "target")

    assert set(engine._parsers) == {"naturstrom", "ryd", "scalable", "vodafone"}


def test_discover_and_plan_handles_provider_files_and_duplicates(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    provider = source / "sample"
    provider.mkdir(parents=True)
    (provider / "first.pdf").write_bytes(b"same content")
    (provider / "duplicate.pdf").write_bytes(b"same content")
    (provider / "unknown.pdf").write_bytes(b"unknown")
    (provider / "broken.pdf").write_bytes(b"broken")
    (source / "root.pdf").write_bytes(b"root")
    (source / "unregistered").mkdir()
    (source / "unregistered" / "ignored.pdf").write_bytes(b"ignored")

    engine = DocumentRouterEngine(source, tmp_path / "target")
    engine.register_parser(FixedParser())

    jobs = engine.discover_and_plan()

    assert len(jobs) == 4
    by_name = {job.source_file_path.name: job.metadata for job in jobs}
    duplicate_metadata = (by_name["first.pdf"], by_name["duplicate.pdf"])
    assert sorted(metadata.action.name for metadata in duplicate_metadata) == [
        "MOVE",
        "QUARANTINE",
    ]
    quarantined_duplicate = next(
        metadata
        for metadata in duplicate_metadata
        if metadata.action == ActionType.QUARANTINE
    )
    assert "Duplicate source content" in (quarantined_duplicate.quarantine_reason or "")
    assert by_name["unknown.pdf"].action == ActionType.IGNORE
    assert by_name["broken.pdf"].action == ActionType.QUARANTINE
    assert by_name["first.pdf"].hash_sha256 == calculate_sha256(provider / "first.pdf")


def test_discover_and_plan_requires_source_directory(tmp_path: Path) -> None:
    engine = DocumentRouterEngine(tmp_path / "missing", tmp_path / "target")

    with pytest.raises(FileNotFoundError, match="Source directory does not exist"):
        engine.discover_and_plan()
