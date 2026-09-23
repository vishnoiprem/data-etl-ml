# Meta Data Engineer (2025) — Interview Prep

10 solutions + a strategy guide distilled from a real Blind interview
experience post (e4, Seattle, TC ~$236K). The questions aren't hard —
**the clock is the enemy**. Most candidates fail because they don't
write fast enough, not because they don't know the answer.

---

## 1. The big picture

| Round | Format | Time | What they test |
|---|---|---|---|
| Screening | 3 SQL + 3 Python | ~45 min each? | Can you write correct code under pressure on a small schema |
| Onsite SQL | Schema given, code doesn't run | ~45 min | Business-style analytics; CTEs encouraged |
| Onsite Python | Similar to screening | ~45 min | "Business question > algorithm" framing |
| Data Modeling | Whiteboard | ~45 min | Facts/dimensions, grain, SCD, bridge tables |
| Product Sense | Open-ended | ~45 min | Metrics, dashboards, line vs bar |
| Ownership (behavioral) | Conversational | ~45 min | 5 signals, ~1-2 questions each |

---

## 2. SQL — the clauses you MUST have at your fingertips

From the post:
> "group by, sum(case), having, cte, where condition, left join, full outer
> join, coalesce, limit, lag"

Build muscle memory. The onsite question *won't* run — they judge
correctness from reading. That changes your style:
- Use CTEs liberally. Each CTE is a labeled thought: `with active_customers as ...`
- Indent consistently. They skim for the `from` and the `where`.
- Round percentages explicitly: `round(100.0 * sum(case when ...) / count(*), 2)`
- Comment the metric definition above the SQL block.

The 10 problems here cover:

| # | File | Skill |
|---|---|---|
| 1 | `1_authors_with_5_books.sql` | GROUP BY + HAVING + JOIN |
| 2 | `2_same_day_sale_percentage.sql` | SUM(CASE WHEN ...) + percentage |
| 3 | `3_customers_3plus_books_first_last_day.sql` | MIN/MAX dates + HAVING + EXCEPT pattern |
| 4 | `4_top5_invitee_payment.sql` | Self-join via invitations + AVG + ORDER BY |
| 5 | `5_authors_website_and_no_sale.sql` | Multi-aggregate + UNION ALL of percentages |
| 6 | `6_total_sales_by_payment_type.sql` | GROUP BY + COUNT(DISTINCT) + ORDER BY |
| 7 | `7_sum_orders_unique_customers.sql` | SUM + COUNT(DISTINCT) + CTE |
| 8 | `8_first_last_buy_window_lag.sql` | Window LAG + CTE — onsite level |
| 9 | `9_running_total_sales_cte.sql` | Window SUM OVER + CTE — onsite level |
| 10 | `10_rfm_segmentation.sql` | Multiple CTEs + NTILE — onsite level |

Files 8-10 are the "show off your SQL fluency" tier — write them with
CTEs even though a one-liner works.

---

## 3. Python — the toolkit

From the post:
> "dict, list, tuple, sort, for loops, set, queue structure, swapping
> key value of dict"

You do NOT need: heapq (usually), bisect, regex (rare), recursion (avoid).
You DO need: comfortable iteration, dict counting, sorting with key=,
set ops, deque for queues, building dicts from tuples.

The 10 problems here cover:

| # | File | Toolkit it stresses |
|---|---|---|
| 1 | `1_average_book_price.py` | sum/len, edge cases (empty) |
| 2 | `2_most_common_comment.py` | dict counting, set for dedup-per-location |
| 3 | `3_max_books_within_budget.py` | greedy + sort |
| 4 | `4_max_concurrent_meeting_attendees.py` | sweep line (meeting rooms II) |
| 5 | `5_consecutive_years_workshops.py` | sort + sliding window on year gaps |
| 6 | `6_smallest_from_odd_digits.py` | string sort or counter, edge cases |
| 7 | `7_most_mentioned_word.py` | nested dict, swapping key/value |
| 8 | `8_search_unsorted_list.py` | linear scan + talk track about hash table |
| 9 | `9_largest_number_from_digits.py` | comparator sort / functools.cmp_to_key |
| 10 | `10_max_overlapping_meetings.py` | meetings at the same instant (variant) |

---

## 4. The "Data Engineer" mindset (vs Software Engineer)

The post says:
> "Focus answering business question than algorithms."

Translation: the interviewer doesn't want a clever solution, they want
a **clear** solution tied to a business metric. Compare:

```python
# BAD: clever
heap = []; heapq.heappush(heap, ...)

# GOOD: clear, narrates the business
# We want to know: at the moment with the most meetings open,
# how many people were in those meetings combined?
events = []  # (time, delta_attendees)
for m in meetings:
    events.append((m.start, m.people))
    events.append((m.end, -m.people))
events.sort()
running = 0; best = 0
for t, d in events:
    running += d
    best = max(best, running)
```

The second one reads like a story. That's what gets you hired.

---

## 5. How to talk in the interview

### SQL pattern (say this out loud)

1. "Let me identify the **grain** of the answer first. The output is
   one row per `<X>`, so I'll group by `<X>`."
2. "I need to JOIN `<dim>` to `<fact>` on `<fk>`."
3. "The filter is `<condition>` — I'll put it in WHERE (pre-aggregation)
   or HAVING (post-aggregation) depending on whether it references an
   aggregate."
4. "For the percentage: numerator = `<count of matches>`, denominator =
   `<count of total>`. I'll guard against divide-by-zero with
   `nullif(denom, 0)`."

### Python pattern (say this out loud)

1. "Brute force: `<O(n²)>` scan. For the size we're talking about that's
   fine, but we can do `<O(n)>` with a `<dict>`."
2. "I'll use a dict keyed by `<X>` counting `<Y>`. Loop once to populate,
   then loop once more to find the max."
3. "Edge cases: empty input, single element, ties."

---

## 6. The clock — the real enemy

From the post:
> "The questions aren't difficult but you're fighting against the clock.
> Getting hint is not a bad thing, using them well is a sign of learning
> ability."

Translation:

- **Don't gold-plate.** First correct solution wins.
- **Use templates.** The 80% SQL answer is `SELECT col, agg(col) FROM t
  JOIN ... ON ... WHERE ... GROUP BY ... HAVING ... ORDER BY ... LIMIT`.
- **Take hints.** When the interviewer nudges, say "Got it — I should
  think about it as `<their hint>`. Let me refactor." That signals
  coachability, which Meta scores on.
- **Practice on StrataScratch**, not LeetCode. The post explicitly
  calls this out.

---

## 7. Data Modeling — quick references

The post calls out:
- **Fact grain**: one row per `<event>` (transaction, click, ride, etc.)
- **Fact types**: transactional, periodic snapshot, accumulating snapshot
- **Dimension types**: type 1 (overwrite), type 2 (history), type 3
  (previous), SCD
- **Bridge tables**: for many-to-many (e.g., customer ↔ product)
- **Role-playing dimensions**: same dim, multiple foreign keys
  (e.g., order_date_key and ship_date_key both → dim_date)

When asked to design, ALWAYS:
1. State the grain of the FACT first ("one row per ...").
2. List dimensions you need.
3. Identify PKs and FKs.
4. Note cardinality (1:1, 1:M, M:M).
5. Discuss one tradeoff (SCD2 vs SCD1, snowflake vs star, etc.).

The example in the post: ride-sharing (Uber/Lyft) is great practice —
`fact_ride`, `dim_rider`, `dim_driver`, `dim_city`, `dim_time`,
`dim_payment`, `bridge_promo_code`.

---

## 8. Product Sense — the cheat sheet

From the post:
> "Know big tech companies and their products: google, amazon, spotify,
> uber, dropbox, facebook, instagram, netflix, snapchat"
> "Think about key metrics these companies care about. Be able to give
> the numerator and denominator and explain your reasoning for the metrics.
> Give about 4-6 metrics, interview will ask follow up if a metric they're
> looking for is missing."

For each product, memorize:
- **Activation metric** (new user does the key action)
- **Engagement metric** (DAU/MAU, sessions/user/week)
- **Retention metric** (D7/D30 retention, churn)
- **Monetization metric** (ARPU, ARPPU, conversion rate)
- **Quality metric** (rating, NPS, completion rate)

Example for Spotify:
- Activation: completed first playlist / followed first artist (num =
  users who followed an artist within 7 days of signup; denom = new
  signups)
- Engagement: weekly listening hours per active user
- Retention: % of users active in week N who return in week N+1

---

## 9. Ownership — the 5 signals (Meta-specific)

The post says: "5 signals they're looking, expect one to two question for
each."

Meta's 5 ownership principles are:
1. **Bias for Action** — moved fast when others waited
2. **Boldness** — took a risk that paid off
3. **Focus** — said no to good ideas to ship the great one
4. **Impact** — measurable business outcome, not just output
5. **Role model** — taught others, raised the bar

For each, prepare **2 stories** (so you have a backup):
- Situation (1 sentence)
- Task (1 sentence)
- Action (3-5 sentences — the meat)
- Result (1-2 sentences with **a number**)
- Reflection (1 sentence — what you'd do differently)

Quantify everything. "Improved performance by 40%" beats "made it faster".

---

## 10. Final tactics from the post

- **Practice speaking out loud.** Your interviewer can't read your mind.
- **Mock interviews are gold.** interviewing.io or pramp.
- **The interviewers are nice.** Don't panic — they're not trying to
  trick you.
- **"Getting a hint is a sign of learning ability."** Use hints.
- **Don't be afraid to give more than one fact table.** Data modeling
  rewards breadth of thinking.

---

## 11. How to use this folder

1. Open a file. Read the **problem** and **expected output**.
2. Set a 12-minute timer. Write the solution from scratch.
3. Run the doctest: `python3 -m doctest file.py`
4. If you got it in time, redo it 24 hours later.
5. When you can solve any of these in <8 minutes cold, you're ready.

The clock is the boss.
