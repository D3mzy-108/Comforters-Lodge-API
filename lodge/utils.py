from __future__ import annotations

import csv
import io
from datetime import date
from typing import Any, Dict, List, Mapping, Tuple, Union


REQUIRED_LESSON_TSV_COLUMNS = [
    "series_title",
    "personal_question",
    "theme",
    "opening_hook",
    "biblical_qa",
    "reflection",
    "story",
    "prayer",
    "activity_guide",
    "date_posted",
]

REQUIRED_DEVOTIONAL_TSV_COLUMNS = [
    "citation",
    "verse_content",
    "date_posted",
]

HYMN_BASE_COLUMNS = [
    "hymn_number",
    "hymn_title",
    "classification",
    "tune_ref",
    "cross_ref",
    "scripture",
    "chorus_title",
    "chorus",
]

VERSE_PREFIX = "verse_"

REQUIRED_COLUMNS_BY_TYPE: Mapping[str, List[str]] = {
    "LESSON": REQUIRED_LESSON_TSV_COLUMNS,
    "DEVOTIONAL": REQUIRED_DEVOTIONAL_TSV_COLUMNS,
}


def _strip_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a parsed TSV row by trimming whitespace from all string values.

    Args:
        row: A single TSV row produced by csv.DictReader.

    Returns:
        A new dict where all string values have leading/trailing whitespace removed.
        Non-string values are returned unchanged.
    """
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def _require_header(fieldnames: List[str], required: List[str]) -> None:
    """
    Validate that the TSV header contains all required column names.

    Args:
        fieldnames: List of column names extracted from the TSV header row.
        required: List of column names that must be present.

    Raises:
        ValueError: If one or more required columns are missing.
    """
    header = set(fieldnames)
    missing = [c for c in required if c not in header]
    if missing:
        raise ValueError(f"TSV header missing columns: {missing}")


def _require_non_empty(row: Dict[str, Any], cols: List[str], line_no: int) -> None:
    """
    Ensure that required columns exist and contain non-empty values for a row.

    Args:
        row: A parsed TSV row as a dictionary.
        cols: Column names that must be present and non-empty.
        line_no: Line number in the TSV file (used for error reporting).

    Raises:
        ValueError: If any required column is missing or empty.
    """
    for c in cols:
        v = row.get(c)
        if v is None or (isinstance(v, str) and not v):
            raise ValueError(f"Row {line_no}: '{c}' is required.")


def _parse_date(row: Dict[str, Any], line_no: int) -> None:
    """
    Parse and convert the 'date_posted' field from ISO string to datetime.date.

    Args:
        row: A parsed TSV row containing a 'date_posted' key.
        line_no: Line number in the TSV file (used for error reporting).

    Mutates:
        Replaces row['date_posted'] with a datetime.date instance.

    Raises:
        ValueError: If the date is missing or not in YYYY-MM-DD format.
    """
    try:
        row["date_posted"] = date.fromisoformat(row["date_posted"])
    except Exception:
        raise ValueError(f"Row {line_no}: date_posted must be YYYY-MM-DD.")


def _unescape_newlines(s: str) -> str:
    # Convert literal backslash-n sequences into real newlines
    return s.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n").replace("\\t", "\t")


def _extract_verses(
    row: Dict[str, Any],
    fieldnames: List[str],
    *,
    verse_prefix: str = VERSE_PREFIX,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Separate verse columns (e.g. verse_1, verse_2, ...) from a hymn row.

    Args:
        row: A parsed TSV row containing base hymn fields and verse_* fields.
        fieldnames: Original header field order from the TSV file.
        verse_prefix: Prefix used to identify verse columns (default: 'verse_').

    Returns:
        A tuple of:
        - base_row: Dict containing all non-verse fields.
        - verses: List of verse strings in header order, excluding empty values.
    """
    verse_cols = [c for c in fieldnames if c.startswith(verse_prefix)]
    verses: List[str] = []

    for col in verse_cols:
        val = row.get(col)
        if isinstance(val, str):
            val = val.strip()
        if val and val != '-':
            verses.append(_unescape_newlines(val))

    base_row = {
        k: _unescape_newlines(v) for k, v in row.items() if not k.startswith(verse_prefix)
    }
    return base_row, verses


ParseResult = Union[
    List[Dict[str, Any]],
    Dict[str, List[Any]],  # {"rows": [...], "extra_data": [...]}
]


def parse_tsv_bytes(tsv_bytes: bytes, tsv_content_type: str) -> ParseResult:
    """
    Parse TSV content into structured Python objects based on content type.

    Args:
        tsv_bytes:
            Raw TSV file content as bytes. UTF-8 with or without BOM is supported.

        tsv_content_type:
            Determines parsing rules and required columns.
            Supported values:
            - 'LESSON'
            - 'DEVOTIONAL'
            - 'HYMN'

    Returns:
        If content type is LESSON or DEVOTIONAL:
            A list of dictionaries, one per row.

        If content type is HYMN:
            A dictionary with:
            - 'rows': list of base hymn metadata (no verses)
            - 'extra_data': list of verse lists, aligned by index with 'rows'

    Raises:
        ValueError:
            - If the content type is invalid
            - If required headers are missing
            - If required fields are empty
            - If date_posted is invalid
            - If the TSV contains no data rows
    """
    text = tsv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")

    fieldnames = reader.fieldnames
    if not fieldnames:
        raise ValueError("TSV appears to have no header row.")

    # HYMN: special handling for variable verse columns
    if tsv_content_type == "HYMN":
        _require_header(fieldnames, HYMN_BASE_COLUMNS)

        if not any(c.startswith(VERSE_PREFIX) for c in fieldnames):
            raise ValueError(
                f"TSV header must include at least one '{VERSE_PREFIX}…' column."
            )

        items: List[Dict[str, Any]] = []

        for line_no, raw in enumerate(reader, start=2):
            row = _strip_row(raw)
            _require_non_empty(row, HYMN_BASE_COLUMNS, line_no)

            base_row, verses = _extract_verses(row, fieldnames)

            if not verses:
                raise ValueError(
                    f"Row {line_no}: at least one verse is required.")

            items.append({"hymn": base_row, "verses": verses})

        if not items:
            raise ValueError("TSV contains a header but no data rows.")

        return items

    # LESSON / DEVOTIONAL
    try:
        required = REQUIRED_COLUMNS_BY_TYPE[tsv_content_type]
    except KeyError:
        raise ValueError(
            "Invalid content type was provided. Use: LESSON, DEVOTIONAL, or HYMN.")

    _require_header(fieldnames, required)

    rows: List[Dict[str, Any]] = []
    for line_no, raw in enumerate(reader, start=2):
        row = _strip_row(raw)
        _require_non_empty(row, required, line_no)
        _parse_date(row, line_no)
        rows.append(row)

    if not rows:
        raise ValueError("TSV contains a header but no data rows.")

    return rows
