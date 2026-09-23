# Lift Calculation

## Problem
Compute relative lift of treatment vs control.

## How to Think
1. AVG(CASE WHEN converted THEN 1 END) per variant.
2. Absolute = p_t - p_c.
3. Relative = (p_t - p_c) / p_c.

## How to Remember
- **Pattern**: "Relative lift = (p_t - p_c) / p_c."
- Always pair with CI and p-value.

## SQL (Presto / Hive)
```sql
SELECT variant,
       COUNT(*) AS n,
       AVG(CASE WHEN converted THEN 1.0 ELSE 0.0 END) AS conversion_rate
FROM ab
GROUP BY variant;
```

## Common Mistakes
- Reporting lift alone — without CI, it's not actionable.
- Computing lift on data before the experiment reaches steady state.

## AI Use Cases
- A/B test reporting.
- AutoML model comparison.
- Bid strategy evaluation.
