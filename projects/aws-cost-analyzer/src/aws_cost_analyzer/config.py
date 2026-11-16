"""Settings, thresholds and the analysis window.

Everything is read from the environment with a conservative default, and
nothing here talks to AWS. The thresholds are the *policy* of the tool: what
counts as "grew", what counts as "worth mentioning". They are settings
rather than constants because a finance team will want to argue with them,
and the right way to win that argument is to make them a number you can
edit rather than a literal buried in a detector.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date

# --------------------------------------------------------------------------- #
# Defaults
# --------------------------------------------------------------------------- #

DEFAULT_REGION = "ap-southeast-1"

#: The window the console view uses. Six months of monthly granularity.
DEFAULT_START = "2026-05-01"
DEFAULT_END = "2026-10-31"

#: How many trailing months the seasonal baseline looks back.
DEFAULT_BASELINE_MONTHS = 3


def _env_float(env: dict[str, str], name: str, default: float) -> float:
    raw = env.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(env: dict[str, str], name: str, default: int) -> int:
    raw = env.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(slots=True)
class Thresholds:
    """What the detectors consider worth a finding.

    These are deliberately *double* thresholds in most cases: a cost that
    moved a lot but stayed small is noise, and a cost that is large but
    stable is not a problem. Requiring both a relative move and an
    absolute floor is what keeps the detector from crying wolf on a $3
    bucket that doubled.
    """

    #: A bucket/prefix must grow at least this much (fraction) to count.
    min_growth_pct: float = 0.20

    #: ...and must be at least this many dollars per month to count.
    min_growth_usd: float = 50.0

    #: A tag/squad must grow at least this much (fraction) to count.
    min_allocation_growth_pct: float = 0.20

    #: ...and must be at least this many dollars per month to count.
    min_allocation_usd: float = 50.0

    #: Access-pattern findings need this much monthly spend to be worth it.
    min_access_usd: float = 25.0

    #: Above this ratio, an access log's coverage is considered partial.
    max_log_coverage_gap: float = 0.20

    #: Objects younger than this are never proposed for a colder class.
    min_age_days_for_glacier: int = 90

    #: Objects smaller than this are billed at the tier minimum, so moving
    #: them to a colder class saves nothing (and costs a retrieval fee).
    min_size_kb_for_ia: int = 128

    #: How many objects to sample when estimating object age.
    age_sample_size: int = 100

    #: A lifecycle transition's minimum age, per AWS's own rules.
    min_transition_days: int = 30

    #: Tagged spend below this fraction of the unfiltered service spend is
    #: reported as a coverage gap rather than presented as a full picture.
    min_tag_coverage: float = 0.90

    #: Confidence is capped at this value when tag coverage is incomplete.
    untagged_confidence_cap: float = 0.60

    #: Confidence is capped at this value when access log coverage is
    #: incomplete.
    partial_log_confidence_cap: float = 0.50


@dataclass(slots=True)
class Settings:
    """The whole configuration of one analysis run."""

    region: str = DEFAULT_REGION
    start: str = DEFAULT_START
    end: str = DEFAULT_END
    granularity: str = "MONTHLY"
    provider: str = "stub"
    ollama_model: str = "qwen2.5:7b-instruct"
    ollama_host: str = "http://localhost:11434"
    thresholds: Thresholds = field(default_factory=Thresholds)

    @property
    def start_date(self) -> date:
        return date.fromisoformat(self.start)

    @property
    def end_date(self) -> date:
        return date.fromisoformat(self.end)

    @property
    def exclusive_end(self) -> str:
        """The end date as the Cost Explorer API wants it.

        ``TimePeriod.End`` is **exclusive** — "up to and including
        2017-04-30 but not including 2017-05-01". So a window that ends
        2026-10-31 must be sent as ``End="2026-11-01"`` or October
        silently disappears from the response with no error at all.
        """
        from datetime import timedelta

        return (self.end_date + timedelta(days=1)).isoformat()

    @property
    def baseline_months(self) -> int:
        return DEFAULT_BASELINE_MONTHS


def load_settings(overrides: dict[str, str] | None = None) -> Settings:
    """Build settings from the environment, with optional overrides.

    ``overrides`` exists so a CLI flag can beat an environment variable
    without the loader having to know about the CLI.
    """
    env = dict(os.environ)
    if overrides:
        env.update({k: v for k, v in overrides.items() if v is not None})

    def get(name: str, default: str) -> str:
        value = env.get(name, "").strip()
        return value or default

    thresholds = Thresholds(
        min_growth_pct=_env_float(env, "AWSCA_MIN_GROWTH_PCT", 0.20),
        min_growth_usd=_env_float(env, "AWSCA_MIN_GROWTH_USD", 50.0),
        min_allocation_growth_pct=_env_float(env, "AWSCA_MIN_ALLOCATION_GROWTH_PCT", 0.20),
        min_allocation_usd=_env_float(env, "AWSCA_MIN_ALLOCATION_USD", 50.0),
        min_access_usd=_env_float(env, "AWSCA_MIN_ACCESS_USD", 25.0),
        max_log_coverage_gap=_env_float(env, "AWSCA_MAX_LOG_COVERAGE_GAP", 0.20),
        min_age_days_for_glacier=_env_int(env, "AWSCA_MIN_AGE_DAYS_FOR_GLACIER", 90),
        min_size_kb_for_ia=_env_int(env, "AWSCA_MIN_SIZE_KB_FOR_IA", 128),
        age_sample_size=_env_int(env, "AWSCA_AGE_SAMPLE_SIZE", 100),
        min_transition_days=_env_int(env, "AWSCA_MIN_TRANSITION_DAYS", 30),
        min_tag_coverage=_env_float(env, "AWSCA_MIN_TAG_COVERAGE", 0.90),
        untagged_confidence_cap=_env_float(env, "AWSCA_UNTAGGED_CONFIDENCE_CAP", 0.60),
        partial_log_confidence_cap=_env_float(env, "AWSCA_PARTIAL_LOG_CONFIDENCE_CAP", 0.50),
    )

    return Settings(
        region=get("AWS_REGION", DEFAULT_REGION),
        start=get("AWSCA_START", DEFAULT_START),
        end=get("AWSCA_END", DEFAULT_END),
        granularity=get("AWSCA_GRANULARITY", "MONTHLY").upper(),
        provider=get("COPYFORGE_LLM_PROVIDER", env.get("AWSCA_PROVIDER", "stub")).lower(),
        ollama_model=get("COPYFORGE_OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        ollama_host=get("COPYFORGE_OLLAMA_HOST", "http://localhost:11434"),
        thresholds=thresholds,
    )
