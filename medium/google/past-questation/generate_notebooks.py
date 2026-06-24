"""Script to generate 5 Jupyter notebooks for Google Data Engineer interview prep."""
import json, os

def nb(cells):
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.9.0"}
        },
        "cells": cells
    }

def md(src):
    return {"cell_type": "markdown", "id": os.urandom(4).hex(), "metadata": {}, "source": src}

def code(src, outputs=None):
    return {
        "cell_type": "code", "id": os.urandom(4).hex(),
        "execution_count": None, "metadata": {},
        "outputs": outputs or [],
        "source": src
    }

# ─────────────────────────────────────────────────────────────────
# NOTEBOOK 1  (com1.pdf – Page 1, Q1–Q411)
# ─────────────────────────────────────────────────────────────────
nb1_cells = [
md("""# 🟢 Google Data Engineer – Page 1 (Q1-Q411)
**Source:** Google Coding Questions – DataInterview.com (Page 1)

Questions covered:
| # | Title | Category | Difficulty |
|---|-------|----------|-----------|
| Q41 | User Reaction Rate | SQL | MEDIUM |
| Q55 | CTR by Website Type | SQL | HARD |
| Q65 | Insert Interval | Python | MEDIUM |
| Q80 | Sliding Window Maximum | Python | HARD |
| Q96 | Counts of Email Labels | SQL | MEDIUM |
| Q127 | Best Actors per Genre | SQL | HARD |
| Q150 | House Robber | Python | MEDIUM |
"""),

# ─────────────── Q41: User Reaction Rate ───────────────
md("""---
## Q41 · User Reaction Rate (Database – MEDIUM)

### Problem
Given a table of user reactions (likes, dislikes, comments) on posts, compute the **reaction rate**
(total reactions / total posts viewed) grouped by user.

**Table: reactions**
| user_id | post_id | action | action_date |
|---------|---------|--------|------------|
| 1       | 101     | like   | 2023-01-01 |
| 1       | 102     | view   | 2023-01-01 |
| 2       | 101     | view   | 2023-01-02 |

> **Reaction Rate** = (likes + dislikes + comments) / total views per user

---
### 🧠 How to Remember (Step by Step)
```
1. THINK: "Rate = reactions ÷ views" → need to COUNT two things separately
2. FILTER: use CASE WHEN or WHERE to split reactions vs views
3. GROUP BY user_id
4. DIVIDE: reaction_count / view_count
5. ROUND to 2 decimal places
```
"""),
code("""import sqlite3
import pandas as pd

# Setup
conn = sqlite3.connect(":memory:")
conn.execute(\"\"\"
CREATE TABLE reactions (
    user_id INT, post_id INT, action TEXT, action_date TEXT
)
\"\"\")
conn.executemany("INSERT INTO reactions VALUES (?,?,?,?)", [
    (1, 101, 'like',    '2023-01-01'),
    (1, 101, 'view',    '2023-01-01'),
    (1, 102, 'view',    '2023-01-02'),
    (1, 103, 'comment', '2023-01-03'),
    (2, 101, 'view',    '2023-01-01'),
    (2, 102, 'like',    '2023-01-02'),
    (2, 103, 'view',    '2023-01-03'),
    (3, 101, 'view',    '2023-01-01'),
])

print("Sample data:")
print(pd.read_sql("SELECT * FROM reactions", conn))
"""),

md("""### ✅ Solution 1 – CASE WHEN in SELECT (Brute Force)
**Time:** O(n) | **Space:** O(u) where u = distinct users
"""),
code("""# Solution 1: CASE WHEN inline aggregation
sql1 = \"\"\"
SELECT
    user_id,
    ROUND(
        1.0 * SUM(CASE WHEN action IN ('like','dislike','comment') THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END), 0),
        2
    ) AS reaction_rate
FROM reactions
GROUP BY user_id
ORDER BY user_id
\"\"\"
print("Solution 1 - CASE WHEN:")
print(pd.read_sql(sql1, conn))
"""),

md("""### ✅ Solution 2 – Subquery with CTEs
**Time:** O(n) | **Space:** O(u)
"""),
code("""# Solution 2: CTE approach - cleaner separation of concerns
sql2 = \"\"\"
WITH views AS (
    SELECT user_id, COUNT(*) AS total_views
    FROM reactions WHERE action = 'view'
    GROUP BY user_id
),
reacts AS (
    SELECT user_id, COUNT(*) AS total_reactions
    FROM reactions WHERE action IN ('like','dislike','comment')
    GROUP BY user_id
)
SELECT v.user_id,
       ROUND(1.0 * COALESCE(r.total_reactions, 0) / v.total_views, 2) AS reaction_rate
FROM views v
LEFT JOIN reacts r ON v.user_id = r.user_id
ORDER BY v.user_id
\"\"\"
print("Solution 2 - CTE:")
print(pd.read_sql(sql2, conn))
"""),

md("""### ✅ Solution 3 – Window Function + Filter (Best for analytics)
**Time:** O(n log n) | **Space:** O(n)
"""),
code("""# Solution 3: Window functions - most readable for OLAP workloads
sql3 = \"\"\"
SELECT DISTINCT user_id,
    ROUND(
        1.0 * SUM(CASE WHEN action != 'view' THEN 1 ELSE 0 END) OVER (PARTITION BY user_id)
        / NULLIF(SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END) OVER (PARTITION BY user_id), 0),
        2
    ) AS reaction_rate
FROM reactions
ORDER BY user_id
\"\"\"
print("Solution 3 - Window Functions:")
print(pd.read_sql(sql3, conn))
"""),

# ─────────────── Q55: CTR by Website Type ───────────────
md("""---
## Q55 · CTR by Website Type (Database – HARD)

### Problem
Given `events` (user, event_type, website_type, ts) where event_type is 'click' or 'impression',
compute **CTR = clicks / impressions** by website_type.

**CTR (Click-Through Rate)** = total clicks / total impressions

---
### 🧠 How to Remember (Step by Step)
```
1. CTR = clicks / impressions  (memorize this formula!)
2. JOIN or CASE WHEN to separate clicks vs impressions
3. GROUP BY website_type
4. Handle division by zero with NULLIF
5. Multiply by 100 if percent needed
```
"""),
code("""conn.execute(\"\"\"
CREATE TABLE events (
    user_id INT, event_type TEXT, website_type TEXT, ts TEXT
)
\"\"\")
conn.executemany("INSERT INTO events VALUES (?,?,?,?)", [
    (1, 'impression', 'news',   '2023-01-01'),
    (1, 'click',      'news',   '2023-01-01'),
    (2, 'impression', 'news',   '2023-01-02'),
    (2, 'impression', 'sports', '2023-01-02'),
    (2, 'click',      'sports', '2023-01-02'),
    (3, 'impression', 'news',   '2023-01-03'),
    (3, 'impression', 'sports', '2023-01-03'),
    (4, 'impression', 'news',   '2023-01-03'),
    (4, 'click',      'news',   '2023-01-03'),
])
print("Events data:")
print(pd.read_sql("SELECT * FROM events", conn))
"""),
code("""# Solution 1: CASE WHEN - most common interview answer
sql_ctr1 = \"\"\"
SELECT website_type,
       COUNT(CASE WHEN event_type = 'click' THEN 1 END) AS clicks,
       COUNT(CASE WHEN event_type = 'impression' THEN 1 END) AS impressions,
       ROUND(
           100.0 * COUNT(CASE WHEN event_type = 'click' THEN 1 END)
           / NULLIF(COUNT(CASE WHEN event_type = 'impression' THEN 1 END), 0),
           2
       ) AS ctr_pct
FROM events
GROUP BY website_type
ORDER BY ctr_pct DESC
\"\"\"
print("CTR Solution 1 - CASE WHEN:")
print(pd.read_sql(sql_ctr1, conn))
"""),
code("""# Solution 2: Self-JOIN approach
sql_ctr2 = \"\"\"
WITH clicks AS (
    SELECT website_type, COUNT(*) AS click_count
    FROM events WHERE event_type = 'click'
    GROUP BY website_type
),
impressions AS (
    SELECT website_type, COUNT(*) AS imp_count
    FROM events WHERE event_type = 'impression'
    GROUP BY website_type
)
SELECT i.website_type,
       COALESCE(c.click_count, 0) AS clicks,
       i.imp_count AS impressions,
       ROUND(100.0 * COALESCE(c.click_count, 0) / i.imp_count, 2) AS ctr_pct
FROM impressions i
LEFT JOIN clicks c ON i.website_type = c.website_type
ORDER BY ctr_pct DESC
\"\"\"
print("CTR Solution 2 - CTE + LEFT JOIN:")
print(pd.read_sql(sql_ctr2, conn))
"""),
code("""# Solution 3: AVG trick - elegant one-liner
# AVG(event_type = 'click') works in MySQL; adapt for SQLite
sql_ctr3 = \"\"\"
SELECT website_type,
       SUM(CASE WHEN event_type='click' THEN 1.0 ELSE 0 END) /
       SUM(CASE WHEN event_type='impression' THEN 1.0 ELSE 0 END) AS ctr,
       COUNT(*) AS total_events
FROM events
GROUP BY website_type
\"\"\"
print("CTR Solution 3 - Ratio trick:")
print(pd.read_sql(sql_ctr3, conn))
"""),

# ─────────────── Q65: Insert Interval ───────────────
md("""---
## Q65 · Insert Interval (Data Structures – MEDIUM)

### Problem
Given a sorted list of non-overlapping intervals and a new interval, insert it and merge overlaps.

**Example:**
- intervals = [[1,3],[6,9]], newInterval = [2,5]
- Output: [[1,5],[6,9]]

---
### 🧠 How to Remember (Step by Step)
```
1. THREE CASES for each existing interval vs new interval:
   a) Existing ends BEFORE new starts → add existing (no overlap)
   b) Existing starts AFTER new ends → add new, then rest
   c) OVERLAP → merge: new = [min(starts), max(ends)]
2. Don't forget to add the merged interval at the end!
3. Key check: interval[1] < new[0]  → before
              interval[0] > new[1]  → after
              else                  → merge
```
"""),
code("""from typing import List

# Solution 1: Brute Force - add all, sort, merge
# Time: O(n log n)  Space: O(n)
def insert_interval_brute(intervals: List[List[int]], new: List[int]) -> List[List[int]]:
    \"\"\"Add new interval, sort all, then merge overlaps.\"\"\"
    all_intervals = intervals + [new]
    all_intervals.sort(key=lambda x: x[0])

    merged = [all_intervals[0]]
    for start, end in all_intervals[1:]:
        if start <= merged[-1][1]:          # overlap
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

# Test
print("Solution 1 (Brute Force):")
print(insert_interval_brute([[1,3],[6,9]], [2,5]))   # [[1,5],[6,9]]
print(insert_interval_brute([[1,2],[3,5],[6,7],[8,10],[12,16]], [4,8]))  # [[1,2],[3,10],[12,16]]
"""),
code("""# Solution 2: Linear scan - Three-case logic
# Time: O(n)  Space: O(n)
def insert_interval_linear(intervals: List[List[int]], new: List[int]) -> List[List[int]]:
    \"\"\"Single pass with 3 cases: before, overlap, after.\"\"\"
    result = []
    i = 0
    n = len(intervals)

    # Case a: intervals that end before new starts (no overlap)
    while i < n and intervals[i][1] < new[0]:
        result.append(intervals[i])
        i += 1

    # Case b: merge overlapping intervals
    while i < n and intervals[i][0] <= new[1]:
        new[0] = min(new[0], intervals[i][0])
        new[1] = max(new[1], intervals[i][1])
        i += 1
    result.append(new)

    # Case c: intervals that start after new ends
    while i < n:
        result.append(intervals[i])
        i += 1

    return result

print("Solution 2 (Linear Scan):")
print(insert_interval_linear([[1,3],[6,9]], [2,5]))
print(insert_interval_linear([[1,2],[3,5],[6,7],[8,10],[12,16]], [4,8]))
"""),
code("""# Solution 3: Pythonic one-liner with list comprehension
# Time: O(n)  Space: O(n)
def insert_interval_pythonic(intervals: List[List[int]], new: List[int]) -> List[List[int]]:
    \"\"\"Elegant Python using conditional building.\"\"\"
    s, e = new
    left  = [i for i in intervals if i[1] < s]       # completely before
    right = [i for i in intervals if i[0] > e]       # completely after
    # overlapping: merge all into one
    overlap = [i for i in intervals if i[0] <= e and i[1] >= s]
    if overlap:
        s = min(s, overlap[0][0])
        e = max(e, overlap[-1][1])
    return left + [[s, e]] + right

print("Solution 3 (Pythonic):")
print(insert_interval_pythonic([[1,3],[6,9]], [2,5]))
print(insert_interval_pythonic([[1,2],[3,5],[6,7],[8,10],[12,16]], [4,8]))

print("\\n⏱ Complexity Summary:")
print("| Solution | Time     | Space |")
print("|----------|----------|-------|")
print("| Brute    | O(n logn)| O(n)  |")
print("| Linear   | O(n)     | O(n)  |")
print("| Pythonic | O(n)     | O(n)  |")
"""),

# ─────────────── Q80: Sliding Window Maximum ───────────────
md("""---
## Q80 · Sliding Window Maximum (Algorithms – HARD)

### Problem
Given an array and window size k, return the maximum value in each sliding window.

**Example:** nums=[1,3,-1,-3,5,3,6,7], k=3 → [3,3,5,5,6,7]

---
### 🧠 How to Remember (Step by Step)
```
1. BRUTE: nested loop O(nk) - too slow
2. DEQUE trick: store INDICES (not values), keep decreasing order
   - Remove from FRONT if out of window (index <= i - k)
   - Remove from BACK while back element <= current (useless)
   - Front of deque is always the MAXIMUM
3. Key insight: deque is MONOTONICALLY DECREASING → front = max
```
"""),
code("""from collections import deque

# Solution 1: Brute Force
# Time: O(n*k)  Space: O(1)
def max_sliding_window_brute(nums: List[int], k: int) -> List[int]:
    \"\"\"Check every window of size k.\"\"\"
    if not nums or k == 0:
        return []
    return [max(nums[i:i+k]) for i in range(len(nums) - k + 1)]

nums = [1,3,-1,-3,5,3,6,7]
print("Solution 1 (Brute Force):", max_sliding_window_brute(nums, 3))
"""),
code("""# Solution 2: Max-Heap (Priority Queue)
# Time: O(n log k)  Space: O(k)
import heapq

def max_sliding_window_heap(nums: List[int], k: int) -> List[int]:
    \"\"\"Use max heap; lazily remove out-of-window elements.\"\"\"
    heap = []  # (-val, index)
    result = []

    for i, num in enumerate(nums):
        heapq.heappush(heap, (-num, i))
        # remove elements outside window
        while heap[0][1] <= i - k:
            heapq.heappop(heap)
        if i >= k - 1:
            result.append(-heap[0][0])
    return result

print("Solution 2 (Heap):", max_sliding_window_heap(nums, 3))
"""),
code("""# Solution 3: Monotonic Deque ← OPTIMAL for interviews
# Time: O(n)  Space: O(k)
def max_sliding_window_deque(nums: List[int], k: int) -> List[int]:
    \"\"\"
    Monotonic decreasing deque stores indices.
    Front = max of current window.
    \"\"\"
    dq = deque()   # stores indices, front = max
    result = []

    for i, num in enumerate(nums):
        # 1) Remove indices outside window from front
        if dq and dq[0] <= i - k:
            dq.popleft()

        # 2) Remove smaller elements from back (they're useless)
        while dq and nums[dq[-1]] <= num:
            dq.pop()

        dq.append(i)

        # 3) Window is full → record max (front of deque)
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result

print("Solution 3 (Monotonic Deque):", max_sliding_window_deque(nums, 3))
print("\\n⏱ Complexity Summary:")
print("| Solution   | Time      | Space |")
print("|------------|-----------|-------|")
print("| Brute      | O(n*k)    | O(1)  |")
print("| Heap       | O(n log k)| O(k)  |")
print("| Deque ✅   | O(n)      | O(k)  |")
"""),

# ─────────────── Q96: Counts of Email Labels ───────────────
md("""---
## Q96 · Counts of Email Labels (Database – MEDIUM)

### Problem
Given a Gmail `emails` table with columns (id, from_user, to_user, label),
count emails per label. Labels include: 'Promotions', 'Social', 'Updates', etc.

---
### 🧠 How to Remember
```
1. Simple GROUP BY + COUNT(*)
2. To show labels with 0 emails → LEFT JOIN with label list
3. For percentage → COUNT per group / total * 100
```
"""),
code("""conn.execute(\"\"\"
CREATE TABLE IF NOT EXISTS emails (
    id INT, from_user TEXT, to_user TEXT, label TEXT
)
\"\"\")
conn.executemany("INSERT INTO emails VALUES (?,?,?,?)", [
    (1, 'a@g.com', 'b@g.com', 'Promotions'),
    (2, 'c@g.com', 'b@g.com', 'Social'),
    (3, 'd@g.com', 'b@g.com', 'Promotions'),
    (4, 'e@g.com', 'b@g.com', 'Updates'),
    (5, 'f@g.com', 'b@g.com', 'Social'),
    (6, 'g@g.com', 'b@g.com', 'Promotions'),
    (7, 'h@g.com', 'b@g.com', 'Primary'),
])

# Solution 1: Simple GROUP BY COUNT
sql_email1 = \"\"\"
SELECT label, COUNT(*) AS email_count
FROM emails
GROUP BY label
ORDER BY email_count DESC
\"\"\"
print("Solution 1 - GROUP BY:")
print(pd.read_sql(sql_email1, conn))
"""),
code("""# Solution 2: WITH percentage
sql_email2 = \"\"\"
SELECT label,
       COUNT(*) AS email_count,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM emails
GROUP BY label
ORDER BY email_count DESC
\"\"\"
print("Solution 2 - With percentage (window function):")
print(pd.read_sql(sql_email2, conn))
"""),
code("""# Solution 3: Ranked labels
sql_email3 = \"\"\"
WITH counts AS (
    SELECT label, COUNT(*) AS email_count
    FROM emails
    GROUP BY label
)
SELECT label, email_count,
       RANK() OVER (ORDER BY email_count DESC) AS rank
FROM counts
\"\"\"
print("Solution 3 - Ranked by count:")
print(pd.read_sql(sql_email3, conn))
"""),

# ─────────────── Q127: Best Actors per Genre ───────────────
md("""---
## Q127 · Best Actors per Genre (Database – HARD)

### Problem
Given `movies` (id, title, genre, rating) and `actors` (movie_id, actor_name),
find the top-rated actor per genre (actor with highest avg rating in that genre).

---
### 🧠 How to Remember
```
1. JOIN movies + actors on movie_id
2. GROUP BY genre, actor_name → get avg rating per actor per genre
3. RANK() OVER (PARTITION BY genre ORDER BY avg_rating DESC)
4. Filter WHERE rank = 1
```
"""),
code("""conn.execute("CREATE TABLE IF NOT EXISTS movies (id INT, title TEXT, genre TEXT, rating REAL)")
conn.execute("CREATE TABLE IF NOT EXISTS actors (movie_id INT, actor_name TEXT)")
conn.executemany("INSERT INTO movies VALUES (?,?,?,?)", [
    (1, 'Movie A', 'Action',  8.5),
    (2, 'Movie B', 'Action',  7.0),
    (3, 'Movie C', 'Comedy',  9.0),
    (4, 'Movie D', 'Comedy',  6.5),
    (5, 'Movie E', 'Drama',   8.0),
    (6, 'Movie F', 'Drama',   9.5),
])
conn.executemany("INSERT INTO actors VALUES (?,?)", [
    (1, 'Tom H'), (2, 'Tom H'), (3, 'Amy A'),
    (4, 'Ben B'), (5, 'Tom H'), (6, 'Amy A'),
    (1, 'Amy A'),
])

# Solution 1: Subquery + GROUP BY
sql_actors1 = \"\"\"
SELECT m.genre, a.actor_name, ROUND(AVG(m.rating),2) AS avg_rating
FROM movies m
JOIN actors a ON m.id = a.movie_id
GROUP BY m.genre, a.actor_name
ORDER BY m.genre, avg_rating DESC
\"\"\"
print("Solution 1 - All actors per genre (ranked):")
print(pd.read_sql(sql_actors1, conn))
"""),
code("""# Solution 2: RANK() to pick top-1 per genre
sql_actors2 = \"\"\"
WITH actor_ratings AS (
    SELECT m.genre, a.actor_name, AVG(m.rating) AS avg_rating
    FROM movies m
    JOIN actors a ON m.id = a.movie_id
    GROUP BY m.genre, a.actor_name
),
ranked AS (
    SELECT *, RANK() OVER (PARTITION BY genre ORDER BY avg_rating DESC) AS rnk
    FROM actor_ratings
)
SELECT genre, actor_name, ROUND(avg_rating, 2) AS avg_rating
FROM ranked WHERE rnk = 1
ORDER BY genre
\"\"\"
print("Solution 2 - Top actor per genre (RANK):")
print(pd.read_sql(sql_actors2, conn))
"""),
code("""# Solution 3: ROW_NUMBER to handle ties differently
sql_actors3 = \"\"\"
WITH actor_ratings AS (
    SELECT m.genre, a.actor_name,
           ROUND(AVG(m.rating), 2) AS avg_rating,
           COUNT(DISTINCT m.id) AS movie_count
    FROM movies m JOIN actors a ON m.id = a.movie_id
    GROUP BY m.genre, a.actor_name
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY genre ORDER BY avg_rating DESC, movie_count DESC) AS rn
    FROM actor_ratings
)
SELECT genre, actor_name, avg_rating, movie_count
FROM ranked WHERE rn = 1
\"\"\"
print("Solution 3 - ROW_NUMBER with tie-breaking by movie count:")
print(pd.read_sql(sql_actors3, conn))
"""),

# ─────────────── Q150: House Robber ───────────────
md("""---
## Q150 · House Robber (Algorithms – MEDIUM)

### Problem
Given amounts in houses in a row, find max money you can rob without robbing adjacent houses.

**Example:** [2,7,9,3,1] → 12 (rob houses 0,2,4 → 2+9+1=12)

---
### 🧠 How to Remember (Step by Step)
```
MANTRA: "At each house, I have TWO choices: rob it or skip it"
  - Rob house i:  dp[i] = dp[i-2] + nums[i]
  - Skip house i: dp[i] = dp[i-1]
  - Take MAX of both

Space optimize: only need prev2 and prev1 (rolling variables)
```
"""),
code("""# Solution 1: Recursion with memoization (Top-down DP)
# Time: O(n)  Space: O(n)
from functools import lru_cache

def house_robber_memo(nums: List[int]) -> int:
    \"\"\"Top-down: rob(i) = max(rob(i-2)+nums[i], rob(i-1))\"\"\"
    @lru_cache(maxsize=None)
    def rob(i):
        if i < 0: return 0
        return max(rob(i-2) + nums[i], rob(i-1))
    return rob(len(nums) - 1)

print("Solution 1 (Memoization):", house_robber_memo([2,7,9,3,1]))  # 12
print("Solution 1:", house_robber_memo([1,2,3,1]))  # 4
"""),
code("""# Solution 2: Bottom-up DP array
# Time: O(n)  Space: O(n)
def house_robber_dp(nums: List[int]) -> int:
    \"\"\"Build dp array: dp[i] = max loot up to house i.\"\"\"
    if not nums: return 0
    n = len(nums)
    if n == 1: return nums[0]

    dp = [0] * n
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])

    for i in range(2, n):
        dp[i] = max(dp[i-2] + nums[i], dp[i-1])

    return dp[-1]

print("Solution 2 (DP Array):", house_robber_dp([2,7,9,3,1]))  # 12
"""),
code("""# Solution 3: Space-optimized DP (rolling 2 vars) ← OPTIMAL
# Time: O(n)  Space: O(1)
def house_robber_optimized(nums: List[int]) -> int:
    \"\"\"Only keep prev2 and prev1 - no array needed.\"\"\"
    prev2, prev1 = 0, 0
    for num in nums:
        curr = max(prev2 + num, prev1)  # rob or skip
        prev2, prev1 = prev1, curr
    return prev1

print("Solution 3 (O(1) Space):", house_robber_optimized([2,7,9,3,1]))  # 12
print("Solution 3:", house_robber_optimized([1,2,3,1]))  # 4

print("\\n⏱ Complexity Summary:")
print("| Solution       | Time | Space |")
print("|----------------|------|-------|")
print("| Memoization    | O(n) | O(n)  |")
print("| DP Array       | O(n) | O(n)  |")
print("| Rolling Vars ✅| O(n) | O(1)  |")
"""),
]

# ─────────────────────────────────────────────────────────────────
# NOTEBOOK 2  (com2.pdf – Page 2, Q420–Q709)
# ─────────────────────────────────────────────────────────────────
nb2_cells = [
md("""# 🟡 Google Data Engineer – Page 2 (Q420-Q709)
| # | Title | Category | Difficulty |
|---|-------|----------|-----------|
| Q427 | Flagging Metrics Summary | SQL | HARD |
| Q464 | Top 10 Highest-Rated Hotels | SQL | MEDIUM |
| Q503 | Meeting Rooms | Python | EASY |
| Q546 | Share of Shippable Orders | SQL | MEDIUM |
| Q578 | Average Pay per Education | SQL | EASY |
| Q595 | Survivors by Sex and Class | SQL | MEDIUM |
| Q662 | Accounts Merge | Python | MEDIUM |
"""),

md("""---
## Q427 · Flagging Metrics Summary (Database – HARD)

### Problem
Given `flags` (user_id, video_id, flag_reason, reviewed, is_correct) table,
compute for each flag_reason: total flags, % reviewed, % correct when reviewed.

---
### 🧠 How to Remember
```
1. Three metrics → three CASE WHEN counts in one GROUP BY
2. % reviewed = SUM(reviewed=1) / COUNT(*) * 100
3. % correct  = SUM(is_correct=1 AND reviewed=1) / SUM(reviewed=1) * 100
4. NULLIF to avoid division by zero
```
"""),
code("""import sqlite3
import pandas as pd

conn2 = sqlite3.connect(":memory:")
conn2.execute(\"\"\"
CREATE TABLE flags (
    user_id INT, video_id INT, flag_reason TEXT,
    reviewed INT, is_correct INT
)
\"\"\")
conn2.executemany("INSERT INTO flags VALUES (?,?,?,?,?)", [
    (1, 101, 'spam',       1, 1),
    (2, 102, 'spam',       1, 0),
    (3, 103, 'hate_speech',1, 1),
    (4, 104, 'spam',       0, None),
    (5, 105, 'hate_speech',1, 1),
    (6, 106, 'violence',   0, None),
    (7, 107, 'spam',       1, 1),
    (8, 108, 'violence',   1, 0),
])

# Solution 1: CASE WHEN aggregation
sql_flag1 = \"\"\"
SELECT
    flag_reason,
    COUNT(*) AS total_flags,
    ROUND(100.0 * SUM(reviewed) / COUNT(*), 1) AS pct_reviewed,
    ROUND(100.0 * SUM(CASE WHEN reviewed=1 AND is_correct=1 THEN 1 ELSE 0 END)
          / NULLIF(SUM(reviewed), 0), 1) AS pct_correct_when_reviewed
FROM flags
GROUP BY flag_reason
ORDER BY total_flags DESC
\"\"\"
print("Solution 1 - CASE WHEN:")
print(pd.read_sql(sql_flag1, conn2))
"""),
code("""# Solution 2: CTE for readability
sql_flag2 = \"\"\"
WITH base AS (
    SELECT flag_reason,
           COUNT(*) AS total,
           SUM(reviewed) AS n_reviewed,
           SUM(CASE WHEN reviewed=1 AND is_correct=1 THEN 1 ELSE 0 END) AS n_correct
    FROM flags
    GROUP BY flag_reason
)
SELECT flag_reason, total AS total_flags,
       ROUND(100.0 * n_reviewed / total, 1) AS pct_reviewed,
       ROUND(100.0 * n_correct / NULLIF(n_reviewed, 0), 1) AS pct_correct_when_reviewed
FROM base
ORDER BY total_flags DESC
\"\"\"
print("Solution 2 - CTE approach:")
print(pd.read_sql(sql_flag2, conn2))
"""),
code("""# Solution 3: Window functions + FILTER clause style
sql_flag3 = \"\"\"
SELECT DISTINCT flag_reason,
    COUNT(*) OVER (PARTITION BY flag_reason) AS total_flags,
    ROUND(100.0 * SUM(reviewed) OVER (PARTITION BY flag_reason)
          / COUNT(*) OVER (PARTITION BY flag_reason), 1) AS pct_reviewed,
    ROUND(100.0 * SUM(CASE WHEN reviewed=1 AND is_correct=1 THEN 1 ELSE 0 END)
                  OVER (PARTITION BY flag_reason)
          / NULLIF(SUM(reviewed) OVER (PARTITION BY flag_reason), 0), 1) AS pct_correct
FROM flags
ORDER BY total_flags DESC
\"\"\"
print("Solution 3 - Window functions:")
print(pd.read_sql(sql_flag3, conn2))
"""),

md("""---
## Q464 · Top 10 Highest-Rated Hotels (Database – MEDIUM)

### Problem
Given `hotel_reviews` (hotel_name, review_score), find the top 10 hotels by average review score.

---
### 🧠 How to Remember
```
1. AVG(review_score) GROUP BY hotel_name
2. ORDER BY avg DESC
3. LIMIT 10
4. For ties: use RANK() or DENSE_RANK()
```
"""),
code("""conn2.execute(\"\"\"
CREATE TABLE hotel_reviews (hotel_name TEXT, review_score REAL, review_date TEXT)
\"\"\")
import random
random.seed(42)
hotels = ['Grand Plaza','City Inn','Beach Resort','Mountain Lodge','Airport Hotel',
          'Downtown Suites','Riverside Hotel','Garden View','Sky Tower','Harbor Inn',
          'Central Park','Budget Stay']
data = [(h, round(random.uniform(3.0,5.0),1), '2023-01-01') for h in hotels for _ in range(random.randint(5,15))]
conn2.executemany("INSERT INTO hotel_reviews VALUES (?,?,?)", data)

# Solution 1: Simple GROUP BY + LIMIT
sql_hotel1 = \"\"\"
SELECT hotel_name, ROUND(AVG(review_score),2) AS avg_score, COUNT(*) AS review_count
FROM hotel_reviews
GROUP BY hotel_name
ORDER BY avg_score DESC
LIMIT 10
\"\"\"
print("Solution 1 - Simple TOP 10:")
print(pd.read_sql(sql_hotel1, conn2))
"""),
code("""# Solution 2: RANK() to handle ties properly
sql_hotel2 = \"\"\"
WITH hotel_stats AS (
    SELECT hotel_name,
           ROUND(AVG(review_score),2) AS avg_score,
           COUNT(*) AS review_count
    FROM hotel_reviews
    GROUP BY hotel_name
)
SELECT hotel_name, avg_score, review_count,
       RANK() OVER (ORDER BY avg_score DESC) AS rank
FROM hotel_stats
WHERE RANK() OVER (ORDER BY avg_score DESC) <= 10
\"\"\"
# SQLite doesn't support window in WHERE directly, use subquery:
sql_hotel2 = \"\"\"
WITH hotel_stats AS (
    SELECT hotel_name,
           ROUND(AVG(review_score),2) AS avg_score,
           COUNT(*) AS review_count
    FROM hotel_reviews GROUP BY hotel_name
),
ranked AS (
    SELECT *, RANK() OVER (ORDER BY avg_score DESC) AS rnk FROM hotel_stats
)
SELECT hotel_name, avg_score, review_count, rnk FROM ranked WHERE rnk <= 10
\"\"\"
print("Solution 2 - With RANK():")
print(pd.read_sql(sql_hotel2, conn2))
"""),
code("""# Solution 3: Weighted by recency (advanced)
sql_hotel3 = \"\"\"
WITH weighted AS (
    SELECT hotel_name,
           ROUND(AVG(review_score),2) AS avg_score,
           COUNT(*) AS review_count,
           MIN(review_date) AS first_review,
           MAX(review_date) AS last_review
    FROM hotel_reviews GROUP BY hotel_name
)
SELECT hotel_name, avg_score, review_count,
       CASE WHEN review_count >= 10 THEN 'High confidence'
            WHEN review_count >= 5  THEN 'Medium confidence'
            ELSE 'Low confidence' END AS confidence
FROM weighted
ORDER BY avg_score DESC
LIMIT 10
\"\"\"
print("Solution 3 - With confidence bands:")
print(pd.read_sql(sql_hotel3, conn2))
"""),

md("""---
## Q503 · Meeting Rooms (Data Structures – EASY)

### Problem
Given intervals [[start,end]] of meetings, determine if a person can attend **all** meetings
(i.e., no two meetings overlap).

**Example:** [[0,30],[5,10],[15,20]] → False (overlap at 5)

---
### 🧠 How to Remember
```
1. SORT by start time
2. Check if any meeting starts before previous ends
3. If intervals[i][0] < intervals[i-1][1] → OVERLAP → return False
```
"""),
code("""# Solution 1: Brute force - check all pairs
# Time: O(n²)  Space: O(1)
def can_attend_meetings_brute(intervals: List[List[int]]) -> bool:
    \"\"\"Check every pair for overlap.\"\"\"
    n = len(intervals)
    for i in range(n):
        for j in range(i+1, n):
            a, b = intervals[i], intervals[j]
            # Overlap if one starts before other ends
            if not (a[1] <= b[0] or b[1] <= a[0]):
                return False
    return True

print("Solution 1:", can_attend_meetings_brute([[0,30],[5,10],[15,20]]))  # False
print("Solution 1:", can_attend_meetings_brute([[7,10],[2,4]]))  # True
"""),
code("""# Solution 2: Sort + Linear Scan ← OPTIMAL
# Time: O(n log n)  Space: O(1)
def can_attend_meetings_sort(intervals: List[List[int]]) -> bool:
    \"\"\"Sort by start, check adjacent pairs only.\"\"\"
    intervals.sort(key=lambda x: x[0])
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i-1][1]:  # new starts before prev ends
            return False
    return True

print("Solution 2:", can_attend_meetings_sort([[0,30],[5,10],[15,20]]))  # False
print("Solution 2:", can_attend_meetings_sort([[7,10],[2,4]]))  # True
"""),
code("""# Solution 3: Event timeline (sweep line)
# Time: O(n log n)  Space: O(n)
def can_attend_meetings_sweep(intervals: List[List[int]]) -> bool:
    \"\"\"Flatten to events: +1 at start, -1 at end. Overlap if count > 1.\"\"\"
    events = []
    for start, end in intervals:
        events.append((start, 1))   # meeting starts
        events.append((end,  -1))   # meeting ends
    events.sort()

    active = 0
    for time, delta in events:
        active += delta
        if active > 1:  # more than 1 meeting at same time
            return False
    return True

print("Solution 3:", can_attend_meetings_sweep([[0,30],[5,10],[15,20]]))  # False
print("Solution 3:", can_attend_meetings_sweep([[7,10],[2,4]]))  # True
print("\\n⏱ Complexity Summary:")
print("| Solution   | Time      | Space |")
print("|------------|-----------|-------|")
print("| Brute      | O(n²)     | O(1)  |")
print("| Sort ✅    | O(n log n)| O(1)  |")
print("| Sweep Line | O(n log n)| O(n)  |")
"""),

md("""---
## Q546 · Share of Shippable Orders (Database – MEDIUM)

### Problem
Given `orders` (order_id, item_id, quantity) and `inventory` (item_id, stock),
find % of orders where ALL items have sufficient stock.

---
### 🧠 How to Remember
```
1. JOIN orders with inventory
2. Flag each order-item pair: can_ship = (stock >= quantity)
3. Per order: all items must be shippable → MIN(can_ship) = 1
4. % shippable = COUNT(shippable orders) / COUNT(all orders) * 100
```
"""),
code("""conn2.execute("CREATE TABLE orders (order_id INT, item_id INT, quantity INT)")
conn2.execute("CREATE TABLE inventory (item_id INT, stock INT)")
conn2.executemany("INSERT INTO orders VALUES (?,?,?)", [
    (1, 10, 2), (1, 20, 3),
    (2, 10, 1), (2, 30, 5),
    (3, 20, 10),
    (4, 10, 1),
])
conn2.executemany("INSERT INTO inventory VALUES (?,?)", [
    (10, 5), (20, 2), (30, 10),
])

# Solution 1: Subquery approach
sql_ship1 = \"\"\"
WITH order_check AS (
    SELECT o.order_id,
           MIN(CASE WHEN i.stock >= o.quantity THEN 1 ELSE 0 END) AS fully_shippable
    FROM orders o
    JOIN inventory i ON o.item_id = i.item_id
    GROUP BY o.order_id
)
SELECT
    COUNT(CASE WHEN fully_shippable = 1 THEN 1 END) AS shippable_orders,
    COUNT(*) AS total_orders,
    ROUND(100.0 * COUNT(CASE WHEN fully_shippable=1 THEN 1 END) / COUNT(*), 1) AS pct_shippable
FROM order_check
\"\"\"
print("Solution 1 - Shippable orders:")
print(pd.read_sql(sql_ship1, conn2))
"""),
code("""# Solution 2: NOT EXISTS approach (exclude orders with any unshippable item)
sql_ship2 = \"\"\"
SELECT
    (SELECT COUNT(DISTINCT order_id) FROM orders o
     WHERE NOT EXISTS (
         SELECT 1 FROM inventory i
         WHERE i.item_id = o.item_id AND i.stock < o.quantity
     )) AS shippable,
    COUNT(DISTINCT order_id) AS total,
    ROUND(100.0 * (SELECT COUNT(DISTINCT order_id) FROM orders o2
          WHERE NOT EXISTS (SELECT 1 FROM inventory i2
                            WHERE i2.item_id=o2.item_id AND i2.stock < o2.quantity))
          / COUNT(DISTINCT order_id), 1) AS pct_shippable
FROM orders
\"\"\"
print("Solution 2 - NOT EXISTS:")
print(pd.read_sql(sql_ship2, conn2))
"""),
code("""# Solution 3: HAVING clause style
sql_ship3 = \"\"\"
WITH item_check AS (
    SELECT o.order_id, o.item_id, o.quantity, i.stock,
           CASE WHEN i.stock >= o.quantity THEN 1 ELSE 0 END AS ok
    FROM orders o LEFT JOIN inventory i ON o.item_id = i.item_id
),
order_status AS (
    SELECT order_id,
           CASE WHEN MIN(ok) = 1 THEN 'Shippable' ELSE 'Blocked' END AS status
    FROM item_check
    GROUP BY order_id
)
SELECT status, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct
FROM order_status GROUP BY status
\"\"\"
print("Solution 3 - Order status breakdown:")
print(pd.read_sql(sql_ship3, conn2))
"""),

md("""---
## Q662 · Accounts Merge (Data Structures – MEDIUM)

### Problem
Given a list of accounts where account[0] is the name and rest are emails,
merge accounts that share at least one email. Return merged list sorted.

**Example:**
```
[["John","j@g.com","j@c.com"],["John","j@c.com","j@g.com"],["Mary","m@g.com"]]
→ [["John","j@c.com","j@g.com"],["Mary","m@g.com"]]
```

---
### 🧠 How to Remember
```
UNION FIND pattern for grouping:
1. Map each email → account index
2. If email seen before → UNION current account with previous
3. Group all emails by their root account
4. Sort emails within each group, prepend name
```
"""),
code("""# Solution 1: DFS Graph approach
# Time: O(n*k log(n*k))  Space: O(n*k) where k=avg emails per account
from collections import defaultdict

def accounts_merge_dfs(accounts: List[List[str]]) -> List[List[str]]:
    \"\"\"Build email graph, DFS to find connected components.\"\"\"
    graph = defaultdict(set)
    email_to_name = {}

    for account in accounts:
        name = account[0]
        for email in account[1:]:
            email_to_name[email] = name
            graph[account[1]].add(email)   # connect all to first email
            graph[email].add(account[1])

    visited = set()
    result = []

    def dfs(email, component):
        visited.add(email)
        component.append(email)
        for neighbor in graph[email]:
            if neighbor not in visited:
                dfs(neighbor, component)

    for email in email_to_name:
        if email not in visited:
            component = []
            dfs(email, component)
            result.append([email_to_name[email]] + sorted(component))

    return result

accounts = [["John","j@g.com","j@c.com"],["John","j@c.com","j@g.com"],["Mary","m@g.com"]]
print("Solution 1 (DFS):", accounts_merge_dfs(accounts))
"""),
code("""# Solution 2: Union Find (Disjoint Set Union)
# Time: O(n*k * α(n))  Space: O(n*k)
class UnionFind:
    def __init__(self):
        self.parent = {}
    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]
    def union(self, x, y):
        self.parent[self.find(x)] = self.find(y)

def accounts_merge_uf(accounts: List[List[str]]) -> List[List[str]]:
    uf = UnionFind()
    email_to_name = {}

    for account in accounts:
        name, emails = account[0], account[1:]
        for email in emails:
            email_to_name[email] = name
            uf.union(emails[0], email)   # union all emails in account

    # Group emails by root
    groups = defaultdict(list)
    for email in email_to_name:
        groups[uf.find(email)].append(email)

    return [[email_to_name[root]] + sorted(emails) for root, emails in groups.items()]

accounts2 = [["John","j@g.com","j@c.com"],["John","j@c.com","j@g.com"],["Mary","m@g.com"]]
print("Solution 2 (Union Find):", accounts_merge_uf(accounts2))
"""),
code("""# Solution 3: BFS approach (alternative to DFS)
# Time: O(n*k log(n*k))  Space: O(n*k)
from collections import deque

def accounts_merge_bfs(accounts: List[List[str]]) -> List[List[str]]:
    \"\"\"BFS traversal of email graph.\"\"\"
    graph = defaultdict(set)
    email_to_name = {}

    for account in accounts:
        name = account[0]
        for email in account[1:]:
            email_to_name[email] = name
            graph[account[1]].add(email)
            graph[email].add(account[1])

    visited = set()
    result = []

    for start_email in email_to_name:
        if start_email not in visited:
            queue = deque([start_email])
            component = []
            while queue:
                email = queue.popleft()
                if email in visited: continue
                visited.add(email)
                component.append(email)
                queue.extend(graph[email] - visited)
            result.append([email_to_name[start_email]] + sorted(component))

    return result

accounts3 = [["John","j@g.com","j@c.com"],["John","j@c.com","j@g.com"],["Mary","m@g.com"]]
print("Solution 3 (BFS):", accounts_merge_bfs(accounts3))
print("\\n⏱ Complexity Summary:")
print("| Solution   | Time           | Space  |")
print("|------------|----------------|--------|")
print("| DFS        | O(nk log(nk))  | O(nk)  |")
print("| Union Find | O(nk·α(n))     | O(nk)  |")
print("| BFS        | O(nk log(nk))  | O(nk)  |")
"""),
]

# ─────────────────────────────────────────────────────────────────
# NOTEBOOK 3  (com3.pdf – Page 3, Q711–Q1111)
# ─────────────────────────────────────────────────────────────────
nb3_cells = [
md("""# 🟠 Google Data Engineer – Page 3 (Q711-Q1111)
| # | Title | Category | Difficulty |
|---|-------|----------|-----------|
| Q711 | Symmetrize Friends Network | SQL | MEDIUM |
| Q775 | Top Visited Website | SQL | HARD |
| Q792 | Longest Winning Run | SQL | MEDIUM |
| Q829 | Subarray Sum Equals K | Python | MEDIUM |
| Q837 | Google Maps Trips | SQL | HARD |
| Q1069 | Email Activity Ranking | SQL | MEDIUM |
| Q1103 | CTR by Ad Type | SQL | MEDIUM |
"""),

md("""---
## Q711 · Symmetrize Friends Network (Database – MEDIUM)

### Problem
Given a `friends` table (user1, user2), some edges appear once-directional.
Symmetrize it: ensure if (A,B) exists, (B,A) also exists. Return unique pairs.

---
### 🧠 How to Remember
```
1. UNION original table with SWAPPED columns
2. Use UNION (not UNION ALL) to deduplicate
3. Or: add WHERE user1 < user2 to get canonical pairs
```
"""),
code("""import sqlite3
import pandas as pd

conn3 = sqlite3.connect(":memory:")
conn3.execute("CREATE TABLE friends (user1 INT, user2 INT)")
conn3.executemany("INSERT INTO friends VALUES (?,?)", [
    (1, 2), (1, 3), (2, 3), (3, 4), (4, 1)
])

# Solution 1: UNION to symmetrize
sql_sym1 = \"\"\"
SELECT user1, user2 FROM friends
UNION
SELECT user2 AS user1, user1 AS user2 FROM friends
ORDER BY user1, user2
\"\"\"
print("Solution 1 - UNION symmetrize:")
print(pd.read_sql(sql_sym1, conn3))
"""),
code("""# Solution 2: Canonical pairs (user1 < user2)
sql_sym2 = \"\"\"
SELECT DISTINCT
    MIN(user1, user2) AS user_a,
    MAX(user1, user2) AS user_b
FROM (
    SELECT user1, user2 FROM friends
    UNION ALL
    SELECT user2, user1 FROM friends
)
ORDER BY user_a, user_b
\"\"\"
print("Solution 2 - Canonical pairs (deduped):")
print(pd.read_sql(sql_sym2, conn3))
"""),
code("""# Solution 3: With mutual friend count
sql_sym3 = \"\"\"
WITH all_edges AS (
    SELECT user1, user2 FROM friends
    UNION
    SELECT user2, user1 FROM friends
)
SELECT a.user1, a.user2,
       COUNT(DISTINCT m.user2) AS mutual_friends
FROM all_edges a
LEFT JOIN all_edges m
    ON m.user1 = a.user1
    AND m.user2 IN (SELECT user2 FROM all_edges WHERE user1 = a.user2)
GROUP BY a.user1, a.user2
ORDER BY a.user1, a.user2
\"\"\"
print("Solution 3 - With mutual friends count:")
print(pd.read_sql(sql_sym3, conn3))
"""),

md("""---
## Q792 · Longest Winning Run (Database – MEDIUM)

### Problem
Given `game_results` (player_id, game_date, win INT), find the longest consecutive
winning streak for each player.

---
### 🧠 How to Remember
```
GAP-AND-ISLANDS technique:
1. ROW_NUMBER() overall
2. ROW_NUMBER() partitioned by player+win
3. Difference = "island id" for consecutive same-results
4. COUNT of consecutive wins per island → MAX per player
```
"""),
code("""conn3.execute(\"\"\"
CREATE TABLE game_results (player_id INT, game_date TEXT, win INT)
\"\"\")
conn3.executemany("INSERT INTO game_results VALUES (?,?,?)", [
    (1, '2023-01-01', 1),
    (1, '2023-01-02', 1),
    (1, '2023-01-03', 0),
    (1, '2023-01-04', 1),
    (1, '2023-01-05', 1),
    (1, '2023-01-06', 1),
    (2, '2023-01-01', 1),
    (2, '2023-01-02', 0),
    (2, '2023-01-03', 1),
])

# Solution 1: Gap-and-islands with ROW_NUMBER
sql_win1 = \"\"\"
WITH numbered AS (
    SELECT player_id, game_date, win,
           ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY game_date) AS rn,
           ROW_NUMBER() OVER (PARTITION BY player_id, win ORDER BY game_date) AS rn_win
    FROM game_results
),
islands AS (
    SELECT player_id, win, (rn - rn_win) AS island_id, COUNT(*) AS streak_len
    FROM numbered
    WHERE win = 1
    GROUP BY player_id, win, island_id
)
SELECT player_id, MAX(streak_len) AS longest_winning_streak
FROM islands
GROUP BY player_id
ORDER BY player_id
\"\"\"
print("Solution 1 - Gap-and-Islands:")
print(pd.read_sql(sql_win1, conn3))
"""),
code("""# Solution 2: Self-join (classic approach)
sql_win2 = \"\"\"
WITH wins_only AS (
    SELECT player_id, game_date,
           ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY game_date) AS rn
    FROM game_results WHERE win = 1
),
grouped AS (
    SELECT player_id, COUNT(*) AS streak,
           date(game_date, '-' || (rn-1) || ' days') AS group_key
    FROM wins_only
    GROUP BY player_id, group_key
)
SELECT player_id, MAX(streak) AS longest_winning_streak
FROM grouped
GROUP BY player_id
ORDER BY player_id
\"\"\"
print("Solution 2 - Date-based grouping:")
print(pd.read_sql(sql_win2, conn3))
"""),
code("""# Solution 3: Python simulation (when SQL isn't available)
# Time: O(n log n)  Space: O(n)
from itertools import groupby

def longest_winning_run(records):
    \"\"\"records: list of (player_id, date, win)\"\"\"
    from collections import defaultdict
    player_games = defaultdict(list)
    for pid, date, win in records:
        player_games[pid].append((date, win))

    result = {}
    for pid, games in player_games.items():
        games.sort()
        max_streak = 0
        curr_streak = 0
        for _, win in games:
            if win == 1:
                curr_streak += 1
                max_streak = max(max_streak, curr_streak)
            else:
                curr_streak = 0
        result[pid] = max_streak
    return result

data = [(1,'2023-01-01',1),(1,'2023-01-02',1),(1,'2023-01-03',0),
        (1,'2023-01-04',1),(1,'2023-01-05',1),(1,'2023-01-06',1),
        (2,'2023-01-01',1),(2,'2023-01-02',0),(2,'2023-01-03',1)]
print("Solution 3 - Python:", longest_winning_run(data))
"""),

md("""---
## Q829 · Subarray Sum Equals K (Data Structures – MEDIUM)

### Problem
Given array nums and integer k, count subarrays that sum to exactly k.

**Example:** nums=[1,1,1], k=2 → 2  (subarrays [1,1] at positions 0-1 and 1-2)

---
### 🧠 How to Remember
```
PREFIX SUM + HASH MAP trick:
1. prefix_sum[i] = sum of nums[0..i]
2. subarray sum from j+1 to i = prefix[i] - prefix[j]
3. We want prefix[i] - prefix[j] = k  →  prefix[j] = prefix[i] - k
4. Count how many times (prefix[i] - k) appeared before!
MANTRA: "If I've seen prefix_sum - k before, I found a valid subarray"
```
"""),
code("""# Solution 1: Brute Force - check all subarrays
# Time: O(n²)  Space: O(1)
def subarray_sum_brute(nums: List[int], k: int) -> int:
    count = 0
    for i in range(len(nums)):
        total = 0
        for j in range(i, len(nums)):
            total += nums[j]
            if total == k:
                count += 1
    return count

print("Solution 1:", subarray_sum_brute([1,1,1], 2))  # 2
print("Solution 1:", subarray_sum_brute([1,2,3], 3))   # 2
"""),
code("""# Solution 2: Prefix Sum array
# Time: O(n²)  Space: O(n)
def subarray_sum_prefix(nums: List[int], k: int) -> int:
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i+1] = prefix[i] + nums[i]

    count = 0
    for i in range(n+1):
        for j in range(i+1, n+1):
            if prefix[j] - prefix[i] == k:
                count += 1
    return count

print("Solution 2:", subarray_sum_prefix([1,1,1], 2))  # 2
"""),
code("""# Solution 3: HashMap of prefix sums ← OPTIMAL
# Time: O(n)  Space: O(n)
from collections import defaultdict

def subarray_sum_hashmap(nums: List[int], k: int) -> int:
    \"\"\"
    Track frequency of prefix sums seen so far.
    If (current_prefix - k) was seen before → valid subarray found!
    \"\"\"
    count = 0
    prefix = 0
    freq = defaultdict(int)
    freq[0] = 1       # empty subarray has sum 0

    for num in nums:
        prefix += num
        count += freq[prefix - k]   # how many j's satisfy sum[j..i] = k
        freq[prefix] += 1

    return count

print("Solution 3:", subarray_sum_hashmap([1,1,1], 2))   # 2
print("Solution 3:", subarray_sum_hashmap([1,2,3], 3))    # 2
print("Solution 3:", subarray_sum_hashmap([-1,-1,1], 0))  # 1
print("\\n⏱ Complexity Summary:")
print("| Solution    | Time  | Space |")
print("|-------------|-------|-------|")
print("| Brute       | O(n²) | O(1)  |")
print("| Prefix Array| O(n²) | O(n)  |")
print("| HashMap ✅  | O(n)  | O(n)  |")
"""),

md("""---
## Q1069 · Email Activity Ranking (Database – MEDIUM)

### Problem
Given `emails` (from_user, to_user, day) count emails sent AND received per user,
then rank users by total activity (sent + received).

---
### 🧠 How to Remember
```
1. Two CTEs: sent (GROUP BY from_user), received (GROUP BY to_user)
2. FULL OUTER JOIN (use UNION in SQLite)
3. total = sent + received, RANK() by total
```
"""),
code("""conn3.execute("CREATE TABLE email_log (from_user TEXT, to_user TEXT, day INT)")
conn3.executemany("INSERT INTO email_log VALUES (?,?,?)", [
    ('Alice','Bob',1), ('Alice','Carol',1), ('Bob','Alice',2),
    ('Carol','Alice',3), ('Carol','Bob',3), ('Bob','Carol',4),
    ('Alice','Bob',5),
])

# Solution 1: UNION-based FULL OUTER JOIN equivalent
sql_email_rank1 = \"\"\"
WITH sent AS (
    SELECT from_user AS user, COUNT(*) AS sent_count
    FROM email_log GROUP BY from_user
),
recv AS (
    SELECT to_user AS user, COUNT(*) AS recv_count
    FROM email_log GROUP BY to_user
),
all_users AS (
    SELECT user FROM sent UNION SELECT user FROM recv
)
SELECT a.user,
       COALESCE(s.sent_count, 0) AS sent,
       COALESCE(r.recv_count, 0) AS received,
       COALESCE(s.sent_count,0) + COALESCE(r.recv_count,0) AS total_activity
FROM all_users a
LEFT JOIN sent s ON a.user = s.user
LEFT JOIN recv r ON a.user = r.user
ORDER BY total_activity DESC
\"\"\"
print("Solution 1 - Email activity:")
print(pd.read_sql(sql_email_rank1, conn3))
"""),
code("""# Solution 2: UNION ALL + GROUP BY (more concise)
sql_email_rank2 = \"\"\"
WITH activity AS (
    SELECT from_user AS user, 'sent' AS type FROM email_log
    UNION ALL
    SELECT to_user AS user, 'received' AS type FROM email_log
)
SELECT user,
       SUM(CASE WHEN type='sent' THEN 1 ELSE 0 END) AS sent,
       SUM(CASE WHEN type='received' THEN 1 ELSE 0 END) AS received,
       COUNT(*) AS total_activity,
       RANK() OVER (ORDER BY COUNT(*) DESC) AS activity_rank
FROM activity
GROUP BY user
ORDER BY total_activity DESC
\"\"\"
print("Solution 2 - UNION ALL approach:")
print(pd.read_sql(sql_email_rank2, conn3))
"""),
code("""# Solution 3: Pandas equivalent (Python)
import pandas as pd as pd_lib
df = pd.read_sql("SELECT * FROM email_log", conn3)
sent = df.groupby('from_user').size().rename('sent')
recv = df.groupby('to_user').size().rename('received')
combined = pd.concat([sent, recv], axis=1).fillna(0).astype(int)
combined['total'] = combined['sent'] + combined['received']
combined = combined.sort_values('total', ascending=False)
combined['rank'] = combined['total'].rank(method='min', ascending=False).astype(int)
print("Solution 3 - Pandas:")
print(combined)
"""),
]

# ─────────────────────────────────────────────────────────────────
# NOTEBOOK 4  (co4.pdf – Page 4, Q1112–Q1489)
# ─────────────────────────────────────────────────────────────────
nb4_cells = [
md("""# 🔴 Google Data Engineer – Page 4 (Q1112-Q1489)
| # | Title | Category | Difficulty |
|---|-------|----------|-----------|
| Q1119 | Speaker Totals by Language | SQL | EASY |
| Q1180 | User Activity Counts | SQL | MEDIUM |
| Q1267 | Latest vs Prior Ratings | SQL | HARD |
| Q1306 | Longest Increasing Subsequence | Python | MEDIUM |
| Q1342 | Count Multilingual Users | SQL | MEDIUM |
| Q1456 | Event Type Summary | SQL | MEDIUM |
| Q1460 | Merge Intervals | Python | MEDIUM |
| Q1463 | Avg Trip Time by Zip | SQL | HARD |
"""),

md("""---
## Q1119 · Speaker Totals by Language (Database – EASY)

### Problem
Given `speakers` (user_id, language), count total speakers per language, sorted descending.

---
### 🧠 How to Remember
```
SELECT language, COUNT(*) → GROUP BY language → ORDER BY DESC
Simple! Just COUNT + GROUP BY
```
"""),
code("""import sqlite3, pandas as pd

conn4 = sqlite3.connect(":memory:")
conn4.execute("CREATE TABLE speakers (user_id INT, language TEXT)")
conn4.executemany("INSERT INTO speakers VALUES (?,?)", [
    (1,'English'),(2,'English'),(3,'Spanish'),(4,'Spanish'),(5,'Spanish'),
    (6,'French'),(7,'English'),(8,'Mandarin'),(9,'French'),(10,'Mandarin'),
    (11,'Mandarin'),(12,'Mandarin'),
])

# Solution 1: Simple GROUP BY
sql_spk1 = \"\"\"
SELECT language, COUNT(*) AS speaker_count
FROM speakers
GROUP BY language
ORDER BY speaker_count DESC
\"\"\"
print("Solution 1 - Simple COUNT:")
print(pd.read_sql(sql_spk1, conn4))
"""),
code("""# Solution 2: With percentage
sql_spk2 = \"\"\"
SELECT language, COUNT(*) AS speaker_count,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_share
FROM speakers
GROUP BY language
ORDER BY speaker_count DESC
\"\"\"
print("Solution 2 - With % share:")
print(pd.read_sql(sql_spk2, conn4))
"""),
code("""# Solution 3: Cumulative rank
sql_spk3 = \"\"\"
WITH lang_counts AS (
    SELECT language, COUNT(*) AS cnt FROM speakers GROUP BY language
)
SELECT language, cnt AS speaker_count,
       RANK() OVER (ORDER BY cnt DESC) AS popularity_rank,
       SUM(cnt) OVER (ORDER BY cnt DESC) AS cumulative_speakers
FROM lang_counts
\"\"\"
print("Solution 3 - With cumulative count:")
print(pd.read_sql(sql_spk3, conn4))
"""),

md("""---
## Q1267 · Latest vs Prior Ratings (Database – HARD)

### Problem
Given `ratings` (user_id, product_id, stars, submitted_at), for each user+product,
compare the LATEST rating to the PRIOR (second latest) rating.
Return rows where latest > prior.

---
### 🧠 How to Remember
```
SELF-JOIN or LAG() window function:
1. LAG(stars) OVER (PARTITION BY user_id, product_id ORDER BY submitted_at)
2. Filter WHERE current > lag_value
3. Or: ROW_NUMBER = 1 (latest) and ROW_NUMBER = 2 (prior) → JOIN on same user+product
```
"""),
code("""conn4.execute(\"\"\"
CREATE TABLE ratings (user_id INT, product_id INT, stars INT, submitted_at TEXT)
\"\"\")
conn4.executemany("INSERT INTO ratings VALUES (?,?,?,?)", [
    (1, 10, 3, '2023-01-01'),
    (1, 10, 4, '2023-02-01'),
    (1, 10, 5, '2023-03-01'),   # latest for user1+prod10
    (2, 10, 5, '2023-01-01'),
    (2, 10, 3, '2023-02-01'),   # latest for user2+prod10 (decreased)
    (3, 20, 4, '2023-01-01'),
    (3, 20, 5, '2023-02-01'),   # latest for user3+prod20
])

# Solution 1: LAG() window function
sql_rating1 = \"\"\"
WITH lagged AS (
    SELECT user_id, product_id, stars,
           LAG(stars) OVER (PARTITION BY user_id, product_id ORDER BY submitted_at) AS prior_stars,
           submitted_at,
           ROW_NUMBER() OVER (PARTITION BY user_id, product_id ORDER BY submitted_at DESC) AS rn
    FROM ratings
)
SELECT user_id, product_id, stars AS latest_rating, prior_stars AS prior_rating
FROM lagged
WHERE rn = 1 AND prior_stars IS NOT NULL AND stars > prior_stars
\"\"\"
print("Solution 1 - LAG() function:")
print(pd.read_sql(sql_rating1, conn4))
"""),
code("""# Solution 2: Self-JOIN with ROW_NUMBER
sql_rating2 = \"\"\"
WITH ranked AS (
    SELECT user_id, product_id, stars, submitted_at,
           ROW_NUMBER() OVER (PARTITION BY user_id, product_id ORDER BY submitted_at DESC) AS rn
    FROM ratings
)
SELECT a.user_id, a.product_id,
       a.stars AS latest_rating, b.stars AS prior_rating,
       a.stars - b.stars AS improvement
FROM ranked a
JOIN ranked b ON a.user_id = b.user_id
              AND a.product_id = b.product_id
              AND b.rn = 2
WHERE a.rn = 1 AND a.stars > b.stars
ORDER BY a.user_id, a.product_id
\"\"\"
print("Solution 2 - Self-JOIN approach:")
print(pd.read_sql(sql_rating2, conn4))
"""),
code("""# Solution 3: Full comparison report (all users)
sql_rating3 = \"\"\"
WITH ranked AS (
    SELECT user_id, product_id, stars,
           ROW_NUMBER() OVER (PARTITION BY user_id, product_id ORDER BY submitted_at DESC) AS rn
    FROM ratings
),
latest AS (SELECT user_id, product_id, stars FROM ranked WHERE rn=1),
prior  AS (SELECT user_id, product_id, stars FROM ranked WHERE rn=2)
SELECT l.user_id, l.product_id,
       l.stars AS latest, p.stars AS prior,
       CASE WHEN l.stars > p.stars THEN 'Improved'
            WHEN l.stars < p.stars THEN 'Declined'
            ELSE 'Same' END AS trend
FROM latest l
JOIN prior p ON l.user_id=p.user_id AND l.product_id=p.product_id
ORDER BY l.user_id
\"\"\"
print("Solution 3 - Full trend report:")
print(pd.read_sql(sql_rating3, conn4))
"""),

md("""---
## Q1306 · Longest Increasing Subsequence (Algorithms – MEDIUM)

### Problem
Given an integer array, find the length of the longest strictly increasing subsequence.

**Example:** [10,9,2,5,3,7,101,18] → 4  (2,3,7,101 or 2,5,7,101)

---
### 🧠 How to Remember (Step by Step)
```
THREE approaches - know all three!
1. DP O(n²): dp[i] = max(dp[j]+1) for all j<i where nums[j]<nums[i]
2. Binary Search O(n log n): maintain 'tails' array
   - tails[i] = smallest tail of all IS of length i+1
   - Binary search to find where new element fits
3. Patience Sorting insight: same as #2, intuition from card game
```
"""),
code("""import bisect

# Solution 1: DP O(n²)
# Time: O(n²)  Space: O(n)
def lis_dp(nums: List[int]) -> int:
    \"\"\"dp[i] = LIS ending at index i.\"\"\"
    if not nums: return 0
    n = len(nums)
    dp = [1] * n

    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)

    return max(dp)

nums = [10,9,2,5,3,7,101,18]
print("Solution 1 (DP O(n²)):", lis_dp(nums))  # 4
"""),
code("""# Solution 2: Binary Search (Patience Sorting)
# Time: O(n log n)  Space: O(n)
def lis_binary_search(nums: List[int]) -> int:
    \"\"\"
    tails[i] = smallest ending element of all IS of length i+1.
    Binary search to find position for each new element.
    \"\"\"
    tails = []

    for num in nums:
        pos = bisect.bisect_left(tails, num)  # where does num fit?
        if pos == len(tails):
            tails.append(num)      # extend LIS
        else:
            tails[pos] = num       # replace to keep tails optimal

    return len(tails)

print("Solution 2 (Binary Search):", lis_binary_search(nums))  # 4
print("  tails trace:", end=" ")
tails = []
for n2 in nums:
    pos = bisect.bisect_left(tails, n2)
    if pos == len(tails): tails.append(n2)
    else: tails[pos] = n2
    print(tails, end=" → ")
print()
"""),
code("""# Solution 3: Reconstruct actual LIS (not just length)
# Time: O(n log n)  Space: O(n)
def lis_reconstruct(nums: List[int]):
    \"\"\"Return the actual subsequence, not just length.\"\"\"
    tails = []
    parent = [-1] * len(nums)
    index_map = []  # maps tail position to nums index

    for i, num in enumerate(nums):
        pos = bisect.bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
            index_map.append(i)
        else:
            tails[pos] = num
            index_map[pos] = i
        if pos > 0:
            parent[i] = index_map[pos-1]

    # Reconstruct path
    seq = []
    idx = index_map[-1]
    while idx != -1:
        seq.append(nums[idx])
        idx = parent[idx]
    return list(reversed(seq))

print("Solution 3 (Reconstruct LIS):", lis_reconstruct(nums))
print("\\n⏱ Complexity Summary:")
print("| Solution         | Time      | Space |")
print("|------------------|-----------|-------|")
print("| DP               | O(n²)     | O(n)  |")
print("| Binary Search ✅ | O(n log n)| O(n)  |")
print("| Reconstruct      | O(n log n)| O(n)  |")
"""),

md("""---
## Q1460 · Merge Intervals (Data Structures – MEDIUM)

### Problem
Given array of [start,end] intervals, merge all overlapping intervals.

**Example:** [[1,3],[2,6],[8,10],[15,18]] → [[1,6],[8,10],[15,18]]

---
### 🧠 How to Remember
```
1. SORT by start time
2. Init result with first interval
3. For each interval: if start <= result[-1][1] → EXTEND (merge)
                       else → APPEND new interval
Key: "If new start ≤ last end → overlap → extend the end"
```
"""),
code("""# Solution 1: Sort + Linear Merge (Standard)
# Time: O(n log n)  Space: O(n)
def merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for start, end in intervals[1:]:
        if start <= merged[-1][1]:           # overlap
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

print("Solution 1:", merge_intervals([[1,3],[2,6],[8,10],[15,18]]))
print("Solution 1:", merge_intervals([[1,4],[4,5]]))  # [[1,5]]
"""),
code("""# Solution 2: Using stack
# Time: O(n log n)  Space: O(n)
def merge_intervals_stack(intervals: List[List[int]]) -> List[List[int]]:
    intervals.sort()
    stack = []
    for start, end in intervals:
        if stack and start <= stack[-1][1]:
            stack[-1][1] = max(stack[-1][1], end)
        else:
            stack.append([start, end])
    return stack

print("Solution 2:", merge_intervals_stack([[1,3],[2,6],[8,10],[15,18]]))
"""),
code("""# Solution 3: Functional / one-liner style
# Time: O(n log n)  Space: O(n)
def merge_intervals_func(intervals: List[List[int]]) -> List[List[int]]:
    \"\"\"Reduce-based merge.\"\"\"
    from functools import reduce

    def merge_two(acc, curr):
        if acc and acc[-1][1] >= curr[0]:
            acc[-1] = [acc[-1][0], max(acc[-1][1], curr[1])]
        else:
            acc.append(list(curr))
        return acc

    return reduce(merge_two, sorted(intervals), [])

print("Solution 3:", merge_intervals_func([[1,3],[2,6],[8,10],[15,18]]))
print("\\n⏱ Complexity Summary:")
print("All solutions: Time O(n log n), Space O(n)")
"""),

md("""---
## Q1463 · Avg Trip Time by Zip (Database – HARD)

### Problem
Given `trips` (trip_id, pickup_zip, dropoff_zip, pickup_ts, dropoff_ts),
compute average trip duration in minutes for each zip code pair.
Only include pairs with at least 3 trips.

---
### 🧠 How to Remember
```
1. Calculate duration per trip: (dropoff - pickup) in minutes
2. GROUP BY pickup_zip, dropoff_zip
3. AVG(duration)
4. HAVING COUNT(*) >= 3
```
"""),
code("""conn4.execute(\"\"\"
CREATE TABLE trips (
    trip_id INT, pickup_zip TEXT, dropoff_zip TEXT,
    pickup_ts TEXT, dropoff_ts TEXT
)
\"\"\")
conn4.executemany("INSERT INTO trips VALUES (?,?,?,?,?)", [
    (1,'94105','94102','2023-01-01 10:00','2023-01-01 10:15'),
    (2,'94105','94102','2023-01-01 11:00','2023-01-01 11:20'),
    (3,'94105','94102','2023-01-01 12:00','2023-01-01 12:18'),
    (4,'94102','94105','2023-01-01 13:00','2023-01-01 13:25'),
    (5,'94102','94105','2023-01-01 14:00','2023-01-01 14:22'),
    (6,'94102','94105','2023-01-01 15:00','2023-01-01 15:28'),
    (7,'94105','94107','2023-01-01 16:00','2023-01-01 16:30'),
    (8,'94105','94107','2023-01-01 17:00','2023-01-01 17:35'),
])

# Solution 1: strftime duration + GROUP BY HAVING
sql_trip1 = \"\"\"
SELECT pickup_zip, dropoff_zip,
       COUNT(*) AS trip_count,
       ROUND(AVG(
           (strftime('%s', dropoff_ts) - strftime('%s', pickup_ts)) / 60.0
       ), 1) AS avg_duration_min
FROM trips
GROUP BY pickup_zip, dropoff_zip
HAVING COUNT(*) >= 3
ORDER BY avg_duration_min DESC
\"\"\"
print("Solution 1 - AVG duration (min 3 trips):")
print(pd.read_sql(sql_trip1, conn4))
"""),
code("""# Solution 2: CTE with explicit duration calc + percentiles
sql_trip2 = \"\"\"
WITH durations AS (
    SELECT pickup_zip, dropoff_zip,
           (strftime('%s', dropoff_ts) - strftime('%s', pickup_ts)) / 60.0 AS duration_min
    FROM trips
)
SELECT pickup_zip, dropoff_zip,
       COUNT(*) AS trip_count,
       ROUND(AVG(duration_min), 1) AS avg_min,
       ROUND(MIN(duration_min), 1) AS min_min,
       ROUND(MAX(duration_min), 1) AS max_min
FROM durations
GROUP BY pickup_zip, dropoff_zip
HAVING COUNT(*) >= 2   -- relaxed for demo
ORDER BY avg_min
\"\"\"
print("Solution 2 - With min/max duration:")
print(pd.read_sql(sql_trip2, conn4))
"""),
code("""# Solution 3: Pandas equivalent
df_trips = pd.read_sql("SELECT * FROM trips", conn4)
df_trips['pickup_ts'] = pd.to_datetime(df_trips['pickup_ts'])
df_trips['dropoff_ts'] = pd.to_datetime(df_trips['dropoff_ts'])
df_trips['duration_min'] = (df_trips['dropoff_ts'] - df_trips['pickup_ts']).dt.total_seconds() / 60

grouped = df_trips.groupby(['pickup_zip','dropoff_zip']).agg(
    trip_count=('trip_id','count'),
    avg_duration=('duration_min','mean')
).reset_index()
print("Solution 3 - Pandas:")
print(grouped[grouped['trip_count'] >= 2].round(1))
"""),
]

# ─────────────────────────────────────────────────────────────────
# NOTEBOOK 5  (com5.pdf – Page 5, Q1498–Q1575)
# ─────────────────────────────────────────────────────────────────
nb5_cells = [
md("""# 🟣 Google Data Engineer – Page 5 (Q1498-Q1575)
| # | Title | Category | Difficulty |
|---|-------|----------|-----------|
| Q1498 | Users With Over 3 Friends | SQL | EASY |
| Q1503 | Row-wise Word Totals | SQL | EASY |
| Q1526 | Search Frequency Users | SQL | HARD |
| Q1541 | Two Sum | Python | EASY |
| Q1547 | Extra Characters in a String | Python | MEDIUM |
| Q1559 | Frog Jump | Python | HARD |
| Q1575 | Final Row Without Sorting | SQL | EASY |
"""),

md("""---
## Q1498 · Users With Over 3 Friends (Database – EASY)

### Problem
Given `friendships` (user_id, friend_id), find users who have more than 3 friends.

---
### 🧠 How to Remember
```
1. Edges are directional or bidirectional?
   → UNION both directions first
2. GROUP BY user_id → COUNT friends
3. HAVING COUNT > 3
```
"""),
code("""import sqlite3, pandas as pd

conn5 = sqlite3.connect(":memory:")
conn5.execute("CREATE TABLE friendships (user_id INT, friend_id INT)")
conn5.executemany("INSERT INTO friendships VALUES (?,?)", [
    (1,2),(1,3),(1,4),(1,5),(1,6),  # user 1 has 5 friends
    (2,1),(2,3),(2,4),               # user 2 has 3 (just 1+3+4)
    (3,1),(3,2),(3,4),(3,5),         # user 3 has 4 friends
    (4,1),
])

# Solution 1: Count one direction only
sql_f1 = \"\"\"
SELECT user_id, COUNT(friend_id) AS friend_count
FROM friendships
GROUP BY user_id
HAVING COUNT(friend_id) > 3
ORDER BY friend_count DESC
\"\"\"
print("Solution 1 - One direction:")
print(pd.read_sql(sql_f1, conn5))
"""),
code("""# Solution 2: Bidirectional (symmetrize first)
sql_f2 = \"\"\"
WITH all_edges AS (
    SELECT user_id, friend_id FROM friendships
    UNION
    SELECT friend_id AS user_id, user_id AS friend_id FROM friendships
)
SELECT user_id, COUNT(DISTINCT friend_id) AS friend_count
FROM all_edges
GROUP BY user_id
HAVING COUNT(DISTINCT friend_id) > 3
ORDER BY friend_count DESC
\"\"\"
print("Solution 2 - Bidirectional:")
print(pd.read_sql(sql_f2, conn5))
"""),
code("""# Solution 3: With friend list
sql_f3 = \"\"\"
WITH all_edges AS (
    SELECT user_id, friend_id FROM friendships
    UNION
    SELECT friend_id, user_id FROM friendships
),
friend_counts AS (
    SELECT user_id, COUNT(*) AS friend_count
    FROM all_edges GROUP BY user_id
)
SELECT f.user_id, f.friend_count,
       RANK() OVER (ORDER BY f.friend_count DESC) AS popularity_rank
FROM friend_counts f
WHERE f.friend_count > 3
\"\"\"
print("Solution 3 - With rank:")
print(pd.read_sql(sql_f3, conn5))
"""),

md("""---
## Q1526 · Search Frequency Users (Database – HARD)

### Problem
Given `searches` (user_id, search_id, country, query, num_results, position),
for each country find % of searches with 0 results AND avg position of the top result.

---
### 🧠 How to Remember
```
1. % zero results = SUM(num_results=0) / COUNT(*) * 100
2. avg top position = AVG(position) WHERE position filtered somehow
3. GROUP BY country
```
"""),
code("""conn5.execute(\"\"\"
CREATE TABLE searches (
    user_id INT, search_id INT, country TEXT,
    query TEXT, num_results INT, position INT
)
\"\"\")
conn5.executemany("INSERT INTO searches VALUES (?,?,?,?,?,?)", [
    (1, 1, 'US', 'python',  10, 1),
    (1, 2, 'US', 'java',    0,  None),
    (2, 3, 'US', 'sql',     5,  2),
    (3, 4, 'UK', 'python',  8,  1),
    (3, 5, 'UK', 'nosql',   0,  None),
    (4, 6, 'UK', 'hadoop',  3,  3),
    (5, 7, 'DE', 'spark',   0,  None),
    (5, 8, 'DE', 'kafka',   0,  None),
    (6, 9, 'DE', 'flink',   7,  1),
])

# Solution 1: CASE WHEN aggregation
sql_search1 = \"\"\"
SELECT country,
       COUNT(*) AS total_searches,
       SUM(CASE WHEN num_results = 0 THEN 1 ELSE 0 END) AS zero_result_searches,
       ROUND(100.0 * SUM(CASE WHEN num_results=0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_zero_results,
       ROUND(AVG(CASE WHEN position IS NOT NULL THEN position END), 2) AS avg_top_position
FROM searches
GROUP BY country
ORDER BY pct_zero_results DESC
\"\"\"
print("Solution 1 - Search quality by country:")
print(pd.read_sql(sql_search1, conn5))
"""),
code("""# Solution 2: Separate CTEs for clarity
sql_search2 = \"\"\"
WITH country_stats AS (
    SELECT country,
           COUNT(*) AS total,
           SUM(CASE WHEN num_results = 0 THEN 1 ELSE 0 END) AS zero_results
    FROM searches GROUP BY country
),
pos_stats AS (
    SELECT country, AVG(CAST(position AS REAL)) AS avg_pos
    FROM searches WHERE position IS NOT NULL
    GROUP BY country
)
SELECT c.country, c.total,
       ROUND(100.0 * c.zero_results / c.total, 1) AS pct_zero,
       ROUND(p.avg_pos, 2) AS avg_position
FROM country_stats c
LEFT JOIN pos_stats p ON c.country = p.country
ORDER BY pct_zero DESC
\"\"\"
print("Solution 2 - CTE approach:")
print(pd.read_sql(sql_search2, conn5))
"""),
code("""# Solution 3: Pandas analysis
df_s = pd.read_sql("SELECT * FROM searches", conn5)
result = df_s.groupby('country').agg(
    total_searches=('search_id','count'),
    zero_result_searches=('num_results', lambda x: (x==0).sum()),
    avg_position=('position','mean')
).round(2)
result['pct_zero'] = (result['zero_result_searches'] / result['total_searches'] * 100).round(1)
print("Solution 3 - Pandas:")
print(result.sort_values('pct_zero', ascending=False))
"""),

md("""---
## Q1541 · Two Sum (Data Structures – EASY)

### Problem
Given an array and target, return indices of two numbers that add up to target.

**Example:** nums=[2,7,11,15], target=9 → [0,1]

---
### 🧠 How to Remember
```
LOOKUP TABLE:
1. For each number, ask: "Have I seen (target - num) before?"
2. Store each number in a HashMap {value → index}
3. Return [stored_index, current_index]
MANTRA: "What do I NEED? = target - current. Have I seen it?"
```
"""),
code("""# Solution 1: Brute Force
# Time: O(n²)  Space: O(1)
def two_sum_brute(nums: List[int], target: int) -> List[int]:
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

print("Solution 1:", two_sum_brute([2,7,11,15], 9))   # [0,1]
print("Solution 1:", two_sum_brute([3,2,4], 6))        # [1,2]
"""),
code("""# Solution 2: Sort + Two Pointers (modifies array, returns values not indices)
# Time: O(n log n)  Space: O(n)
def two_sum_two_pointers(nums: List[int], target: int):
    \"\"\"Returns the values (not indices). Sort first.\"\"\"
    indexed = sorted(enumerate(nums), key=lambda x: x[1])
    l, r = 0, len(indexed) - 1
    while l < r:
        s = indexed[l][1] + indexed[r][1]
        if s == target:
            return [indexed[l][0], indexed[r][0]]
        elif s < target:
            l += 1
        else:
            r -= 1
    return []

print("Solution 2:", two_sum_two_pointers([2,7,11,15], 9))
print("Solution 2:", two_sum_two_pointers([3,2,4], 6))
"""),
code("""# Solution 3: HashMap - OPTIMAL for unsorted
# Time: O(n)  Space: O(n)
def two_sum_hashmap(nums: List[int], target: int) -> List[int]:
    seen = {}   # {value: index}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

print("Solution 3:", two_sum_hashmap([2,7,11,15], 9))  # [0,1]
print("Solution 3:", two_sum_hashmap([3,2,4], 6))       # [1,2]
print("Solution 3:", two_sum_hashmap([3,3], 6))         # [0,1]
print("\\n⏱ Complexity Summary:")
print("| Solution       | Time      | Space |")
print("|----------------|-----------|-------|")
print("| Brute          | O(n²)     | O(1)  |")
print("| Two Pointers   | O(n log n)| O(n)  |")
print("| HashMap ✅     | O(n)      | O(n)  |")
"""),

md("""---
## Q1559 · Frog Jump (Algorithms – HARD)

### Problem
A frog starts at stone 0. Each stone has position. The frog can jump from stone with
last jump of k → next jump can be k-1, k, or k+1. Can frog reach last stone?

**Example:** [0,1,3,5,6,8,12,17] → True

---
### 🧠 How to Remember
```
DP with SETS:
1. dp[position] = set of jump sizes that can reach this stone
2. For each stone, try k-1, k, k+1 jumps
3. If next position exists in stones → add jump size to dp[next_pos]
4. Return True if dp[last_stone] is non-empty
```
"""),
code("""# Solution 1: Recursion with memoization
# Time: O(n²)  Space: O(n²)
from functools import lru_cache

def frog_jump_memo(stones: List[int]) -> bool:
    stone_set = set(stones)

    @lru_cache(maxsize=None)
    def can_reach(pos, k):
        if pos == stones[-1]:
            return True
        for jump in [k-1, k, k+1]:
            if jump > 0 and (pos + jump) in stone_set:
                if can_reach(pos + jump, jump):
                    return True
        return False

    return can_reach(0, 0)

print("Solution 1 (Memo):", frog_jump_memo([0,1,3,5,6,8,12,17]))  # True
print("Solution 1:", frog_jump_memo([0,1,2,3,4,8,9,11]))           # False
"""),
code("""# Solution 2: BFS
# Time: O(n²)  Space: O(n²)
from collections import deque

def frog_jump_bfs(stones: List[int]) -> bool:
    stone_set = set(stones)
    target = stones[-1]
    queue = deque([(0, 0)])  # (position, last_jump)
    visited = set([(0, 0)])

    while queue:
        pos, k = queue.popleft()
        for jump in [k-1, k, k+1]:
            if jump <= 0:
                continue
            next_pos = pos + jump
            if next_pos == target:
                return True
            if next_pos in stone_set and (next_pos, jump) not in visited:
                visited.add((next_pos, jump))
                queue.append((next_pos, jump))
    return False

print("Solution 2 (BFS):", frog_jump_bfs([0,1,3,5,6,8,12,17]))  # True
"""),
code("""# Solution 3: DP with sets ← most space-efficient
# Time: O(n²)  Space: O(n)
def frog_jump_dp(stones: List[int]) -> bool:
    \"\"\"dp[pos] = set of jump sizes that can reach pos.\"\"\"
    dp = {stone: set() for stone in stones}
    dp[0].add(0)

    for stone in stones:
        for k in dp[stone]:
            for jump in [k-1, k, k+1]:
                if jump > 0 and (stone + jump) in dp:
                    dp[stone + jump].add(jump)

    return bool(dp[stones[-1]])

print("Solution 3 (DP Sets):", frog_jump_dp([0,1,3,5,6,8,12,17]))  # True
print("Solution 3:", frog_jump_dp([0,1,2,3,4,8,9,11]))              # False
print("\\n⏱ Complexity Summary:")
print("| Solution   | Time  | Space |")
print("|------------|-------|-------|")
print("| Memoization| O(n²) | O(n²) |")
print("| BFS        | O(n²) | O(n²) |")
print("| DP Sets ✅ | O(n²) | O(n)  |")
"""),

md("""---
## Q1575 · Final Row Without Sorting (Database – EASY)

### Problem
Given `records` (id, value, created_at), return the row with the maximum id
WITHOUT using ORDER BY ... LIMIT 1.

---
### 🧠 How to Remember
```
Use MAX() in WHERE or subquery:
WHERE id = (SELECT MAX(id) FROM records)
OR use NOT EXISTS:
WHERE NOT EXISTS (SELECT 1 FROM records r2 WHERE r2.id > records.id)
```
"""),
code("""conn5.execute("CREATE TABLE records (id INT, value TEXT, created_at TEXT)")
conn5.executemany("INSERT INTO records VALUES (?,?,?)", [
    (1,'alpha','2023-01-01'),
    (2,'beta', '2023-01-02'),
    (3,'gamma','2023-01-03'),
    (4,'delta','2023-01-04'),
])

# Solution 1: Subquery MAX
sql_last1 = \"\"\"
SELECT * FROM records
WHERE id = (SELECT MAX(id) FROM records)
\"\"\"
print("Solution 1 - MAX() subquery:")
print(pd.read_sql(sql_last1, conn5))
"""),
code("""# Solution 2: NOT EXISTS (no row has higher id)
sql_last2 = \"\"\"
SELECT r1.* FROM records r1
WHERE NOT EXISTS (
    SELECT 1 FROM records r2 WHERE r2.id > r1.id
)
\"\"\"
print("Solution 2 - NOT EXISTS:")
print(pd.read_sql(sql_last2, conn5))
"""),
code("""# Solution 3: ALL comparison
sql_last3 = \"\"\"
SELECT * FROM records
WHERE id >= ALL(SELECT id FROM records)
\"\"\"
print("Solution 3 - ALL comparison:")
try:
    print(pd.read_sql(sql_last3, conn5))
except Exception as e:
    # SQLite may not support ALL; fallback
    print("(SQLite limitation - works in PostgreSQL/MySQL)")
    print(pd.read_sql("SELECT * FROM records WHERE id = (SELECT MAX(id) FROM records)", conn5))
"""),
]

# ─────────────────────────────────────────────────────────────────
# Write all notebooks
# ─────────────────────────────────────────────────────────────────
notebooks = {
    "Google_DE_Page1_Q1_Q411.ipynb": nb(nb1_cells),
    "Google_DE_Page2_Q420_Q709.ipynb": nb(nb2_cells),
    "Google_DE_Page3_Q711_Q1111.ipynb": nb(nb3_cells),
    "Google_DE_Page4_Q1112_Q1489.ipynb": nb(nb4_cells),
    "Google_DE_Page5_Q1498_Q1575.ipynb": nb(nb5_cells),
}

for fname, notebook in notebooks.items():
    with open(fname, 'w') as f:
        json.dump(notebook, f, indent=1)
    print(f"✅ Created: {fname}")

print("\nAll notebooks created!")
