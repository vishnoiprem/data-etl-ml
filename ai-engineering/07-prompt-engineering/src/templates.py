"""Lightweight Jinja-style template engine.

Just `{{ name }}` and `{{ name | filter }}` substitution — no logic, no loops.
Keeping templates dumb is a feature: it makes them easy to test, version, and
review.

Filters supported: `trim`, `upper`, `lower`, `truncate(N)`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][\w]*)(?:\s*\|\s*([a-zA-Z_]+(?:\(\d+\))?))?\s*\}\}")


def _apply_filter(value, fname: str) -> str:
    if fname == "trim":
        return str(value).strip()
    if fname == "upper":
        return str(value).upper()
    if fname == "lower":
        return str(value).lower()
    if fname.startswith("truncate(") and fname.endswith(")"):
        n = int(fname[len("truncate("):-1])
        s = str(value)
        return s if len(s) <= n else s[: n - 1] + "…"
    return str(value)


@dataclass
class Template:
    name: str
    body: str

    def variables(self) -> list[str]:
        return sorted({m.group(1) for m in _VAR_RE.finditer(self.body)})

    def render(self, **kwargs) -> str:
        def sub(match: re.Match) -> str:
            var = match.group(1)
            filt = match.group(2)
            if var not in kwargs:
                raise KeyError(f"missing template variable: {var}")
            v = kwargs[var]
            return _apply_filter(v, filt) if filt else str(v)
        return _VAR_RE.sub(sub, self.body)
