from pathlib import Path

from codescape.parse import BankIdentifier, DocumentCategory, parse_document
from codescape.parse import DocumentMetadata as BankDocumentMetadata

from document_router.core.models import ActionType, DocumentMetadata
from document_router.parsers.base import BaseDocumentParser


class ScalableParser(BaseDocumentParser):
    """Parser for Scalable Capital bank documents."""

    @property
    def provider_id(self) -> str:
        return BankIdentifier.SCALABLE

    def parse(self, file_path: Path) -> DocumentMetadata | None:

        metadata: BankDocumentMetadata | None = parse_document(file_path)

        if not metadata:
            return None

        if metadata.bank != BankIdentifier.SCALABLE:
            return None

        # For now, ignore documents that are not account statements
        if metadata.category not in [DocumentCategory.ACCOUNT_STATEMENT]:
            return None

        year: int | None = None
        if metadata.statement_period_year:
            year = metadata.statement_period_year
        elif metadata.document_date:
            year = metadata.document_date.year

        target_folder = (
            Path("finances")
            / "scalable"
            / "statements"
            / (str(year) if year else "unknown")
        )

        return DocumentMetadata(
            provider=self.provider_id,
            document_type=metadata.category.value,
            document_date=metadata.document_date,
            target_subfolder=target_folder,
            target_filename=file_path.name,
            action=ActionType.MOVE,
        )
