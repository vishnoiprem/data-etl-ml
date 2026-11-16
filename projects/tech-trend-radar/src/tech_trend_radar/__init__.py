"""Tech Trend Radar — find what is trending in tech across many platforms.

The project reads from several public, credential-free developer communities,
extracts topics from what they post, and ranks those topics by *acceleration*
rather than raw volume: a topic that is suddenly accelerating beats one that is
merely loud. Every ranked topic carries the evidence that made it trend, so a
claim can be checked back against the source item that produced it.

The ranking is computed in plain Python, and the explanations are derived
from the same numbers that produced it. There is no language model in the
decision path. That is deliberate: a deterministic scoring layer is testable
and auditable, and an LLM producing the ranking is neither.

Topic extraction does use an embedding model, in one place: a post about a
technology the vocabulary has never heard of is matched against the known
technologies by similarity, so it still contributes a mention to the nearest
one the radar tracks. It produces vectors and scores — never text, never a
ranking — and it is an optional dependency. Without it the radar runs on the
lexical signals alone.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
