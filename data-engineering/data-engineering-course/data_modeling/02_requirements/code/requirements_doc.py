"""Requirements document helper.

A `RequirementsDoc` is the artifact you produce (on paper, on a
whiteboard, or in chat) at the *start* of a data modeling interview,
before drawing any tables. It pins down the consumers, the use cases,
the source systems, the freshness, and the retention. The interview
rubric explicitly scores this step.

This module also exposes `render()` so the doc can be printed,
embedded in a README, or pasted into a Confluence page.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FactSpec:
    """A single fact table the warehouse must produce.

    Attributes:
        name: snake_case name of the fact table.
        grain: a one-sentence statement of what one row is.
        measures: the numeric measures the table holds.
        dimensions: the dimensions it joins to.
    """

    name: str
    grain: str
    measures: List[str] = field(default_factory=list)
    dimensions: List[str] = field(default_factory=list)


@dataclass
class RequirementsDoc:
    """The full requirements document for a data modeling round.

    >>> doc = RequirementsDoc(product="FitnessApp")
    >>> doc.add_consumer("Analytics team", "Monthly engagement dashboard")
    >>> doc.add_use_case("MAU = unique users with >=1 workout in a month")
    >>> doc.add_source("users", "OLTP PostgreSQL", "1k rows/day")
    >>> doc.add_fact(FactSpec("fact_workouts", "one row per workout session",
    ...                       ["duration_minutes", "calories_burned"],
    ...                       ["dim_users", "dim_workout_types"]))
    >>> "fact_workouts" in doc.render()
    True
    """

    product: str
    consumers: List[Dict[str, str]] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    sources: List[Dict[str, str]] = field(default_factory=list)
    facts: List[FactSpec] = field(default_factory=list)
    volume: Optional[str] = None
    freshness: Optional[str] = None
    retention: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    # ---- builders -------------------------------------------------------

    def add_consumer(self, name: str, purpose: str) -> None:
        """Record a consumer team and what they'll use the warehouse for."""
        self.consumers.append({"name": name, "purpose": purpose})

    def add_use_case(self, description: str) -> None:
        """Record a question the warehouse must answer."""
        self.use_cases.append(description)

    def add_source(
        self, name: str, system: str, volume: str, freshness: str = ""
    ) -> None:
        """Record a source system.

        Args:
            name: snake_case name of the source (e.g. "users", "events").
            system: the system of origin (e.g. "OLTP PostgreSQL",
                "Kafka events", "S3 JSONL").
            volume: orders of magnitude (e.g. "1k rows/day", "10M/day").
            freshness: optional freshness (e.g. "real-time", "hourly").
        """
        self.sources.append({
            "name": name,
            "system": system,
            "volume": volume,
            "freshness": freshness,
        })

    def add_fact(
        self,
        name: str,
        grain: str,
        measures: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None,
    ) -> None:
        """Record a fact table the warehouse must produce."""
        self.facts.append(FactSpec(
            name=name,
            grain=grain,
            measures=list(measures or []),
            dimensions=list(dimensions or []),
        ))

    def add_note(self, note: str) -> None:
        """Append an open-ended note (assumptions, risks, ambiguities)."""
        self.notes.append(note)

    # ---- rendering ------------------------------------------------------

    def render(self) -> str:
        """Render the doc as a Markdown string."""
        lines: List[str] = [f"# Requirements — {self.product}", ""]

        if self.consumers:
            lines.append("## Consumers")
            for c in self.consumers:
                lines.append(f"- **{c['name']}** — {c['purpose']}")
            lines.append("")

        if self.use_cases:
            lines.append("## Use cases")
            for i, uc in enumerate(self.use_cases, 1):
                lines.append(f"{i}. {uc}")
            lines.append("")

        if self.sources:
            lines.append("## Source systems")
            lines.append("| name | system | volume | freshness |")
            lines.append("| --- | --- | --- | --- |")
            for s in self.sources:
                lines.append(
                    f"| {s['name']} | {s['system']} | {s['volume']} "
                    f"| {s['freshness']} |"
                )
            lines.append("")

        if self.facts:
            lines.append("## Fact tables (with grain)")
            for f in self.facts:
                dims = ", ".join(f.dimensions) if f.dimensions else "—"
                meas = ", ".join(f.measures) if f.measures else "—"
                lines.append(
                    f"- **{f.name}** — grain: *{f.grain}* — "
                    f"measures: {meas} — dimensions: {dims}"
                )
            lines.append("")

        if self.volume or self.freshness or self.retention:
            lines.append("## Non-functional")
            if self.volume:
                lines.append(f"- **Volume:** {self.volume}")
            if self.freshness:
                lines.append(f"- **Freshness:** {self.freshness}")
            if self.retention:
                lines.append(f"- **Retention:** {self.retention}")
            lines.append("")

        if self.notes:
            lines.append("## Assumptions / open questions")
            for n in self.notes:
                lines.append(f"- {n}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def to_dict(self) -> Dict[str, Any]:
        """Return the doc as a plain dict (useful for tests, JSON, etc.)."""
        return {
            "product": self.product,
            "consumers": list(self.consumers),
            "use_cases": list(self.use_cases),
            "sources": list(self.sources),
            "facts": [
                {
                    "name": f.name,
                    "grain": f.grain,
                    "measures": list(f.measures),
                    "dimensions": list(f.dimensions),
                }
                for f in self.facts
            ],
            "volume": self.volume,
            "freshness": self.freshness,
            "retention": self.retention,
            "notes": list(self.notes),
        }
