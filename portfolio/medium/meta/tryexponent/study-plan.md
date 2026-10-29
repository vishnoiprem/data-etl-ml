# Meta DE Interview — 4-Week Study Plan

Based on the Exponent guide. Structure: Mon–Fri, ~2 hr/day weekdays, longer blocks on weekends.

---

## Week 1: Foundations + SQL Drill Rhythm

**Goal:** Build fluency with the SQL half of the technical screen at pace.

| Day | Focus | Tasks |
|-----|-------|-------|
| Mon | Joins + GROUP BY | Refresh INNER/LEFT/RIGHT/SELF joins; solve 5 group-by exercises |
| Tue | CTEs + Subqueries | Rewrite 5 nested subqueries as CTEs; practice readability |
| Wed | Window functions | LAG, LEAD, RANK, DENSE_RANK, ROW_NUMBER, NTILE; 6 problems |
| Thu | Aggregations + CASE | Conditional aggregation, pivot-style queries; 5 problems |
| Fri | **Mock SQL screen** | 5 questions, 25 min timer; review misses |
| Sat | Review week + weak topics | Re-solve every missed question |
| Sun | Light review | Re-read schema patterns + sample questions |

## Week 2: Python Drill Rhythm + SQL Refinement

**Goal:** Match the screen tempo on Python without losing SQL sharpness.

| Day | Focus | Tasks |
|-----|-------|-------|
| Mon | Strings + lists | 6 string/list manipulation problems |
| Tue | Dicts + hash tables | 6 dict-based problems (group-by, count, second-highest) |
| Wed | File I/O + exceptions | 4 file-processing problems with try/except |
| Thu | Sorting + custom keys | 5 problems with `sorted(..., key=...)` |
| Fri | **Mock Python screen** | 5 questions, 25 min timer; review misses |
| Sat | **Mixed mock** | 5 SQL + 5 Python, back-to-back, 50 min total |
| Sun | Rest / light review | Skim error log |

## Week 3: Product Sense + Data Modeling

**Goal:** Own the product→model→SQL→Python flow used in every onsite round.

| Day | Focus | Tasks |
|-----|-------|-------|
| Mon | Ride-sharing (Uber) | Schema design + 1 SQL metric + 1 streaming Python |
| Tue | Ecommerce | Schema design + funnel SQL + inventory Python |
| Wed | Reddit-style notifications | Schema design + delivery-rate SQL + windowing Python |
| Thu | Movie ticketing | Schema design + per-show SQL + reservation Python |
| Fri | Instagram metric drop | Root-cause framework + supporting schema + diagnostic SQL |
| Sat | **Mock round (full hour)** | One product case → model → SQL → Python, timed |
| Sun | Review + trade-offs | Partitioning, indexing, bucketing deep-dive |

## Week 4: Behavioral + Full-Loop Mocks

**Goal:** Solidify ownership stories and run end-to-end mock loops.

| Day | Focus | Tasks |
|-----|-------|-------|
| Mon | Story prep | Write 5 ownership stories, each ≤5 min (Situation→Action→Measurable Result) |
| Tue | Story polish | Cut filler; tighten to 3-4 min each; rehearse aloud |
| Wed | Friction + learning stories | Disagreement story + new-tool-learning story (STAR format) |
| Thu | **Behavioral mock** | 30 min, 4-5 questions, time-boxed |
| Fri | **Full onsite mock** | 4 rounds × 1 hr (one back-to-back), then debrief |
| Sat | Weak spots | Re-attack every missed topic from the loop |
| Sun | Rest + final review | Re-read guide, re-read your own notes |

---

## Daily Templates

### SQL Practice (25 min, 5 questions)
1. Read question aloud, restate, list assumptions.
2. Write query.
3. Self-check: does it return the right grain? Edge cases (NULL, empty)?
4. Discuss index/filter order if table were 100× larger.

### Python Practice (25 min, 5 questions)
1. Restate prompt; list function signature + return type.
2. Write clean code (prefer readability over cleverness).
3. Run mental test cases; consider empty input, single element, duplicates.

### Mock Round (60 min)
| Block | Time | Activity |
|-------|------|----------|
| Product sense | 10 min | Clarify product, define metrics, list user/business questions |
| Data modeling | 15 min | Sketch tables, define PKs/FKs, discuss partition/index strategy |
| SQL | 15 min | Write 1-2 queries tied to the case |
| Python | 15 min | Write 1-2 functions (often streaming/pipeline) |
| Trade-offs | 5 min | Discuss scale, costs, edge cases out loud |

### Behavioral Story (3-5 min)
- **S**ituation (≤30 sec) — context, stakes
- **T**ask / Problem (≤30 sec) — your specific responsibility
- **A**ction (≤2 min) — what **you** did (use "I", not "we")
- **R**esult (≤30 sec) — measurable impact + what you'd change

---

## Pre-Interview Day Checklist

- [ ] Language preference confirmed with recruiter
- [ ] CoderPad familiar (or local equivalent practiced)
- [ ] Two strong technical stories (one personal, one work)
- [ ] Five ownership stories (each ≤5 min)
- [ ] Partitioning trade-offs rehearsed (round-robin vs hash vs bucket by ts)
- [ ] Window functions mental sheet (LAG, LEAD, RANK, NTILE)
- [ ] Streaming Python rehearsed (tumbling vs sliding, late events)
- [ ] Schedule/lunch/team time confirmed with recruiter
