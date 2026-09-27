"""
Problem 03: CUPED — variance reduction using a pre-experiment covariate.

Meta flavor: "The experiment is underpowered. How do you detect the same effect
with less traffic?"

How to Think:
- CUPED = Controlled-experiment Using Pre-Existing Data. You subtract the part
  of the metric that was already predictable BEFORE the experiment started:
      theta  = cov(Y, X) / var(X)          (X = pre-period metric, pooled)
      Y_adj  = Y - theta * (X - mean(X))
- Why it is unbiased: X is measured BEFORE assignment, so it cannot be affected
  by treatment. Randomisation makes E[X] equal across arms, so subtracting a
  function of X shifts both arms identically and the treatment effect survives.
- What you gain: variance drops by roughly (1 - corr(X,Y)^2). Less variance for
  the same n = more power = smaller detectable effect.
- The hard constraint worth stating: NEVER use an in-experiment covariate. If X
  is measured after assignment, treatment can move it, and the adjustment
  becomes biased. That single sentence separates people who have run CUPED from
  people who have read about it.

This file's data is constructed so the covariate perfectly predicts within-arm
variation (Y = X + constant per arm), which is the clean limiting case:
  - raw variance     = 2.5 in both arms
  - adjusted variance = 0.0 in both arms
  - the 4.0 treatment effect is PRESERVED exactly
Real covariates are far weaker; the mechanism is identical.

Spark note:
- theta must be computed on POOLED data (both arms together), not per arm.
  Computing it per arm leaks the treatment effect into the adjustment.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect

# Pre-period (X) and post-period (Y) per user.
# X means are equal across arms (9.0 each) — that is what randomisation buys.
# Within each arm Y = X + c, so the covariate explains all within-arm variance.
spark.createDataFrame([
    (1,  "control",   11.0, 12.0),
    (2,  "control",    8.0,  9.0),
    (3,  "control",   10.0, 11.0),
    (4,  "control",    9.0, 10.0),
    (5,  "control",    7.0,  8.0),
    (6,  "treatment", 10.0, 15.0),
    (7,  "treatment",  9.0, 14.0),
    (8,  "treatment", 11.0, 16.0),
    (9,  "treatment",  7.0, 12.0),
    (10, "treatment",  8.0, 13.0),
], ["user_id", "variant", "pre_metric", "post_metric"]).createOrReplaceTempView("cuped_exp")

# Sanity: arms are balanced on the covariate, and raw effect is 4.0.
expect("pre-period balance + raw effect", """
SELECT variant, COUNT(*) AS n,
       ROUND(AVG(pre_metric), 2)  AS mean_pre,
       ROUND(AVG(post_metric), 2) AS mean_post,
       ROUND(VAR_SAMP(post_metric), 4) AS raw_var
FROM cuped_exp GROUP BY variant ORDER BY variant
""", [
    ("control",   5, 9.00, 10.00, 2.5),
    ("treatment", 5, 9.00, 14.00, 2.5),
])

# theta from POOLED data, then the adjusted metric.
expect("theta (pooled)", """
SELECT ROUND(COVAR_SAMP(post_metric, pre_metric) / VAR_SAMP(pre_metric), 4) AS theta
FROM cuped_exp
""", [(1.0,)])

expect("CUPED-adjusted: effect preserved, variance eliminated", """
WITH pooled AS (
    SELECT AVG(pre_metric) AS x_bar,
           COVAR_SAMP(post_metric, pre_metric) / VAR_SAMP(pre_metric) AS theta
    FROM cuped_exp
),
adj AS (
    SELECT e.variant,
           e.post_metric - p.theta * (e.pre_metric - p.x_bar) AS y_adj
    FROM cuped_exp e CROSS JOIN pooled p
)
SELECT variant,
       ROUND(AVG(y_adj), 4) AS mean_adj,
       ROUND(VAR_SAMP(y_adj), 4) AS var_adj
FROM adj GROUP BY variant ORDER BY variant
""", [
    ("control",   10.0, 0.0),
    ("treatment", 14.0, 0.0),
])
