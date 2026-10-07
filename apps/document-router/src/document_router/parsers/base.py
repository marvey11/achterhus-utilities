"""Base class and specification for provider document parsers."""

from abc import ABC, abstractmethod
from pathlib import Path

from document_router.core.models import DocumentMetadata


class BaseDocumentParser(ABC):
    """Abstract base class for provider document parsers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Subfolder name inside drop-zone this parser registers to."""
        ...

    @abstractmethod
    def parse(self, file_path: Path) -> DocumentMetadata | None:
        """Parse a given file and return metadata, or None if it can't be handled."""
        ...
