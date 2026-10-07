import re
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

from pypdf import PdfReader

from document_router.core.models import ActionType, DocumentMetadata
from document_router.parsers.base import BaseDocumentParser


class InvoiceType(StrEnum):
    CORRECTION = "Korrekturrechnung"
    CANCELLATION = "Stornierung"
    REGULAR = "Rechnung"


class ExtractedInvoiceData(TypedDict):
    contract_id: str | None
    date: date | None
    invoice_type: InvoiceType | None


# Regex pattern for both dd.mm.yyyy and dd. Month yyyy
DATE_PATTERN = re.compile(
    r"\b(?P<day>\d{1,2})\.\s*(?:(?P<month_num>\d{1,2})\.|\b(?P<month_name>[A-Za-zÄÖÜäöüß]+))\s*(?P<year>\d{4})\b"
)

GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


class NaturstromParser(BaseDocumentParser):
    """Parser for naturstrom invoices and communications."""

    @property
    def provider_id(self) -> str:
        return "naturstrom"

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
        extracted_fields = self._extract_fields(document_text)

        if (
            extracted_fields["contract_id"] is None
            or extracted_fields["date"] is None
            or extracted_fields["invoice_type"] is None
        ):
            return None

        iso_date = extracted_fields["date"]
        contract_id = extracted_fields["contract_id"]
        document_type = extracted_fields["invoice_type"].value
        target_filename = f"{iso_date}_{document_type}_{contract_id}.pdf"
        return DocumentMetadata(
            provider=self.provider_id,
            document_date=iso_date,
            document_type="invoice",
            target_subfolder=Path("strom/naturstrom.de/rechnungen"),
            target_filename=target_filename,
            action=ActionType.MOVE,
        )

    def _extract_fields(self, pdf_text: str) -> ExtractedInvoiceData:
        contract_match = re.search(r"Vertragsnummer\s*\n\s*([\d-]+)", pdf_text)

        return {
            "contract_id": (contract_match.group(1) if contract_match else None),
            "invoice_type": self._classify_invoice(pdf_text),
            "date": self._extract_date(pdf_text),
        }

    def _classify_invoice(self, pdf_text: str) -> InvoiceType | None:
        INVOICE_PATTERNS = [
            (
                InvoiceType.CORRECTION,
                re.compile(
                    r"Korrekturrechnung\s*zu\s*Ihrer\s*(Stromrechnung|naturstrom-Verbrauchsabrechnung)",
                    re.IGNORECASE,
                ),
            ),
            (
                InvoiceType.CANCELLATION,
                re.compile(
                    r"(Stornierung der naturstrom-Rechnung)",
                    re.IGNORECASE,
                ),
            ),
            (
                InvoiceType.REGULAR,
                re.compile(
                    r"(Ihre\s*Strom\s*rechnung|Ihre\s*Schlussrechnung\s*Strom|Ihre\s*naturstrom-Verbrauchsabrechnung)",
                    re.IGNORECASE,
                ),
            ),
        ]

        for invoice_type, pattern in INVOICE_PATTERNS:
            if pattern.search(pdf_text):
                return invoice_type

        return None

    def _extract_date(self, pdf_text: str) -> date | None:
        """
        Finds a German numeric or long-form date following 'Datum'
        and returns it in ISO format (YYYY-MM-DD).
        """
        # Look for the date after 'Datum' (allowing optional newlines or whitespace)
        datum_block_match = re.search(r"Datum\s*\n?\s*(.+)", pdf_text, re.IGNORECASE)
        search_target = datum_block_match.group(1) if datum_block_match else pdf_text

        match = DATE_PATTERN.search(search_target)
        if not match:
            return None

        day = int(match.group("day"))
        year = int(match.group("year"))

        month: int | None

        if match.group("month_num"):
            month = int(match.group("month_num"))
        else:
            month_str = match.group("month_name").lower()
            month = GERMAN_MONTHS.get(month_str)

        if not month:
            return None

        try:
            return date(year, month, day)
        except ValueError:
            # Handles invalid date numbers like 31.02.2026
            return None
