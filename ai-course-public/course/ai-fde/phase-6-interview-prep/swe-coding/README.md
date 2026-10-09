# Module 9 — SWE Coding Questions

> **The classic SWE coding round is being replaced by the practical coding round (Module 3), but it's not gone.** Anthropic, OpenAI, Palantir, and AWS FDE still test data structures + algorithms. **The signal: a candidate who can solve a medium-difficulty problem in 25 minutes, with clean code and clear thinking, is showing they can debug a codebase in production.**

---

## The 8 patterns (the cheat sheet)

### Pattern 1: Arrays

- **2 pointers:** left + right, move toward each other. O(n).
- **Sliding window:** maintain a window of size k, slide it. O(n).
- **Prefix sum:** precompute cumulative sum, answer range queries in O(1).

**Sample problem:** "Given an array of integers, find the contiguous subarray with the largest sum." (Kadane's algorithm, O(n).)

### Pattern 2: Hash tables

- **Frequency counter:** count occurrences in O(n).
- **Two-sum:** store seen values, check complement in O(n).
- **Group by:** group items by key in O(n).

**Sample problem:** "Given an array of strings, group anagrams together." (Sort each string, use as key, O(n × k log k).)

### Pattern 3: Strings

- **Reverse:** in-place, O(n).
- **Anagram check:** frequency counter, O(n).
- **Substring search:** KMP / Rabin-Karp, O(n + m).

**Sample problem:** "Given two strings, check if one is a permutation of the other." (Frequency counter, O(n).)

### Pattern 4: Trees

- **DFS (pre/in/post-order):** recursive or iterative with stack. O(n).
- **BFS (level-order):** queue. O(n).
- **Binary search tree:** O(log n) for search/insert/delete if balanced.

**Sample problem:** "Given a binary tree, find the maximum depth." (DFS, O(n).)

### Pattern 5: Graphs

- **DFS / BFS:** traverse the graph. O(V + E).
- **Topological sort:** DFS with a stack, or Kahn's algorithm with in-degree. O(V + E).
- **Dijkstra:** shortest path with non-negative weights. O((V + E) log V).

**Sample problem:** "Given a directed graph, detect if there's a cycle." (DFS with 3 colors, O(V + E).)

### Pattern 6: Dynamic programming

- **Memoization (top-down):** recursive + cache. O(n) typically.
- **Tabulation (bottom-up):** iterative + array. O(n) typically.
- **State compression:** keep only the last 2 states, O(1) space.

**Sample problem:** "Given a staircase with n steps, how many ways can you climb 1 or 2 steps at a time?" (Fibonacci, O(n) time, O(1) space.)

### Pattern 7: Recursion + backtracking

- **Permutations:** generate all orderings. O(n!).
- **Combinations:** generate all subsets. O(2^n).
- **Constraint satisfaction:** N-Queens, Sudoku. Exponential.

**Sample problem:** "Generate all valid combinations of n pairs of parentheses." (Backtracking, O(4^n / sqrt(n)).)

### Pattern 8: Linked lists

- **Reverse:** iterative with 3 pointers, O(n).
- **Cycle detection:** Floyd's algorithm (slow + fast pointers), O(n).
- **Merge two sorted:** iterative with dummy head, O(n + m).

**Sample problem:** "Reverse a linked list." (Iterative, O(n) time, O(1) space.)

---

## The 4 SWE coding anti-patterns

1. **Jumping to code without a plan.** "I'll just start coding" is a junior answer. The plan is the signal.
2. **Skipping edge cases.** Empty input, single element, all duplicates, negative numbers. The edge cases are the signal.
3. **Using the wrong data structure.** "I'll use a list when I need a hash table" is O(n) instead of O(1). The data structure is the signal.
4. **Not testing the code.** Walk through 1-2 examples out loud. The test is the signal.

---

## The 5 SWE coding etiquette rules

1. **Clarify the problem first.** "Can the array be empty? Are the numbers positive? Should I handle duplicates?" The questions are the signal.
2. **State the brute force.** "The naive solution is O(n²). Can I do better?" The brute force is the floor.
3. **State the optimized solution.** "I can use a hash table for O(n)." The optimization is the signal.
4. **Walk through the code out loud.** "I start with i=0, j=n-1. While i < j, I swap arr[i] and arr[j]..." The walkthrough is the signal.
5. **Test with edge cases.** "If the array is empty, I return []. If the array has 1 element, I return [arr[0]]." The edge cases are the signal.

---

## How to use this module

1. **Memorize the 8 patterns.** They're the cheat sheet for 80% of SWE coding questions.
2. **Practice 1 problem per pattern.** Total: 8 problems, 30 min each = 4 hours of practice.
3. **Use LeetCode / HackerRank.** The problems are the same; the platform is just the venue.
4. **Rehearse out loud, timed.** 25 minutes per problem. The time pressure is real.
5. **Rehearse with an AI assistant.** Have it score you on the 4 anti-patterns.

---

## The 3 most common SWE coding follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the time + space complexity?" | "O(n) time, O(1) space. The hash table is O(n) but the answer is O(1) because we only store the seen values." |
| 2. "How would you test this?" | "3 cases: empty input, single element, all duplicates. The edge cases are the canary." |
| 3. "How would you scale this to 1B records?" | "External sort + map-reduce. Or a streaming algorithm with O(1) memory. The trade-off is accuracy vs memory." |

**Memorize these 3.** They're the Q&A for 80% of SWE coding follow-ups.
