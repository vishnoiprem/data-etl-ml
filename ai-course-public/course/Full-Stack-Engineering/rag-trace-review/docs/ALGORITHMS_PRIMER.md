# Algorithms & Coding Interview Primer

A 60-minute framework for Meta/Google-style coding interviews. Read this before Day 27.

---

## The 60-minute format (real interview)

| Time | What you do | What the interviewer is watching |
|---|---|---|
| 0–2 min | Read problem twice, restate it | Clarity of thought |
| 2–5 min | Ask 2–3 clarifying questions | Engagement, edge-case awareness |
| 5–8 min | State brute-force + complexity | Self-awareness, communication |
| 8–10 min | Describe optimal approach | Pattern recognition |
| 10–35 min | Code (clean, runnable, no syntax errors) | Hands-on skill |
| 35–40 min | Trace through with an example | Correctness verification |
| 40–50 min | Test edge cases (empty, 1, max, duplicates) | Thoroughness |
| 50–60 min | Discuss complexity, alternatives, follow-ups | Depth |

**Rule of thumb:** if you can't write bug-free code for the happy path in 25 min, you don't have the pattern. Drill until you do.

---

## Big-O cheat sheet

| Notation | Name | Example | 1M items takes |
|---|---|---|---|
| O(1) | constant | hash lookup | instant |
| O(log n) | logarithmic | binary search | 20 ops |
| O(n) | linear | scan | 1M ops (~10ms) |
| O(n log n) | linearithmic | mergesort | 20M ops |
| O(n²) | quadratic | nested loops | 10⁹ ops (too slow) |
| O(2ⁿ) | exponential | subsets | instant death |
| O(n!) | factorial | permutations | call mom |

**Mnemonic:** if you have a nested loop, you're probably O(n²). If you have a loop with a hash inside, you're O(n). If you sort, you're O(n log n).

---

## Top 12 patterns (cover 90% of problems)

### 1. Hash map
- "Two Sum", "Group Anagrams", "Top K Frequent", "Subarray Sum Equals K"
- **Key insight:** trade O(n) space for O(1) lookups.
- **When to use:** "find if X exists", "count frequencies", "complement lookup".

### 2. Two pointers
- "Container With Most Water", "3Sum", "Valid Palindrome", "Trapping Rain Water"
- **Key insight:** sorted array + two ends = O(n) instead of O(n²).
- **When to use:** sorted input, pairs, partitioning.

### 3. Sliding window
- "Longest Substring Without Repeating Chars", "Min Window Substring", "Permutation in String"
- **Key insight:** maintain a window [l, r]; expand right, shrink left.
- **When to use:** contiguous subarray/substring, "longest/shortest/most", constraint window.

### 4. Fast & slow pointers
- "Linked List Cycle", "Happy Number", "Find Middle"
- **Key insight:** slow moves 1, fast moves 2; they meet in a cycle.
- **When to use:** cycle detection, midpoint, nth from end.

### 5. Binary search
- "Search in Rotated Sorted Array", "Find Minimum in Rotated", "Koko Eating Bananas"
- **Key insight:** `lo + (hi - lo) // 2` to avoid overflow; be careful with off-by-one.
- **When to use:** sorted array, "find boundary", "find first/last true".

### 6. BFS / DFS on tree
- "Level Order", "Validate BST", "Max Depth", "Lowest Common Ancestor"
- **Key insight:** BFS = queue (level by level); DFS = stack/recursion (path by path).
- **When to use:** trees, "level order", "max depth", "all paths".

### 7. BFS / DFS on graph
- "Number of Islands", "Course Schedule", "Clone Graph", "Word Ladder"
- **Key insight:** BFS = shortest path in unweighted graph; DFS = topo sort / cycle detection.
- **When to use:** grid problems, dependencies, shortest path.

### 8. Heap / priority queue
- "Kth Largest", "Merge K Sorted Lists", "Top K Frequent", "Median of Stream"
- **Key insight:** heap gives O(log n) insert and O(1) peek.
- **When to use:** "kth", "top k", "running median", "merge streams".

### 9. Stack / monotonic stack
- "Valid Parentheses", "Daily Temperatures", "Largest Rectangle in Histogram"
- **Key insight:** stack of "indices whose answer is still unknown".
- **When to use:** "next greater", "valid brackets", "expression parsing".

### 10. Dynamic programming
- "Climbing Stairs", "Coin Change", "Longest Common Subsequence", "Edit Distance"
- **Key insight:** dp[i] = function of dp[i-1] or dp[i-2] (1D), or dp[i][j] (2D).
- **When to use:** "count ways", "min/max cost", "is it possible".

### 11. Backtracking
- "Permutations", "Combinations", "Word Search", "N-Queens"
- **Key insight:** choose → explore → unchoose. Prune aggressively.
- **When to use:** "all combinations", "all valid arrangements".

### 12. Greedy
- "Jump Game", "Gas Station", "Interval Scheduling", "Candy"
- **Key insight:** local optimum → global optimum. Sort first, then sweep.
- **When to use:** scheduling, intervals, "can you reach the end".

---

## The 50 most-asked LeetCode problems (by company frequency)

### Arrays & strings (15)
1. Two Sum (Easy)
2. Best Time to Buy/Sell Stock (Easy)
3. Contains Duplicate (Easy)
4. Product of Array Except Self (Medium)
5. Maximum Subarray (Medium) — Kadane's
6. Maximum Product Subarray (Medium)
7. Find Minimum in Rotated Sorted Array (Medium)
8. Search in Rotated Sorted Array (Medium)
9. 3Sum (Medium)
10. Container With Most Water (Medium)
11. Trapping Rain Water (Hard)
12. Longest Substring Without Repeating Chars (Medium)
13. Longest Repeating Character Replacement (Medium)
14. Minimum Window Substring (Hard)
15. Valid Anagram (Easy)

### Hash map (5)
16. Group Anagrams (Medium)
17. Top K Frequent Elements (Medium)
18. Encode/Decode Strings (Medium)
19. Longest Consecutive Sequence (Medium)
20. Subarray Sum Equals K (Medium)

### Linked list (5)
21. Reverse Linked List (Easy)
22. Merge Two Sorted Lists (Easy)
23. Linked List Cycle (Easy)
24. Remove Nth from End (Medium)
25. LRU Cache (Medium)

### Trees (10)
26. Maximum Depth of Binary Tree (Easy)
27. Same Tree (Easy)
28. Invert Binary Tree (Easy)
29. Binary Tree Level Order Traversal (Medium)
30. Validate BST (Medium)
31. Kth Smallest in BST (Medium)
32. Lowest Common Ancestor (Medium)
33. Construct Tree from Preorder + Inorder (Medium)
34. Serialize/Deserialize Binary Tree (Hard)
35. Word Search II (Hard)

### Graphs (5)
36. Number of Islands (Medium)
37. Clone Graph (Medium)
38. Course Schedule (Medium)
39. Pacific Atlantic Water Flow (Medium)
40. Word Ladder (Hard)

### Heap (3)
41. Kth Largest Element (Medium)
42. Merge K Sorted Lists (Hard)
43. Find Median from Data Stream (Hard)

### DP (5)
44. Climbing Stairs (Easy)
45. Coin Change (Medium)
46. Longest Increasing Subsequence (Medium)
47. Longest Common Subsequence (Medium)
48. Edit Distance (Hard)

### Backtracking (2)
49. Permutations (Medium)
50. Word Search (Medium)

**Minimum bar:** 30 of these solved in under 20 min each before the interview.

---

## The 6-week study plan (8–12 hours/week)

| Week | Topics | Problems |
|---|---|---|
| 1 | Arrays, strings, hash map | 1–20 |
| 2 | Two pointers, sliding window, fast/slow | 1–14 (arrays), 21–24 (LL) |
| 3 | Trees BFS/DFS | 26–35 |
| 4 | Graphs, heap, binary search | 36–43, 7–8 |
| 5 | DP, backtracking, greedy | 44–50, plus Coin Change family |
| 6 | Mock interviews (3 timed 45-min) | 1 randomized problem each |

---

## How to practice (the right way)

1. **Solve before you peek.** 25 min hard cap. If stuck, write down *why* you got stuck.
2. **Pattern-first, problem-second.** For each problem, name the pattern. "This is a sliding window because the answer is a contiguous substring with a constraint."
3. **Code clean from the start.** Variable names, helper functions, no print-debugging in the final.
4. **Test on edge cases first.** Empty, 1, 2, max, duplicates, negative.
5. **State complexity out loud.** Even when the interviewer doesn't ask, say it.
6. **Time yourself.** A 20-min problem is a Medium, a 5-min is an Easy, a 40-min is a Hard.

---

## Red flags in an interview

- Silent for 2+ minutes → speak out your thinking, always.
- Writing code before explaining → communicate first, code second.
- Edge cases ignored → ask, then handle.
- "I think it's correct" → trace through an example.
- O(n²) solution that you can't improve → at least mention the brute force.
- Can't state complexity → practice saying "this is O(n log n) because of the sort and the linear scan".

---

## Meta vs. Google style

| | Meta | Google |
|---|---|---|
| Focus | Speed, practical code | Depth, edge cases, follow-ups |
| Difficulty | Mostly Medium | Mix of Medium and Hard |
| Style | "Ship it" mindset | "What's the optimal?" |
| Common | Trees, arrays, DP | Graphs, DP, system design |
| Tip | Communicate the brute first | Optimize aggressively |

**Universal tip:** both want you to **think out loud**.

---

## 50/80 score = hire; 35/80 = no-hire

| Area | What's graded |
|---|---|
| Correctness | Does it work? Edge cases? |
| Code quality | Clean, readable, no dead code? |
| Debugging | Trace correctly? Spot bugs? |
| API design | N/A (algorithmic round) |
| Frontend | N/A |
| Performance | Right Big-O? Optimal pattern? |
| Testing | Edge cases covered? |
| Communication | Articulate? Pattern identified? |

For this course, we adapt the rubric to a 7-area / 70 scale (no API/frontend), pass = 49/70.

---

## One more thing

The interview is not about being clever. It's about being **fast, correct, and communicative**. Practice the patterns until they're reflex. On interview day, you'll see a problem, name the pattern, and write 20 lines of clean code in 15 minutes.

That's it. Go solve.
