"""Build human-readable summaries of an uploaded code/doc pair.

Produces a structural overview that works offline (no LLM): what the code
defines, what the docs cover, where they overlap (similarities), and where they
diverge (differences — undocumented code, undocumented doc sections, and the
concrete mismatches found by the auditor).
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .models import ChunkKind, CodeChunk, DocSection, Link

_KIND_LABEL = {
    "function": "function",
    "method": "method",
    "class": "class",
    "api_route": "API route",
    "config": "config value",
    "cli_command": "CLI command",
}


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def _code_sentence(chunks: list[CodeChunk]) -> str:
    if not chunks:
        return "No recognizable symbols were parsed from this file."
    counts = Counter(c.kind.value for c in chunks)
    parts = [_plural(n, _KIND_LABEL.get(k, k)) for k, n in counts.most_common()]
    if len(parts) > 1:
        listed = ", ".join(parts[:-1]) + " and " + parts[-1]
    else:
        listed = parts[0]
    names = ", ".join(f"`{c.symbol}`" for c in chunks[:6])
    more = "" if len(chunks) <= 6 else f", and {len(chunks) - 6} more"
    return f"This file defines {listed} — {names}{more}."


def _doc_sentence(sections: list[DocSection], linked_ids: set[str]) -> str:
    real = [s for s in sections if s.content.strip()]
    if not real:
        return "No documentation sections were found."
    headings = ", ".join(f"“{s.heading_path.split('>')[-1].strip()}”" for s in real[:6])
    more = "" if len(real) <= 6 else f", and {len(real) - 6} more"
    linked = sum(1 for s in real if s.section_id in linked_ids)
    return (
        f"These docs contain {_plural(len(real), 'section')} ({headings}{more}); "
        f"{linked} reference the uploaded code."
    )


def build_overview(
    chunks: list[CodeChunk],
    sections: list[DocSection],
    links: list[Link],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    by_id = {c.chunk_id: c for c in chunks}
    sec_by_id = {s.section_id: s for s in sections}
    linked_chunk_ids = {l.code_chunk_id for l in links}
    linked_section_ids = {l.doc_section_id for l in links}

    similarities = []
    seen = set()
    for l in links:
        key = (l.code_chunk_id, l.doc_section_id)
        if key in seen:
            continue
        seen.add(key)
        chunk = by_id.get(l.code_chunk_id)
        sec = sec_by_id.get(l.doc_section_id)
        if chunk and sec:
            similarities.append(
                {
                    "code": chunk.symbol,
                    "doc": sec.heading_path.split(">")[-1].strip(),
                    "via": l.link_type.value,
                }
            )

    undocumented_code = [
        c.symbol
        for c in chunks
        if c.chunk_id not in linked_chunk_ids and c.kind is not ChunkKind.MODULE
    ]
    unrelated_sections = [
        s.heading_path.split(">")[-1].strip()
        for s in sections
        if s.section_id not in linked_section_ids and s.content.strip()
    ]

    return {
        "code": {
            "text": _code_sentence(chunks),
            "symbols": [{"name": c.symbol, "kind": c.kind.value} for c in chunks],
        },
        "docs": {
            "text": _doc_sentence(sections, linked_section_ids),
            "sections": [s.heading_path for s in sections if s.content.strip()],
        },
        "similarities": similarities,
        "differences": {
            "mismatches": len(findings),
            "undocumented_code": undocumented_code,
            "unrelated_doc_sections": unrelated_sections,
        },
    }
