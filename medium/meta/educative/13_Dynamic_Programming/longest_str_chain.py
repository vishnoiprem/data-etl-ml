"""
Longest String Chain
Medium | 30 min

Given words (array of lowercase strings), word_A is a predecessor of word_B
if exactly one letter can be added anywhere to word_A to get word_B.

Find the length of the longest possible word chain (sequence where each
word is a predecessor of the next). A single word is a chain of length 1.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-string-chain

Constraints:
- 1 <= words.length <= 10^3
- 1 <= words[i].length <= 16
- words[i] consists of lowercase English letters

Examples:
    words=["a","b","ba","bca","bda","bdca"] -> 4
    (b -> bd -> bda -> bdca)
    words=["xbc","pcxbcf","xb","cxbc","pcxbc"] -> 5
    (xb -> xbc -> cxbc -> pcxbc -> pcxbcf)
    words=["abcd","dbqca"] -> 1

Key Insight:
Sort words by length. For each word, check all possible predecessors
(remove each character) and use DP: dp[word] = max chain ending at word.

dp[word] = 1 + max(dp[predecessor]) for valid predecessors, else 1.

Time:  O(n * L^2) where L = max word length (16).
Space: O(n) for dp.
"""


# =============================================================================
# WAY 1: Sort + DP with hashmap (BEST - Memorize!)
# =============================================================================
def longest_str_chain_1(words):
    """
    Sort by length. For each word, check predecessors (remove each char).
    """
    words.sort(key=len)
    dp = {}
    longest = 1
    for word in words:
        chain_len = 1
        # Try removing each character to find predecessors
        for i in range(len(word)):
            pred = word[:i] + word[i + 1:]
            if pred in dp:
                chain_len = max(chain_len, dp[pred] + 1)
        dp[word] = chain_len
        longest = max(longest, chain_len)
    return longest


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def longest_str_chain_2(words):
    """Verbose."""
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
        if chain_len > longest:
            longest = chain_len
    return longest


# =============================================================================
# WAY 3: Brute force - try all orderings (exponential)
# =============================================================================
def longest_str_chain_3(words):
    """Brute force recursion with memo."""

    word_set = set(words)
    memo = {}

    def dfs(word):
        if word in memo:
            return memo[word]
        if word not in word_set:
            memo[word] = 0
            return 0
        max_chain = 1
        # Try inserting each letter at each position to find successors
        for i in range(len(word) + 1):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                longer = word[:i] + c + word[i:]
                if longer in word_set:
                    max_chain = max(max_chain, 1 + dfs(longer))
        memo[word] = max_chain
        return max_chain

    # Start from each word
    best = 0
    for w in words:
        best = max(best, dfs(w))
    return best


# =============================================================================
# WAY 4: Sort + DP with cached predecessors
# =============================================================================
def longest_str_chain_4(words):
    """Same as Way 1 but explicit cache."""

    def predecessors(word):
        """Generate all predecessors of word."""
        preds = []
        for i in range(len(word)):
            preds.append(word[:i] + word[i + 1:])
        return preds

    words.sort(key=len)
    dp = {}
    for word in words:
        best = 1
        for pred in predecessors(word):
            if pred in dp:
                best = max(best, dp[pred] + 1)
        dp[word] = best
    return max(dp.values()) if dp else 1


# =============================================================================
# WAY 5: Group by length, BFS within groups
# =============================================================================
def longest_str_chain_5(words):
    """Group by length, build DAG, find longest path."""
    if not words:
        return 0
    word_set = set(words)
    # For each word, find longer successors
    # dp[word] = longest chain starting at word (going to longer words)
    dp = {}

    def longest_from(word):
        if word not in word_set:
            return 0
        if word in dp:
            return dp[word]
        max_len = 1
        # Try adding each letter at each position
        for i in range(len(word) + 1):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                longer = word[:i] + c + word[i:]
                if longer in word_set:
                    max_len = max(max_len, 1 + longest_from(longer))
        dp[word] = max_len
        return max_len

    return max(longest_from(w) for w in words)


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class StringChainFinder:
    def __init__(self, words):
        self.words = words

    def find(self):
        words = sorted(self.words, key=len)
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


def longest_str_chain_6(words):
    """Class-based."""
    return StringChainFinder(words).find()


# =============================================================================
# WAY 7: numpy version
# =============================================================================
def longest_str_chain_7(words):
    """Vectorized with numpy (limited usefulness here)."""
    try:
        import numpy as np
        words = sorted(words, key=len)
        dp = {}
        for word in words:
            best = 1
            for i in range(len(word)):
                pred = word[:i] + word[i + 1:]
                if pred in dp:
                    best = max(best, dp[pred] + 1)
            dp[word] = best
        return max(dp.values()) if dp else 1
    except ImportError:
        return longest_str_chain_1(words)


# =============================================================================
# WAY 8: With cache decorator
# =============================================================================
def longest_str_chain_8(words):
    """Use functools.lru_cache."""
    from functools import lru_cache
    word_set = set(words)

    @lru_cache(maxsize=None)
    def longest_from(word):
        if word not in word_set:
            return 0
        max_len = 1
        for i in range(len(word) + 1):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                longer = word[:i] + c + word[i:]
                if longer in word_set:
                    max_len = max(max_len, 1 + longest_from(longer))
        return max_len

    return max(longest_from(w) for w in words)


# =============================================================================
# WAY 9: enumerate
# =============================================================================
def longest_str_chain_9(words):
    """Use enumerate."""
    words.sort(key=len)
    dp = {}
    longest = 1
    for word in words:
        chain_len = 1
        for i, _ in enumerate(word):
            pred = word[:i] + word[i + 1:]
            if pred in dp:
                chain_len = max(chain_len, dp[pred] + 1)
        dp[word] = chain_len
        longest = max(longest, chain_len)
    return longest


# =============================================================================
# WAY 10: Helper function approach
# =============================================================================
def longest_str_chain_10(words):
    """Extract helpers."""

    def get_predecessors(word):
        return [word[:i] + word[i + 1:] for i in range(len(word))]

    def chain_length(word, dp):
        best = 1
        for pred in get_predecessors(word):
            if pred in dp:
                best = max(best, dp[pred] + 1)
        return best

    words.sort(key=len)
    dp = {}
    for word in words:
        dp[word] = chain_length(word, dp)
    return max(dp.values()) if dp else 1


# =============================================================================
# WAY 11: Functional with map
# =============================================================================
def longest_str_chain_11(words):
    """Functional style."""
    words.sort(key=len)
    dp = {}
    for word in words:
        preds = [word[:i] + word[i + 1:] for i in range(len(word))]
        candidates = [dp[p] + 1 for p in preds if p in dp]
        dp[word] = max(candidates) if candidates else 1
    return max(dp.values()) if dp else 1


# =============================================================================
# WAY 12: One-liner with sorted
# =============================================================================
def longest_str_chain_12(words):
    """Concise one-liner."""
    words.sort(key=len)
    dp = {}
    for w in words:
        dp[w] = max((dp.get(w[:i] + w[i + 1:], 0) for i in range(len(w))), default=0) + 1
    return max(dp.values()) if dp else 1


# =============================================================================
# WAY 13: BFS approach
# =============================================================================
def longest_str_chain_13(words):
    """BFS from shortest to longest."""
    if not words:
        return 0
    word_set = set(words)
    # Build adjacency: predecessor -> [successors]
    successors = {}
    for word in words:
        for i in range(len(word)):
            pred = word[:i] + word[i + 1:]
            if pred in word_set:
                successors.setdefault(pred, []).append(word)

    # BFS from each word with no predecessors
    longest = 1
    for w in words:
        if not successors.get(w):  # No longer successors
            continue
        # BFS from w
        depth = {w: 1}
        from collections import deque
        queue = deque([w])
        while queue:
            node = queue.popleft()
            for succ in successors.get(node, []):
                if succ not in depth or depth[node] + 1 > depth[succ]:
                    depth[succ] = depth[node] + 1
                    queue.append(succ)
        if depth:
            longest = max(longest, max(depth.values()))
    return longest


# =============================================================================
# WAY 14: defaultdict
# =============================================================================
def longest_str_chain_14(words):
    """Use defaultdict."""
    from collections import defaultdict
    words.sort(key=len)
    dp = defaultdict(int)
    longest = 1
    for word in words:
        for i in range(len(word)):
            pred = word[:i] + word[i + 1:]
            if pred in dp:
                dp[word] = max(dp[word], dp[pred] + 1)
        if dp[word] == 0:
            dp[word] = 1
        longest = max(longest, dp[word])
    return longest


# =============================================================================
# WAY 15: Iterative DAG longest path
# =============================================================================
def longest_str_chain_15(words):
    """Find longest path in DAG."""
    if not words:
        return 0
    word_set = set(words)
    # Build adjacency
    successors = {}
    for word in words:
        for i in range(len(word)):
            pred = word[:i] + word[i + 1:]
            if pred in word_set:
                successors.setdefault(pred, []).append(word)

    # DP: longest chain starting from each node
    memo = {}

    def longest_from(node):
        if node in memo:
            return memo[node]
        max_len = 1
        for succ in successors.get(node, []):
            max_len = max(max_len, 1 + longest_from(succ))
        memo[node] = max_len
        return max_len

    return max(longest_from(w) for w in words)


# =============================================================================
# WAY 16: With reversed direction (successors)
# =============================================================================
def longest_str_chain_16(words):
    """Build successors (longer) and compute dp from longest."""
    word_set = set(words)
    # Sort by length descending
    words_sorted = sorted(words, key=len, reverse=True)
    dp = {}
    for word in words_sorted:
        best = 1
        # Look for longer successors
        for i in range(len(word) + 1):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                longer = word[:i] + c + word[i:]
                if longer in word_set:
                    best = max(best, 1 + dp.get(longer, 0))
        dp[word] = best
    return max(dp.values()) if dp else 1


# =============================================================================
# WAY 17: With while loop
# =============================================================================
def longest_str_chain_17(words):
    """While loop variant."""
    words.sort(key=len)
    dp = {}
    for word in words:
        chain_len = 1
        i = 0
        while i < len(word):
            pred = word[:i] + word[i + 1:]
            if pred in dp:
                chain_len = max(chain_len, dp[pred] + 1)
            i += 1
        dp[word] = chain_len
    return max(dp.values()) if dp else 1


# =============================================================================
# WAY 18: Tabulation with index pointer
# =============================================================================
def longest_str_chain_18(words):
    """Tabulation with index."""
    if not words:
        return 0
    # Group by length
    by_len = {}
    for w in words:
        by_len.setdefault(len(w), []).append(w)

    # Sort all lengths
    lengths = sorted(by_len.keys())

    # dp[word] = max chain length ending at word
    dp = {}
    longest = 1
    for length in lengths:
        for word in by_len[length]:
            if length == lengths[0]:
                dp[word] = 1
                continue
            best = 1
            for i in range(length):
                pred = word[:i] + word[i + 1:]
                if pred in dp:
                    best = max(best, dp[pred] + 1)
            dp[word] = best
            longest = max(longest, best)
    return longest


# =============================================================================
# WAY 19: Most concise (using dict.get)
# =============================================================================
def longest_str_chain_19(words):
    """Use dict.get for cleaner code."""
    words.sort(key=len)
    dp = {}
    for w in words:
        dp[w] = max((dp.get(w[:i] + w[i + 1:], 0) for i in range(len(w))), default=0) + 1
    return max(dp.values())


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def longest_str_chain_20(words):
    """
    Final clean version.

    Algorithm:
    1. Sort words by length (shortest to longest).
    2. For each word, check all possible predecessors (by removing each char).
    3. dp[word] = max chain length ending at word.
       = 1 + max(dp[pred]) for valid predecessor, else 1.
    4. Track overall maximum.

    Why this works:
    - A chain is shortest to longest. Sorting ensures predecessors are
      processed before successors.
    - For each word, its predecessors are exactly L candidates (one per
      character removal). Check each in O(1) via hashmap.

    Time:  O(n * L) where L = max word length (16).
    Space: O(n * L) for dp.

    Edge cases:
    - Single word: return 1.
    - No chain possible: each word has chain length 1.
    - All same length: return 1 (no predecessors possible).
    """
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


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the longest chain where each word is a predecessor of the
next (one letter can be added to form the next word)."

Key Insight:
"Sort by length. For each word, check predecessors (remove each character).
Use DP: dp[word] = max chain length ending at word."

Algorithm:
"1. Sort words by length.
2. For each word:
   a. Try removing each character to get a predecessor.
   b. If predecessor is in dp, update chain_len.
   c. dp[word] = chain_len (default 1).
3. Track maximum across all words."

Why this works:
"A chain goes from short to long. By sorting, we process predecessors
before successors. For each word, we know the chain length of all its
potential predecessors."

Edge cases:
- Single word: return 1.
- All same length: return 1 (no predecessors possible).
- No chain: each word is its own chain of length 1.

Complexity:
- Time:  O(n * L) — L = max word length (16).
- Space: O(n * L) for dp.

KEY TRICK:
Sort by length ensures dp[pred] is computed BEFORE dp[word] (since pred is
shorter than word by exactly 1).

ALTERNATIVE: BFS / longest path in DAG
Build a graph of predecessor -> successor, find longest path.

ALTERNATIVE: Recursive with memo
Top-down dp. Same complexity.

INTERVIEW TIPS:
1. Sort by length FIRST.
2. Use a hashmap (dict) for O(1) predecessor lookup.
3. For each word, generate all L predecessors by removing each character.

RELATIONSHIP TO OTHER PROBLEMS:
- Longest Increasing Subsequence (LIS): Similar DP structure.
- Longest Common Subsequence: Different but similar DP.
- Word Ladder: Similar predecessor/successor concept.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + DP (BEST)", longest_str_chain_1),
        ("Way 2: Verbose", longest_str_chain_2),
        ("Way 3: Brute force", longest_str_chain_3),
        ("Way 4: Sort + DP cached", longest_str_chain_4),
        ("Way 5: Group + BFS", longest_str_chain_5),
        ("Way 6: Class-based", longest_str_chain_6),
        ("Way 7: numpy", longest_str_chain_7),
        ("Way 8: lru_cache", longest_str_chain_8),
        ("Way 9: enumerate", longest_str_chain_9),
        ("Way 10: Helper functions", longest_str_chain_10),
        ("Way 11: Functional map", longest_str_chain_11),
        ("Way 12: One-liner", longest_str_chain_12),
        ("Way 13: BFS", longest_str_chain_13),
        ("Way 14: defaultdict", longest_str_chain_14),
        ("Way 15: DAG longest path", longest_str_chain_15),
        ("Way 16: Reversed direction", longest_str_chain_16),
        ("Way 17: While loop", longest_str_chain_17),
        ("Way 18: Tabulation by len", longest_str_chain_18),
        ("Way 19: Most concise", longest_str_chain_19),
        ("Way 20: Final cleanest", longest_str_chain_20),
    ]

    test_cases = [
        # Standard example 1
        # ["a","b","ba","bca","bda","bdca"]
        # Chains: a -> ba -> bda -> bdca (length 4)
        #         a -> ba -> bca -> bdca? Wait bca -> bdca? bca -> bdca?
        #         bca = 'b','c','a'. bdca = 'b','d','c','a'. Adding 'd' at position 2 gives b,c,d,a = bcda. Not bdca.
        #         Actually let me trace: a -> ba (add b), ba -> bda (add d), bda -> bdca (add c). Length 4.
        #         Or: a -> ba (add b), ba -> bca (add c), bca -> bdca (add d). Length 4.
        (["a", "b", "ba", "bca", "bda", "bdca"], 4),

        # Standard example 2
        # ["xbc","pcxbcf","xb","cxbc","pcxbc"]
        # xb -> xbc -> cxbc -> pcxbc -> pcxbcf (length 5)
        (["xbc", "pcxbcf", "xb", "cxbc", "pcxbc"], 5),

        # No chain
        # ["abcd","dbqca"] - no relation. Each chain length 1.
        (["abcd", "dbqca"], 1),

        # Single word
        (["a"], 1),

        # Two unrelated words
        (["abc", "def"], 1),

        # Simple chain
        # a -> ab -> abc -> abcd (length 4)
        (["a", "ab", "abc", "abcd"], 4),

        # All same length (no chain possible)
        (["abc", "def", "ghi"], 1),

        # Complex
        # ["a","b","ba","bca","bda","bdca","bdcab","bdcaba"]
        # Longest: bdca -> bdcab -> bdcaba (length 3)
        # Or bda -> bdca -> bdcab -> bdcaba (length 4)
        # Or ba -> bda -> bdca -> bdcab -> bdcaba (length 5)
        # Or a -> ba -> bda -> bdca -> bdcab -> bdcaba (length 6)
        # Let me trace: a (1), b (1), ba (max(a,b)+1=2), bda (max(ba)+1=3), bca (max(ba)+1=3),
        # bdca (max(bda,bca)+1=4), bdcab (max(bdca)+1=5), bdcaba (max(bdcab)+1=6).
        # Answer: 6.
        (["a", "b", "ba", "bca", "bda", "bdca", "bdcab", "bdcaba"], 6),
    ]

    print("=" * 70)
    print("LONGEST STRING CHAIN - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-string-chain")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for words, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(words))
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: words={words} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on words={words} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)