# Meta (Facebook) — DataLemur Question Bank

SQL and Python coding questions from [DataLemur's Meta question list](https://datalemur.com/questions), filtered by Meta.

Each file uses a **3-format template**:

1. **Simple way to think** — plain-English mental model
2. **Interview write-up** — what you'd actually say/write in the round
3. **Best optimized solution** — production-grade version + "Why it's optimal"

---

## How to use this guide

These DataLemur problems are the **easier end** of the Meta DE interview — they show up on phone screens and as warm-up questions on the on-site. Pair with the harder PracHub batch (`../prachub/`) for full coverage.

| Folder | Count | Difficulty range | Best round |
|---|---|---|---|
| `sql/` | 6 | Easy → Hard | Phone screen SQL |
| `python/` | 3 | Easy → Medium | On-site Python round |

**Total: 9 question files.** (Skipped 🔒 premium-locked and Statistics/ML questions.)

---

## sql/ — SQL problems (6)

| # | File | Difficulty | Pattern |
|---|---|---|---|
| 1 | [page-with-no-likes.md](./sql/page-with-no-likes.md) | Easy | LEFT JOIN / NOT IN anti-join |
| 2 | [average-post-hiatus.md](./sql/average-post-hiatus.md) | Easy | LAG window function |
| 3 | [app-clickthrough-rate.md](./sql/app-clickthrough-rate.md) | Easy | Conditional aggregation |
| 4 | [active-user-retention.md](./sql/active-user-retention.md) | Hard | D7 retention — self-join on dates |
| 5 | [advertiser-status.md](./sql/advertiser-status.md) | Hard | Day-over-day classification with LAG |
| 6 | [reactivated-users.md](./sql/reactivated-users.md) | Hard | 30-day inactivity gap, gaps-and-islands |

---

## Drill plan (if pairing with PracHub)

- **Day 1 (warm-up):** `page-with-no-likes`, `average-post-hiatus`, `app-clickthrough-rate`
- **Day 2:** `active-user-retention`, `advertiser-status`, `reactivated-users` (all 3 are variations on temporal-log SQL — the hardest pattern on Meta DE phone screens)
- **Python:** Do all 3 in one sitting; they're short

---

## When you're ready for the harder stuff

Move to `../prachub/01-sql-coding/` and `../prachub/02-python-coding/` — those have 24 problems at interview difficulty (multi-join analytics, intervals, graphs, top-k) with the same 3-format template.