"""Main document routing engine connecting plugins, scanning, and execution."""

from pathlib import Path

from document_router.core.models import ActionType, DocumentMetadata, ProcessingJob
from document_router.core.processor import DocumentProcessor
from document_router.core.utils import calculate_sha256
from document_router.parsers.base import BaseDocumentParser
from document_router.parsers.naturstrom import NaturstromParser
from document_router.parsers.ryd import RydParser
from document_router.parsers.scalable import ScalableParser
from document_router.parsers.vodafone import VodafoneParser


class DocumentRouterEngine:
    """Orchestrates directory traversal, parser matching, and job execution."""

    def __init__(
        self, source_dir: Path, target_dir: Path, dry_run: bool = False
    ) -> None:
        self.source_dir = source_dir.resolve()
        self.target_dir = target_dir.resolve()
        self.processor = DocumentProcessor(dry_run=dry_run)
        self._parsers: dict[str, BaseDocumentParser] = {}
        for parser in (
            NaturstromParser(),
            RydParser(),
            ScalableParser(),
            VodafoneParser(),
        ):
            self.register_parser(parser)

    def register_parser(self, parser: BaseDocumentParser) -> None:
        """Register a parser for its provider folder, rejecting duplicates."""
        provider_id = parser.provider_id.lower()
        if provider_id in self._parsers:
            raise ValueError(f"A parser is already registered for {provider_id!r}.")
        self._parsers[provider_id] = parser

    def discover_and_plan(self) -> list[ProcessingJob]:
        """Scans drop-zone directory and constructs execution plan."""
        jobs: list[ProcessingJob] = []

        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {self.source_dir}"
            )

        for path in self.source_dir.rglob("*"):
            if not path.is_file():
                continue

            # Determine provider subfolder relative to drop zone base
            relative_path = path.relative_to(self.source_dir)
            if len(relative_path.parts) < 2:
                # File dropped directly in root source dir with no provider subfolder
                continue

            provider_key = relative_path.parts[0].lower()
            parser = self._parsers.get(provider_key)

            if parser is None:
                # Unregistered folder; ignored as specified
                continue

            try:
                metadata = parser.parse(path)
            except Exception as err:
                metadata = DocumentMetadata(
                    provider=provider_key,
                    action=ActionType.QUARANTINE,
                    quarantine_reason=f"Parser failure: {err}",
                )

            if metadata is None:
                # Document could not be matched by the parser.
                metadata = DocumentMetadata(
                    provider=provider_key,
                    action=ActionType.IGNORE,
                )

            if metadata.action in (ActionType.IGNORE, ActionType.QUARANTINE):
                # Document will not be moved to the target directory, and therefore
                # checking for source collisions is not required.
                jobs.append(
                    ProcessingJob(
                        source_base_path=self.source_dir,
                        target_base_path=self.target_dir,
                        source_file_path=path,
                        metadata=metadata,
                    )
                )
                continue

            # Avoid batch collision, i.e. two or more files in the provider's source
            # folder match. This could mean

            file_hash = calculate_sha256(path)
            metadata.hash_sha256 = file_hash

            filtered_jobs = [
                job for job in jobs if job.metadata.hash_sha256 == file_hash
            ]

            if len(filtered_jobs) > 0:
                metadata.action = ActionType.QUARANTINE
                matching_files = [str(x.source_file_path.name) for x in filtered_jobs]
                metadata.quarantine_reason = (
                    f"Duplicate source content (matches {', '.join(matching_files)})"
                )

            jobs.append(
                ProcessingJob(
                    source_base_path=self.source_dir,
                    target_base_path=self.target_dir,
                    source_file_path=path,
                    metadata=metadata,
                )
            )

        return jobs
