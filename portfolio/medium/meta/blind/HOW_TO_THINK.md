re# How to Think — the simple version

One page. For each problem: **spot the pattern → say 3 steps → write the skeleton.**
If you remember only the skeletons, you will pass the screen.

---

## The 4 questions to ask yourself (every problem)

1. **What does ONE row / ONE answer look like?** (per author? one number? a word?)
2. **What do I need to COUNT or SUM?**
3. **Is the filter BEFORE grouping (WHERE) or AFTER (HAVING)?**
4. **Edge case:** empty input? divide by zero? ties?

Say these out loud. That *is* the interview.

---

# SQL — only 5 patterns

| Pattern | When you hear… | Skeleton |
|---|---|---|
| **A. Group + filter** | "authors with at least 5…" | `GROUP BY x HAVING COUNT(*) >= 5` |
| **B. Percentage** | "what % of…" | `100.0 * SUM(CASE WHEN cond THEN 1 ELSE 0 END) / COUNT(*)` |
| **C. Count unique** | "unique customers" | `COUNT(DISTINCT customer_id)` |
| **D. Keep empty groups** | "for EACH payment type / author" (even with 0) | `LEFT JOIN` + `COALESCE(x, 0)` |
| **E. Window** | "running total", "previous", "first/last", "rank" | `SUM(x) OVER (ORDER BY d)`, `LAG(d) OVER (PARTITION BY c ORDER BY d)` |

### Problem by problem

| # | Question | Pattern | Think |
|---|---|---|---|
| 1 | Authors with ≥ 5 books | A | join books→authors, group by author, `HAVING COUNT(*) >= 5` |
| 2 | % sales on signup day | B | join tx→customers, case `purchase_date = registered_on` |
| 3 | 3+ books on first AND last day | A + CTE | CTE1: first/last date per customer. CTE2: books per customer per day. Keep where day=first has ≥3 AND day=last has ≥3 AND `COUNT(DISTINCT purchase_date) > 1` (rows are books, not visits) |
| 4 | Top 5 inviters by invitees' avg payment | join + A | invitations → invitee's transactions, `GROUP BY inviter`, `AVG(amount)`, `ORDER BY … DESC LIMIT 5` |
| 5 | Total authors, % `.com`, % no sale | B + D | CTE: one row per author with flags (`LIKE '%.com%'`, sale count via LEFT JOIN). Then one SELECT of `COUNT(*)` and two percentages |
| 6 | Sales + unique customers by payment type | C + D | `LEFT JOIN` payment_types→tx, `COALESCE(SUM(amount),0)`, `COUNT(DISTINCT customer_id)` |
| 7 | Total orders + unique customers | C | `SELECT COUNT(*), COUNT(DISTINCT customer_id) FROM transactions` |
| 8 | Days first→last purchase | E (or MIN/MAX) | per customer `MIN(date)`, `MAX(date)`, subtract, `HAVING COUNT(*) >= 2` |
| 9 | Running total by day | E | CTE: daily sum. Then `SUM(daily) OVER (ORDER BY date)` |
| 10 | RFM segments | E (NTILE) | CTE1: recency/frequency/monetary per customer. CTE2: `NTILE(4) OVER (ORDER BY …)` each. Final: `CASE` to label |

### The SQL template (write this first, fill in blanks)

```sql
WITH base AS (            -- 1. get the rows you need (joins + WHERE)
    SELECT ...
    FROM fact f
    JOIN dim d ON d.id = f.dim_id
    WHERE ...
)
SELECT key,               -- 2. the grain of the answer
       COUNT(*), SUM(...) -- 3. the metric
FROM base
GROUP BY key
HAVING ...                -- 4. filter on aggregates
ORDER BY ... DESC
LIMIT ...;
```

---

# Python — only 4 patterns

| Pattern | When you hear… | Skeleton |
|---|---|---|
| **A. Count with dict** | "most common", "most mentioned" | `counts[x] = counts.get(x, 0) + 1` then `max(counts, key=counts.get)` |
| **B. Sort then walk** | "max within budget", "smallest/largest number" | `sorted(...)` then one loop |
| **C. Sweep line** | "meetings at the same time" | events `(start,+1)`, `(end,-1)`, sort, running sum, track max |
| **D. Simple scan** | "average", "search" | one `for` loop / `sum()/len()` |

### Problem by problem

| # | Question | Pattern | Think in 3 steps |
|---|---|---|---|
| 1 | Average price | D | empty? → 0. else `sum/len` |
| 2 | Most common comment (dedup per location) | A | for each location use `set(loc)` → count → max |
| 3 | Max books within budget | B | sort cheap→expensive, buy until money runs out |
| 4 | Max people in meetings at once | C | `(start,+people)`, `(end,-people)`, sort, running max |
| 5 | Max classes in consecutive years | B | sort by year; if `year == prev+1` add to run, else restart run; track max |
| 6 | Smallest number from odd digits | B | keep odd digits of `str(n)`, sort ascending, join; none → 0 |
| 7 | Most mentioned word in dict of lists | A | loop every list, count words, return `(word, count)` |
| 8 | Search unsorted list | D | loop with `enumerate`, return index, else -1 |
| 9 | Largest number from digits | B | sort digits descending, join |
| 10 | Max meetings overlapping | C | same as #4 but `+1 / -1` |

### The 4 skeletons to memorize

```python
# A. Count with dict
counts = {}
for x in items:
    counts[x] = counts.get(x, 0) + 1
best = max(counts, key=counts.get) if counts else ''

# B. Sort then walk (greedy)
total = 0; n = 0
for p in sorted(prices):
    if total + p > budget: break
    total += p; n += 1

# C. Sweep line (meetings)
events = []
for s, e in meetings:
    events.append((s, +1))
    events.append((e, -1))
events.sort()                 # (10,-1) sorts before (10,+1) → end before start ✔
running = best = 0
for _, d in events:
    running += d
    best = max(best, running)

# D. Consecutive run
best = run = 0; prev = None
for year, n in sorted(workshops):
    run = run + n if prev is not None and year == prev + 1 else n
    best = max(best, run); prev = year
```

---

## In the room — the 30-second script

1. **Repeat the question** in one sentence.
2. **Say the pattern:** "This is a count-with-dict problem" / "This is GROUP BY + HAVING."
3. **Say the edge case:** "If the list is empty I return 0."
4. **Write the skeleton**, then fill in the details.
5. **Walk through one example by hand.**

Don't try to be clever. Clear code that answers the business question is what gets you through.

---

## Drill plan

- Day 1–2: write the 4 Python and 5 SQL skeletons from memory until each takes under 1 minute.
- Day 3–5: do all 20 problems with a **8-minute timer**, without looking.
- Day 6+: redo only the ones you missed. Then StrataScratch "Meta" tag.
