"""Configuration for Trade-Sourcing AI.

Everything the agent needs to know about *where the data lives* and *how much a
decision is worth* lives here, so the business assumptions are in one auditable
place rather than scattered through the code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

# src/trade_sourcing_ai/config.py -> src/trade_sourcing_ai -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# The real trade-finder dataset this project reasons over.
TRADE_FINDER_DIR = PROJECT_ROOT.parent / "realtime-stock-pipeline" / "trade-finder"

DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
AUDIT_DIR = PROJECT_ROOT / "reports" / "audit"

QUOTES_PATH = DATA_DIR / "quotes.json"

# The trade-finder modules we import. Kept as names so the corpus module can
# assert they exist and give a clear error if the sibling project moves.
TRADE_FINDER_MODULES = (
    "find_opportunities",
    "verify_suppliers",
    "demand_in",
)

# --------------------------------------------------------------------------- #
# Model configuration
# --------------------------------------------------------------------------- #

#: Local embedding model. Small enough to run on CPU, good enough for a corpus
#: of this size (40 documents).
EMBEDDING_MODEL_NAME = os.environ.get(
    "TRADE_AI_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

#: Reciprocal-rank-fusion constant. 60 is the value used by Cormack et al. and
#: the same constant the repo's enterprise-search agent uses.
RRF_K = 60


# --------------------------------------------------------------------------- #
# Business assumptions
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ValueConfig:
    """The knobs that turn agent activity into money.

    These are *assumptions*, not measurements, except where a value is derived
    from the trade-finder dataset itself. They are surfaced in every value
    report so a reader can disagree with them explicitly.
    """

    #: What one hour of the operator's attention costs, in USD. Used to price
    #: the manual baseline and the agent's own runtime.
    operator_hourly_usd: float = 75.0

    #: Minutes a human is assumed to spend reading the shortlist, waiting on
    #: supplier replies, and hand-comparing quotes. This is the baseline the
    #: agent is measured against.
    manual_minutes_per_decision: float = 90.0

    #: Cost per 1K tokens for the optional hosted path. Zero in stub/Ollama
    #: mode — the local paths genuinely cost nothing per token.
    hosted_cost_per_1k_tokens_usd: float = 0.0

    #: Cost per 1K tokens for embedding calls, when a hosted embedder is used.
    hosted_embedding_cost_per_1k_tokens_usd: float = 0.0

    #: Order value used to convert a per-unit margin into a per-order margin.
    default_order_units: int = 500

    #: Minimum margin_pct for a route to be considered viable.
    min_margin_pct: float = 0.15

    #: Number of Monte-Carlo style scenarios to project.
    scenarios: int = 3

    extra: dict = field(default_factory=dict)

    @property
    def manual_hours_per_decision(self) -> float:
        return self.manual_minutes_per_decision / 60.0

    @property
    def manual_cost_per_decision_usd(self) -> float:
        return self.manual_hours_per_decision * self.operator_hourly_usd


@dataclass(frozen=True)
class Settings:
    """Runtime settings, resolved once and passed around explicitly."""

    #: "stub" (default, deterministic, offline) or "ollama" (optional local LLM).
    llm_provider: str = "stub"

    #: Model name for the optional Ollama backend.
    ollama_model: str = "qwen2.5:7b-instruct"

    #: Ollama endpoint.
    ollama_host: str = "http://localhost:11434"

    #: Whether to attempt dense retrieval at all.
    use_dense: bool = True

    #: Default number of documents returned by a search.
    top_k: int = 5

    value: ValueConfig = field(default_factory=ValueConfig)

    @classmethod
    def from_env(cls) -> Settings:
        provider = os.environ.get("TRADE_AI_LLM_PROVIDER", "").strip().lower()
        if not provider:
            # Auto-detect: only use Ollama if it is explicitly requested. We do
            # not probe the network at import time.
            provider = "stub"
        return cls(
            llm_provider=provider,
            ollama_model=os.environ.get("TRADE_AI_OLLAMA_MODEL", "qwen2.5:7b-instruct"),
            ollama_host=os.environ.get("TRADE_AI_OLLAMA_HOST", "http://localhost:11434"),
            use_dense=os.environ.get("TRADE_AI_USE_DENSE", "1").strip() != "0",
            top_k=int(os.environ.get("TRADE_AI_TOP_K", "5")),
            value=ValueConfig(),
        )


#: FX rates per USD. Mirrors the fallback table in
#: `trade-finder/find_opportunities.py::_fetch_fx` so the two models agree when
#: the network is down. Kept local so this project never makes a network call.
FX_FALLBACK: dict[str, float] = {
    "USD": 1.0, "CNY": 7.20, "INR": 83.0, "VND": 25000, "TRY": 32.0,
    "MXN": 17.5, "BDT": 110.0, "IDR": 16000, "THB": 36.0, "EUR": 0.92,
    "GBP": 0.78, "AUD": 1.52, "JPY": 152.0, "CAD": 1.36, "AED": 3.67,
}
