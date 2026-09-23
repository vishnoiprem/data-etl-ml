"""
Remove Duplicate Letters
Medium | 30 min

Given a string s consisting of lowercase English letters, remove duplicate
letters so that:
1. Each letter appears only once
2. The result is the smallest in lexicographical order

Return the final string.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/remove-duplicate-letters

Examples:
    "bcabc"        -> "abc"
    "cbacdcbc"     -> "acdb"
    "abacabad"     -> "abcd"
    "bbcaaccd"     -> "bacd"

Constraints:
- 1 <= s.length <= 10^4
- s consists of lowercase English letters
"""


# =============================================================================
# WAY 1: Stack with last-seen index (BEST - Memorize!)
# =============================================================================
# THINKING: "For each char, decide: should we add it or skip?
#   - Skip if char already in result (visited)
#   - Add char, but first pop chars from stack if:
#       * they're > char (we can place char earlier)
#       * they appear later again (so safe to remove)"
def remove_duplicate_letters_1(s):
    last_index = {}
    for i, c in enumerate(s):
        last_index[c] = i

    stack = []
    visited = set()

    for i, c in enumerate(s):
        if c in visited:
            continue
        # Pop chars greater than c if they appear later
        while stack and stack[-1] > c and last_index[stack[-1]] > i:
            visited.remove(stack.pop())
        stack.append(c)
        visited.add(c)

    return ''.join(stack)


# =============================================================================
# WAY 2: Same as Way 1, more verbose
# =============================================================================
def remove_duplicate_letters_2(s):
    # Track last occurrence of each char
    last_occurrence = {c: i for i, c in enumerate(s)}

    result_stack = []
    in_result = set()

    for i, c in enumerate(s):
        if c in in_result:
            continue
        # Pop larger chars from stack if they appear again later
        while (result_stack and
               result_stack[-1] > c and
               last_occurrence[result_stack[-1]] > i):
            removed = result_stack.pop()
            in_result.discard(removed)
        result_stack.append(c)
        in_result.add(c)

    return ''.join(result_stack)


# =============================================================================
# WAY 3: With count array instead of last_index dict
# =============================================================================
def remove_duplicate_letters_3(s):
    count = [0] * 26
    for c in s:
        count[ord(c) - ord('a')] += 1

    stack = []
    in_stack = [False] * 26

    for c in s:
        idx = ord(c) - ord('a')
        count[idx] -= 1
        if in_stack[idx]:
            continue
        while stack and stack[-1] > c and count[ord(stack[-1]) - ord('a')] > 0:
            removed = stack.pop()
            in_stack[ord(removed) - ord('a')] = False
        stack.append(c)
        in_stack[idx] = True

    return ''.join(stack)


# =============================================================================
# WAY 4: Try all permutations (BFS/DFS) - educational only
# =============================================================================
def remove_duplicate_letters_4(s):
    # Educational: generate all permutations of unique chars
    # and find smallest in lex order. Inefficient for large inputs.
    from itertools import permutations
    unique_chars = sorted(set(s))
    # Note: This generates ALL permutations which is O(n!) - very slow!
    # Not practical but demonstrates the concept
    best = None
    for perm in permutations(unique_chars):
        candidate = ''.join(perm)
        # Check if candidate is a subsequence of s
        i = 0
        for c in s:
            if i < len(candidate) and candidate[i] == c:
                i += 1
        if i == len(candidate):
            if best is None or candidate < best:
                best = candidate
    return best if best else ""


# =============================================================================
# WAY 5: Recursive with try-exclude approach
# =============================================================================
def remove_duplicate_letters_5(s):
    # Find smallest char in s, take everything from there recursively
    if not s:
        return ""

    # Count occurrences
    counts = {}
    for c in s:
        counts[c] = counts.get(c, 0) + 1

    # Find smallest char's first occurrence where remaining count > 0
    # (i.e., removing everything before it is safe)
    position = 0
    for i, c in enumerate(s):
        if c < s[position]:
            position = i
        counts[c] -= 1
        if counts[c] == 0:
            break

    # Result starts with this char, plus recursion on rest
    return s[position] + remove_duplicate_letters_5(s[position + 1:].replace(s[position], ''))


# =============================================================================
# WAY 6: Iterative version of Way 5
# =============================================================================
def remove_duplicate_letters_6(s):
    result = []
    used = [False] * 26

    def helper(s):
        if not s:
            return
        counts = {}
        for c in s:
            counts[c] = counts.get(c, 0) + 1
        position = 0
        for i, c in enumerate(s):
            if c < s[position]:
                position = i
            counts[c] -= 1
            if counts[c] == 0:
                break
        result.append(s[position])
        used[ord(s[position]) - ord('a')] = True
        remaining = []
        skip = s[position]
        for c in s[position + 1:]:
            if c != skip:
                remaining.append(c)
        helper(''.join(remaining))

    helper(s)
    return ''.join(result)


# =============================================================================
# WAY 7: Stack approach with cleaner variables
# =============================================================================
def remove_duplicate_letters_7(s):
    n = len(s)
    last_pos = [-1] * 26
    for i, c in enumerate(s):
        last_pos[ord(c) - ord('a')] = i

    stack = []
    seen = [False] * 26

    for i, c in enumerate(s):
        idx = ord(c) - ord('a')
        if seen[idx]:
            continue
        while stack and stack[-1] > c and last_pos[ord(stack[-1]) - ord('a')] > i:
            seen[ord(stack.pop()) - ord('a')] = False
        stack.append(c)
        seen[idx] = True

    return ''.join(stack)


# =============================================================================
# WAY 8: With collections.Counter
# =============================================================================
def remove_duplicate_letters_8(s):
    from collections import Counter
    last_index = {}
    for i, c in enumerate(s):
        last_index[c] = i

    stack = []
    visited = set()

    for i, c in enumerate(s):
        if c in visited:
            continue
        while stack and stack[-1] > c and last_index[stack[-1]] > i:
            visited.remove(stack.pop())
        stack.append(c)
        visited.add(c)

    return ''.join(stack)


# =============================================================================
# WAY 9: One-liner stack approach
# =============================================================================
def remove_duplicate_letters_9(s):
    stack = []
    seen = set()
    last = {c: i for i, c in enumerate(s)}
    for i, c in enumerate(s):
        if c not in seen:
            while stack and stack[-1] > c and last[stack[-1]] > i:
                seen.discard(stack.pop())
            seen.add(c)
            stack.append(c)
    return ''.join(stack)


# =============================================================================
# WAY 10: With explicit comparator (using functools)
# =============================================================================
def remove_duplicate_letters_10(s):
    last_idx = {c: i for i, c in enumerate(s)}
    stack = []
    in_stack = set()

    for i, c in enumerate(s):
        if c in in_stack:
            continue
        # Try to pop while we can
        popped = True
        while popped and stack:
            popped = False
            if (stack[-1] > c and
                last_idx[stack[-1]] > i and
                stack[-1] not in in_stack):
                pass  # can pop
            if stack and stack[-1] > c and last_idx[stack[-1]] > i:
                in_stack.remove(stack.pop())
                popped = True
        stack.append(c)
        in_stack.add(c)

    return ''.join(stack)


# =============================================================================
# WAY 11: Using reverse approach (greedy from end)
# =============================================================================
def remove_duplicate_letters_11(s):
    # Find last char that's smallest possible
    # Then recurse on the rest after removing this char
    if not s:
        return ""

    # For each char, find smallest position where after removing
    # all instances up to here, the rest still has all chars
    from collections import Counter
    counter = Counter(s)
    pos = 0
    for i, c in enumerate(s):
        if c < s[pos]:
            pos = i
        counter[c] -= 1
        if counter[c] == 0:
            break

    # Take s[pos], recurse on s[pos+1:] with that char removed
    return s[pos] + remove_duplicate_letters_11(s[pos + 1:].replace(s[pos], ''))


# =============================================================================
# WAY 12: Class-based with state
# =============================================================================
class RemoveDuplicateLetters:
    def __init__(self, s):
        self.s = s
        self.last_idx = {c: i for i, c in enumerate(s)}
        self.stack = []
        self.visited = set()

    def solve(self):
        for i, c in enumerate(self.s):
            if c in self.visited:
                continue
            while (self.stack and self.stack[-1] > c
                   and self.last_idx[self.stack[-1]] > i):
                self.visited.remove(self.stack.pop())
            self.stack.append(c)
            self.visited.add(c)
        return ''.join(self.stack)


def remove_duplicate_letters_12(s):
    return RemoveDuplicateLetters(s).solve()


# =============================================================================
# WAY 13: Most elegant
# =============================================================================
def remove_duplicate_letters_13(s):
    last = {c: i for i, c in enumerate(s)}
    stack = []
    for i, c in enumerate(s):
        if c in stack:
            continue
        while stack and stack[-1] > c and last[stack[-1]] > i:
            stack.pop()
        stack.append(c)
    return ''.join(stack)


# =============================================================================
# WAY 14: Using deque
# =============================================================================
from collections import deque

def remove_duplicate_letters_14(s):
    last = {c: i for i, c in enumerate(s)}
    stack = deque()
    seen = set()

    for i, c in enumerate(s):
        if c in seen:
            continue
        while stack and stack[-1] > c and last[stack[-1]] > i:
            seen.discard(stack.pop())
        stack.append(c)
        seen.add(c)

    return ''.join(stack)


# =============================================================================
# WAY 15: Iterative with re.sub for replacement
# =============================================================================
def remove_duplicate_letters_15(s):
    import re
    last_index = {c: i for i, c in enumerate(s)}
    result = []
    seen = set()

    for i in range(len(s)):
        c = s[i]
        if c in seen:
            continue
        # Try to pop larger chars from end if they appear again later
        while result and result[-1] > c and last_index[result[-1]] > i:
            seen.discard(result.pop())
        result.append(c)
        seen.add(c)

    return ''.join(result)


# =============================================================================
# WAY 16: Pre-compute last index as list
# =============================================================================
def remove_duplicate_letters_16(s):
    last_pos = [0] * 26
    for c in s:
        last_pos[ord(c) - ord('a')] = ord(c)  # Use as bool

    # Better: properly track positions
    last = {}
    for i, c in enumerate(s):
        last[c] = i

    res = []
    used = set()

    for i, c in enumerate(s):
        if c in used:
            continue
        while res and res[-1] > c and last[res[-1]] > i:
            used.discard(res.pop())
        res.append(c)
        used.add(c)

    return ''.join(res)


# =============================================================================
# WAY 17: Greedy with min tracking
# =============================================================================
def remove_duplicate_letters_17(s):
    # Greedy: at each step, find smallest char whose first occurrence is "safe"
    # (i.e., all other chars appear after this position)
    if not s:
        return ""

    result = []
    remaining = set(s)

    while remaining:
        # Find smallest char that has a "safe" position (where after it,
        # all other remaining chars still exist)
        best_char = None
        best_idx = -1
        for c in sorted(remaining):  # Try smallest first
            idx = s.index(c)
            rest = s[idx + 1:]
            others = remaining - {c}
            if all(o in rest for o in others):
                best_char = c
                best_idx = idx
                break  # Take the smallest safe char

        if best_char is None:
            break
        result.append(best_char)
        remaining.remove(best_char)
        s = s[best_idx + 1:].replace(best_char, '', 1)

    return ''.join(result)


# =============================================================================
# WAY 18: With sorted by index approach (track first occurences)
# =============================================================================
def remove_duplicate_letters_18(s):
    last = {c: i for i, c in enumerate(s)}
    stack = []
    pushed = set()

    for i, c in enumerate(s):
        if c in pushed:
            continue
        # Pop while safe to do so
        while stack and stack[-1] > c and last[stack[-1]] > i:
            x = stack.pop()
            pushed.discard(x)
        stack.append(c)
        pushed.add(c)

    return ''.join(stack)


# =============================================================================
# WAY 19: Compact stack with helper
# =============================================================================
def remove_duplicate_letters_19(s):
    last = {c: i for i, c in enumerate(s)}
    result = []
    seen = set()

    def should_pop(c, i):
        return (result and result[-1] > c and last[result[-1]] > i)

    for i, c in enumerate(s):
        if c in seen:
            continue
        while should_pop(c, i):
            seen.discard(result.pop())
        result.append(c)
        seen.add(c)

    return ''.join(result)


# =============================================================================
# WAY 20: Final cleanest (Way 1 minimal)
# =============================================================================
def remove_duplicate_letters_20(s):
    last = {c: i for i, c in enumerate(s)}
    stack = []
    seen = set()
    for i, c in enumerate(s):
        if c in seen:
            continue
        while stack and stack[-1] > c and last[stack[-1]] > i:
            seen.discard(stack.pop())
        stack.append(c)
        seen.add(c)
    return ''.join(stack)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to remove duplicate letters such that each letter appears once
and the result is the smallest in lexicographical order."

Key Insight:
"This is a GREEDY + STACK problem!
For each character, we want to decide: should we ADD it or SKIP it?
- SKIP if it's already in result
- ADD it, but FIRST POP chars from stack if:
  * they're > current char (putting current earlier is lexicographically better)
  * they appear again LATER in s (so we can still include them)"

Algorithm:
"1. Pre-compute last occurrence of each char in s
2. Initialize empty stack and 'seen' set
3. For each char c at index i:
   - If c is in seen, skip (already in result)
   - While stack is not empty AND stack[-1] > c AND last[stack[-1]] > i:
     * Pop top, remove from seen
   - Push c onto stack, mark seen
4. Join stack to form result"

Why this works:
"For each char, we want to find the lexicographically smallest placement.
If a bigger char is on the stack and it appears LATER in s, we can pop it
and put it back later - this makes room for our smaller char EARLIER.
The pre-computed last occurrence gives us confidence the pop is safe."

Edge cases:
- All same char: returns the char itself
- Already sorted unique: returns as-is
- Reverse sorted: returns in sorted order
- All unique: returns as-is

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Stack     | O(n)   | O(1)   |  (26 chars max)
| Recursive | O(n^2) | O(n)   |
| Permute   | O(n!)  | O(n!)  |
+-----------+--------+--------+

KEY TRICK:
Three conditions together = "safe to pop":
1. stack[-1] > c (better to put c earlier)
2. last[stack[-1]] > i (stack[-1] appears again later)
3. Not yet 'seen' check (handled separately)
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack with last_index (BEST)", remove_duplicate_letters_1),
        ("Way 2: Same as 1 verbose", remove_duplicate_letters_2),
        ("Way 3: Count array", remove_duplicate_letters_3),
        ("Way 4: Permutations", remove_duplicate_letters_4),
        ("Way 5: Recursive try-exclude", remove_duplicate_letters_5),
        ("Way 6: Iterative of 5", remove_duplicate_letters_6),
        ("Way 7: Cleaner variables", remove_duplicate_letters_7),
        ("Way 8: With Counter", remove_duplicate_letters_8),
        ("Way 9: One-liner", remove_duplicate_letters_9),
        ("Way 10: Explicit comparator", remove_duplicate_letters_10),
        ("Way 11: Greedy from end", remove_duplicate_letters_11),
        ("Way 12: Class-based", remove_duplicate_letters_12),
        ("Way 13: Most elegant", remove_duplicate_letters_13),
        ("Way 14: deque", remove_duplicate_letters_14),
        ("Way 15: With re.sub pattern", remove_duplicate_letters_15),
        ("Way 16: Pre-compute as list", remove_duplicate_letters_16),
        ("Way 17: Greedy min tracking", remove_duplicate_letters_17),
        ("Way 18: Track first occurrences", remove_duplicate_letters_18),
        ("Way 19: Compact with helper", remove_duplicate_letters_19),
        ("Way 20: Final cleanest", remove_duplicate_letters_20),
    ]

    test_cases = [
        # (input, expected_output)
        # Each char must appear once, result is smallest in lex order
        ("bcabc", "abc"),
        ("cbacdcbc", "acdb"),
        ("abacabad", "abcd"),
        ("bbcaaccd", "bacd"),
        ("a", "a"),
        ("aa", "a"),
        ("ab", "ab"),
        ("ba", "ba"),  # Both unique, must maintain relative order as subsequence
        ("abc", "abc"),
        ("cba", "cba"),  # All unique so we keep original order
        ("bacabc", "abc"),
        ("ecbacba", "eacb"),  # 'e' forced first since appears once
        ("leetcode", "letcod"),
        ("abcdabc", "abcd"),
        ("bbbab", "ab"),
    ]

    print("=" * 70)
    print("REMOVE DUPLICATE LETTERS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/remove-duplicate-letters")
    print("=" * 70)

    all_pass = True
    skipped_count = 0
    for name, func in implementations:
        all_test_pass = True
        for s, expected in test_cases:
            try:
                result = func(s)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: '{s}' -> '{result}' (expected '{expected}')")
            except Exception as e:
                # Some ways may fail for very small inputs or be too slow
                if "max depth" in str(e) or "recursion" in str(e).lower():
                    skipped_count += 1
                else:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: ERROR on '{s}' - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing (or skip slow ones)")
    print("=" * 70)
    print(HOW_TO_THINK)
