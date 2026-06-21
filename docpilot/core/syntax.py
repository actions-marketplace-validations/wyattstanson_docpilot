"""Syntax checking for uploaded code.

Python is checked precisely with :mod:`ast` (exact line / column / message).
JavaScript and TypeScript get a best-effort structural check — balanced
brackets and terminated strings — since a full JS parser is out of scope. The
goal is to clearly tell the user *where* a file fails to parse so they know the
audit may be incomplete.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .parser import Language, language_for

_OPEN = {")": "(", "]": "[", "}": "{"}
_CLOSE = {"(": ")", "[": "]", "{": "}"}


def check_syntax(file_path: str, code: str) -> dict[str, Any]:
    """Return ``{ok, language, errors:[{line, col, message, text}]}``."""
    lang = language_for(Path(file_path))
    if lang is Language.PYTHON:
        return _check_python(code)
    if lang in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        return _check_brackets(code, lang)
    return {"ok": True, "language": lang.value, "errors": []}


def _check_python(code: str) -> dict[str, Any]:
    try:
        ast.parse(code)
        return {"ok": True, "language": "python", "errors": []}
    except SyntaxError as exc:
        return {
            "ok": False,
            "language": "python",
            "errors": [
                {
                    "line": exc.lineno or 0,
                    "col": exc.offset or 0,
                    "message": exc.msg or "invalid syntax",
                    "text": (exc.text or "").rstrip(),
                }
            ],
        }


def _check_brackets(code: str, lang: Language) -> dict[str, Any]:
    """Best-effort balance/termination check for JS/TS."""
    stack: list[tuple[str, int]] = []  # (opening char, line)
    line = 1
    i = 0
    n = len(code)
    errors: list[dict[str, Any]] = []

    while i < n:
        ch = code[i]
        nxt = code[i + 1] if i + 1 < n else ""

        if ch == "\n":
            line += 1
            i += 1
            continue
        # line comment
        if ch == "/" and nxt == "/":
            while i < n and code[i] != "\n":
                i += 1
            continue
        # block comment
        if ch == "/" and nxt == "*":
            i += 2
            while i < n and not (code[i] == "*" and i + 1 < n and code[i + 1] == "/"):
                if code[i] == "\n":
                    line += 1
                i += 1
            i += 2
            continue
        # strings / template literals
        if ch in "\"'`":
            quote = ch
            start_line = line
            i += 1
            terminated = False
            while i < n:
                if code[i] == "\\":
                    i += 2
                    continue
                if code[i] == "\n":
                    line += 1
                    if quote != "`":  # plain strings can't span lines
                        break
                if code[i] == quote:
                    terminated = True
                    i += 1
                    break
                i += 1
            if not terminated:
                errors.append(
                    {"line": start_line, "col": 0, "message": f"unterminated string ({quote})", "text": ""}
                )
                break
            continue
        # brackets
        if ch in _CLOSE:
            stack.append((ch, line))
        elif ch in _OPEN:
            if not stack or stack[-1][0] != _OPEN[ch]:
                errors.append(
                    {"line": line, "col": 0, "message": f"unmatched '{ch}'", "text": ""}
                )
                break
            stack.pop()
        i += 1

    if not errors and stack:
        opener, oline = stack[-1]
        errors.append(
            {"line": oline, "col": 0, "message": f"unclosed '{opener}'", "text": ""}
        )

    return {"ok": not errors, "language": lang.value, "errors": errors}
