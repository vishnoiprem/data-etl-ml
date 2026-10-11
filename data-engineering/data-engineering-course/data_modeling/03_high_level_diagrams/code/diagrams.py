"""Print Mermaid-compatible diagrams for the star schemas.

This is a small helper for the *narrative* part of the interview:
when you say "I'll draw the star schema," the interviewer can
either get a Mermaid block (which they can paste into a doc) or
a plain-text box (which they can read aloud).

The Mermaid output uses the `erDiagram` notation, which is the
most readable on a virtual whiteboard (Coderpad, Coderabbit,
Quokka, etc.).

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

from typing import Iterable, List, Tuple

from common import Table

# A relationship in Mermaid `erDiagram` is a triple
# (left, cardinality, right) where cardinality is one of
# "||--o{", "||--|{", "}o--o{", "||--||", etc.
Card = str
Rel = Tuple[str, Card, str]


# ---- 1. e-commerce --------------------------------------------------------


def ecommerce_er() -> str:
    """Mermaid ER for the e-commerce star schema.

    The Mermaid `erDiagram` notation uses Unicode-style
    cardinality markers. We render the conceptual ER, *not* the
    physical star schema, because the conceptual ER is what the
    candidate narrates first.
    """
    rels: List[Rel] = [
        ("dim_customers", "||--o{", "fact_order_items"),
        ("dim_products", "||--o{", "fact_order_items"),
        ("dim_orders", "||--o{", "fact_order_items"),
        ("dim_date", "||--o{", "fact_order_items"),
    ]
    return render_er("ecommerce", rels)


# ---- 2. ride-sharing -----------------------------------------------------


def rideshare_er() -> str:
    rels: List[Rel] = [
        ("dim_drivers", "||--o{", "fact_trips"),
        ("dim_riders", "||--o{", "fact_trips"),
        ("dim_cities", "||--o{", "dim_drivers"),
        ("dim_cities", "||--o{", "fact_trips"),
        ("dim_date", "||--o{", "fact_trips"),
        ("dim_time_of_day", "||--o{", "fact_trips"),
        ("dim_drivers", "||--o{", "fact_cancellations"),
        ("dim_riders", "||--o{", "fact_cancellations"),
        ("dim_date", "||--o{", "fact_cancellations"),
    ]
    return render_er("rideshare", rels)


# ---- 3. Instagram --------------------------------------------------------


def instagram_er() -> str:
    rels: List[Rel] = [
        ("dim_users", "||--o{", "dim_posts"),
        ("dim_users", "||--o{", "fact_post_events"),
        ("dim_posts", "||--o{", "fact_post_events"),
        ("dim_event_type", "||--o{", "fact_post_events"),
        ("dim_date", "||--o{", "fact_post_events"),
    ]
    return render_er("instagram", rels)


# ---- 4. customer support -------------------------------------------------


def support_er() -> str:
    rels: List[Rel] = [
        ("dim_customers", "||--o{", "fact_ticket_events"),
        ("dim_tickets", "||--o{", "fact_ticket_events"),
        ("dim_agents", "||--o{", "fact_ticket_events"),
        ("dim_event_type", "||--o{", "fact_ticket_events"),
        ("dim_date", "||--o{", "fact_ticket_events"),
    ]
    return render_er("support", rels)


# ---- 5. Spotify ----------------------------------------------------------


def spotify_er() -> str:
    rels: List[Rel] = [
        ("dim_users", "||--o{", "fact_streams"),
        ("dim_artists", "||--o{", "dim_albums"),
        ("dim_artists", "||--o{", "dim_songs"),
        ("dim_albums", "||--o{", "dim_songs"),
        ("dim_songs", "||--o{", "fact_streams"),
        ("dim_artists", "||--o{", "fact_streams"),
        ("dim_albums", "||--o{", "fact_streams"),
        ("dim_device_type", "||--o{", "fact_streams"),
        ("dim_date", "||--o{", "fact_streams"),
    ]
    return render_er("spotify", rels)


# ---- generic renderer ----------------------------------------------------


def render_er(name: str, rels: Iterable[Rel]) -> str:
    """Render a Mermaid `erDiagram` block from a list of relationships.

    >>> out = render_er("test", [("a", "||--o{", "b")])
    >>> out.startswith("erDiagram")
    True
    >>> "a ||--o{ b" in out
    True
    """
    lines: List[str] = [f"erDiagram  %% {name}"]
    for left, card, right in rels:
        lines.append(f"    {left} {card} {right}")
    return "\n".join(lines) + "\n"


def render_text_star(tables: List[Table]) -> str:
    """Render a plain-text star-schema sketch.

    Useful when the whiteboard is text-only (e.g., a phone screen,
    a plain chat). It just lists each table on its own line, with
    the fact table marked.
    """
    out: List[str] = []
    for t in tables:
        marker = "★" if t.name.startswith("fact_") else " "
        out.append(f"{marker} {t.name}  ({len(t.columns)} cols)")
    return "\n".join(out) + "\n"
