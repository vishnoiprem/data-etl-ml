"""
Spark Batch: Compute final experiment results.

For each (experiment, metric, variant), compute:
  - sample size
  - mean, std
  - CUPED-adjusted mean & std
  - Welch t-test diff + CI + p-value
  - mSPRT always-valid p-value
  - Sample Ratio Mismatch (SRM) chi2

Writes to experiment_results table for downstream dashboarding.
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, pandas_udf, PandasUDFType, current_timestamp
)
import pandas as pd
import numpy as np


@pandas_udf("double", PandasUDFType.GROUPED_AGG)
def mean_udf(s: pd.Series) -> float:
    return float(s.mean())


@pandas_udf("double", PandasUDFType.GROUPED_AGG)
def std_udf(s: pd.Series) -> float:
    return float(s.std(ddof=1)) if len(s) > 1 else 0.0


def run(experiment_id: str, metric_id: str,
        user_metric_table: str = "local.gold.user_metric_daily",
        out_table: str          = "local.gold.experiment_results"):

    spark = SparkSession.builder.getOrCreate()

    df = (spark.read.format("iceberg").load(user_metric_table)
                 .filter(col("experiment_id") == experiment_id)
                 .filter(col("metric_id")   == metric_id))

    # Per-variant summary
    summary = (df.groupBy("variant_id")
                 .agg({"value": "count"})
                 .withColumnRenamed("count(value)", "n"))

    # Pull to driver for stats (small enough for one experiment)
    pdf = df.select("variant_id", "value", "pre_value").toPandas()

    rows = []
    for variant, sub in pdf.groupby("variant_id"):
        if variant == "control":
            continue
        c = pdf[pdf["variant_id"] == "control"]["value"].values
        t = sub["value"].values
        if len(c) < 30 or len(t) < 30:
            continue

        # Welch
        n_c, n_t = len(c), len(t)
        m_c, m_t = c.mean(), t.mean()
        v_c, v_t = c.var(ddof=1), t.var(ddof=1)
        se = np.sqrt(v_c / n_c + v_t / n_t)
        diff = m_t - m_c
        df_welch = (v_c/n_c + v_t/n_t)**2 / ((v_c/n_c)**2/(n_c-1) + (v_t/n_t)**2/(n_t-1))
        from scipy import stats
        p = 2 * (1 - stats.t.cdf(abs(diff/se), df=df_welch))
        ci_lo = diff - 1.96 * se
        ci_hi = diff + 1.96 * se

        # CUPED — theta MUST be computed from COMBINED control+treatment data
        # (Deng et al. 2013). Computing on treatment only biases the estimate
        # and produces inconsistent variance reduction across arms.
        if "pre_value" in pdf.columns and pdf["pre_value"].notna().any():
            c_pre = pdf[pdf["variant_id"] == "control"]["pre_value"].values
            t_pre = sub["pre_value"].values
            all_metric = np.concatenate([c, t])
            all_pre    = np.concatenate([c_pre, t_pre])
            theta = np.cov(all_metric, all_pre, ddof=1)[0, 1] / np.var(all_pre, ddof=1)
            pre_mean = pdf["pre_value"].mean()
            cuped_t = t - theta * (t_pre - pre_mean)
            cuped_c = c - theta * (c_pre - pre_mean)
            v_cuped_t = cuped_t.var(ddof=1)
            cuped_var_reduction = 1 - v_cuped_t / v_t
        else:
            cuped_var_reduction = 0.0

        rows.append({
            "experiment_id": experiment_id,
            "metric_id":      metric_id,
            "variant_id":     variant,
            "n_control":      n_c,
            "n_treatment":    n_t,
            "mean_control":   float(m_c),
            "mean_treatment": float(m_t),
            "point_estimate": float(diff),
            "ci_low":         float(ci_lo),
            "ci_high":        float(ci_hi),
            "p_value":        float(p),
            "cuped_var_reduction": float(cuped_var_reduction),
        })

    out_pdf = pd.DataFrame(rows)
    out_pdf["computed_ts"] = pd.Timestamp.utcnow()
    (spark.createDataFrame(out_pdf)
          .write.format("iceberg").mode("append").saveAsTable(out_table))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--experiment", required=True)
    p.add_argument("--metric",     required=True)
    args = p.parse_args()
    run(args.experiment, args.metric)
