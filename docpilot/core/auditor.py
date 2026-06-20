"""Documentation auditor: check docs against the *current* code (no diff).

Where the staleness checker compares an old and new version of code, the auditor
takes a single snapshot — your code as it is now plus your docs — and reports
sections that contradict the code. It powers the dashboard's "Audit" upload mode
(drop in a code file + a docs file, including PDFs).

Two kinds of finding are produced:

* **mismatch** -- a doc section linked to a code chunk makes a claim the chunk
  contradicts (wrong parameter name, wrong default value, missing parameter).
* **missing_symbol** -- the docs reference a function/class/config/route that
  exists in no parsed chunk (often a renamed or removed symbol).

With a real provider the per-section check is LLM-driven; offline it uses
deterministic heuristics so the feature works in mock mode.
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .config import Config
from .llm import LLMClient, get_llm_client
from .models import ChunkKind, CodeChunk, DocSection, Mapping
from .prompt_loader import render
from .staleness_checker import _default_literals, _params_from_signature

logger = logging.getLogger("docpilot.auditor")


@dataclass
class AuditFinding:
    doc_section_id: str
    heading: str
    chunk_id: Optional[str]
    kind: str  # "mismatch" | "missing_symbol"
    confidence: str  # high | medium | low
    diagnosis: str
    suggested_fix: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditReport:
    sections_checked: int = 0
    findings: list[AuditFinding] = field(default_factory=list)

    @property
    def consistent(self) -> int:
        return self.sections_checked - len({f.doc_section_id for f in self.findings})

    def to_dict(self) -> dict[str, Any]:
        return {
            "sections_checked": self.sections_checked,
            "inconsistent": len({f.doc_section_id for f in self.findings}),
            "consistent": self.consistent,
            "findings": [f.to_dict() for f in self.findings],
        }


def _doc_call_args(symbol: str, content: str) -> Optional[list[str]]:
    """Extract argument names from a documented call like ``symbol(a, b)``."""
    short = symbol.split(".")[-1]
    m = re.search(rf"\b{re.escape(short)}\s*\(([^)]*)\)", content)
    if not m:
        return None
    args = []
    for part in m.group(1).split(","):
        name = part.strip().strip("`").split("=")[0].strip()
        if name and name not in ("self", "cls", "...", ""):
            args.append(name)
    return args


class Auditor:
    def __init__(self, config: Config, client: Optional[LLMClient] = None) -> None:
        self.config = config
        self.client = client or get_llm_client(config)

    def audit(self, mapping: Mapping) -> AuditReport:
        report = AuditReport()
        chunk_symbols = {c.symbol for c in mapping.code_chunks}
        chunk_symbols |= {c.symbol.split(".")[-1] for c in mapping.code_chunks}

        seen_sections: set[str] = set()
        for section in mapping.doc_sections:
            linked = mapping.sections_for_chunk  # noqa: F841 (clarity below)
            chunks = self._linked_chunks(section, mapping)
            if section.section_id not in seen_sections:
                report.sections_checked += 1
                seen_sections.add(section.section_id)

            section_has_finding = False
            for chunk in chunks:
                finding = self._check(chunk, section)
                if finding is not None:
                    report.findings.append(finding)
                    section_has_finding = True

            # Documented-but-missing symbols (referenced, but in no chunk).
            # Skip if this section already produced a concrete mismatch.
            if section_has_finding:
                continue
            for ref in section.code_references:
                base = ref.split(".")[-1].split("(")[0].strip()
                if base and base[0].isalpha() and base not in chunk_symbols and ref not in chunk_symbols:
                    # Only flag identifier-like refs, not prose words.
                    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", base) and (base.islower() or base.isupper() or base[0].isupper()):
                        if self._looks_documented_symbol(base, section.content):
                            report.findings.append(
                                AuditFinding(
                                    doc_section_id=section.section_id,
                                    heading=section.heading_path,
                                    chunk_id=None,
                                    kind="missing_symbol",
                                    confidence="medium",
                                    diagnosis=f"Documentation references `{base}`, which was not found in the provided code.",
                                )
                            )
                            break
        return report

    @staticmethod
    def _linked_chunks(section: DocSection, mapping: Mapping) -> list[CodeChunk]:
        ids = {l.code_chunk_id for l in mapping.links if l.doc_section_id == section.section_id}
        return [c for c in mapping.code_chunks if c.chunk_id in ids]

    @staticmethod
    def _looks_documented_symbol(name: str, content: str) -> bool:
        # backticked or call-like reference, to avoid flagging plain prose words.
        return bool(re.search(rf"`{re.escape(name)}`|\b{re.escape(name)}\s*\(", content))

    # -- per-chunk check -----------------------------------------------------

    def _check(self, chunk: CodeChunk, section: DocSection) -> Optional[AuditFinding]:
        if self.client.is_mock:
            return self._heuristic_check(chunk, section)
        try:
            return self._llm_check(chunk, section)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM audit failed, using heuristic: %s", exc)
            return self._heuristic_check(chunk, section)

    def _llm_check(self, chunk: CodeChunk, section: DocSection) -> Optional[AuditFinding]:
        system, user = render(
            "audit",
            symbol=chunk.symbol,
            language=chunk.language.value,
            code=chunk.source,
            heading_path=section.heading_path,
            doc_content=section.content,
        )
        data = self.client.chat_json(system, user)
        if data.get("consistent", True):
            return None
        return AuditFinding(
            doc_section_id=section.section_id,
            heading=section.heading_path,
            chunk_id=chunk.chunk_id,
            kind="mismatch",
            confidence=str(data.get("confidence", "medium")),
            diagnosis=str(data.get("diagnosis", "")),
            suggested_fix=(data.get("suggested_fix") or None),
        )

    def _heuristic_check(self, chunk: CodeChunk, section: DocSection) -> Optional[AuditFinding]:
        content = section.content

        if chunk.kind in (ChunkKind.FUNCTION, ChunkKind.METHOD):
            actual = _params_from_signature(chunk.signature)
            claimed = _doc_call_args(chunk.symbol, content)
            if claimed and actual:
                wrong = [c for c in claimed if c not in actual]
                if wrong:
                    fix = content
                    for w, a in zip(wrong, [p for p in actual if p not in claimed]):
                        fix = re.sub(rf"(?<![\w]){re.escape(w)}(?![\w])", a, fix)
                    return AuditFinding(
                        doc_section_id=section.section_id,
                        heading=section.heading_path,
                        chunk_id=chunk.chunk_id,
                        kind="mismatch",
                        confidence="high",
                        diagnosis=(
                            f"Docs describe `{chunk.symbol}` with argument(s) {wrong}, but the "
                            f"current signature is `{chunk.signature}` (params: {actual})."
                        ),
                        suggested_fix=fix if fix != content else None,
                    )

        if chunk.kind is ChunkKind.CONFIG:
            actual_lits = _default_literals(chunk.source)
            doc_nums = set(re.findall(r"\b\d+\b", content))
            actual_nums = {l for l in actual_lits if l.isdigit()}
            stale_nums = [n for n in doc_nums if n not in actual_nums and actual_nums]
            # Only flag when the doc states a number near the config name.
            if stale_nums and chunk.symbol.lower() in content.lower():
                new_val = sorted(actual_nums)[0]
                fix = content
                for n in stale_nums:
                    fix = re.sub(rf"\b{re.escape(n)}\b", new_val, fix)
                return AuditFinding(
                    doc_section_id=section.section_id,
                    heading=section.heading_path,
                    chunk_id=chunk.chunk_id,
                    kind="mismatch",
                    confidence="medium",
                    diagnosis=(
                        f"Docs state value(s) {stale_nums} for `{chunk.symbol}`, but the code "
                        f"uses {sorted(actual_nums)}."
                    ),
                    suggested_fix=fix if fix != content else None,
                )

        return None
