# Variance and Pooled Standard Error

## Problem
Compute per-arm variance and the SE for the difference in means.

## How to Think
1. Variance: AVG(x^2) - AVG(x)^2 (population variance).
2. SE of difference: sqrt(var_t/n_t + var_c/n_c) (Welch).
3. Pooled: (var_t + var_c)/2 if variances are similar.

## How to Remember
- **Pattern**: "var = AVG(x*x) - AVG(x)*AVG(x). se = sqrt(var/n)."
- population vs sample variance: divide by n vs n-1.

## SQL (Presto / Hive)
```sql
SELECT variant,
       COUNT(*) AS n,
       AVG(watch_time) AS mean,
       AVG(watch_time * watch_time) - AVG(watch_time) * AVG(watch_time) AS variance
FROM ab GROUP BY variant;
```

## Common Mistakes
- Using population variance (n) when you want sample variance (n-1).
- Pooling unequal-variance groups — use Welch.

## AI Use Cases
- Pre-computing variance in Presto/Spark for downstream stats.
- Sample size re-estimation mid-experiment.
