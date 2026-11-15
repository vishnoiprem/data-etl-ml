"""Trade-Sourcing AI — a sourcing agent that decides which supplier to buy from.

The agent retrieves over the real trade-finder dataset (products, suppliers,
India demand signals), recomputes the landed margin for incoming quotes, and
recommends one supplier with an auditable rationale.

The recommendation itself is computed in plain Python, not by the LLM. The LLM
only explains the recommendation. That split is deliberate: a deterministic
decision layer is testable and auditable, an LLM making the pick is neither.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
