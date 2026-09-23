# FIRST_VALUE / LAST_VALUE

## Problem
Find the first and last page each user visited in their session.

## How to Think
1. FIRST_VALUE reads from the top of the window frame.
2. LAST_VALUE has a trap: default frame ends at CURRENT ROW, so it returns the current row's value, not the partition's last.
3. To get the true last row, set frame to `BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.

## How to Remember
- **Pattern**: "FIRST_VALUE = top, LAST_VALUE = bottom — but watch the frame."
- Always specify the full frame when using LAST_VALUE.

## SQL (Presto / Hive)
```sql
SELECT user_id, step, page,
       FIRST_VALUE(page) OVER (PARTITION BY user_id ORDER BY step) AS first_page,
       LAST_VALUE(page)  OVER (PARTITION BY user_id ORDER BY step
                               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_page
FROM session_events;
```

## Common Mistakes
- Forgetting the explicit frame on LAST_VALUE -> returns current row only.
- Confusing FIRST_VALUE with MIN — FIRST_VALUE respects ORDER BY; MIN just gives the smallest value.

## AI Use Cases
- Session entry/exit analysis.
- First-touch vs last-touch attribution in marketing.
- Sequence start/end detection for ML.
