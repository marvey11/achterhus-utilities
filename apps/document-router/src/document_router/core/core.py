from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field


class RoutingAction(StrEnum):
    COPY = "copy"
    MOVE = "move"
    QUARANTINE = "quarantine"


class RoutingResult(BaseModel):
    """Output contract produced by a processor after analyzing a document."""

    source_path: Path
    destination_path: Path
    processor_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    action: RoutingAction = RoutingAction.MOVE


class DocumentProcessor(Protocol):
    """Protocol defining the mandatory interface for all routing processors."""

    name: str

    def can_handle(self, file_path: Path) -> bool:
        """
        Lightweight check (e.g., file extension, subfolder match, or header check).
        """
        ...

    def process(self, file_path: Path) -> RoutingResult | None:
        """Extract metadata, resolve target path, and return routing instructions."""
        ...
