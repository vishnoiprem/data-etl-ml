import json, os

def nb(cells):
    return {"nbformat":4,"nbformat_minor":5,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.9.0"}},"cells":cells}

def md(src): return {"cell_type":"markdown","id":os.urandom(4).hex(),"metadata":{},"source":src}
def code(src): return {"cell_type":"code","id":os.urandom(4).hex(),"execution_count":None,"metadata":{},"outputs":[],"source":src}

cells = []

# ─── Title ───────────────────────────────────────────────────────────────────
cells.append(md("""# Google Data Engineer Interview Prep — Page 5 (Q1498–Q1575)
**Topics:** SQL (sqlite3 + pandas), Algorithms, Data Structures, Statistics, Data Engineering
**Coverage:** 23 questions × 3 solutions each
*All code cells run and print output. Time & Space complexity included for every solution.*"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1498 — Users With Over 3 Friends
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1498 · Users With Over 3 Friends (Database · EASY)

**Problem:** Given a `Friendship` table with `(user1_id, user2_id)` pairs (each pair stored once),
find every user who has **strictly more than 3** friends.

**Example:**
```
user1_id | user2_id
---------|----------
1        | 2
1        | 3
1        | 4
1        | 5
2        | 3
```
User 1 appears 4 times → output user 1.

🧠 **How to Remember:** "HAVING COUNT > 3 — HAVING is WHERE for groups; COUNT both directions because friendship is symmetric."
"""))

cells.append(code("""import sqlite3, pandas as pd

# ── Setup ──────────────────────────────────────────────────────────────────
con = sqlite3.connect(":memory:")
con.executescript(\"\"\"
CREATE TABLE Friendship(user1_id INT, user2_id INT);
INSERT INTO Friendship VALUES
  (1,2),(1,3),(1,4),(1,5),
  (2,3),(2,6),(3,6),(4,5),(4,6),(5,6);
\"\"\")

print("=== Friendship Table ===")
print(pd.read_sql("SELECT * FROM Friendship", con))
"""))

cells.append(code("""# ── Solution 1: UNION ALL + HAVING ────────────────────────────────────────
q1 = \"\"\"
SELECT user_id, COUNT(*) AS friend_count
FROM (
    SELECT user1_id AS user_id FROM Friendship
    UNION ALL
    SELECT user2_id AS user_id FROM Friendship
) t
GROUP BY user_id
HAVING COUNT(*) > 3
ORDER BY user_id;
\"\"\"
print("Solution 1 — UNION ALL + HAVING:")
print(pd.read_sql(q1, con))
print()

# Time: O(N log N) — GROUP BY sort; Space: O(N)
print("Time: O(N log N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 2: CTE with bidirectional edges ──────────────────────────────
q2 = \"\"\"
WITH all_edges AS (
    SELECT user1_id AS uid FROM Friendship
    UNION ALL
    SELECT user2_id  AS uid FROM Friendship
)
SELECT uid AS user_id, COUNT(*) AS friend_count
FROM all_edges
GROUP BY uid
HAVING COUNT(*) > 3
ORDER BY user_id;
\"\"\"
print("Solution 2 — CTE bidirectional:")
print(pd.read_sql(q2, con))
print()
print("Time: O(N log N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 3: Pandas pure-Python ────────────────────────────────────────
import pandas as pd

df = pd.read_sql("SELECT * FROM Friendship", con)
# Combine both directions
both = pd.concat([df['user1_id'].rename('uid'), df['user2_id'].rename('uid')])
result = both.value_counts().reset_index()
result.columns = ['user_id', 'friend_count']
result = result[result['friend_count'] > 3].sort_values('user_id')
print("Solution 3 — Pandas:")
print(result.to_string(index=False))
print()
print("Time: O(N log N) | Space: O(N)")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1503 — Row-wise Word Totals
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1503 · Row-wise Word Totals (Database · EASY)

**Problem:** Given a table `Posts(post_id, content)` count the number of words (space-separated tokens) in each row's `content`.

**Example:**
```
post_id | content
--------|--------------------
1       | "Hello World"
2       | "one two three four"
3       | "single"
```
Expected: 2, 4, 1

🧠 **How to Remember:** "Word count = length minus spaces + 1; or split and count tokens."
"""))

cells.append(code("""con2 = sqlite3.connect(":memory:")
con2.executescript(\"\"\"
CREATE TABLE Posts(post_id INT, content TEXT);
INSERT INTO Posts VALUES
  (1,'Hello World'),
  (2,'one two three four'),
  (3,'single'),
  (4,'The quick brown fox jumps'),
  (5,'');
\"\"\")
print("=== Posts Table ===")
print(pd.read_sql("SELECT * FROM Posts", con2))
"""))

cells.append(code("""# ── Solution 1: SQLite LENGTH trick ───────────────────────────────────────
# words = len(content) - len(content without spaces) + 1 (unless empty)
q = \"\"\"
SELECT post_id,
       content,
       CASE
           WHEN TRIM(content) = '' THEN 0
           ELSE LENGTH(TRIM(content)) - LENGTH(REPLACE(TRIM(content),' ','')) + 1
       END AS word_count
FROM Posts
ORDER BY post_id;
\"\"\"
print("Solution 1 — LENGTH trick:")
print(pd.read_sql(q, con2))
print("Time: O(N*L) | Space: O(1) per row")
"""))

cells.append(code("""# ── Solution 2: Pandas str.split().str.len() ──────────────────────────────
df = pd.read_sql("SELECT * FROM Posts", con2)
df['word_count'] = df['content'].str.strip().apply(
    lambda x: len(x.split()) if x.strip() else 0)
print("Solution 2 — Pandas split:")
print(df[['post_id','content','word_count']].to_string(index=False))
print("Time: O(N*L) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 3: Python regex word tokeniser ────────────────────────────────
import re
df2 = pd.read_sql("SELECT * FROM Posts", con2)
df2['word_count'] = df2['content'].apply(lambda x: len(re.findall(r'\\S+', x)))
print("Solution 3 — regex \\\\S+:")
print(df2[['post_id','content','word_count']].to_string(index=False))
print("Time: O(N*L) | Space: O(N)")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1504 — Cherry Pickup II
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1504 · Cherry Pickup II (Algorithms · HARD)

**Problem:** Two robots start at `(0,0)` and `(0,cols-1)` of an `rows×cols` grid.
Each step both move down one row and shift ±1 or stay. Collect maximum cherries without double-counting same cell.

**Example:** grid = [[3,1,1],[2,5,1],[1,5,5],[2,1,1]] → 24

🧠 **How to Remember:** "3-D DP: row × col1 × col2. At each row advance both robots simultaneously."
"""))

cells.append(code("""# ── Solution 1: Top-down DP with memoisation ──────────────────────────────
from functools import lru_cache

def cherry_pickup_memo(grid):
    rows, cols = len(grid), len(grid[0])
    @lru_cache(maxsize=None)
    def dp(r, c1, c2):
        if r == rows: return 0
        cherries = grid[r][c1] + (grid[r][c2] if c2 != c1 else 0)
        best = 0
        for dc1 in (-1,0,1):
            for dc2 in (-1,0,1):
                nc1, nc2 = c1+dc1, c2+dc2
                if 0 <= nc1 < cols and 0 <= nc2 < cols:
                    best = max(best, dp(r+1, nc1, nc2))
        return cherries + best
    return dp(0, 0, cols-1)

grid1 = [[3,1,1],[2,5,1],[1,5,5],[2,1,1]]
grid2 = [[1,0,0,0,0,0,1],[2,0,0,0,0,3,0],[2,0,9,0,0,0,0],[0,3,0,5,4,0,0],[1,0,2,3,0,0,6]]
print(f"Solution 1 (memo) grid1 = {cherry_pickup_memo(grid1)}  expected 24")
print(f"Solution 1 (memo) grid2 = {cherry_pickup_memo(grid2)}  expected 28")
print("Time: O(rows * cols^2 * 9) | Space: O(rows * cols^2)")
"""))

cells.append(code("""# ── Solution 2: Bottom-up 3-D DP ──────────────────────────────────────────
def cherry_pickup_bottom_up(grid):
    rows, cols = len(grid), len(grid[0])
    NEG = float('-inf')
    # dp[c1][c2] = max cherries from current row onward
    dp = [[NEG]*cols for _ in range(cols)]
    dp[0][cols-1] = grid[0][0] + grid[0][cols-1]

    for r in range(1, rows):
        ndp = [[NEG]*cols for _ in range(cols)]
        for c1 in range(cols):
            for c2 in range(cols):
                if dp[c1][c2] == NEG: continue
                for dc1 in (-1,0,1):
                    for dc2 in (-1,0,1):
                        nc1, nc2 = c1+dc1, c2+dc2
                        if 0 <= nc1 < cols and 0 <= nc2 < cols:
                            gain = grid[r][nc1] + (grid[r][nc2] if nc1!=nc2 else 0)
                            ndp[nc1][nc2] = max(ndp[nc1][nc2], dp[c1][c2]+gain)
        dp = ndp
    return max(dp[c1][c2] for c1 in range(cols) for c2 in range(cols) if dp[c1][c2]!=NEG)

print(f"Solution 2 (bottom-up) grid1 = {cherry_pickup_bottom_up(grid1)}  expected 24")
print(f"Solution 2 (bottom-up) grid2 = {cherry_pickup_bottom_up(grid2)}  expected 28")
print("Time: O(rows * cols^2 * 9) | Space: O(cols^2)")
"""))

cells.append(code("""# ── Solution 3: Space-optimised with numpy ─────────────────────────────────
import numpy as np

def cherry_pickup_numpy(grid):
    rows, cols = len(grid), len(grid[0])
    INF = -10**9
    dp = np.full((cols, cols), INF, dtype=float)
    dp[0, cols-1] = grid[0][0] + grid[0][cols-1]
    for r in range(1, rows):
        ndp = np.full((cols, cols), INF, dtype=float)
        for dc1 in (-1,0,1):
            for dc2 in (-1,0,1):
                # shift dp by dc1/dc2 along axes
                shifted = np.roll(np.roll(dp, dc1, axis=0), dc2, axis=1)
                # zero out wrapped entries
                if dc1 == 1:  shifted[0, :] = INF
                elif dc1 == -1: shifted[-1, :] = INF
                if dc2 == 1:  shifted[:, 0] = INF
                elif dc2 == -1: shifted[:, -1] = INF
                gain = np.full((cols,cols), 0.0)
                for c1 in range(cols):
                    for c2 in range(cols):
                        gain[c1,c2] = grid[r][c1] + (grid[r][c2] if c1!=c2 else 0)
                ndp = np.maximum(ndp, shifted + gain)
        dp = ndp
    return int(dp.max())

print(f"Solution 3 (numpy) grid1 = {cherry_pickup_numpy(grid1)}  expected 24")
print(f"Solution 3 (numpy) grid2 = {cherry_pickup_numpy(grid2)}  expected 28")
print()
print("| Solution     | Time            | Space    |")
print("|--------------|-----------------|----------|")
print("| Memoisation  | O(R*C^2*9)      | O(R*C^2) |")
print("| Bottom-up    | O(R*C^2*9)      | O(C^2)   |")
print("| NumPy shift  | O(R*C^2*9)      | O(C^2)   |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1505 — Uncrossed Lines
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1505 · Uncrossed Lines (Algorithms · MEDIUM)

**Problem:** Draw lines connecting equal numbers between two arrays `A` and `B` such that lines do not cross. Return maximum lines.

*This is identical to Longest Common Subsequence (LCS).*

🧠 **How to Remember:** "Uncrossed lines = LCS. Lines can't cross ↔ order must be preserved."
"""))

cells.append(code("""# ── Solution 1: Classic 2-D DP (LCS) ──────────────────────────────────────
def max_uncrossed_lines_2d(A, B):
    m, n = len(A), len(B)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if A[i-1] == B[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]

A1,B1 = [1,4,2],[1,2,4]
A2,B2 = [2,5,1,2,5],[10,5,2,1,5,2]
A3,B3 = [1,3,7,1,7,5],[1,9,2,5,1]

print(f"Test1: {max_uncrossed_lines_2d(A1,B1)}  expected 2")
print(f"Test2: {max_uncrossed_lines_2d(A2,B2)}  expected 3")
print(f"Test3: {max_uncrossed_lines_2d(A3,B3)}  expected 2")
print("Time: O(M*N) | Space: O(M*N)")
"""))

cells.append(code("""# ── Solution 2: Space-optimised 1-D DP ────────────────────────────────────
def max_uncrossed_lines_1d(A, B):
    n = len(B)
    prev = [0]*(n+1)
    for a in A:
        curr = [0]*(n+1)
        for j,b in enumerate(B,1):
            if a == b:
                curr[j] = prev[j-1]+1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev = curr
    return prev[n]

print(f"Test1: {max_uncrossed_lines_1d(A1,B1)}  expected 2")
print(f"Test2: {max_uncrossed_lines_1d(A2,B2)}  expected 3")
print(f"Test3: {max_uncrossed_lines_1d(A3,B3)}  expected 2")
print("Time: O(M*N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 3: difflib SequenceMatcher (LCS via longest block) ────────────
from difflib import SequenceMatcher

def max_uncrossed_lines_seq(A, B):
    # SequenceMatcher finds matching blocks; sum their sizes = LCS length
    sm = SequenceMatcher(None, A, B, autojunk=False)
    return sum(block.size for block in sm.get_matching_blocks())

print(f"Test1: {max_uncrossed_lines_seq(A1,B1)}  expected 2")
print(f"Test2: {max_uncrossed_lines_seq(A2,B2)}  expected 3")
print(f"Test3: {max_uncrossed_lines_seq(A3,B3)}  expected 2")
print()
print("| Solution           | Time    | Space |")
print("|--------------------|---------|-------|")
print("| 2-D DP             | O(M*N)  | O(M*N)|")
print("| 1-D DP             | O(M*N)  | O(N)  |")
print("| SequenceMatcher    | O(M*N)  | O(N)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1508 — Reconstruct Itinerary
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1508 · Reconstruct Itinerary (Data Structures · HARD)

**Problem:** Given a list of airline tickets `[from, to]`, reconstruct the full itinerary starting from `"JFK"`. Use all tickets exactly once; when multiple valid itineraries exist, return the lexicographically smallest one.

**Example:** tickets = [["MUC","LHR"],["JFK","MUC"],["SFO","SJC"],["LHR","SFO"]] → ["JFK","MUC","LHR","SFO","SJC"]

🧠 **How to Remember:** "Hierholzer's algorithm: DFS + post-order append + reverse. Sort adjacency lists for lex order."
"""))

cells.append(code("""from collections import defaultdict

# ── Solution 1: Hierholzer's (iterative DFS) ──────────────────────────────
def find_itinerary_hierholzer(tickets):
    graph = defaultdict(list)
    for src, dst in sorted(tickets, reverse=True):  # reverse sort so pop() gives lex-smallest
        graph[src].append(dst)
    path, stack = [], ['JFK']
    while stack:
        while graph[stack[-1]]:
            stack.append(graph[stack[-1]].pop())
        path.append(stack.pop())
    return path[::-1]

t1 = [["MUC","LHR"],["JFK","MUC"],["SFO","SJC"],["LHR","SFO"]]
t2 = [["JFK","SFO"],["JFK","ATL"],["SFO","ATL"],["ATL","JFK"],["ATL","SFO"]]
print("Test1:", find_itinerary_hierholzer(t1))
print("Test2:", find_itinerary_hierholzer(t2))
print("Time: O(E log E) sort | Space: O(E)")
"""))

cells.append(code("""import heapq

# ── Solution 2: Min-heap adjacency list (always pops smallest) ─────────────
def find_itinerary_heap(tickets):
    graph = defaultdict(list)
    for src, dst in tickets:
        heapq.heappush(graph[src], dst)
    path, stack = [], ['JFK']
    while stack:
        while graph[stack[-1]]:
            stack.append(heapq.heappop(graph[stack[-1]]))
        path.append(stack.pop())
    return path[::-1]

print("Test1:", find_itinerary_heap(t1))
print("Test2:", find_itinerary_heap(t2))
print("Time: O(E log E) | Space: O(E)")
"""))

cells.append(code("""# ── Solution 3: Recursive DFS (Euler path) ────────────────────────────────
def find_itinerary_recursive(tickets):
    graph = defaultdict(list)
    for src, dst in sorted(tickets):  # sort for lex order
        graph[src].append(dst)
    # convert lists to sorted deques
    from collections import deque
    for k in graph:
        graph[k] = deque(sorted(graph[k]))
    result = []
    def dfs(node):
        while graph[node]:
            dfs(graph[node].popleft())
        result.append(node)
    dfs('JFK')
    return result[::-1]

print("Test1:", find_itinerary_recursive(t1))
print("Test2:", find_itinerary_recursive(t2))
print()
print("| Solution      | Time        | Space |")
print("|---------------|-------------|-------|")
print("| Hierholzer    | O(E log E)  | O(E)  |")
print("| Min-heap      | O(E log E)  | O(E)  |")
print("| Recursive DFS | O(E log E)  | O(E)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1510 — Rows With g-Prefixed Words
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1510 · Rows With g-Prefixed Words (Database · MEDIUM)

**Problem:** Find all rows in a `Posts` table where the `content` contains at least one word starting with the letter `'g'` (case-insensitive).

🧠 **How to Remember:** "LIKE '% g%' catches mid-string; OR LIKE 'g%' catches start. Combine for full match."
"""))

cells.append(code("""con3 = sqlite3.connect(":memory:")
con3.executescript(\"\"\"
CREATE TABLE Post(post_id INT, content TEXT);
INSERT INTO Post VALUES
  (1,'google is great'),
  (2,'hello world'),
  (3,'good morning everyone'),
  (4,'The data engineer guru'),
  (5,'no match here'),
  (6,'Graph theory is fascinating');
\"\"\")
print(pd.read_sql("SELECT * FROM Post", con3))
"""))

cells.append(code("""# ── Solution 1: LIKE with word-boundary pattern ───────────────────────────
q = \"\"\"
SELECT post_id, content
FROM Post
WHERE content LIKE 'g%'
   OR content LIKE '% g%'
   OR content LIKE 'G%'
   OR content LIKE '% G%'
ORDER BY post_id;
\"\"\"
print("Solution 1 — LIKE patterns:")
print(pd.read_sql(q, con3))
print("Time: O(N*L) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: REGEXP via Python sqlite3 function ────────────────────────
import re
con3.create_function("REGEXP", 2, lambda pat, val: bool(re.search(pat, val or '', re.IGNORECASE)))
q2 = \"\"\"
SELECT post_id, content
FROM Post
WHERE REGEXP('\\\\bg', content)
ORDER BY post_id;
\"\"\"
print("Solution 2 — REGEXP \\\\bg:")
print(pd.read_sql(q2, con3))
print("Time: O(N*L) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: Pandas str contains word boundary ─────────────────────────
df = pd.read_sql("SELECT * FROM Post", con3)
mask = df['content'].str.contains(r'\\bg', case=False, regex=True)
print("Solution 3 — pandas regex:")
print(df[mask][['post_id','content']].to_string(index=False))
print("Time: O(N*L) | Space: O(N)")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1520 — Nontransitive Dice Simulator
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1520 · Nontransitive Dice Simulator (Statistics · MEDIUM)

**Problem:** Three dice A, B, C satisfy A > B, B > C, C > A (nontransitive). Simulate N rolls and verify/demonstrate the paradox.

**Classic example:**
- A = [2,2,4,4,9,9]
- B = [1,1,6,6,8,8]
- C = [3,3,5,5,7,7]

🧠 **How to Remember:** "Rock-Paper-Scissors with dice. Monte Carlo reveals the cycle: A beats B beats C beats A."
"""))

cells.append(code("""import random, numpy as np
from itertools import product

# ── Solution 1: Monte Carlo simulation ────────────────────────────────────
def simulate_nontransitive(dice, n=100_000, seed=42):
    random.seed(seed)
    results = {}
    names = list(dice.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a_name, b_name = names[i], names[j]
            a_wins = sum(random.choice(dice[a_name]) > random.choice(dice[b_name]) for _ in range(n))
            results[f"{a_name}>{b_name}"] = a_wins/n
    return results

dice = {'A':[2,2,4,4,9,9], 'B':[1,1,6,6,8,8], 'C':[3,3,5,5,7,7]}
res = simulate_nontransitive(dice)
print("Solution 1 — Monte Carlo (100k rolls):")
for k,v in res.items():
    print(f"  P({k}) = {v:.4f}  {'← A wins' if v>0.5 else '← B wins'}")
print()
print("Time: O(N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: Exact probability via enumeration ─────────────────────────
def exact_win_prob(d1, d2):
    wins = sum(1 for a,b in product(d1,d2) if a>b)
    return wins / (len(d1)*len(d2))

print("Solution 2 — Exact enumeration:")
pairs = [('A','B'),('B','C'),('C','A')]
for a,b in pairs:
    p = exact_win_prob(dice[a], dice[b])
    print(f"  P({a}>{b}) = {p:.6f}  (Nontransitive: {a} beats {b})" if p>0.5 else f"  P({a}>{b}) = {p:.6f}")
print()
print("Time: O(|d1|*|d2|) per pair | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: Vectorised numpy comparison ───────────────────────────────
def np_win_prob(d1, d2, n=200_000, seed=99):
    rng = np.random.default_rng(seed)
    a = rng.choice(d1, n)
    b = rng.choice(d2, n)
    return (a > b).mean()

print("Solution 3 — NumPy vectorised:")
for a,b in pairs:
    p = np_win_prob(dice[a], dice[b])
    print(f"  P({a}>{b}) = {p:.4f}")
print()
print("| Solution     | Time      | Space  |")
print("|--------------|-----------|--------|")
print("| Monte Carlo  | O(N)      | O(1)   |")
print("| Enumeration  | O(|d|^2)  | O(1)   |")
print("| NumPy        | O(N)      | O(N)   |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1526 — Search Frequency Users
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1526 · Search Frequency Users (Database · HARD)

**Problem:** Given a `Searches` table with `(user_id, query, results, position, country)`, compute:
1. Percentage of zero-result searches per country
2. Average click position for non-zero-result searches, grouped by country

🧠 **How to Remember:** "CASE WHEN + AVG is the SQL way to compute conditional aggregates in one pass."
"""))

cells.append(code("""con4 = sqlite3.connect(":memory:")
con4.executescript(\"\"\"
CREATE TABLE Searches(user_id INT, query TEXT, results INT, position INT, country TEXT);
INSERT INTO Searches VALUES
  (1,'python',10,3,'US'),(1,'java',0,NULL,'US'),(2,'sql',5,1,'UK'),
  (2,'nosql',0,NULL,'UK'),(3,'spark',8,2,'US'),(3,'kafka',0,NULL,'US'),
  (4,'flink',3,4,'DE'),(4,'airflow',0,NULL,'DE'),(5,'dbt',7,1,'US'),
  (5,'prefect',2,5,'US'),(6,'looker',0,NULL,'UK'),(6,'tableau',6,2,'UK');
\"\"\")
print(pd.read_sql("SELECT * FROM Searches", con4))
"""))

cells.append(code("""# ── Solution 1: CASE WHEN aggregates ──────────────────────────────────────
q = \"\"\"
SELECT country,
       COUNT(*) AS total_searches,
       SUM(CASE WHEN results=0 THEN 1 ELSE 0 END) AS zero_results,
       ROUND(100.0*SUM(CASE WHEN results=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS zero_pct,
       ROUND(AVG(CASE WHEN results>0 THEN position END),2) AS avg_click_position
FROM Searches
GROUP BY country
ORDER BY country;
\"\"\"
print("Solution 1 — CASE WHEN:")
print(pd.read_sql(q, con4).to_string(index=False))
print("Time: O(N log N) | Space: O(K) K=countries")
"""))

cells.append(code("""# ── Solution 2: Two CTEs — zero-results and avg position ─────────────────
q2 = \"\"\"
WITH zero AS (
    SELECT country, COUNT(*) AS zero_cnt
    FROM Searches WHERE results=0 GROUP BY country
),
total AS (
    SELECT country, COUNT(*) AS total_cnt,
           AVG(CASE WHEN results>0 THEN CAST(position AS FLOAT) END) AS avg_pos
    FROM Searches GROUP BY country
)
SELECT t.country, t.total_cnt, COALESCE(z.zero_cnt,0) AS zero_cnt,
       ROUND(100.0*COALESCE(z.zero_cnt,0)/t.total_cnt,2) AS zero_pct,
       ROUND(t.avg_pos,2) AS avg_click_position
FROM total t LEFT JOIN zero z ON t.country=z.country
ORDER BY t.country;
\"\"\"
print("Solution 2 — Two CTEs:")
print(pd.read_sql(q2, con4).to_string(index=False))
print("Time: O(N log N) | Space: O(K)")
"""))

cells.append(code("""# ── Solution 3: Pandas groupby agg ───────────────────────────────────────
df = pd.read_sql("SELECT * FROM Searches", con4)
agg = df.groupby('country').apply(lambda g: pd.Series({
    'total': len(g),
    'zero_cnt': (g['results']==0).sum(),
    'zero_pct': round(100*(g['results']==0).mean(),2),
    'avg_click_pos': round(g.loc[g['results']>0,'position'].mean(),2)
})).reset_index()
print("Solution 3 — Pandas:")
print(agg.to_string(index=False))
print("Time: O(N log N) | Space: O(N)")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1528 — Determine if String Halves Are Alike
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1528 · Determine if String Halves Are Alike (Algorithms · EASY)

**Problem:** Split string `s` (even length) in half. Return `True` if both halves have equal number of vowels (aeiouAEIOU).

🧠 **How to Remember:** "Count vowels in left half, count in right half — equal means alike. Set intersection for speed."
"""))

cells.append(code("""# ── Solution 1: Two-pass count ────────────────────────────────────────────
def halves_alike_count(s):
    vowels = set('aeiouAEIOU')
    mid = len(s)//2
    return sum(c in vowels for c in s[:mid]) == sum(c in vowels for c in s[mid:])

tests = [("book","True"),("textbook","False"),("AbCdEfGh","True"),("MerryChristmas","False")]
print("Solution 1 — two-pass count:")
for s,exp in tests:
    print(f"  '{s}' → {halves_alike_count(s)}  expected {exp}")
print("Time: O(N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: Single pass with signed counter ───────────────────────────
def halves_alike_signed(s):
    vowels = set('aeiouAEIOU')
    mid, n = len(s)//2, len(s)
    count = 0
    for i,c in enumerate(s):
        if c in vowels:
            count += 1 if i < mid else -1
    return count == 0

print("Solution 2 — signed counter:")
for s,exp in tests:
    print(f"  '{s}' → {halves_alike_signed(s)}  expected {exp}")
print("Time: O(N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: Counter intersection ─────────────────────────────────────
from collections import Counter

def halves_alike_counter(s):
    vowels = 'aeiouAEIOU'
    mid = len(s)//2
    l = sum(1 for c in s[:mid] if c in vowels)
    r = sum(1 for c in s[mid:] if c in vowels)
    return l == r

print("Solution 3 — Counter approach:")
for s,exp in tests:
    print(f"  '{s}' → {halves_alike_counter(s)}  expected {exp}")
print()
print("| Solution       | Time | Space |")
print("|----------------|------|-------|")
print("| Two-pass count | O(N) | O(1)  |")
print("| Signed counter | O(N) | O(1)  |")
print("| Counter        | O(N) | O(1)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1532 — Count of Smaller Numbers After Self
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1532 · Count of Smaller Numbers After Self (Data Structures · HARD)

**Problem:** Given array `nums`, for each element return the count of smaller numbers to its right.

**Example:** [5,2,6,1] → [2,1,1,0]

🧠 **How to Remember:** "Merge sort counts during merge phase. BIT (Fenwick tree) counts prefix sums in rank-compressed array."
"""))

cells.append(code("""# ── Solution 1: Merge Sort ─────────────────────────────────────────────────
def count_smaller_mergesort(nums):
    n = len(nums)
    counts = [0]*n
    indexed = list(enumerate(nums))

    def merge_sort(arr):
        if len(arr) <= 1: return arr
        mid = len(arr)//2
        left = merge_sort(arr[:mid])
        right = merge_sort(arr[mid:])
        merged, j = [], 0
        for i, (idx, val) in enumerate(left):
            while j < len(right) and right[j][1] < val:
                merged.append(right[j]); j += 1
            counts[idx] += j
            merged.append((idx,val))
        merged.extend(right[j:])
        return merged

    merge_sort(indexed)
    return counts

tests_cs = [
    ([5,2,6,1], [2,1,1,0]),
    ([2,0,1],   [2,0,0]),
    ([1],       [0]),
]
print("Solution 1 — Merge Sort:")
for inp, exp in tests_cs:
    out = count_smaller_mergesort(inp[:])
    print(f"  {inp} → {out}  expected {exp}  {'OK' if out==exp else 'FAIL'}")
print("Time: O(N log N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 2: Binary Indexed Tree (Fenwick Tree) ────────────────────────
def count_smaller_bit(nums):
    # coordinate compress
    sorted_unique = sorted(set(nums))
    rank = {v:i+1 for i,v in enumerate(sorted_unique)}
    m = len(sorted_unique)
    bit = [0]*(m+1)

    def update(i):
        while i <= m: bit[i] += 1; i += i & (-i)

    def query(i):
        s = 0
        while i > 0: s += bit[i]; i -= i & (-i)
        return s

    counts = []
    for num in reversed(nums):
        r = rank[num]
        counts.append(query(r-1))
        update(r)
    return counts[::-1]

print("Solution 2 — Fenwick Tree (BIT):")
for inp, exp in tests_cs:
    out = count_smaller_bit(inp[:])
    print(f"  {inp} → {out}  expected {exp}  {'OK' if out==exp else 'FAIL'}")
print("Time: O(N log N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 3: SortedList (bisect) ──────────────────────────────────────
from sortedcontainers import SortedList

def count_smaller_sorted_list(nums):
    sl = SortedList()
    counts = []
    for num in reversed(nums):
        counts.append(sl.bisect_left(num))
        sl.add(num)
    return counts[::-1]

print("Solution 3 — SortedList bisect:")
for inp, exp in tests_cs:
    out = count_smaller_sorted_list(inp[:])
    print(f"  {inp} → {out}  expected {exp}  {'OK' if out==exp else 'FAIL'}")
print()
print("| Solution      | Time       | Space |")
print("|---------------|------------|-------|")
print("| Merge Sort    | O(N log N) | O(N)  |")
print("| BIT/Fenwick   | O(N log N) | O(N)  |")
print("| SortedList    | O(N log N) | O(N)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1533 — M/M/1 Queue Simulator
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1533 · M/M/1 Queue Simulator (Statistics · MEDIUM)

**Problem:** Simulate an M/M/1 queue with arrival rate λ and service rate μ. Compute:
- Average queue length (Lq)
- Average waiting time (Wq)
- Utilisation ρ = λ/μ

**Theory:** ρ = λ/μ; Lq = ρ²/(1−ρ); Wq = ρ/(μ(1−ρ)) (Little's Law)

🧠 **How to Remember:** "M/M/1: Markovian arrivals, Markovian service, 1 server. ρ < 1 for stability."
"""))

cells.append(code("""import numpy as np

# ── Solution 1: Event-driven simulation ───────────────────────────────────
def mm1_simulation(lam, mu, n_customers=10000, seed=42):
    rng = np.random.default_rng(seed)
    inter_arrivals = rng.exponential(1/lam, n_customers)
    service_times  = rng.exponential(1/mu,  n_customers)

    arrival = np.cumsum(inter_arrivals)
    departure = np.zeros(n_customers)
    wait = np.zeros(n_customers)

    departure[0] = arrival[0] + service_times[0]
    for i in range(1, n_customers):
        start = max(arrival[i], departure[i-1])
        wait[i] = start - arrival[i]
        departure[i] = start + service_times[i]

    rho_sim = lam/mu
    rho_theory = lam/mu
    lq_sim = (wait > 0).mean() * (lam/mu)**2/(1-lam/mu) # approx
    wq_sim = wait.mean()
    wq_theory = (lam/mu)/(mu*(1-lam/mu))
    print(f"  λ={lam}, μ={mu}, ρ={rho_theory:.2f}")
    print(f"  Wq simulated={wq_sim:.4f}  theory={wq_theory:.4f}")
    return wq_sim

print("Solution 1 — Event-driven simulation:")
mm1_simulation(0.5, 1.0)
mm1_simulation(0.8, 1.0)
print("Time: O(N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 2: Little's Law verification ─────────────────────────────────
def mm1_littles_law(lam, mu):
    rho = lam/mu
    assert rho < 1, f"Queue unstable: rho={rho}"
    Lq = rho**2 / (1-rho)
    Wq = Lq / lam          # Little's Law: L = λ * W
    L  = rho / (1-rho)
    W  = L / lam
    print(f"  λ={lam}, μ={mu}")
    print(f"  ρ={rho:.4f}  L={L:.4f}  Lq={Lq:.4f}  W={W:.4f}  Wq={Wq:.4f}")

print("Solution 2 — Analytical (Little's Law):")
mm1_littles_law(0.5, 1.0)
mm1_littles_law(0.8, 1.0)
print("Time: O(1) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: SimPy discrete-event simulation ───────────────────────────
try:
    import simpy
    HAS_SIMPY = True
except ImportError:
    HAS_SIMPY = False

if HAS_SIMPY:
    import simpy, random as rnd

    def mm1_simpy(lam, mu, n=5000, seed=0):
        rnd.seed(seed)
        waits = []
        def customer(env, server):
            arr = env.now
            with server.request() as req:
                yield req
                waits.append(env.now - arr)
                yield env.timeout(rnd.expovariate(mu))
        def source(env, server):
            for _ in range(n):
                yield env.timeout(rnd.expovariate(lam))
                env.process(customer(env, server))
        env = simpy.Environment()
        server = simpy.Resource(env, capacity=1)
        env.process(source(env, server))
        env.run()
        print(f"  SimPy Wq={sum(waits)/len(waits):.4f}  theory={(lam/mu)/(mu*(1-lam/mu)):.4f}")

    print("Solution 3 — SimPy:")
    mm1_simpy(0.5, 1.0)
else:
    print("Solution 3 — SimPy not installed; showing numpy replacement:")
    # numpy-based alternative
    def mm1_numpy_fast(lam, mu, n=10000, seed=7):
        rng = np.random.default_rng(seed)
        ia = rng.exponential(1/lam, n)
        st = rng.exponential(1/mu,  n)
        arr = np.cumsum(ia)
        dep = np.zeros(n)
        dep[0] = arr[0]+st[0]
        for i in range(1,n):
            dep[i] = max(arr[i], dep[i-1])+st[i]
        wq = np.maximum(0, dep-st-arr)
        theory = (lam/mu)/(mu*(1-lam/mu))
        print(f"  NumPy Wq={wq.mean():.4f}  theory={theory:.4f}")
    mm1_numpy_fast(0.5, 1.0)
print("Time: O(N) | Space: O(N)")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1536 — Backpressure Flow Controller (Token Bucket)
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1536 · Backpressure Flow Controller (Data Engineering · MEDIUM)

**Problem:** Implement a token-bucket rate limiter. Requests are allowed if tokens are available; otherwise rejected (backpressure). Parameters: capacity C, refill rate R tokens/second.

🧠 **How to Remember:** "Token bucket: fill at rate R up to capacity C. Consume 1 per request. Refill = elapsed × rate."
"""))

cells.append(code("""import time

# ── Solution 1: Classic token bucket ──────────────────────────────────────
class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity = capacity
        self.rate = rate          # tokens per second
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def allow(self, cost=1):
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

# Simulate 20 requests at t=0 with capacity=5, rate=2/s
bucket = TokenBucket(capacity=5, rate=2)
results = []
for i in range(10):
    results.append(('allowed' if bucket.allow() else 'rejected', round(bucket.tokens,2)))
print("Solution 1 — Token Bucket (10 rapid requests, cap=5):")
for i,(status,tok) in enumerate(results):
    print(f"  req {i+1}: {status:8s}  remaining_tokens={tok}")
print("Time: O(1) per request | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: Leaky bucket (queue-based) ────────────────────────────────
from collections import deque

class LeakyBucket:
    \"\"\"Leaky bucket: requests drip out at fixed rate; excess is dropped.\"\"\"
    def __init__(self, capacity, rate):
        self.capacity = capacity
        self.rate = rate    # requests/second drained
        self.queue = deque()
        self.last_drain = time.monotonic()

    def _drain(self):
        now = time.monotonic()
        elapsed = now - self.last_drain
        n_drain = int(elapsed * self.rate)
        for _ in range(min(n_drain, len(self.queue))):
            self.queue.popleft()
        self.last_drain = now

    def allow(self):
        self._drain()
        if len(self.queue) < self.capacity:
            self.queue.append(time.monotonic())
            return True
        return False

lb = LeakyBucket(capacity=3, rate=1)
print("Solution 2 — Leaky Bucket (8 rapid requests, cap=3):")
for i in range(8):
    status = 'allowed' if lb.allow() else 'dropped'
    print(f"  req {i+1}: {status:7s}  queue_size={len(lb.queue)}")
print("Time: O(1) amortised | Space: O(capacity)")
"""))

cells.append(code("""# ── Solution 3: Sliding window counter ────────────────────────────────────
import time
from collections import deque

class SlidingWindowRateLimiter:
    \"\"\"Allow at most `limit` requests per `window` seconds.\"\"\"
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.timestamps = deque()

    def allow(self):
        now = time.monotonic()
        # evict old timestamps
        while self.timestamps and now - self.timestamps[0] > self.window:
            self.timestamps.popleft()
        if len(self.timestamps) < self.limit:
            self.timestamps.append(now)
            return True
        return False

sw = SlidingWindowRateLimiter(limit=3, window=1.0)
print("Solution 3 — Sliding Window (6 rapid requests, limit=3/sec):")
for i in range(6):
    status = 'allowed' if sw.allow() else 'blocked'
    print(f"  req {i+1}: {status:7s}  window_count={len(sw.timestamps)}")
print()
print("| Solution        | Time | Space        |")
print("|-----------------|------|--------------|")
print("| Token Bucket    | O(1) | O(1)         |")
print("| Leaky Bucket    | O(1) | O(capacity)  |")
print("| Sliding Window  | O(W) | O(limit)     |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1539 — Path with Maximum Minimum Value
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1539 · Path with Maximum Minimum Value (Data Structures · MEDIUM)

**Problem:** Find a path from `(0,0)` to `(m-1,n-1)` in a grid such that the minimum value along the path is maximised. Return that maximum-minimum.

🧠 **How to Remember:** "Binary search on answer + BFS reachability check. Or max-heap Dijkstra-like: always expand the largest available cell."
"""))

cells.append(code("""from heapq import heappush, heappop

# ── Solution 1: Max-heap Dijkstra (greedy) ────────────────────────────────
def max_min_path_heap(grid):
    m, n = len(grid), len(grid[0])
    heap = [(-grid[0][0], 0, 0)]  # max-heap via negation
    visited = [[False]*n for _ in range(m)]
    visited[0][0] = True
    min_val = grid[0][0]
    while heap:
        neg_val, r, c = heappop(heap)
        min_val = min(min_val, -neg_val)
        if r == m-1 and c == n-1:
            return min_val
        for dr,dc in ((0,1),(0,-1),(1,0),(-1,0)):
            nr,nc = r+dr, c+dc
            if 0<=nr<m and 0<=nc<n and not visited[nr][nc]:
                visited[nr][nc] = True
                heappush(heap, (-grid[nr][nc], nr, nc))
    return -1

g1 = [[5,4,5],[1,2,6],[7,4,6]]
g2 = [[2,2,1,2,2,2],[1,2,2,2,1,2]]
print(f"Solution 1 (heap) g1={max_min_path_heap(g1)}  expected 4")
print(f"Solution 1 (heap) g2={max_min_path_heap(g2)}  expected 2")
print("Time: O(M*N log(M*N)) | Space: O(M*N)")
"""))

cells.append(code("""from collections import deque

# ── Solution 2: Binary search + BFS ───────────────────────────────────────
def max_min_path_bsearch(grid):
    m, n = len(grid), len(grid[0])

    def reachable(threshold):
        if grid[0][0] < threshold: return False
        q = deque([(0,0)])
        visited = {(0,0)}
        while q:
            r,c = q.popleft()
            if r==m-1 and c==n-1: return True
            for dr,dc in ((0,1),(0,-1),(1,0),(-1,0)):
                nr,nc = r+dr, c+dc
                if 0<=nr<m and 0<=nc<n and (nr,nc) not in visited and grid[nr][nc]>=threshold:
                    visited.add((nr,nc)); q.append((nr,nc))
        return False

    all_vals = sorted(set(v for row in grid for v in row), reverse=True)
    # binary search on sorted unique values
    lo, hi, ans = 0, len(all_vals)-1, 0
    while lo <= hi:
        mid = (lo+hi)//2
        if reachable(all_vals[mid]):
            ans = all_vals[mid]; hi = mid-1
        else:
            lo = mid+1
    return ans

print(f"Solution 2 (binary search+BFS) g1={max_min_path_bsearch(g1)}  expected 4")
print(f"Solution 2 (binary search+BFS) g2={max_min_path_bsearch(g2)}  expected 2")
print("Time: O(M*N log(M*N)) | Space: O(M*N)")
"""))

cells.append(code("""# ── Solution 3: Union-Find (Kruskal-like) ─────────────────────────────────
def max_min_path_uf(grid):
    m, n = len(grid), len(grid[0])
    parent = list(range(m*n))

    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x

    def union(a,b): parent[find(a)] = find(b)

    # Sort all cells by value descending; add them one by one and check connectivity
    cells = sorted(((grid[r][c],r,c) for r in range(m) for c in range(n)), reverse=True)
    added = [[False]*n for _ in range(m)]
    for val, r, c in cells:
        added[r][c] = True
        for dr,dc in ((0,1),(0,-1),(1,0),(-1,0)):
            nr,nc = r+dr, c+dc
            if 0<=nr<m and 0<=nc<n and added[nr][nc]:
                union(r*n+c, nr*n+nc)
        if find(0) == find((m-1)*n+(n-1)):
            return val
    return 0

print(f"Solution 3 (Union-Find) g1={max_min_path_uf(g1)}  expected 4")
print(f"Solution 3 (Union-Find) g2={max_min_path_uf(g2)}  expected 2")
print()
print("| Solution          | Time                | Space   |")
print("|-------------------|---------------------|---------|")
print("| Heap (Dijkstra)   | O(M*N log(M*N))     | O(M*N)  |")
print("| Binary search+BFS | O(M*N log(M*N))     | O(M*N)  |")
print("| Union-Find        | O(M*N α(M*N))       | O(M*N)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1541 — Two Sum
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1541 · Two Sum (Data Structures · EASY)

**Problem:** Given an array `nums` and target `t`, return indices of two numbers that add to `t`.

🧠 **How to Remember:** "One-pass hashmap: for each number, check if complement (target - num) already seen."
"""))

cells.append(code("""# ── Solution 1: Hashmap one-pass ──────────────────────────────────────────
def two_sum_hash(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        comp = target - n
        if comp in seen:
            return [seen[comp], i]
        seen[n] = i
    return []

tests_ts = [([2,7,11,15],9,[0,1]),([3,2,4],6,[1,2]),([3,3],6,[0,1])]
print("Solution 1 — hashmap:")
for nums,t,exp in tests_ts:
    print(f"  {nums} t={t} → {two_sum_hash(nums,t)}  expected {exp}")
print("Time: O(N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 2: Brute force O(N^2) ───────────────────────────────────────
def two_sum_brute(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i]+nums[j] == target:
                return [i,j]
    return []

print("Solution 2 — brute force:")
for nums,t,exp in tests_ts:
    print(f"  {nums} t={t} → {two_sum_brute(nums,t)}  expected {exp}")
print("Time: O(N^2) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: Sort + two-pointer (returns values, not indices) ──────────
def two_sum_twoptr_vals(nums, target):
    sorted_nums = sorted(enumerate(nums), key=lambda x: x[1])
    lo, hi = 0, len(sorted_nums)-1
    while lo < hi:
        s = sorted_nums[lo][1] + sorted_nums[hi][1]
        if s == target:
            i, j = sorted_nums[lo][0], sorted_nums[hi][0]
            return sorted([i,j])
        elif s < target: lo += 1
        else: hi -= 1
    return []

print("Solution 3 — two-pointer:")
for nums,t,exp in tests_ts:
    print(f"  {nums} t={t} → {two_sum_twoptr_vals(nums,t)}  expected {exp}")
print()
print("| Solution      | Time    | Space |")
print("|---------------|---------|-------|")
print("| Hashmap       | O(N)    | O(N)  |")
print("| Brute force   | O(N^2)  | O(1)  |")
print("| Two-pointer   | O(N log N)| O(N)|")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1546 — Successful Pairs of Spells and Potions
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1546 · Successful Pairs of Spells and Potions (Algorithms · MEDIUM)

**Problem:** `spells[i] * potions[j] >= success`. For each spell, count how many potions form a successful pair.

🧠 **How to Remember:** "Sort potions, binary search for minimum potion that satisfies: ceil(success/spell)."
"""))

cells.append(code("""import bisect, math

# ── Solution 1: Sort + bisect_left ────────────────────────────────────────
def successful_pairs_bisect(spells, potions, success):
    potions.sort()
    n = len(potions)
    result = []
    for s in spells:
        # need s * p >= success → p >= ceil(success/s)
        min_p = math.ceil(success / s)
        idx = bisect.bisect_left(potions, min_p)
        result.append(n - idx)
    return result

sp1,pt1,suc1 = [5,1,3],[1,2,3,4,5],7
sp2,pt2,suc2 = [3,1,2],[8,5,8],16
print(f"Solution 1: {successful_pairs_bisect(sp1,pt1[:],suc1)}  expected [4,0,3]")
print(f"Solution 1: {successful_pairs_bisect(sp2,pt2[:],suc2)}  expected [2,0,2]")
print("Time: O((N+M) log M) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: Two-pointer after sorting both ────────────────────────────
def successful_pairs_twoptr(spells, potions, success):
    n, m = len(spells), len(potions)
    potions_sorted = sorted(potions)
    # sort spells by value keeping original index
    spells_indexed = sorted(enumerate(spells), key=lambda x: x[1])
    result = [0]*n
    ptr = m-1  # potions pointer from right
    for orig_i, s in spells_indexed:
        while ptr >= 0 and s * potions_sorted[ptr] >= success:
            ptr -= 1
        result[orig_i] = m - (ptr+1)
    return result

print(f"Solution 2: {successful_pairs_twoptr(sp1,pt1[:],suc1)}  expected [4,0,3]")
print(f"Solution 2: {successful_pairs_twoptr(sp2,pt2[:],suc2)}  expected [2,0,2]")
print("Time: O(N log N + M log M) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 3: Pandas/numpy vectorised ───────────────────────────────────
import numpy as np

def successful_pairs_numpy(spells, potions, success):
    pt = np.array(sorted(potions))
    result = []
    for s in spells:
        min_p = math.ceil(success / s)
        idx = np.searchsorted(pt, min_p, side='left')
        result.append(len(pt)-idx)
    return result

print(f"Solution 3: {successful_pairs_numpy(sp1,pt1[:],suc1)}  expected [4,0,3]")
print(f"Solution 3: {successful_pairs_numpy(sp2,pt2[:],suc2)}  expected [2,0,2]")
print()
print("| Solution     | Time                  | Space |")
print("|--------------|-----------------------|-------|")
print("| bisect       | O((N+M) log M)        | O(1)  |")
print("| Two-pointer  | O(N log N + M log M)  | O(N)  |")
print("| NumPy        | O(N log M)            | O(M)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1547 — Extra Characters in a String
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1547 · Extra Characters in a String (Data Structures · MEDIUM)

**Problem:** Split string `s` using words from `dictionary`. Return the minimum number of extra (unused) characters.

🧠 **How to Remember:** "DP[i] = min extra chars in s[0..i]. Try every end j; if s[i..j] in dict, dp[j+1] = dp[i]."
"""))

cells.append(code("""# ── Solution 1: DP + set lookup ───────────────────────────────────────────
def min_extra_char_dp(s, dictionary):
    n = len(s)
    word_set = set(dictionary)
    dp = [0]*(n+1)
    dp[0] = 0
    for i in range(n):
        dp[i+1] = dp[i]+1   # skip s[i] as extra
        for j in range(i+1, n+1):
            if s[i:j] in word_set:
                dp[j] = min(dp[j], dp[i])
    return dp[n]

tests_ec = [
    ("leetscode",["leet","code","leetcode"],1),
    ("sayhelloworld",["hello","world"],3),
    ("abcd",["ab","cd"],0),
]
print("Solution 1 — DP + set:")
for s,d,exp in tests_ec:
    print(f"  '{s}' → {min_extra_char_dp(s,d)}  expected {exp}")
print("Time: O(N^2 * L) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 2: DP + Trie ─────────────────────────────────────────────────
class TrieNode:
    def __init__(self): self.children={}; self.is_end=False

def min_extra_char_trie(s, dictionary):
    root = TrieNode()
    for word in dictionary:
        node = root
        for c in word:
            node = node.children.setdefault(c, TrieNode())
        node.is_end = True

    n = len(s)
    dp = [0]*(n+1)
    for i in range(n):
        dp[i+1] = dp[i]+1
        node = root
        for j in range(i, n):
            if s[j] not in node.children: break
            node = node.children[s[j]]
            if node.is_end:
                dp[j+1] = min(dp[j+1], dp[i])
    return dp[n]

print("Solution 2 — DP + Trie:")
for s,d,exp in tests_ec:
    print(f"  '{s}' → {min_extra_char_trie(s,d)}  expected {exp}")
print("Time: O(N*L) | Space: O(N + dict_size*L)")
"""))

cells.append(code("""# ── Solution 3: Memoised recursion ────────────────────────────────────────
from functools import lru_cache

def min_extra_char_memo(s, dictionary):
    word_set = set(dictionary)
    n = len(s)
    @lru_cache(maxsize=None)
    def dp(i):
        if i == n: return 0
        best = dp(i+1)+1   # skip char i
        for j in range(i+1, n+1):
            if s[i:j] in word_set:
                best = min(best, dp(j))
        return best
    return dp(0)

print("Solution 3 — memoised recursion:")
for s,d,exp in tests_ec:
    print(f"  '{s}' → {min_extra_char_memo(s,d)}  expected {exp}")
print()
print("| Solution    | Time      | Space              |")
print("|-------------|-----------|--------------------|")
print("| DP+set      | O(N^2*L)  | O(N)               |")
print("| DP+Trie     | O(N*L)    | O(N+dict*L)        |")
print("| Memoised    | O(N^2*L)  | O(N)               |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1554 — Frequency of the Most Frequent Element
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1554 · Frequency of the Most Frequent Element (Algorithms · MEDIUM)

**Problem:** You can increment any element by 1 at most `k` times total. Return the maximum frequency of any element.

🧠 **How to Remember:** "Sort + sliding window. Cost to raise all window elements to nums[r] = nums[r]*(r-l+1) - window_sum. Shrink if cost > k."
"""))

cells.append(code("""# ── Solution 1: Sorting + Sliding Window ──────────────────────────────────
def max_frequency_sw(nums, k):
    nums.sort()
    lo = total = 0
    ans = 1
    for hi in range(len(nums)):
        total += nums[hi]
        # cost = nums[hi]*(hi-lo+1) - total > k
        while nums[hi]*(hi-lo+1) - total > k:
            total -= nums[lo]; lo += 1
        ans = max(ans, hi-lo+1)
    return ans

tests_mf = [([1,2,4],5,3),([1,4,8,13],5,2),([3,9,6],2,1)]
print("Solution 1 — sliding window:")
for nums,k,exp in tests_mf:
    print(f"  {nums} k={k} → {max_frequency_sw(nums[:],k)}  expected {exp}")
print("Time: O(N log N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: Sort + binary search per element ──────────────────────────
import bisect

def max_frequency_bs(nums, k):
    nums.sort()
    prefix = [0]*(len(nums)+1)
    for i,v in enumerate(nums): prefix[i+1] = prefix[i]+v

    ans = 1
    for r in range(len(nums)):
        target = nums[r]
        # binary search for leftmost l where target*(r-l+1) - sum(l..r) <= k
        lo, hi = 0, r
        while lo < hi:
            mid = (lo+hi)//2
            window_sum = prefix[r+1]-prefix[mid]
            cost = target*(r-mid+1) - window_sum
            if cost <= k: hi = mid
            else: lo = mid+1
        ans = max(ans, r-lo+1)
    return ans

print("Solution 2 — binary search:")
for nums,k,exp in tests_mf:
    print(f"  {nums} k={k} → {max_frequency_bs(nums[:],k)}  expected {exp}")
print("Time: O(N log^2 N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 3: Sort + deque-based sliding window ─────────────────────────
from collections import deque

def max_frequency_deque(nums, k):
    nums.sort()
    window = deque()
    window_sum = ans = 0
    for num in nums:
        window.append(num)
        window_sum += num
        while window[-1]*len(window) - window_sum > k:
            window_sum -= window.popleft()
        ans = max(ans, len(window))
    return ans

print("Solution 3 — deque window:")
for nums,k,exp in tests_mf:
    print(f"  {nums} k={k} → {max_frequency_deque(nums[:],k)}  expected {exp}")
print()
print("| Solution       | Time         | Space |")
print("|----------------|--------------|-------|")
print("| Sliding Window | O(N log N)   | O(1)  |")
print("| Binary Search  | O(N log^2 N) | O(N)  |")
print("| Deque Window   | O(N log N)   | O(N)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1559 — Frog Jump
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1559 · Frog Jump (Algorithms · HARD)

**Problem:** A frog starts at stone 0. At stone `x` with last jump `k`, it can next jump `k-1`, `k`, or `k+1`. Can it reach the last stone?

🧠 **How to Remember:** "DP with sets: dp[stone] = set of jump sizes that can reach it. For each stone, propagate k-1, k, k+1 forward."
"""))

cells.append(code("""# ── Solution 1: DP with dict of sets ─────────────────────────────────────
def can_cross_dp(stones):
    stone_set = set(stones)
    dp = {s: set() for s in stones}
    dp[0].add(0)
    for stone in stones:
        for k in dp[stone]:
            for nk in (k-1, k, k+1):
                if nk > 0 and stone+nk in stone_set:
                    dp[stone+nk].add(nk)
    return bool(dp[stones[-1]])

tests_fj = [([0,1,3,5,6,8,12,17],True),([0,1,2,3,4,8,9,11],False)]
print("Solution 1 — DP dict of sets:")
for stones, exp in tests_fj:
    print(f"  {stones} → {can_cross_dp(stones)}  expected {exp}")
print("Time: O(N^2) | Space: O(N^2)")
"""))

cells.append(code("""# ── Solution 2: BFS / DFS with visited set ────────────────────────────────
from collections import deque

def can_cross_bfs(stones):
    stone_set = set(stones)
    last = stones[-1]
    visited = set()
    q = deque([(0,0)])  # (position, last_jump)
    while q:
        pos, k = q.popleft()
        for nk in (k-1,k,k+1):
            npos = pos+nk
            if npos==last: return True
            if nk>0 and npos in stone_set and (npos,nk) not in visited:
                visited.add((npos,nk))
                q.append((npos,nk))
    return False

print("Solution 2 — BFS:")
for stones, exp in tests_fj:
    print(f"  {stones} → {can_cross_bfs(stones)}  expected {exp}")
print("Time: O(N^2) | Space: O(N^2)")
"""))

cells.append(code("""# ── Solution 3: Recursive memoisation ─────────────────────────────────────
from functools import lru_cache

def can_cross_memo(stones):
    stone_set = set(stones)
    last = stones[-1]
    @lru_cache(maxsize=None)
    def dfs(pos, k):
        if pos == last: return True
        for nk in (k-1,k,k+1):
            if nk > 0 and pos+nk in stone_set:
                if dfs(pos+nk, nk): return True
        return False
    return dfs(0,0)

print("Solution 3 — memoised DFS:")
for stones, exp in tests_fj:
    print(f"  {stones} → {can_cross_memo(stones)}  expected {exp}")
print()
print("| Solution   | Time   | Space  |")
print("|------------|--------|--------|")
print("| DP-sets    | O(N^2) | O(N^2) |")
print("| BFS        | O(N^2) | O(N^2) |")
print("| Memo DFS   | O(N^2) | O(N^2) |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1567 — Fisher's Exact Test
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1567 · Fisher's Exact Test (Statistics · MEDIUM)

**Problem:** Given a 2×2 contingency table, test if two categorical variables are independent using Fisher's Exact Test.

**Table:**
```
         | Success | Failure
---------|---------|---------
Group A  |    a    |    b
Group B  |    c    |    d
```

🧠 **How to Remember:** "Fisher's: exact p-value = sum of hypergeometric probabilities ≤ observed. scipy.stats.fisher_exact() wraps it."
"""))

cells.append(code("""from scipy import stats
import numpy as np
from math import comb, factorial

# ── Solution 1: scipy.stats.fisher_exact ──────────────────────────────────
tables = [
    ([[8,2],[1,5]], "Strong association"),
    ([[3,3],[3,3]], "No association"),
    ([[14,4],[12,2]], "Borderline"),
]
print("Solution 1 — scipy fisher_exact:")
for table, desc in tables:
    odds, p = stats.fisher_exact(table)
    print(f"  {desc}: table={table}  OR={odds:.3f}  p={p:.4f}  {'significant' if p<0.05 else 'not significant'}")
print("Time: O(min(a,b,c,d)) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: Manual hypergeometric calculation ─────────────────────────
def fisher_exact_manual(a, b, c, d):
    \"\"\"Compute two-sided Fisher exact p-value manually.\"\"\"
    n = a+b+c+d
    row1, col1 = a+b, a+c

    def hyper_prob(k):
        try:
            return comb(row1,k)*comb(n-row1,col1-k)/comb(n,col1)
        except:
            return 0.0

    observed_p = hyper_prob(a)
    # sum all configurations at least as extreme
    p_val = sum(hyper_prob(k) for k in range(col1+1) if hyper_prob(k) <= observed_p+1e-9)
    return p_val

print("Solution 2 — manual hypergeometric:")
for (table,desc) in tables:
    a,b,c,d = table[0][0],table[0][1],table[1][0],table[1][1]
    p = fisher_exact_manual(a,b,c,d)
    _,p_ref = stats.fisher_exact(table)
    print(f"  {desc}: p_manual={p:.4f}  p_scipy={p_ref:.4f}  match={abs(p-p_ref)<0.001}")
print("Time: O(min(R,C)) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: Permutation test approximation ────────────────────────────
import numpy as np

def fisher_permutation(table, n_perm=10000, seed=42):
    rng = np.random.default_rng(seed)
    a,b,c,d = table[0][0],table[0][1],table[1][0],table[1][1]
    # observed odds ratio
    obs_or = (a*d)/(b*c+1e-10)
    # generate labels
    labels = np.array([1]*(a+b)+[0]*(c+d))
    group  = np.array([1]*a+[0]*b+[1]*c+[0]*d)
    count = 0
    for _ in range(n_perm):
        perm = rng.permutation(group)
        # recompute 2x2
        pa = ((labels==1)&(perm==1)).sum()
        pb = ((labels==1)&(perm==0)).sum()
        pc = ((labels==0)&(perm==1)).sum()
        pd = ((labels==0)&(perm==0)).sum()
        sim_or = (pa*pd)/(pb*pc+1e-10)
        if abs(np.log(sim_or+1e-10)) >= abs(np.log(obs_or+1e-10)):
            count += 1
    return count/n_perm

print("Solution 3 — permutation test (10k perms):")
for (table,desc) in tables:
    p_perm = fisher_permutation(table)
    _, p_ref = stats.fisher_exact(table)
    print(f"  {desc}: p_perm≈{p_perm:.3f}  p_scipy={p_ref:.4f}")
print()
print("| Solution        | Time      | Space |")
print("|-----------------|-----------|-------|")
print("| scipy           | O(min RC) | O(1)  |")
print("| Manual hyper    | O(min RC) | O(1)  |")
print("| Permutation     | O(N*P)    | O(N)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1568 — Next Greater Element I
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1568 · Next Greater Element I (Data Structures · EASY)

**Problem:** `nums1` is a subset of `nums2`. For each element in `nums1`, find the next greater element in `nums2`. Return -1 if none.

🧠 **How to Remember:** "Monotonic stack on nums2: maintain decreasing stack, pop when we find a greater element → that's the answer."
"""))

cells.append(code("""# ── Solution 1: Monotonic stack ───────────────────────────────────────────
def next_greater_stack(nums1, nums2):
    stack, nge = [], {}
    for num in nums2:
        while stack and stack[-1] < num:
            nge[stack.pop()] = num
        stack.append(num)
    return [nge.get(n, -1) for n in nums1]

tests_ng = [
    ([4,1,2],[1,3,4,2],[-1,3,-1]),
    ([2,4],[1,2,3,4],[3,-1]),
]
print("Solution 1 — monotonic stack:")
for n1,n2,exp in tests_ng:
    print(f"  {n1} in {n2} → {next_greater_stack(n1,n2)}  expected {exp}")
print("Time: O(M+N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 2: Brute force O(M*N) ───────────────────────────────────────
def next_greater_brute(nums1, nums2):
    result = []
    for n in nums1:
        idx = nums2.index(n)
        found = -1
        for j in range(idx+1, len(nums2)):
            if nums2[j] > n:
                found = nums2[j]; break
        result.append(found)
    return result

print("Solution 2 — brute force:")
for n1,n2,exp in tests_ng:
    print(f"  {n1} in {n2} → {next_greater_brute(n1,n2)}  expected {exp}")
print("Time: O(M*N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: Precompute dict then lookup ────────────────────────────────
def next_greater_dict(nums1, nums2):
    pos = {v:i for i,v in enumerate(nums2)}
    nge = {}
    for v in nums2:
        for j in range(pos[v]+1, len(nums2)):
            if nums2[j] > v:
                nge[v] = nums2[j]; break
        else:
            nge[v] = -1
    return [nge[n] for n in nums1]

print("Solution 3 — precompute dict:")
for n1,n2,exp in tests_ng:
    print(f"  {n1} in {n2} → {next_greater_dict(n1,n2)}  expected {exp}")
print()
print("| Solution         | Time   | Space |")
print("|------------------|--------|-------|")
print("| Monotonic stack  | O(M+N) | O(N)  |")
print("| Brute force      | O(M*N) | O(1)  |")
print("| Precompute dict  | O(N^2) | O(N)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1569 — Shuffle an Array
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1569 · Shuffle an Array (Math · MEDIUM)

**Problem:** Design an object to shuffle an array of integers. `reset()` returns the original. `shuffle()` returns a uniformly random permutation.

🧠 **How to Remember:** "Fisher-Yates: for i from n-1 to 1, swap nums[i] with nums[random(0..i)]. Every permutation equally likely."
"""))

cells.append(code("""import random

# ── Solution 1: Fisher-Yates (Knuth Shuffle) ──────────────────────────────
class ShuffleFisherYates:
    def __init__(self, nums):
        self.original = nums[:]
        self.nums = nums[:]

    def reset(self):
        self.nums = self.original[:]
        return self.nums

    def shuffle(self):
        for i in range(len(self.nums)-1, 0, -1):
            j = random.randint(0, i)
            self.nums[i], self.nums[j] = self.nums[j], self.nums[i]
        return self.nums

obj = ShuffleFisherYates([1,2,3,4,5])
print("Solution 1 — Fisher-Yates:")
for _ in range(5):
    print(f"  shuffle: {obj.shuffle()}")
print(f"  reset:   {obj.reset()}")
print("Time: O(N) shuffle, O(N) reset | Space: O(N)")
"""))

cells.append(code("""# ── Solution 2: random.sample (library) ───────────────────────────────────
class ShuffleLibrary:
    def __init__(self, nums):
        self.original = nums[:]
        self.nums = nums[:]

    def reset(self): self.nums = self.original[:]; return self.nums

    def shuffle(self):
        self.nums = random.sample(self.nums, len(self.nums))
        return self.nums

obj2 = ShuffleLibrary([1,2,3,4,5])
print("Solution 2 — random.sample:")
for _ in range(5):
    print(f"  shuffle: {obj2.shuffle()}")
print(f"  reset:   {obj2.reset()}")
print("Time: O(N) | Space: O(N)")
"""))

cells.append(code("""# ── Solution 3: numpy random permutation ──────────────────────────────────
import numpy as np

class ShuffleNumpy:
    def __init__(self, nums):
        self.original = nums[:]
        self.arr = np.array(nums)

    def reset(self): self.arr = np.array(self.original); return self.arr.tolist()

    def shuffle(self):
        np.random.shuffle(self.arr)
        return self.arr.tolist()

obj3 = ShuffleNumpy([1,2,3,4,5])
print("Solution 3 — numpy:")
for _ in range(5):
    print(f"  shuffle: {obj3.shuffle()}")
print(f"  reset:   {obj3.reset()}")
print()
# Uniformity test
from collections import Counter
counts = Counter()
test_obj = ShuffleFisherYates([1,2,3])
for _ in range(60000):
    counts[tuple(test_obj.shuffle())] += 1
print("Uniformity check (60k shuffles of [1,2,3], each of 6 permutations ~10000):")
for k,v in sorted(counts.items()): print(f"  {k}: {v}")
print("Time: O(N) | Space: O(N)")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1572 — Two Sum II Input Array Is Sorted
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1572 · Two Sum II – Input Array Is Sorted (Data Structures · EASY)

**Problem:** 1-indexed sorted array; find two numbers summing to target. Must use O(1) space.

🧠 **How to Remember:** "Two pointers: left=1, right=n. If sum < target: left++. If sum > target: right--. Stop when equal."
"""))

cells.append(code("""# ── Solution 1: Two Pointers (O(1) space) ─────────────────────────────────
def two_sum_sorted_tp(numbers, target):
    lo, hi = 0, len(numbers)-1
    while lo < hi:
        s = numbers[lo]+numbers[hi]
        if s == target: return [lo+1, hi+1]
        elif s < target: lo += 1
        else: hi -= 1
    return []

tests_t2 = [([2,7,11,15],9,[1,2]),([2,3,4],6,[1,3]),([-1,0],[-1,1,2])]
tests_t2 = [([2,7,11,15],9,[1,2]),([2,3,4],6,[1,3]),([- 1,0],-1,[1,2])]
print("Solution 1 — two pointers:")
for nums,t,exp in tests_t2:
    print(f"  {nums} t={t} → {two_sum_sorted_tp(nums,t)}  expected {exp}")
print("Time: O(N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: Binary search for complement ──────────────────────────────
import bisect

def two_sum_sorted_bs(numbers, target):
    for i,n in enumerate(numbers):
        comp = target-n
        idx = bisect.bisect_left(numbers, comp, i+1)
        if idx < len(numbers) and numbers[idx]==comp:
            return [i+1, idx+1]
    return []

print("Solution 2 — binary search:")
for nums,t,exp in tests_t2:
    print(f"  {nums} t={t} → {two_sum_sorted_bs(nums,t)}  expected {exp}")
print("Time: O(N log N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: hashmap (O(N) space, still correct) ───────────────────────
def two_sum_sorted_hash(numbers, target):
    seen = {}
    for i,n in enumerate(numbers):
        if target-n in seen:
            return [seen[target-n]+1, i+1]
        seen[n] = i
    return []

print("Solution 3 — hashmap:")
for nums,t,exp in tests_t2:
    print(f"  {nums} t={t} → {two_sum_sorted_hash(nums,t)}  expected {exp}")
print()
print("| Solution      | Time       | Space |")
print("|---------------|------------|-------|")
print("| Two pointers  | O(N)       | O(1)  |")
print("| Binary search | O(N log N) | O(1)  |")
print("| Hashmap       | O(N)       | O(N)  |")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Q1575 — Final Row Without Sorting
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Q1575 · Final Row Without Sorting (Database · EASY)

**Problem:** Find the row with the maximum `score` in a table **without using ORDER BY**. Use a MAX subquery.

🧠 **How to Remember:** "WHERE score = (SELECT MAX(score) FROM ...) — subquery finds max, outer query filters rows."
"""))

cells.append(code("""con5 = sqlite3.connect(":memory:")
con5.executescript(\"\"\"
CREATE TABLE Scores(id INT, player TEXT, score INT, game TEXT);
INSERT INTO Scores VALUES
  (1,'Alice',95,'Chess'),(2,'Bob',87,'Chess'),
  (3,'Carol',95,'Chess'),(4,'Dave',72,'Chess'),
  (5,'Eve',100,'Go'),(6,'Frank',85,'Go');
\"\"\")
print(pd.read_sql("SELECT * FROM Scores", con5))
"""))

cells.append(code("""# ── Solution 1: WHERE score = MAX subquery ────────────────────────────────
q = \"\"\"
SELECT *
FROM Scores
WHERE score = (SELECT MAX(score) FROM Scores);
\"\"\"
print("Solution 1 — MAX subquery:")
print(pd.read_sql(q, con5).to_string(index=False))
print("Time: O(N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 2: CTE + MAX ─────────────────────────────────────────────────
q2 = \"\"\"
WITH max_score AS (SELECT MAX(score) AS ms FROM Scores)
SELECT s.*
FROM Scores s JOIN max_score m ON s.score = m.ms;
\"\"\"
print("Solution 2 — CTE:")
print(pd.read_sql(q2, con5).to_string(index=False))
print("Time: O(N) | Space: O(1)")
"""))

cells.append(code("""# ── Solution 3: Pandas idxmax ─────────────────────────────────────────────
df = pd.read_sql("SELECT * FROM Scores", con5)
max_score = df['score'].max()
result = df[df['score'] == max_score]
print("Solution 3 — Pandas:")
print(result.to_string(index=False))
print()
print("| Solution     | Time | Space |")
print("|--------------|------|-------|")
print("| MAX subquery | O(N) | O(1)  |")
print("| CTE+MAX      | O(N) | O(1)  |")
print("| Pandas       | O(N) | O(N)  |")
"""))

# ─── Final summary cell ──────────────────────────────────────────────────────
cells.append(md("""---
## Summary Table — All 23 Questions

| # | Question | Topic | Difficulty | Key Insight |
|---|----------|-------|-----------|-------------|
|1498|Users With Over 3 Friends|DB|EASY|UNION ALL + HAVING COUNT > 3|
|1503|Row-wise Word Totals|DB|EASY|LENGTH minus spaces + 1|
|1504|Cherry Pickup II|Algo|HARD|3-D DP row×col1×col2|
|1505|Uncrossed Lines|Algo|MEDIUM|= LCS, 1-D DP|
|1508|Reconstruct Itinerary|DS|HARD|Hierholzer's Euler path|
|1510|Rows With g-Prefixed Words|DB|MEDIUM|LIKE 'g%' OR '% g%'|
|1520|Nontransitive Dice|Stats|MEDIUM|Monte Carlo + exact enum|
|1526|Search Frequency Users|DB|HARD|CASE WHEN conditional aggregates|
|1528|String Halves Alike|Algo|EASY|Signed vowel counter|
|1532|Count Smaller After Self|DS|HARD|Merge sort / BIT Fenwick|
|1533|M/M/1 Queue Simulator|Stats|MEDIUM|Little's Law: L=λW|
|1536|Backpressure Flow Controller|DE|MEDIUM|Token bucket / sliding window|
|1539|Path with Max Min Value|DS|MEDIUM|Max-heap Dijkstra / Union-Find|
|1541|Two Sum|DS|EASY|One-pass hashmap|
|1546|Successful Spell-Potion Pairs|Algo|MEDIUM|Sort + bisect_left|
|1547|Extra Characters in String|DS|MEDIUM|DP + Trie|
|1554|Freq of Most Frequent Element|Algo|MEDIUM|Sort + sliding window cost|
|1559|Frog Jump|Algo|HARD|DP dict of jump-size sets|
|1567|Fisher's Exact Test|Stats|MEDIUM|Hypergeometric p-value|
|1568|Next Greater Element I|DS|EASY|Monotonic stack|
|1569|Shuffle an Array|Math|MEDIUM|Fisher-Yates in-place|
|1572|Two Sum II Sorted|DS|EASY|Two pointers O(1) space|
|1575|Final Row Without Sorting|DB|EASY|WHERE score=(SELECT MAX…)|
"""))

# ─── Write notebook ───────────────────────────────────────────────────────────
out_path = "/Users/prem/PycharmProjects/data-etl-ml/medium/google/past-questation/Google_DE_Page5_Q1498_Q1575.ipynb"
with open(out_path, "w") as f:
    json.dump(nb(cells), f, indent=1)

print(f"Notebook written: {out_path}")
print(f"Total cells: {len(cells)}")
