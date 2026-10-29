# Longest String Chain - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/longest-string-chain

## The Problem
```
Given words (array of lowercase strings), word_A is a predecessor of word_B
if exactly one letter can be added to word_A anywhere to get word_B.

Find the length of the longest possible word chain.

Examples:
    words=["a","b","ba","bca","bda","bdca"] -> 4
    (a -> ba -> bda -> bdca)
    words=["xbc","pcxbcf","xb","cxbc","pcxbc"] -> 5
    (xb -> xbc -> cxbc -> pcxbc -> pcxbcf)

Constraints:
- 1 <= words.length <= 10^3
- 1 <= words[i].length <= 16
- words[i] lowercase English letters
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Each word has length L. A predecessor is a word of length L-1 that, after
removing exactly one letter, becomes the longer word. We want the longest
sequence of such relations.
```

### Step 2: The Trick
> "KEY INSIGHT: Sort by length (shortest to longest). For each word,
> check all possible predecessors (remove each character).
>
> dp[word] = max chain length ending at word.
> dp[word] = max(1, dp[pred] + 1) over all valid predecessors."

### Step 3: Why sort by length?
> "A chain goes from shortest to longest. Sorting ensures predecessors
> are processed before successors, so dp[pred] is already known when
> we compute dp[word]."

### Step 4: Algorithm
> "1. Sort words by length.
> 2. For each word:
>    a. For each character position, generate predecessor by removing
>       that character.
>    b. If predecessor in dp, update chain_len = max(chain_len, dp[pred] + 1).
>    c. dp[word] = chain_len (default 1).
> 3. Return max(dp.values())."

### Step 5: Edge cases
> "- Single word: return 1.
> - No chain: each word is its own chain of length 1.
> - All same length: return 1 (no predecessor possible)."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the longest chain where each word is a predecessor of the next."

**Key Insight:**
> "Sort by length. For each word, check predecessors (remove each char). dp[word] = max chain length ending at word."

**Algorithm:**
> "1. Sort words by length.
> 2. For each word: generate L predecessors by removing each character. dp[word] = max(dp[pred]+1) over valid preds, else 1.
> 3. Return max."

**Why this works:**
> "Chains go shortest to longest. By sorting, predecessors are processed first. For each word, we know all predecessor chain lengths."

**Edge cases:**
- Single word: 1.
- All same length: 1.
- No relations: 1.

**Complexity:**
- Time:  O(n * L) — L = max word length (16).
- Space: O(n * L) for dp.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + DP with hashmap (BEST - Memorize!)
```python
def longest_str_chain_1(words):
    words.sort(key=len)
    dp = {}
    longest = 1
    for word in words:
        chain_len = 1
        for i in range(len(word)):
            pred = word[:i] + word[i + 1:]
            if pred in dp:
                chain_len = max(chain_len, dp[pred] + 1)
        dp[word] = chain_len
        longest = max(longest, chain_len)
    return longest
```

### Way 2: Verbose
### Way 3: Brute force (top-down memo)
### Way 4: Sort + DP cached
### Way 5: Group by length + BFS
### Way 6: Class-based
### Way 7: numpy
### Way 8: lru_cache
### Way 9: enumerate
### Way 10: Helper functions
### Way 11: Functional map
### Way 12: One-liner
### Way 13: BFS
### Way 14: defaultdict
### Way 15: DAG longest path
### Way 16: Reversed direction
### Way 17: While loop
### Way 18: Tabulation by length
### Way 19: Most concise
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Sort + DP    |
| Top-down           | Way 3    | Memoization  |
| DAG-based          | Way 15   | Graph theory |
| Pythonic           | Way 19   | Concise      |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + DP (Way 1) | O(n * L) | O(n * L) | Best |
| Top-down memo (Way 3) | O(n * L * 26) | O(n * L) | Slower |
| BFS (Way 13) | O(n * L) | O(n * L) | Same |

---

## Walkthrough Example

```
words = ["a","b","ba","bca","bda","bdca"]
sorted by length: ["a","b","ba","bca","bda","bdca"]

dp:
  "a": no preds. dp["a"] = 1.
  "b": no preds. dp["b"] = 1.
  "ba": preds = ["a"]. dp["a"]=1. dp["ba"] = 1+1 = 2.
  "bca": preds = ["ba","bc","bca"-"a"="bc", "bca"-"c"="ba", "bca"-"a"="bc"]
    Wait preds from removing each char:
    Remove 'b': "ca" - not in set.
    Remove 'c': "ba" - in set, dp=2.
    Remove 'a': "bc" - not in set.
    So preds in dp: "ba" -> 2. dp["bca"] = 2+1 = 3.
  "bda": preds by removing each char:
    "da" (not), "ba" (dp=2), "bd" (not). dp["bda"] = 2+1 = 3.
  "bdca": preds:
    "dca" (not), "bca" (dp=3), "bda" (dp=3), "bdc" (not). 
    dp["bdca"] = 3+1 = 4.

Max = 4. ✓
```

---

## Best Answer to Memorize

```python
def longestStrChain(words):
    words.sort(key=len)
    dp = {}
    longest = 1
    for word in words:
        chain_len = 1
        for i in range(len(word)):
            pred = word[:i] + word[i + 1:]
            if pred in dp:
                chain_len = max(chain_len, dp[pred] + 1)
        dp[word] = chain_len
        longest = max(longest, chain_len)
    return longest
```

**~10 lines. O(n * L) time. O(n * L) space. Interview-ready!**

---

## Key Insights

### Why sort by length?
> "Chains go shortest to longest. Sorting guarantees predecessors are
> processed before their successors, so dp[pred] is known when computing
> dp[word]."

### Why remove each character?
> "A predecessor has length L-1 and differs by exactly one letter. There are
> exactly L possible predecessors (one per character removal)."

### Why hashmap for dp?
> "O(1) predecessor lookup. Without hashmap, we'd scan all words (O(n) per
> lookup, giving O(n^2 * L) total)."

### Why default chain_len = 1?
> "Every word is at least a chain of length 1 (itself)."

### What if all words same length?
> "No chain possible (predecessor has different length). All dp values = 1.
> Return 1."

### What's the optimal substructure?
> "dp[word] = 1 + max(dp[pred]) for valid predecessors. Each subproblem is
> independent once predecessors are computed."

---

## Test Cases

| words | Expected | Notes |
|-------|----------|-------|
| ["a","b","ba","bca","bda","bdca"] | 4 | Standard |
| ["xbc","pcxbcf","xb","cxbc","pcxbc"] | 5 | Standard |
| ["abcd","dbqca"] | 1 | No relation |
| ["a"] | 1 | Single |
| ["abc","def"] | 1 | Two unrelated |
| ["a","ab","abc","abcd"] | 4 | Simple chain |
| ["abc","def","ghi"] | 1 | All same length |
| ["a","b","ba","bca","bda","bdca","bdcab","bdcaba"] | 6 | Long |

---

## Common Pitfalls

1. **Not sorting**: Without sort, predecessors may not be computed yet.
2. **Wrong predecessor**: Removing each char is correct; inserting each char into all positions is the inverse.
3. **Hashmap vs set confusion**: dp is a hashmap (word -> chain length), not just a set.
4. **Default chain length**: Always 1, not 0.
5. **Forgetting max**: Return max over all dp values, not just the last.

---

## Why This Problem Matters

> "Tests:
> 1. Sort + DP combination.
> 2. Hashmap for O(1) lookup.
> 3. String manipulation.
> 4. Foundation for: longest path in DAG, word ladder."

---

## Beyond This Problem: Related Patterns

### 1. Longest Increasing Subsequence (LC 300)
```python
# Same structure: sort (or not), DP with predecessor.
```

### 2. Word Ladder (LC 127)
```python
# BFS through word transformations.
```

### 3. Russian Doll Envelopes (LC 354)
```python
# Sort by one dimension, LIS on other.
```

### 4. Longest Chain of Pairs (variation)
```python
# Similar: chain pairs where one fits inside another.
```

---

## Connection to Longest Path in DAG

This problem is finding the longest path in a DAG:

```
DAG CONSTRUCTION:
- Node: each word.
- Edge: word_A -> word_B if word_A is predecessor of word_B.
- DAG because lengths strictly increase along edges.

LONGEST PATH:
- Topological order: by length (since edges increase length).
- dp[word] = 1 + max(dp[pred]).
```

The sort by length gives a topological order, enabling bottom-up DP.

---

## Quick Checklist

When given a similar problem:
- [ ] What's the predecessor relation?
- [ ] Does sorting by some property give topological order?
- [ ] Define dp[word] clearly.
- [ ] Generate all valid predecessors (or successors).
- [ ] Use hashmap for O(1) lookup.
- [ ] Return max over all dp values.
- [ ] Default chain_len = 1 (single word is a chain).

---

## Mathematical Formulation

Given words W, define a DAG where edge w_A -> w_B iff w_A is predecessor of w_B:

```
dp[w] = 1 + max(dp[p] for p in predecessors(w))
dp[w] = 1 if w has no predecessors in W

Answer = max(dp[w] for w in W).
```

The DAG is acyclic because edge length increases by exactly 1, so paths
have bounded length.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1048 - Longest String Chain](https://leetcode.com/problems/longest-string-chain/)