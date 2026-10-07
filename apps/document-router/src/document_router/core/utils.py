import hashlib
from datetime import datetime
from pathlib import Path


def calculate_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file using buffered reading."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def convert_to_isodate(date_str: str, input_fmt: str) -> str:
    """
    Converts a date string to ISO format ('YYYY-MM-DD').

    Applies the specified input format when parsing the input.
    """
    parsed_date = datetime.strptime(date_str, input_fmt)
    return parsed_date.strftime("%Y-%m-%d")
