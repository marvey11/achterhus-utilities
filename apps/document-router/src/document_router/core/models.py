"""Domain models for document routing and parsing lifecycle."""

from datetime import date
from enum import Enum, auto
from pathlib import Path

from pydantic import BaseModel


class ActionType(Enum):
    """Supported processing actions for routed files."""

    MOVE = auto()
    COPY = auto()
    IGNORE = auto()
    QUARANTINE = auto()


class DocumentMetadata(BaseModel):
    """Metadata extracted by provider-specific parsers."""

    provider: str
    document_type: str = "generic"
    document_date: date | None = None
    target_filename: str | None = None
    target_subfolder: Path | None = None
    action: ActionType = ActionType.MOVE
    quarantine_reason: str | None = None
    ignore_reason: str | None = None
    hash_sha256: str | None = None


class ProcessingJob(BaseModel):
    """A single queued operation to be executed after parsing."""

    source_base_path: Path
    source_file_path: Path
    target_base_path: Path
    metadata: DocumentMetadata

    def resolve_target_path(self) -> Path:
        """Determines initial target destination based on metadata rules."""
        base = self.target_base_path
        if self.metadata.target_subfolder:
            base = base / self.metadata.target_subfolder

        filename = self.metadata.target_filename or self.source_file_path.name
        return base / filename
