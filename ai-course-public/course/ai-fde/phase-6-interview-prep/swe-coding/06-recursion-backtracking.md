# SWE Coding Sub-Lesson 6 — Recursion & Backtracking (permutations, combinations, constraint satisfaction)

> **Recursion and backtracking are the sixth most common SWE coding pattern.** 5-10% of LeetCode medium-hard problems are recursion/backtracking problems. The FDE signal: a candidate who can identify the base case + the recursive case, write clean recursive code, and prune the search space — is showing they can solve constraint satisfaction problems. **This sub-lesson covers 3 sub-patterns: permutations, combinations, constraint satisfaction.**

---

## Why recursion + backtracking are the FDE signal

The 3 things the interviewer is testing:

1. **Can you identify the base case + recursive case?** Every recursive function has a base case (when to stop) and a recursive case (how to make progress). The candidate who can name both is showing they understand recursion.
2. **Can you prune the search space?** Backtracking explores all possibilities, then prunes the ones that don't work. The candidate who prunes early is showing they can optimize.
3. **Can you handle the recursion depth?** Python's default recursion limit is 1000. The candidate who mentions `sys.setrecursionlimit()` or iterative alternatives is showing depth.

**The FDE pattern:** clarify → brute force → identify base + recursive cases → prune → code → test. Same as the other patterns, but the structure is recursive.

---

## Sub-pattern 1: Permutations

**The pattern:** generate all orderings of a set. O(n!) time, O(n) space for the recursion stack + output.

**When to use:** permutation problems, all possible orderings, brute force search.

**The template:**

```python
def permutations(nums: list[int]) -> list[list[int]]:
    result = []
    def backtrack(path, remaining):
        if not remaining:
            result.append(path[:])
            return
        for i in range(len(remaining)):
            path.append(remaining[i])
            backtrack(path, remaining[:i] + remaining[i+1:])
            path.pop()
    backtrack([], nums)
    return result
```

**Sample problem 1: Permutations**

> Given an array of distinct integers, return all possible permutations.

```python
def permute(nums: list[int]) -> list[list[int]]:
    result = []
    def backtrack(path, remaining):
        if not remaining:
            result.append(path[:])
            return
        for i in range(len(remaining)):
            path.append(remaining[i])
            backtrack(path, remaining[:i] + remaining[i+1:])
            path.pop()
    backtrack([], nums)
    return result
```

**Time:** O(n × n!). **Space:** O(n) for recursion stack.

**Sample problem 2: Permutations II (with duplicates)**

> Given an array that may contain duplicates, return all unique permutations.

```python
def permute_unique(nums: list[int]) -> list[list[int]]:
    nums.sort()  # Group duplicates
    result = []
    used = [False] * len(nums)
    def backtrack(path):
        if len(path) == len(nums):
            result.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            # Skip duplicates: if same value and previous not used, skip
            if i > 0 and nums[i] == nums[i - 1] and not used[i - 1]:
                continue
            path.append(nums[i])
            used[i] = True
            backtrack(path)
            path.pop()
            used[i] = False
    backtrack([])
    return result
```

**Time:** O(n × n!). **Space:** O(n).

**The 3 edge cases:** empty input, single element, all duplicates.

---

## Sub-pattern 2: Combinations

**The pattern:** generate all subsets of size k. O(2^n) time, O(n) space.

**When to use:** subset problems, choose k from n, brute force search.

**The template:**

```python
def combinations(n: int, k: int) -> list[list[int]]:
    result = []
    def backtrack(start, path):
        if len(path) == k:
            result.append(path[:])
            return
        for i in range(start, n + 1):
            path.append(i)
            backtrack(i + 1, path)
            path.pop()
    backtrack(1, [])
    return result
```

**Sample problem 1: Combinations**

> Given two integers `n` and `k`, return all possible combinations of `k` numbers from `1` to `n`.

```python
def combine(n: int, k: int) -> list[list[int]]:
    result = []
    def backtrack(start, path):
        if len(path) == k:
            result.append(path[:])
            return
        for i in range(start, n + 1):
            path.append(i)
            backtrack(i + 1, path)
            path.pop()
    backtrack(1, [])
    return result
```

**Time:** O(C(n, k) × k). **Space:** O(k).

**Sample problem 2: Subsets**

> Given an array of distinct integers, return all possible subsets (the power set).

```python
def subsets(nums: list[int]) -> list[list[int]]:
    result = []
    def backtrack(start, path):
        result.append(path[:])  # Every state is a valid subset
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()
    backtrack(0, [])
    return result
```

**Time:** O(n × 2^n). **Space:** O(n).

**The 3 edge cases:** empty input, k = 0, k = n.

---

## Sub-pattern 3: Constraint Satisfaction

**The pattern:** find a solution that satisfies all constraints. Exponential time, prune early.

**When to use:** N-Queens, Sudoku, word search, scheduling with constraints.

**The template (N-Queens):**

```python
def solve_n_queens(n: int) -> list[list[str]]:
    result = []
    board = [["."] * n for _ in range(n)]
    cols = set()
    diag1 = set()  # row - col
    diag2 = set()  # row + col

    def backtrack(row):
        if row == n:
            result.append(["".join(row) for row in board])
            return
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            board[row][col] = "Q"
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            backtrack(row + 1)
            board[row][col] = "."
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)

    backtrack(0)
    return result
```

**Sample problem 1: N-Queens**

> Place n queens on an n×n chessboard such that no two queens attack each other. Return all distinct solutions.

(Code above.)

**Time:** O(n!). **Space:** O(n).

**Sample problem 2: Word Search**

> Given a 2D board and a word, find if the word exists in the grid. The word can be constructed from letters of sequentially adjacent cells (horizontally or vertically). The same cell may not be used more than once.

```python
def exist(board: list[list[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])

    def backtrack(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c] != word[idx]:
            return False
        board[r][c] = "#"  # Mark as visited
        found = (backtrack(r + 1, c, idx + 1) or
                 backtrack(r - 1, c, idx + 1) or
                 backtrack(r, c + 1, idx + 1) or
                 backtrack(r, c - 1, idx + 1))
        board[r][c] = word[idx]  # Unmark
        return found

    for r in range(rows):
        for c in range(cols):
            if backtrack(r, c, 0):
                return True
    return False
```

**Time:** O(rows × cols × 4^len(word)). **Space:** O(len(word)).

**The 3 edge cases:** empty board, single character word, no valid path.

---

## The 4-step framework for backtracking

The 4 steps to solve any backtracking problem:

1. **Identify the choices.** What are the possible moves at each step? (e.g., place a queen in any column, try any adjacent cell)
2. **Identify the constraints.** What makes a move invalid? (e.g., column already has a queen, cell is out of bounds)
3. **Identify the goal.** When do we have a valid solution? (e.g., all rows have a queen, all characters matched)
4. **Prune early.** Can we skip choices that can't lead to a solution? (e.g., if remaining characters don't exist on the board, skip)

**The FDE answer:** "The choices are the columns for each row. The constraints are no two queens in the same column, diagonal, or anti-diagonal. The goal is all rows have a queen. I prune by checking the constraints before placing a queen."

---

## The 5 anti-patterns for recursion + backtracking

1. **Jumping to code without identifying the base case.** "I'll just start coding" is a junior answer. The base case is the signal.
2. **Not pruning the search space.** The candidate who explores all possibilities without pruning is signaling they can't optimize.
3. **Forgetting to unmark the cell.** The candidate who marks `board[r][c] = "Q"` but forgets to unmark it is signaling they don't understand backtracking.
4. **Hitting the recursion limit.** Python's default limit is 1000. The candidate who doesn't mention `sys.setrecursionlimit()` is showing they don't think about edge cases.
5. **Not naming the complexity.** "O(n!) time, O(n) space" is the FDE answer. "It's fast" is a junior answer.

---

## The 5 SWE coding etiquette rules for recursion + backtracking

1. **Clarify the problem first.** "Are there duplicates? Should I return all solutions or just one? Are the constraints strict?" The questions are the signal.
2. **State the brute force.** "The naive solution is O(n!) (try all permutations). Can I prune?" The brute force is the floor.
3. **Identify the base case + recursive case.** "The base case is when the path has length n. The recursive case is to try each remaining element." The base + recursive case is the signal.
4. **Walk through the code out loud.** "I start with an empty path. I try the first element. I recurse with the rest..." The walkthrough is the signal.
5. **Test with edge cases.** "If the input is empty, I return [[]]. If k = 0, I return [[]]. If k = n, I return [permutation]." The edge cases are the signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the time + space complexity?" | "O(n!) time, O(n) space for the recursion stack + output. I can prune to O(n! / k!) with early termination." |
| 2. "How would you test this?" | "3 cases: empty input, single element, all duplicates. The edge cases are the canary." |
| 3. "How would you scale this to n = 50?" | "Iterative deepening, memoization, or constraint propagation. For N-Queens specifically, bitmask optimization reduces to O(n!)." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../practical-coding/README.md` | The AI-assisted coding round (the new norm) |
| `../swe-coding/04-trees-graphs.md` | The DFS / BFS / topological sort patterns |
| `../swe-coding/05-dynamic-programming.md` | The memoization / tabulation / state compression patterns |

---

## The thesis

**Recursion and backtracking are the sixth most common SWE coding pattern.** The candidate who can identify the base case + the recursive case, write clean recursive code, and prune the search space — is showing they can solve constraint satisfaction problems.

**The 3 sub-patterns (permutations, combinations, constraint satisfaction) cover 80% of recursion/backtracking problems.** The 5 sample problems (permutations, combinations, subsets, N-Queens, word search) are the muscle memory. Practice them out loud, time yourself at 25 minutes per problem, and rehearse with an AI assistant.

**General prep gets you past the resume screen. SWE coding prep gets you past the classic LeetCode round at Anthropic, OpenAI, Palantir, and AWS FDE.**