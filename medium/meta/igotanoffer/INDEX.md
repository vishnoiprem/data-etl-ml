# Meta DE Coding — iGotAnOffer 10-Approach Solutions

All unique coding + SQL questions from the iGotAnOffer Meta DE article, each solved 10 distinct ways.

---

## Files

| File | Problems covered | Count |
|------|------------------|-------|
| `coding-1-12.md` | Friends count, ffill None, mismatched words, char count, char frequency, IP validate, monotonic, sym-diff words, neighbors, nth-key, flatten dict, friends-per-person | 12 |
| `coding-13-24.md` | Infinite loop, recursive parser, spell-checker, second-highest salary, avg price, max books within budget, sequels, most-freq review, location dedup review, largest odd, max consecutive workshops, smallest from digits | 12 |
| `sql-25-38.md` | Top colleges, avg friend requests, books/renewals, 4-table sales summary, top customers 2019, avg by membership × season, % top-5 revenue, multi-day customers, % promo sales, product family %, % unsold, apples/oranges diff, most-common name | 14 |

**Total: 38 problems × 10 approaches = 380 solutions.**

---

## Approach taxonomy — the 10 patterns used

Each problem is solved using a mix of these primitives:

1. **Built-in / idiomatic** — `Counter`, `defaultdict`, `set` ops, `str.count`, `pandas`, `numpy`
2. **Manual dict / loop** — the obvious `for ... get(..., 0)` style
3. **Recursive** — function calls itself with a smaller subproblem
4. **Generator / iterator** — `yield from`, `itertools.chain`, `itertools.count`
5. **Reduce / fold** — `functools.reduce` over a sequence
6. **CTE / subquery / window** — SQL: `WITH`, `ROW_NUMBER`, `DENSE_RANK`, `LAG/LEAD`, `FILTER`
7. **GROUP BY + HAVING** — SQL: standard aggregate with filters
8. **CASE / FILTER** — SQL: conditional aggregation on a single pass
9. **Regex / parser** — `re.findall`, `re.fullmatch`, `re.finditer`
10. **Library swap** — `pandas`, `numpy`, `heapq`, `sorted`, `bisect`, `statistics`

---

## Cheat-sheet — best approach per problem

### Coding

| # | Problem | Best approach |
|---|---------|---------------|
| 1 | Friends count | `Counter(chain.from_iterable(pairs))` |
| 2 | ffill None | `itertools.accumulate(a, lambda acc, x: x if x is not None else acc)` |
| 3 | Mismatched words | `set(s1.split()) ^ set(s2.split())` |
| 4 | Char count | `str.count(c)` |
| 5 | Char freq format | `Counter(s)` (Python 3.7+ preserves insertion order) |
| 6 | IP validation | `ipaddress.IPv4Address` (production), manual split+range (interview) |
| 7 | Monotonic | Single-pass `inc`/`dec` flag |
| 8 | Sym-diff words | Set XOR |
| 9 | Neighbors count | `Counter(chain.from_iterable(graph))` |
| 10 | nth-highest key | Sort once with tie-breaker `(value desc, key asc)` |
| 11 | Flatten dict | Recursive generator |
| 12 | Friends per person | `Counter` |
| 13 | Infinite loop | `while True:` |
| 14 | Recursive parser | Generator recursion with backtracking |
| 15 | Spell-checker | Set lookup; Trie for huge dictionaries |
| 16 | 2nd-highest salary | SQL: `DENSE_RANK() = 2` |
| 17 | Avg price | `sum / len` |
| 18 | Max books in budget | Sort + greedy |
| 19 | Sequels | First-word-in-set check |
| 20 | Most-freq review | `Counter(chain.from_iterable(books.values()))` |
| 21 | Most-freq dedup | `Counter(chain.from_iterable(set(rs) for rs in ...))` |
| 22 | Largest odd | Sort odds/evens separately, place largest odd last |
| 23 | Max consecutive workshops | Sort + adjacent sum |
| 24 | Smallest from digits | Count zeros, place smallest non-zero first |

### SQL

| # | Problem | Best approach |
|---|---------|---------------|
| 25 | Top 10 entities | CTE + `ROW_NUMBER` |
| 26 | Avg friend requests | CTE + AVG over per-user counts |
| 27 | Books condition/renewals | Single pass with `FILTER` |
| 28 | 4-table summary | JOIN + GROUP BY |
| 29 | Top customers 2019 | CTE + `DENSE_RANK` |
| 30 | Avg by membership × season | `FILTER` with two averages |
| 31 | % top-5 revenue | CTE with `DENSE_RANK` |
| 32 | Multi-day customers | CTE for bounds + HAVING |
| 33 | % promo sales | `FILTER` on first/last dates |
| 34 | product_family % | JOIN + `FILTER` |
| 35 | % unsold | LEFT JOIN + `FILTER` on NULL |
| 36 | Apples/oranges diff | `FILTER` |
| 37 | Most common name | `MODE() WITHIN GROUP` (PG) |
| 38 | Most common name | Same |

---

## Rehearsal protocol (matches the study plan)

1. **Read the problem** + clarify input/output shape.
2. **Pick 3 of the 10 approaches** that you'd actually write in an interview (built-in, manual, recursive or SQL).
3. **Time yourself** — 5 min max for the chosen approach.
4. **Say "I'd index X" out loud** — interview trade-off bonus.

This bundle gives you ten angles per problem so you can pick the one that fits the prompt best, instead of always reaching for the same primitive.
