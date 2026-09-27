"""
Spark Batch: Detect interaction effects between concurrent experiments.

Approach (industry-standard): fit a two-way ANOVA / linear model
   metric ~ variant_A * variant_B + user_covariates

Then check whether the interaction term is statistically significant.
If yes, mark the pair as 'non-orthogonal' so PMs know to interpret carefully.

Output:
    - interaction_report table with effect size, p-value, recommendation
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, count, avg, stddev
import numpy as np
from scipy import stats

# --------------------------------------------------------------------- #
# At scale, use Spark UDFs + scipy or distributed statsmodels
# For brevity, here is the pairwise ANOVA on top of metric_daily
# --------------------------------------------------------------------- #


def detect_interactions(
    user_metric_table: str,
    assignments_table: str,
    out_table: str,
    max_pairs: int = 200,        # safety cap
    min_users_per_cell: int = 100,
):
    spark = SparkSession.builder.getOrCreate()

    metrics = spark.read.format("iceberg").load(user_metric_table) \
                       .filter(col("metric_id") == "primary_metric")
    assignments = spark.read.format("iceberg").load(assignments_table) \
                            .filter(col("status") == "RUNNING")

    # At scale, you'd build a (user_id, experiment_id, variant_id) long table
    # then pivot to wide with one column per active experiment. That requires
    # knowing experiment_ids up front; for this demo we hard-code two.
    # ----- demo with two experiments -----
    A = (assignments.filter(col("experiment_id") == "exp_A")
                    .select(col("user_id"), col("variant_id").alias("variant_A")))
    B = (assignments.filter(col("experiment_id") == "exp_B")
                    .select(col("user_id"), col("variant_id").alias("variant_B")))
    joined = (metrics
              .join(A, "user_id")
              .join(B, "user_id")
              .select("variant_A", "variant_B", "value"))

    # Bring to driver; only safe for moderate scale
    pdf = joined.toPandas()

    # Two-way ANOVA without replication (Type II)
    cells = pdf.groupby(["variant_A", "variant_B"])["value"].agg(["mean", "count", "std"])
    cells = cells.reset_index()

    print(cells)
    # If interaction is suspected, recompute using statsmodels
    import statsmodels.api as sm
    from statsmodels.formula.api import ols
    model = ols("value ~ C(variant_A) * C(variant_B)", data=pdf).fit()
    anova = sm.stats.anova_lm(model, typ=2)
    print(anova)

    # Save report
    report_pdf = cells.copy()
    report_pdf["interaction_p"] = anova.loc["C(variant_A):C(variant_B)", "PR(>F)"]
    report_pdf["recommendation"] = np.where(
        report_pdf["interaction_p"] < 0.01,
        "INTERACTION_DETECTED",
        "ORTHOGONAL_OK",
    )
    spark.createDataFrame(report_pdf).write.format("iceberg") \
         .mode("overwrite").saveAsTable(out_table)


if __name__ == "__main__":
    detect_interactions("local.gold.user_metric_daily",
                        "local.gold.assignments",
                        "local.gold.interaction_report")
