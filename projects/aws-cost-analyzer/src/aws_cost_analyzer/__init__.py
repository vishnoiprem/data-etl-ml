"""AWS Cost Analyzer — deterministic S3 cost root-cause analysis.

The *decision* path is plain Python: detectors read normalised cost records
and emit findings with evidence. A local model may write the narrative that
explains a finding, but it cannot change a severity, a dollar figure, or a
recommendation.

The same split as the sibling ``copyforge-ai`` and ``tech-trend-radar``
projects: a model in the decision path makes the decisions unauditable, and
an unauditable decision is not worth making.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
