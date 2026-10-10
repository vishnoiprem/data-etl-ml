# 28 — Data Quality: The Five Checks Every Pipeline Must Have

> **Lesson 28 of 30 — Performance & Fault Tolerance**

The most important lesson in this module. A pipeline that
runs on time but produces wrong data is worse than one that
fails loudly — it produces wrong dashboards, wrong ML
models, and wrong decisions. This lesson is the *expectation
pattern*: the five checks every pipeline must have, the
code that runs them, and the interview answer that
demonstrates you can actually do it.

---

## 1. The five standard checks

Every production pipeline — without exception — runs at
least these five:

| # | Check | What it answers | How |
|---|---|---|---|
| 1 | **Row count** | "Did the pipeline produce the expected number of rows?" | Compare current count to source count or to a 30-day baseline. |
| 2 | **Null rate** | "Are the columns mostly populated?" | Per-column `null / total`, alert if > threshold or > baseline + 3σ. |
| 3 | **Distribution drift** | "Have the values shifted?" | KS test or summary stats compared to a baseline snapshot. |
| 4 | **Freshness** | "Is the data recent?" | `MAX(ts)` vs the SLA window. |
| 5 | **Schema conformance** | "Does the destination match the contract?" | Column presence, column types, nullability. |

The senior move: name all five unprompted. "Row count,
null rate, distribution drift, freshness, and schema. Every
production table."

---

## 2. Where they run: the three gates

Checks run at three points in a pipeline's life:

| Stage | Purpose | Action on failure |
|---|---|---|
| **Pre-load** (gate) | Block bad data from entering the destination. | Halt the pipeline, page on-call. |
| **Post-load** (warn) | Detect drift that wouldn't block but should alert. | Send a Slack alert, open a ticket. |
| **Continuous** (anomaly detection) | Catch silent issues hours or days later. | Dashboard, anomaly detector, weekly report. |

**The senior move:** "Row count and schema conformance are
*pre-load* gates — they fail the pipeline. Null rate and
distribution drift are *post-load* warnings — they page but
don't fail. Freshness is *continuous* — it runs every 5
minutes and pages if the source is stale."

---

## 3. The `QualityCheck` class

The course provides a Python class with the five checks.
Each method returns a `CheckResult` with `passed: bool`,
`value: float`, and `message: str`.

```python
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Sequence, Mapping
from scipy import stats


@dataclass
class CheckResult:
    name: str
    passed: bool
    value: float
    message: str


class QualityCheck:
    """Five standard data-quality checks for a single table.

    Each check returns a CheckResult. The caller decides
    whether to fail the pipeline (pre-load), warn (post-load),
    or page (continuous).
    """

    def __init__(self, df: pd.DataFrame, name: str = "table"):
        self.df = df
        self.name = name

    # ---- Check 1: row count ------------------------------------

    def check_row_count(
        self,
        expected: Optional[int] = None,
        baseline: Optional[pd.Series] = None,
        tolerance: float = 0.10,
    ) -> CheckResult:
        """Compare current row count to expected or baseline.

        Args:
            expected:    If set, the exact row count to assert.
            baseline:    If set, a 30-day history of row counts.
                         Current count must be within tolerance of mean.
            tolerance:   Allowed fractional deviation (default 10%).
        """
        n = len(self.df)
        if expected is not None:
            passed = n == expected
            return CheckResult(
                name=f"{self.name}.row_count",
                passed=passed,
                value=float(n),
                message=f"row_count={n}, expected={expected}",
            )
        if baseline is not None and len(baseline) > 0:
            mean = float(baseline.mean())
            dev = abs(n - mean) / max(mean, 1)
            passed = dev <= tolerance
            return CheckResult(
                name=f"{self.name}.row_count",
                passed=passed,
                value=float(n),
                message=(
                    f"row_count={n}, baseline_mean={mean:.0f}, "
                    f"deviation={dev:.1%}"
                ),
            )
        return CheckResult(
            name=f"{self.name}.row_count",
            passed=True,
            value=float(n),
            message=f"row_count={n} (no baseline)",
        )

    # ---- Check 2: null rate -------------------------------------

    def check_null_rate(
        self,
        columns: Sequence[str],
        max_rate: float = 0.01,
    ) -> list[CheckResult]:
        """Per-column null rate must be <= max_rate."""
        results = []
        for col in columns:
            if col not in self.df.columns:
                results.append(CheckResult(
                    name=f"{self.name}.null_rate.{col}",
                    passed=False,
                    value=float("nan"),
                    message=f"column '{col}' missing",
                ))
                continue
            rate = float(self.df[col].isna().mean())
            results.append(CheckResult(
                name=f"{self.name}.null_rate.{col}",
                passed=rate <= max_rate,
                value=rate,
                message=f"null_rate({col})={rate:.2%}, max={max_rate:.2%}",
            ))
        return results

    # ---- Check 3: distribution drift ----------------------------

    def check_distribution(
        self,
        column: str,
        baseline_sample: np.ndarray,
        alpha: float = 0.01,
    ) -> CheckResult:
        """Two-sample KS test: current vs baseline.

        Fails if p-value < alpha. The KS statistic measures the
        max absolute difference between the two empirical CDFs.
        """
        if column not in self.df.columns:
            return CheckResult(
                name=f"{self.name}.distribution.{column}",
                passed=False,
                value=float("nan"),
                message=f"column '{column}' missing",
            )
        current = self.df[column].dropna().to_numpy()
        if len(current) == 0 or len(baseline_sample) == 0:
            return CheckResult(
                name=f"{self.name}.distribution.{column}",
                passed=True,
                value=float("nan"),
                message="insufficient samples for KS test",
            )
        ks_stat, p_value = stats.ks_2samp(current, baseline_sample)
        return CheckResult(
            name=f"{self.name}.distribution.{column}",
            passed=p_value > alpha,
            value=float(ks_stat),
            message=(
                f"ks_stat={ks_stat:.3f}, p_value={p_value:.3f}, "
                f"alpha={alpha}"
            ),
        )

    # ---- Check 4: freshness -------------------------------------

    def check_freshness(
        self,
        ts_column: str,
        sla: timedelta,
        now: Optional[datetime] = None,
    ) -> CheckResult:
        """Max timestamp must be within `sla` of `now`."""
        if ts_column not in self.df.columns:
            return CheckResult(
                name=f"{self.name}.freshness.{ts_column}",
                passed=False,
                value=float("nan"),
                message=f"column '{ts_column}' missing",
            )
        last_update = self.df[ts_column].max()
        if pd.isna(last_update):
            return CheckResult(
                name=f"{self.name}.freshness.{ts_column}",
                passed=False,
                value=float("inf"),
                message="no timestamps found",
            )
        now = now or datetime.utcnow()
        lag = now - pd.to_datetime(last_update).to_pydatetime()
        passed = lag <= sla
        return CheckResult(
            name=f"{self.name}.freshness.{ts_column}",
            passed=passed,
            value=float(lag.total_seconds()),
            message=(
                f"lag={lag}, sla={sla}, last_update={last_update}"
            ),
        )

    # ---- Check 5: schema conformance ----------------------------

    def check_schema(
        self,
        contract: Mapping[str, str],
    ) -> list[CheckResult]:
        """Assert each required column is present with the expected dtype.

        Args:
            contract: {column_name: expected_dtype_string}.
        """
        results = []
        for col, expected_dtype in contract.items():
            if col not in self.df.columns:
                results.append(CheckResult(
                    name=f"{self.name}.schema.{col}",
                    passed=False,
                    value=float("nan"),
                    message=f"column '{col}' missing",
                ))
                continue
            actual_dtype = str(self.df[col].dtype)
            # Loose match: int64 matches 'int', float64 matches 'float'.
            ok = expected_dtype.lower() in actual_dtype.lower()
            results.append(CheckResult(
                name=f"{self.name}.schema.{col}",
                passed=ok,
                value=float("nan"),
                message=(
                    f"column '{col}' dtype={actual_dtype}, "
                    f"expected={expected_dtype}"
                ),
            ))
        return results
```

---

## 4. Using the class in a pipeline

```python
# Post-load: warn but don't fail
def run_post_load_checks(df: pd.DataFrame) -> None:
    qc = QualityCheck(df, "orders")

    # 1. Row count vs 30-day baseline
    baseline = load_baseline_row_counts("orders", days=30)
    rc = qc.check_row_count(baseline=baseline, tolerance=0.20)
    if not rc.passed:
        alert_slack(f"Row count drift: {rc.message}")

    # 2. Null rate on critical columns
    for r in qc.check_null_rate(
        ["order_id", "user_id", "amount", "status"],
        max_rate=0.001,
    ):
        if not r.passed:
            alert_slack(f"Null rate: {r.message}")

    # 3. Distribution drift on amount
    baseline_amount = load_baseline_sample("orders", "amount", n=10_000)
    dd = qc.check_distribution("amount", baseline_amount)
    if not dd.passed:
        alert_slack(f"Distribution drift: {dd.message}")


# Pre-load: gate the load
def run_pre_load_checks(df: pd.DataFrame, contract: dict) -> None:
    qc = QualityCheck(df, "orders")

    # 4. Schema conformance
    for r in qc.check_schema(contract):
        if not r.passed:
            raise PipelineError(f"Schema violation: {r.message}")


# Continuous: freshness every 5 minutes
def run_freshness_check() -> None:
    last_update = read_max("orders", "updated_at")
    qc = QualityCheck(
        pd.DataFrame({"updated_at": [last_update]}), "orders"
    )
    fr = qc.check_freshness(
        "updated_at",
        sla=timedelta(minutes=30),
    )
    if not fr.passed:
        page_oncall(f"Freshness breach: {fr.message}")
```

---

## 5. Tooling landscape

The course ships the `QualityCheck` class, but in production
you'll usually reach for a tool. The senior move is knowing
which one fits which situation.

| Tool | Best for | Pros | Cons |
|---|---|---|---|
| **Great Expectations** | Open-source expectation suite; YAML + Python. | Open-source, large community, integrates with Airflow. | UI is weak; YAML can get verbose. |
| **dbt tests** | Tests on dbt models. | Native to dbt, simple `not_null`, `unique`, `accepted_values`. | Limited to dbt; no anomaly detection. |
| **Soda** | YAML-defined checks with a clean UI. | Soda Cloud UI is excellent; SLAs as code. | Core is open-source, advanced is paid. |
| **Monte Carlo** | Enterprise anomaly detection. | Full data observability — lineage + freshness + drift. | Expensive; vendor lock-in. |
| **Datafold** | Column-level diff between environments. | Best-in-class for "what changed in this column?" | Focused on diff, less on continuous monitoring. |
| **Bigeye** | Metric-based anomaly detection. | Easy to set up; good for non-engineers. | Less control than GE / Soda. |

**The senior move:** "For a small team I'd start with dbt
tests (free, native) plus Great Expectations for the
non-dbt loads. For a larger org I'd add Soda or Monte Carlo
on top for the UI and the anomaly detection."

---

## 6. The fail-loud principle

The single most important principle: **fail loud, not
silent**. A pipeline that catches exceptions and continues
is worse than one that crashes.

```python
# BAD: catch and continue
try:
    write_to_warehouse(rows)
except Exception:
    log.error("write failed")
    # continues with the next batch — wrong data downstream

# GOOD: catch and re-raise
try:
    write_to_warehouse(rows)
except Exception as e:
    log.error("write failed")
    raise  # crash the pipeline, page on-call
```

**The senior move:** "I'd rather have a pipeline that pages
on-call at 3 AM than one that silently produces wrong data.
Wrong data is the failure mode you don't notice until the
quarterly review."

---

## 7. The interview answer

> "Every production pipeline runs five standard data-quality
> checks: row count compared to source or baseline, null
> rate per column, distribution drift via a KS test,
> freshness of the latest timestamp vs the SLA, and schema
> conformance against the contract. The first two are
> pre-load gates that fail the pipeline; the next two are
> post-load warnings that alert on Slack; the fifth runs
> continuously on a 5-minute cron. For tooling I'd start
> with dbt tests plus Great Expectations, then add Soda or
> Monte Carlo if the team needs a UI. The principle is
> fail loud: I'd rather page on-call at 3 AM than silently
> produce wrong data."

That single paragraph covers: the five checks, where each
runs, the tooling tiers, and the fail-loud principle. Senior
answer in 45 seconds.

---

## Try it

Look at the most recent pipeline you've worked on. Does it
have row count? Null rate? Distribution drift? Freshness?
Schema? If any is missing, the pipeline is one bad row away
from producing wrong data — and the downstream won't know
for weeks.

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
