# LeetCode Problems for Google Data Engineer (Non-SQL / Coding Round)

> **Calibration first — read this.** Google's DE coding round is **easy-to-medium**, data-flavored, and focused on arrays, strings, dictionaries (hashmaps), and sets. Multiple data engineers who've interviewed advise: do **not** grind trees, linked lists, graphs, or LeetCode "Hard" problems unless you have specific signal the team uses them. Google's coding rounds pull from public LeetCode problems — there's no secret bank — so pattern recognition + clear communication is the edge.
>
> The Hard problems Google asks (Max Path Sum, Min Window, etc.) come from **software engineer** reports, not data engineer reports. For your "Code Comprehension & Programming" round, prioritize Tiers 1–2 below.

---

## TIER 1 — CORE WARM-UPS (do ALL of these first; they map directly to DE work)
Arrays, strings, dictionaries, sets, counting. This is the heart of a DE coding round.

| # | Problem | LC # | Difficulty | Pattern / Why it matters for DE |
|---|---------|------|-----------|--------------------------------|
| 1 | Two Sum | 1 | Easy | Hashmap lookup — the foundational DE pattern |
| 2 | Valid Anagram | 242 | Easy | Frequency counting with dict/Counter |
| 3 | Contains Duplicate | 217 | Easy | Set membership — dedup logic |
| 4 | Valid Palindrome | 125 | Easy | String cleaning + two pointers |
| 5 | Roman to Integer | 13 | Easy | Dict-based mapping/parsing |
| 6 | First Unique Character in a String | 387 | Easy | Frequency dict, order preservation |
| 7 | Majority Element | 169 | Easy | Counting / Boyer-Moore |
| 8 | Intersection of Two Arrays | 349 | Easy | Set operations (mirrors JOIN logic) |
| 9 | Intersection of Two Arrays II | 350 | Easy | Counter intersection (handles duplicates) |
| 10 | Single Number | 136 | Easy | Set/XOR — finding the odd one out |
| 11 | Best Time to Buy and Sell Stock | 121 | Easy | One-pass running min/max |
| 12 | Move Zeroes | 283 | Easy | In-place array mutation, two pointers |
| 13 | Fizz Buzz | 412 | Easy | Classic opener — flow control |
| 14 | Plus One | 66 | Easy | Array digit manipulation, carry logic |
| 15 | Merge Sorted Array | 88 | Easy | Two-pointer merge (core of merge-sort/joins) |
| 16 | Missing Number | 268 | Easy | Math/set — gap detection |
| 17 | Word Pattern | 290 | Easy | Bijective dict mapping |
| 18 | Group Anagrams | 49 | Medium | Dict-of-lists bucketing — grouping/aggregation |
| 19 | Top K Frequent Elements | 347 | Medium | Counter + heap — top-N, very DE-relevant |

---

## TIER 2 — MEDIUM STAPLES (do these next; high-frequency Google mediums that fit DE)
Sliding window, two pointers, prefix sums, intervals, hashmap patterns.

| # | Problem | LC # | Difficulty | Pattern / Why it matters for DE |
|---|---------|------|-----------|--------------------------------|
| 20 | Longest Substring Without Repeating Characters | 3 | Medium | Sliding window — sessionization analogue |
| 21 | Product of Array Except Self | 238 | Medium | Prefix/suffix products — no-division trick |
| 22 | Subarray Sum Equals K | 560 | Medium | Prefix sum + hashmap — running totals |
| 23 | Merge Intervals | 56 | Medium | Interval merging — time-window logic |
| 24 | Insert Interval | 57 | Medium | Interval manipulation |
| 25 | Group Anagrams | 49 | Medium | (also Tier 1) grouping by key |
| 26 | Top K Frequent Words | 692 | Medium | Counter + heap with tie-break sorting |
| 27 | Kth Largest Element in an Array | 215 | Medium | Quickselect / heap — "n-th value" DE question |
| 28 | Sort Colors | 75 | Medium | Dutch-flag partition, in-place |
| 29 | Find All Anagrams in a String | 438 | Medium | Fixed sliding window + counter |
| 30 | Longest Consecutive Sequence | 128 | Medium | Set-based O(n) — streak detection |
| 31 | Encode and Decode Strings | 271 | Medium | Serialization — directly relevant to DE I/O |
| 32 | Decode String | 394 | Medium | Stack parsing (reported in Google DE guide) |
| 33 | Daily Temperatures | 739 | Medium | Monotonic stack |
| 34 | Task Scheduler | 621 | Medium | Greedy + counting (scheduling/throughput) |
| 35 | 3Sum | 15 | Medium | Sorting + two pointers |
| 36 | Set Matrix Zeroes | 73 | Medium | In-place matrix mutation |
| 37 | Spiral Matrix | 54 | Medium | Matrix traversal / boundary control |

---

## TIER 3 — DATA-WRANGLING / FILE-STYLE (the most "DE-real" problems)
These mirror actual pipeline work — parsing, flattening, aggregating. Practice these especially for "Code Comprehension."

| # | Task | Source | Why it matters |
|---|------|--------|---------------|
| 38 | Parse a CSV/flat file and return top-N by a column | DE-reported (Google) | Real ingestion + top-N |
| 39 | Flatten a nested JSON / dictionary to dot-notation keys | Common DE | Schema flattening |
| 40 | Flatten a nested list of arbitrary depth | Common DE | Recursion / stack |
| 41 | Forward-fill: replace None with previous non-null value | Google-reported | Data cleaning (handles leading None, empty, None input) |
| 42 | Count friends per person from a list of pairs → dict | Google-reported | Adjacency counting with dict |
| 43 | Print key of nth-highest value in a dict (tie-break by key sort) | Google-reported | Dict sorting + edge cases |
| 44 | Uncommon words between two sentences | Google-reported | Counter across two inputs |
| 45 | Letter / word frequency count | Common DE | Counter aggregation |
| 46 | Group a list of dicts by a key and aggregate (mini-GROUP BY) | Common DE | Replicates SQL aggregation in Python |
| 47 | Sum values in a range A..B (clarify: ints? list? repeated queries?) | Google-reported | Tests whether you CLARIFY before coding |
| 48 | Two sorted lists → merge / dedup preserving order | Common DE | Merge logic |
| 49 | Validate & convert timestamps between formats; compute deltas | Common DE | Time handling |
| 50 | Process a file too big for memory (generators/chunking) | Google-reported (discussion) | Streaming, memory awareness |

> Tier 3 has no LeetCode numbers because they're DE-flavored variants — but solving Tiers 1–2 gives you every technique you need for them. Implement each from scratch in a plain editor.

---

## TIER 4 — STRETCH ONLY (skip unless you have time / specific signal)
These appear in Google **SWE** reports, not DE reports. The IGotAnOffer DE guide explicitly pulled these from software-engineer reports. Do a couple only after Tiers 1–3 are solid.

| # | Problem | LC # | Difficulty |
|---|---------|------|-----------|
| 51 | Binary Tree Maximum Path Sum | 124 | Hard |
| 52 | Minimum Window Substring | 76 | Hard |
| 53 | Number of Submatrices That Sum to Target | 1074 | Hard |
| 54 | Snapshot Array | 1146 | Medium-Hard |
| 55 | Climbing Stairs (DP intro) | 70 | Easy (but DP) |
| 56 | Course Schedule (topological sort) | 207 | Medium (graph) |
| 57 | Number of Islands (BFS/DFS) | 200 | Medium (graph) |

---

## RECOMMENDED STUDY ORDER (for ~1 week)
1. **Days 1–2:** Tier 1 (all 19). Goal: solve ~75% of Easy within an hour → then you're ready for Medium.
2. **Days 3–4:** Tier 2 mediums (focus on sliding window, prefix sum, intervals, top-K).
3. **Days 5–6:** Tier 3 — implement each data-wrangling task in a plain Google Doc (no autocomplete), since that mirrors the real environment.
4. **Day 7:** Re-attempt anything you failed; do 1–2 Tier 4 only if confident.

## HOW TO PRACTICE FOR "CODE COMPREHENSION" SPECIFICALLY
For each problem above, also do the reverse: take a working solution, and practice (a) explaining it line-by-line aloud, (b) predicting its output on a tricky input, (c) spotting a deliberately introduced bug. That's exactly what the comprehension portion tests.

## TOOLS
- LeetCode: filter by "Google" tag (top 50 most recent) + Easy/Medium, topics Array/String/Hash Table.
- NeetCode 150 — free, grouped by pattern; do the Arrays & Hashing, Two Pointers, Sliding Window, Stack, and Intervals sections (skip Graphs/Advanced Trees/DP-heavy).
- Practice in a plain text editor or Google Doc — no syntax highlighting, can't run code — to match Google's phone-screen setup.
