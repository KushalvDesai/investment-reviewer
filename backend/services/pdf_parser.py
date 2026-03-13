from __future__ import annotations
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF


@dataclass
class ParsedDocument:
    text: str
    tables: list[str]
    metadata: dict
    month_key: str  # "YYYY-MM"


# Patterns to detect a statement date in the text
_DATE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # "Statement Period: 01/2025" or "Statement Period: 01/25"
    (re.compile(r"Statement\s+Period[:\s]+(\d{1,2})[/\-](\d{4})", re.IGNORECASE), "MM/YYYY"),
    # "Month: January 2025"
    (re.compile(r"Month[:\s]+([A-Za-z]+)\s+(\d{4})", re.IGNORECASE), "Month YYYY"),
    # "January 2025" standalone
    (re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b", re.IGNORECASE), "Month YYYY"),
    # "2025-01" or "2025/01"
    (re.compile(r"\b(\d{4})[/\-](0[1-9]|1[0-2])\b"), "YYYY-MM"),
    # "01/2025"
    (re.compile(r"\b(0[1-9]|1[0-2])[/\-](\d{4})\b"), "MM/YYYY"),
    # "Jan 2025" abbreviated
    (re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+(\d{4})\b", re.IGNORECASE), "Month YYYY"),
]

_MONTH_NAME_MAP = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def _extract_month_key(text: str) -> str:
    """Return the first statement month found as 'YYYY-MM', or 'unknown' if none."""
    for pattern, fmt in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            if fmt == "MM/YYYY":
                month, year = m.group(1).zfill(2), m.group(2)
                return f"{year}-{month}"
            if fmt == "YYYY-MM":
                year, month = m.group(1), m.group(2)
                return f"{year}-{month}"
            if fmt == "Month YYYY":
                month_name = m.group(1).lower()[:3]
                year = m.group(2)
                month_num = _MONTH_NAME_MAP.get(month_name)
                if month_num:
                    return f"{year}-{month_num}"
    return "unknown"


def _is_table_block(block: dict) -> bool:
    """Heuristic: a block is table-like if it has multiple short lines with digit-heavy content."""
    lines = block.get("lines", [])
    if len(lines) < 2:
        return False
    digit_lines = 0
    for line in lines:
        text = " ".join(span["text"] for span in line.get("spans", []))
        if re.search(r"\d[\d,\.]+", text):
            digit_lines += 1
    return digit_lines >= len(lines) * 0.5


def _block_to_table_text(block: dict) -> str:
    """Convert a table block into tab-separated row strings."""
    rows: list[str] = []
    for line in block.get("lines", []):
        cells = [span["text"].strip() for span in line.get("spans", []) if span["text"].strip()]
        if cells:
            rows.append("\t".join(cells))
    return "\n".join(rows)


def parse_pdf(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Parse a PDF from raw bytes.

    Extracts:
    - Full text (all pages concatenated)
    - Tables as tab-separated strings
    - Metadata (filename, pages, detected_date, month_key)
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    full_text_parts: list[str] = []
    tables: list[str] = []

    for page in doc:
        page_dict = page.get_text("dict")
        page_text_parts: list[str] = []

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:  # 0 = text block
                continue
            if _is_table_block(block):
                table_text = _block_to_table_text(block)
                if table_text.strip():
                    tables.append(table_text)
                    page_text_parts.append(table_text)
            else:
                for line in block.get("lines", []):
                    line_text = " ".join(span["text"] for span in line.get("spans", []))
                    if line_text.strip():
                        page_text_parts.append(line_text.strip())

        full_text_parts.append("\n".join(page_text_parts))

    full_text = "\n\n".join(full_text_parts)
    month_key = _extract_month_key(full_text)

    metadata = {
        "filename": filename,
        "num_pages": len(doc),
        "detected_date": month_key,
        "month_key": month_key,
    }

    doc.close()
    return ParsedDocument(
        text=full_text,
        tables=tables,
        metadata=metadata,
        month_key=month_key,
    )
