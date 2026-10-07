import re
from datetime import date
from pathlib import Path

from document_router.core.models import ActionType, DocumentMetadata
from document_router.parsers.base import BaseDocumentParser


class VodafoneParser(BaseDocumentParser):
    """Parser for Vodafone invoices and communications."""

    @property
    def provider_id(self) -> str:
        return "vodafone"

    def parse(self, file_path: Path) -> DocumentMetadata | None:
        filename = file_path.name

        pattern = (
            r"^(?P<date>\d{4}-\d{2}-\d{2})_Rechnung_Kundennr_(?P<account>\d+)\.pdf$"
        )
        match = re.match(pattern, filename, re.IGNORECASE)

        if not match:
            return None

        try:
            doc_date = date.fromisoformat(match.group("date"))
        except ValueError:
            return None

        year = doc_date.year
        return DocumentMetadata(
            provider=self.provider_id,
            document_type="invoice",
            document_date=doc_date,
            target_subfolder=Path("telecom/vodafone.com") / str(year),
            target_filename=filename,
            action=ActionType.MOVE,
        )
