"""
Problem 02: Welch's t-test for an A/B result.

Meta flavor: "Is that 40% lift real, or noise?"

How to Think:
- Standard error of a difference of means, UNEQUAL variances (Welch):
      se = sqrt(var_t/n_t + var_c/n_c)
      t  = (mean_t - mean_c) / se
- Use Welch, not Student's pooled t-test. Pooled assumes equal variances; in
  product experiments they are routinely unequal, and the pooled test is then
  anti-conservative (it over-declares significance). Naming Welch specifically
  is the signal here.
- |t| > ~1.96 is significant at 95% for large n. With n=5 per arm the critical
  value is much larger (~2.3 on ~8 df), so a small-sample result needs a bigger
  t. Say this rather than blindly comparing to 1.96.
- Sanity check first: se = sqrt(2.5/5 + 2.5/5) = sqrt(1.0) = 1.0, so t = 4/1 = 4.

Spark note:
- All scalar arithmetic on aggregates — one pass, no shuffle beyond the group-by.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect

SQL = """
WITH stats AS (
    SELECT variant, COUNT(*) AS n, AVG(metric) AS mean_m, VAR_SAMP(metric) AS var_m
    FROM experiment GROUP BY variant
),
p AS (
    SELECT
      MAX(CASE WHEN variant = 'control'   THEN n      END) AS nc,
      MAX(CASE WHEN variant = 'control'   THEN mean_m END) AS mc,
      MAX(CASE WHEN variant = 'control'   THEN var_m  END) AS vc,
      MAX(CASE WHEN variant = 'treatment' THEN n      END) AS nt,
      MAX(CASE WHEN variant = 'treatment' THEN mean_m END) AS mt,
      MAX(CASE WHEN variant = 'treatment' THEN var_m  END) AS vt
    FROM stats
)
SELECT ROUND(mt - mc, 4) AS abs_lift,
       ROUND(SQRT(vt / nt + vc / nc), 4) AS std_error,
       ROUND((mt - mc) / SQRT(vt / nt + vc / nc), 4) AS t_stat
FROM p
"""
expect("Welch t-test", SQL, [(4.0, 1.0, 4.0)])
