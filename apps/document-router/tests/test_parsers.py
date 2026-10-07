from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from codescape.parse import BankIdentifier, DocumentCategory

from document_router.core.models import ActionType
from document_router.parsers import naturstrom, ryd, scalable
from document_router.parsers.naturstrom import NaturstromParser
from document_router.parsers.ryd import RydParser
from document_router.parsers.scalable import ScalableParser
from document_router.parsers.vodafone import VodafoneParser


class DummyPage:
    def __init__(self, text: str | None) -> None:
        self.text = text

    def extract_text(self) -> str | None:
        return self.text


def test_ryd_parser_extracts_invoice_date(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _dummy_ryd_reader(_: Path) -> SimpleNamespace:
        return SimpleNamespace(pages=[DummyPage("Rechnungsdatum:\n12.03.2025")])

    monkeypatch.setattr(ryd, "PdfReader", _dummy_ryd_reader)

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

    def _dummy_reader(_: Path) -> SimpleNamespace:
        return SimpleNamespace(pages=[DummyPage(text), DummyPage(None)])

    monkeypatch.setattr(naturstrom, "PdfReader", _dummy_reader)

    result = NaturstromParser().parse(tmp_path / "invoice.pdf")

    assert result is not None
    assert result.document_date == date(2025, 3, 12)
    assert result.target_filename == "2025-03-12_Rechnung_123456.pdf"


def test_naturstrom_parser_ignores_unmatched_document(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _dummy_reader(_: Path) -> SimpleNamespace:
        return SimpleNamespace(pages=[DummyPage("unrelated document")])

    monkeypatch.setattr(naturstrom, "PdfReader", _dummy_reader)

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

    def _dummy_parse_document(_: Path) -> SimpleNamespace | None:
        return metadata

    monkeypatch.setattr(scalable, "parse_document", _dummy_parse_document)

    result = ScalableParser().parse(tmp_path / "statement.pdf")

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

    def _dummy_parse_document(_: Path) -> SimpleNamespace | None:
        return metadata

    monkeypatch.setattr(scalable, "parse_document", _dummy_parse_document)

    assert ScalableParser().parse(tmp_path / "statement.pdf") is None
