"""AI code assistance utilities.

Provides a function `suggest_corrections(code: str) -> str` that will attempt to
generate concise correction / improvement suggestions for the provided Python
quantum circuit code. If a Gemini API key is available (env var GEMINI_API_KEY)
and the `google-generativeai` package is installed, it will query the Gemini
model. Otherwise, it falls back to a lightweight static analysis heuristic.

NOTE: Never hard‑code or commit API keys. Set an environment variable instead, e.g.:
  (PowerShell)  $Env:GEMINI_API_KEY = "your_key_here"
"""
from __future__ import annotations

import os
import ast
import textwrap
from typing import List

_GEMINI_MODEL = os.getenv("QUBO_GEMINI_MODEL", "gemini-1.5-flash")


def _gemini_suggest(code: str) -> str:
    """Call Gemini if available, else raise ImportError/RuntimeError.

    Returns raw text suggestions from the model.
    """
    api_key = os.getenv("AIzaSyBairimJFFTO4sDVnEUVKJECjKywoakC3g")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    try:
        import google.generativeai as genai  # type: ignore
    except Exception as e:  # pragma: no cover - library missing
        raise ImportError("google-generativeai package not installed") from e

    genai.configure(api_key=AIzaSyBairimJFFTO4sDVnEUVKJECjKywoakC3g)
    prompt = (
        "You are a concise Python code review assistant for a minimal quantum "
        "circuit toolkit. Given the user's code, list concrete, *actionable* "
        "corrections or improvements (bugs, style, potential runtime issues, "
        "numerical stability, missing validations). Use bullet points. Avoid "
        "rewriting the whole code; keep each bullet short. If the code is fine, "
        "say 'No critical issues found.'\n\nCode:\n```python\n" + code + "\n```"
    )
    try:
        model = genai.GenerativeModel(_GEMINI_MODEL)
        resp = model.generate_content(prompt)
        txt = getattr(resp, "text", None) or "No suggestions returned."
        return txt.strip()
    except Exception as e:  # pragma: no cover - network/runtime errors
        raise RuntimeError(f"Gemini request failed: {e}") from e


def _static_analysis(code: str) -> List[str]:
    """Very small heuristic analysis producing bullet suggestions."""
    suggestions: List[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"Syntax error at line {e.lineno}: {e.msg}", "Fix syntax before execution."]

    # Heuristics
    has_measure = "add_gate('M'" in code or "Measure(" in code
    if not has_measure:
        suggestions.append("No measurement found; circuit will return statevector only.")

    # Look for bare exec/ eval usage (unsafe)
    if "exec(" in code or "eval(" in code:
        suggestions.append("Avoid using exec/eval for safety; not needed for circuit construction.")

    # Detect large qubit counts without comment
    if "QuantumCircuit(" in code:
        import re
        m = re.search(r"QuantumCircuit\((\d+)\)", code)
        if m:
            qn = int(m.group(1))
            if qn > 12:
                suggestions.append("High qubit count (>12); consider performance optimizations or sparse techniques.")

    # Simple unused import detection
    class ImportVisitor(ast.NodeVisitor):
        def __init__(self):
            self.imported = []
            self.used = set()
        def visit_Import(self, node):
            for n in node.names:
                self.imported.append(n.asname or n.name.split('.')[-1])
        def visit_ImportFrom(self, node):
            for n in node.names:
                self.imported.append(n.asname or n.name)
        def visit_Name(self, node):
            self.used.add(node.id)

    iv = ImportVisitor()
    iv.visit(tree)
    for name in iv.imported:
        if name not in iv.used:
            suggestions.append(f"Imported '{name}' but never used.")

    if not suggestions:
        suggestions.append("No critical issues detected by static analyzer.")
    return suggestions


def suggest_corrections(code: str) -> str:
    """Return a bullet list string of suggestions.

    Attempts Gemini first (if key + lib available) else falls back to static analysis.
    """
    # Try Gemini
    try:
        return _gemini_suggest(code)
    except Exception:
        bullets = _static_analysis(code)
        return "\n".join(f"- {b}" for b in bullets)


__all__ = ["suggest_corrections"]
