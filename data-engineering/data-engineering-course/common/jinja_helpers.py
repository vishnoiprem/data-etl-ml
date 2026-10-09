"""Tiny SQL templating — ``{{ table_name }}`` style, no external deps.

Why not use Jinja2? Because importing Jinja just to swap a table
name into a SELECT is overkill. This module supports exactly two
constructs:

  * ``{{ var }}`` — replaced with the value of ``var`` (strings
    are auto-quoted; numbers are not; ``None`` becomes ``NULL``)
  * ``{% if var %}...{% else %}...{% endif %}`` — conditional blocks

Anything more complex (loops, filters, includes) → use real Jinja2.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_VAR_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")
_IF_RE = re.compile(
    r"\{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%\}(.*?)\{%\s*end\s*if\s*%\}",
    re.DOTALL,
)


def _coerce(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    # Strings: escape single quotes by doubling them, then wrap.
    return "'" + str(value).replace("'", "''") + "'"


def render_sql(template: str, **vars: Any) -> str:
    """Substitute ``{{ var }}`` and ``{% if var %}`` in a SQL template.

    >>> render_sql("SELECT * FROM {{ table }} WHERE n = {{ n }}",
    ...            table="orders", n=42)
    "SELECT * FROM 'orders' WHERE n = 42"
    """
    rendered = template

    # Pass 1: {% if var %}...{% endif %} blocks.
    def _if_sub(m: re.Match) -> str:
        var_name = m.group(1)
        body = m.group(2)
        return body if vars.get(var_name) else ""

    rendered = _IF_RE.sub(_if_sub, rendered)

    # Pass 2: {{ var }} substitutions. We resolve variables fresh
    # so the if-block pass doesn't see the substitutions it removed.
    def _var_sub(m: re.Match) -> str:
        var_name = m.group(1)
        if var_name not in vars:
            # Leave it visible — the missing-variable signal is more
            # useful than raising mid-render.
            return m.group(0)
        return _coerce(vars[var_name])

    rendered = _VAR_RE.sub(_var_sub, rendered)
    return rendered
