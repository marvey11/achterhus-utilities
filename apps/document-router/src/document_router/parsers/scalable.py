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

        target_folder = self._construct_target_folder(metadata)

        if target_folder is None:
            return None

        return DocumentMetadata(
            provider=self.provider_id,
            document_type=metadata.category.value,
            document_date=metadata.document_date,
            target_subfolder=target_folder,
            target_filename=file_path.name,
            action=ActionType.MOVE,
        )

    def _construct_target_folder(self, metadata: BankDocumentMetadata) -> Path | None:
        """Construct the target folder path based on the document metadata."""

        if metadata.category == DocumentCategory.ACCOUNT_STATEMENT:
            year: int | None = None
            if metadata.statement_period_year:
                year = metadata.statement_period_year
            elif metadata.document_date:
                year = metadata.document_date.year

            return (
                Path("finances")
                / "scalable"
                / "statements"
                / (str(year) if year else "unknown")
            )

        if metadata.category in (
            DocumentCategory.CORPORATE_ACTION,
            DocumentCategory.SECURITY_TRANSACTION,
        ):
            if not metadata.security_identifier:
                return None

            return (
                Path("finances")
                / "scalable"
                / "securities"
                / metadata.security_identifier
            )

        return None
