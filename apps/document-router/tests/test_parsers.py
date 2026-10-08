from datetime import date
from pathlib import Path
from types import SimpleNamespace

from codescape.parse import BankIdentifier, DocumentCategory
from pytest_mock import MockerFixture

from document_router.core.models import ActionType
from document_router.parsers import (
    NaturstromParser,
    RydParser,
    ScalableParser,
    VodafoneParser,
    naturstrom,
    ryd,
)


class DummyPage:
    def __init__(self, text: str | None) -> None:
        self.text = text

    def extract_text(self) -> str | None:
        return self.text


def test_ryd_parser_extracts_invoice_date(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    _dummy_reader = SimpleNamespace(pages=[DummyPage("Rechnungsdatum:\n12.03.2025")])

    mock_parse = mocker.patch.object(ryd, "PdfReader", return_value=_dummy_reader)

    result = RydParser().parse(tmp_path / "invoice.pdf")

    assert result is not None
    assert result.document_date == date(2025, 3, 12)
    assert result.target_filename == "2025-03-12_invoice.pdf"

    mock_parse.assert_called_once_with(tmp_path / "invoice.pdf")


def test_ryd_parser_quarantines_reader_errors(
    mocker: MockerFixture, tmp_path: Path
) -> None:

    mock_parse = mocker.patch.object(
        ryd, "PdfReader", side_effect=OSError("unreadable")
    )

    result = RydParser().parse(tmp_path / "bad.pdf")

    assert result is not None
    assert result.action == ActionType.QUARANTINE
    assert "unreadable" in (result.quarantine_reason or "")

    mock_parse.assert_called_once_with(tmp_path / "bad.pdf")


def test_vodafone_parser_accepts_valid_invoice_filename(tmp_path: Path) -> None:
    result = VodafoneParser().parse(tmp_path / "2025-03-12_Rechnung_Kundennr_12345.pdf")

    assert result is not None
    assert result.document_date == date(2025, 3, 12)
    assert result.target_subfolder == Path("telecom/vodafone.com/2025")


def test_vodafone_parser_rejects_invalid_date(tmp_path: Path) -> None:
    result = VodafoneParser().parse(tmp_path / "2025-99-12_Rechnung_Kundennr_12345.pdf")

    assert result is None


def test_naturstrom_parser_extracts_invoice_metadata(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    text = "Vertragsnummer\n123456\nIhre Stromrechnung\nDatum\n12. März 2025"

    _dummy_reader = SimpleNamespace(pages=[DummyPage(text), DummyPage(None)])

    mock_parse = mocker.patch.object(
        naturstrom, "PdfReader", return_value=_dummy_reader
    )

    result = NaturstromParser().parse(tmp_path / "invoice.pdf")

    assert result is not None
    assert result.document_date == date(2025, 3, 12)
    assert result.target_filename == "2025-03-12_Rechnung_123456.pdf"

    mock_parse.assert_called_once_with(tmp_path / "invoice.pdf")


def test_naturstrom_parser_ignores_unmatched_document(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    _dummy_reader = SimpleNamespace(pages=[DummyPage("unrelated document")])

    mock_parse = mocker.patch.object(
        naturstrom, "PdfReader", return_value=_dummy_reader
    )

    result = NaturstromParser().parse(tmp_path / "other.pdf")
    assert result is None

    mock_parse.assert_called_once_with(tmp_path / "other.pdf")


def test_scalable_parser_uses_statement_year(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    metadata = SimpleNamespace(
        bank=BankIdentifier.SCALABLE,
        category=DocumentCategory.ACCOUNT_STATEMENT,
        statement_period_year=2024,
        document_date=date(2025, 1, 2),
    )

    mock_parse = mocker.patch(
        "document_router.parsers.scalable.parse_document", return_value=metadata
    )

    result = ScalableParser().parse(tmp_path / "statement.pdf")

    assert result is not None
    assert result.target_subfolder == Path("finances/scalable/statements/2024")

    mock_parse.assert_called_once_with(tmp_path / "statement.pdf")


def test_scalable_parser_ignores_other_banks(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    metadata = SimpleNamespace(
        bank="other",
        category=DocumentCategory.ACCOUNT_STATEMENT,
        statement_period_year=None,
        document_date=None,
    )

    mock_parse = mocker.patch(
        "document_router.parsers.scalable.parse_document", return_value=metadata
    )

    result = ScalableParser().parse(tmp_path / "statement.pdf")

    assert result is None

    mock_parse.assert_called_once_with(tmp_path / "statement.pdf")
