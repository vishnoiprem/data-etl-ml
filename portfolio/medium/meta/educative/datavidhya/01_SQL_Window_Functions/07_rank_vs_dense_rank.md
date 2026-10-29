# RANK vs DENSE_RANK vs ROW_NUMBER

## Problem
Leaderboard: rank creators by weekly views. How do ties behave?

## How to Think
1. ROW_NUMBER — strictly 1,2,3,4… (ties broken arbitrarily).
2. RANK — Olympic medal style: 1,1,3,4 (gap after ties).
3. DENSE_RANK — packed: 1,1,2,3 (no gap).

## How to Remember
- **Pattern**: "ROW_NUMBER = unique. RANK = gap. DENSE_RANK = packed."
- Tie-break ORDER BY multiple columns to make ranking deterministic.

## SQL (Presto / Hive)
```sql
SELECT creator_id, views,
       ROW_NUMBER() OVER (ORDER BY views DESC) AS rn,
       RANK()       OVER (ORDER BY views DESC) AS rk,
       DENSE_RANK() OVER (ORDER BY views DESC) AS drk
FROM creator_weekly;
```

## Common Mistakes
- Using ROW_NUMBER() when ties should share a rank.
- Forgetting to add tie-breaker columns — results are nondeterministic across runs.

## AI Use Cases
- Top-N leaderboards with strict cutoffs (ROW_NUMBER).
- Ranking with ties (RANK / DENSE_RANK) for competitions.
- Multi-criteria ranking (combine via tie-breaker columns).
