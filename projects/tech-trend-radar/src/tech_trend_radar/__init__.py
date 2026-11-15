"""Tech Trend Radar — find what is trending in tech across many platforms.

The project reads from several public, credential-free developer communities,
extracts topics from what they post, and ranks those topics by *acceleration*
rather than raw volume: a topic that is suddenly accelerating beats one that is
merely loud. Every ranked topic carries the evidence that made it trend, so a
claim can be checked back against the source item that produced it.

The ranking is computed in plain Python. The language model only narrates the
result. That split is deliberate: a deterministic scoring layer is testable and
auditable, an LLM producing the ranking is neither.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
