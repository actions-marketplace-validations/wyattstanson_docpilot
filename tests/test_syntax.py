"""Tests for syntax checking and the audit summary."""

from __future__ import annotations

from docpilot.core.pipeline import Pipeline
from docpilot.core.syntax import check_syntax


def test_python_valid():
    assert check_syntax("a.py", "def f():\n    return 1\n")["ok"]


def test_python_error_reports_line():
    r = check_syntax("a.py", "def f(:\n    return 1\n")
    assert r["ok"] is False
    assert r["errors"][0]["line"] == 1
    assert r["errors"][0]["message"]


def test_python_missing_colon():
    r = check_syntax("a.py", "def f(a, b)\n    return a\n")
    assert r["ok"] is False
    assert r["errors"][0]["line"] == 1


def test_js_valid():
    assert check_syntax("a.js", "function f() { return 1; }\n")["ok"]


def test_js_unclosed_brace():
    r = check_syntax("a.js", "function f() {\n  return 1;\n")
    assert r["ok"] is False


def test_js_unterminated_string():
    r = check_syntax("a.js", "const x = 'hello;\n")
    assert r["ok"] is False


def test_markdown_is_skipped():
    assert check_syntax("a.md", "totally {[( not balanced")["ok"]


def test_audit_includes_summary_and_syntax(mock_config):
    code = "def greet(name):\n    return name\nLIMIT = 5\n"
    docs = "# Doc\n\n## Greeting\n\nCall `greet(name)` to greet someone.\n"
    r = Pipeline(mock_config).audit("m.py", code, docs)
    assert r["syntax"]["ok"] is True
    summary = r["summary"]
    assert any(s["name"] == "greet" for s in summary["code"]["symbols"])
    assert any(sim["code"] == "greet" for sim in summary["similarities"])
    assert "LIMIT" in summary["differences"]["undocumented_code"]
