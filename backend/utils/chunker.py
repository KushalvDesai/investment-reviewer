from __future__ import annotations
import re
from dataclasses import dataclass, field


_CHUNK_SIZE = 600
_OVERLAP = 80

# A line that looks like a financial data row: starts with optional whitespace,
# optional $/-/+ sign, then a digit followed by digits, commas, or dots.
_FINANCIAL_LINE_RE = re.compile(r"^\s*[\$\-\+]?\d[\d,\.]+")


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def _split_text_to_chunks(text: str) -> list[str]:
    """
    Split text into chunks of ~CHUNK_SIZE characters with OVERLAP overlap.

    Financial data lines are never separated from the line immediately above them.
    """
    lines = text.splitlines()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        line_len = len(line) + 1  # +1 for newline

        # If the next line is a financial data line, keep it glued to the current line.
        # We detect this by peeking ahead.
        next_is_financial = (
            i + 1 < len(lines) and _FINANCIAL_LINE_RE.match(lines[i + 1])
        )

        current.append(line)
        current_len += line_len

        should_flush = current_len >= _CHUNK_SIZE and not next_is_financial

        if should_flush:
            chunk_text = "\n".join(current).strip()
            if chunk_text:
                chunks.append(chunk_text)
            # Carry over the last OVERLAP characters worth of lines for context.
            overlap_chars = 0
            overlap_lines: list[str] = []
            for prev_line in reversed(current):
                overlap_chars += len(prev_line) + 1
                overlap_lines.insert(0, prev_line)
                if overlap_chars >= _OVERLAP:
                    break
            current = overlap_lines
            current_len = sum(len(l) + 1 for l in current)

        i += 1

    # Flush remaining content
    remainder = "\n".join(current).strip()
    if remainder:
        chunks.append(remainder)

    return chunks


def chunk_document(
    parsed_doc,
    source_filename: str,
) -> list[Chunk]:
    """
    Chunk a ParsedDocument into Chunk objects with metadata.

    Tables are chunked separately and tagged with chunk_type="table".
    Regular text is tagged with chunk_type="text".
    """
    chunks: list[Chunk] = []
    chunk_index = 0
    month_key = parsed_doc.month_key

    # Chunk the main text body
    text_chunks = _split_text_to_chunks(parsed_doc.text)
    for raw in text_chunks:
        if not raw.strip():
            continue
        chunks.append(
            Chunk(
                text=raw,
                metadata={
                    "month_key": month_key,
                    "chunk_index": chunk_index,
                    "source_filename": source_filename,
                    "chunk_type": "text",
                    "text": raw,
                },
            )
        )
        chunk_index += 1

    # Chunk each table separately; tables are usually short enough to fit in one chunk,
    # but we still apply the same splitter to handle very large tables.
    for table_text in parsed_doc.tables:
        table_chunks = _split_text_to_chunks(table_text)
        for raw in table_chunks:
            if not raw.strip():
                continue
            chunks.append(
                Chunk(
                    text=raw,
                    metadata={
                        "month_key": month_key,
                        "chunk_index": chunk_index,
                        "source_filename": source_filename,
                        "chunk_type": "table",
                        "text": raw,
                    },
                )
            )
            chunk_index += 1

    return chunks
