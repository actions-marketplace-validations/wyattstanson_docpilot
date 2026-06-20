"""Minimal PDF text extraction for the audit feature.

Uses ``pypdf`` when available. Documentation PDFs rarely carry markdown
headings, so callers should feed the extracted text through
:meth:`DocParser.parse_text_loose`, which falls back to paragraph-based
sectioning when no headings are present.
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger("docpilot.pdf")


def extract_pdf_text(data: bytes) -> str:
    """Return the concatenated text of every page in a PDF byte stream."""
    try:
        from pypdf import PdfReader  # lazy import
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pypdf is required to read PDF input. Install with `pip install pypdf`."
        ) from exc
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:  # noqa: BLE001 - never fail on one bad page
            logger.warning("Failed to extract a PDF page: %s", exc)
    return "\n\n".join(p for p in pages if p.strip())
