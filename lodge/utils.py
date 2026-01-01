from __future__ import annotations
import csv
import io
from datetime import date
from typing import Any, Dict, List, Optional

REQUIRED_TSV_COLUMNS = [
    "series_title",
    "personal_question",
    "theme",
    "opening_hook",
    "biblical_qa",
    "reflection",
    "story",
    "prayer",
    "activity_guide",
    "date_posted",  # ISO date like 2025-12-29
]

def parse_tsv_bytes(tsv_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Reads TSV bytes and returns a list of dict rows.

    Expected:
      - First row is a header with the exact column names in REQUIRED_TSV_COLUMNS
      - Each subsequent row is one DailyPost
      - date_posted should be ISO format: YYYY-MM-DD

    This function raises ValueError with a helpful message when input is invalid.
    """
    text = tsv_bytes.decode("utf-8-sig")  # utf-8-sig tolerates BOM
    f = io.StringIO(text)
    reader = csv.DictReader(f, delimiter="\t")

    if reader.fieldnames is None:
        raise ValueError("TSV appears to have no header row.")

    missing = [c for c in REQUIRED_TSV_COLUMNS if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"TSV header missing columns: {missing}")

    rows: List[Dict[str, Any]] = []
    for idx, row in enumerate(reader, start=2):  # line 1 is header
        # Basic validation: ensure required fields are present and non-empty
        for c in REQUIRED_TSV_COLUMNS:
            if row.get(c) is None or str(row[c]).strip() == "":
                raise ValueError(f"Row {idx}: '{c}' is required.")

        # Parse date
        try:
            y, m, d = row["date_posted"].strip().split("-")
            row["date_posted"] = date(int(y), int(m), int(d))
        except Exception:
            raise ValueError(f"Row {idx}: date_posted must be YYYY-MM-DD.")

        rows.append(row)

    if not rows:
        raise ValueError("TSV contains a header but no data rows.")

    return rows
