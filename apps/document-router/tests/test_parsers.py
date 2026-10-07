from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from codescape.parse import BankIdentifier, DocumentCategory

from document_router.core.models import ActionType
from document_router.parsers import naturstrom, ryd, scalable
from document_router.parsers.naturstrom import NaturstromParser
from document_router.parsers.ryd import RydParser
from document_router.parsers.vodafone import VodafoneParser


class FakePage:
    def __init__(self, text: str | None) -> None:
        self.text = text

    def extract_text(self) -> str | None:
        return self.text


def test_ryd_parser_extracts_invoice_date(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        ryd,
        "PdfReader",
        lambda _: SimpleNamespace(pages=[FakePage("Rechnungsdatum:\n12.03.2025")]),
    )

    result = RydParser().parse(tmp_path / "invoice.pdf")

    assert result is not None
    assert result.document_date == date(2025, 3, 12)
    assert result.target_filename == "2025-03-12_invoice.pdf"


def test_ryd_parser_quarantines_reader_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail(_: Path) -> None:
        raise OSError("unreadable")

    monkeypatch.setattr(ryd, "PdfReader", fail)

    result = RydParser().parse(tmp_path / "bad.pdf")

    assert result is not None
    assert result.action == ActionType.QUARANTINE
    assert "unreadable" in (result.quarantine_reason or "")


def test_vodafone_parser_accepts_valid_invoice_filename(tmp_path: Path) -> None:
    result = VodafoneParser().parse(tmp_path / "2025-03-12_Rechnung_Kundennr_12345.pdf")

    assert result is not None
    assert result.document_date == date(2025, 3, 12)
    assert result.target_subfolder == Path("telecom/vodafone.com/2025")


def test_vodafone_parser_rejects_invalid_date(tmp_path: Path) -> None:
    result = VodafoneParser().parse(tmp_path / "2025-99-12_Rechnung_Kundennr_12345.pdf")

    assert result is None


def test_naturstrom_parser_extracts_invoice_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    text = "Vertragsnummer\n123456\nIhre Stromrechnung\nDatum\n12. März 2025"
    monkeypatch.setattr(
        naturstrom,
        "PdfReader",
        lambda _: SimpleNamespace(pages=[FakePage(text), FakePage(None)]),
    )

    result = NaturstromParser().parse(tmp_path / "invoice.pdf")

    assert result is not None
    assert result.document_date == date(2025, 3, 12)
    assert result.target_filename == "2025-03-12_Rechnung_123456.pdf"


def test_naturstrom_parser_ignores_unmatched_document(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        naturstrom,
        "PdfReader",
        lambda _: SimpleNamespace(pages=[FakePage("unrelated document")]),
    )

    assert NaturstromParser().parse(tmp_path / "other.pdf") is None


def test_scalable_parser_uses_statement_year(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    metadata = SimpleNamespace(
        bank=BankIdentifier.SCALABLE,
        category=DocumentCategory.ACCOUNT_STATEMENT,
        statement_period_year=2024,
        document_date=date(2025, 1, 2),
    )
    monkeypatch.setattr(scalable, "parse_document", lambda _: metadata)

    result = scalable.ScalableParser().parse(tmp_path / "statement.pdf")

    assert result is not None
    assert result.target_subfolder == Path("finances/scalable/statements/2024")


def test_scalable_parser_ignores_other_banks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    metadata = SimpleNamespace(
        bank="other",
        category=DocumentCategory.ACCOUNT_STATEMENT,
        statement_period_year=None,
        document_date=None,
    )
    monkeypatch.setattr(scalable, "parse_document", lambda _: metadata)

    assert scalable.ScalableParser().parse(tmp_path / "statement.pdf") is None
