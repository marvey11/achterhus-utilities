import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from document_router.core.models import ActionType, DocumentMetadata
from document_router.parsers.base import BaseDocumentParser


class RydParser(BaseDocumentParser):
    """Parser for invoices from ryd.one."""

    @property
    def provider_id(self) -> str:
        return "ryd"

    def parse(self, file_path: Path) -> DocumentMetadata | None:
        try:
            reader = PdfReader(file_path)
            pages_text: list[str] = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

        except Exception as err:
            return DocumentMetadata(
                provider=self.provider_id,
                action=ActionType.QUARANTINE,
                quarantine_reason=f"Failed to read PDF text: {err}",
            )

        document_text = "\n\n".join(pages_text)

        datum_match = re.search(
            r"Rechnungsdatum\:\s*\n\s*(\d{2}\.\d{2}\.\d{4})", document_text
        )

        if datum_match is None:
            # Invalid date or date not found
            return None

        try:
            doc_date = datetime.strptime(datum_match.group(1), "%d.%m.%Y").date()
        except ValueError:
            return None

        # prepend the ISO date
        target_filename = f"{doc_date.isoformat()}_{file_path.name}"

        return DocumentMetadata(
            provider=self.provider_id,
            document_date=doc_date,
            document_type="invoice",
            target_subfolder=Path("auto/ryd"),
            target_filename=target_filename,
            action=ActionType.MOVE,
        )
