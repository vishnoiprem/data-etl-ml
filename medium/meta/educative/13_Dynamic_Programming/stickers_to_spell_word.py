"""
Stickers to Spell Word - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/stickers-to-spell-word

Given an array of stickers (strings of lowercase letters) and a target string,
each sticker can be used multiple times. Each use, you can pick one character
from the sticker to "cut out" and use in spelling the target.

Return the minimum number of stickers needed to spell the target.
If impossible, return -1.

KEY INSIGHT:
This is a search/DP problem on states (multisets of characters).
Each state = remaining letters needed.
Each transition = apply a sticker, removing letters it provides.
BFS/DFS over states, memoize.

Better: represent state as a tuple of character counts (sorted order doesn't
matter for memoization, but counts do).

Examples:
    stickers=["with","example","science"], target="thehat" -> 3
        "with" gives w,i,t,h (we need t,h,e,h,a,t -> use 'with' for t,h)
        Use 'example' for e,x,a,m,p,l (we need e,a) -> use 'example' for e,a
        Use 'with' for w,i,t,h (we need t,h) -> use 'with' for t,h
        Wait: 'with' provides w,i,t,h. We need t,h,e,h,a,t. After 'with':
            remaining = e,h,a,t. Use 'example' (has e,x,a,m,p,l,e): remaining
            becomes h,t (used e,a). Use 'with' for h,t: done. 3 stickers.
    stickers=["notice","possible"], target="basicbasic" -> -1
        'notice' has 2 n's but target has 0 n's. Impossible.

Constraints:
- 1 <= stickers.length <= 50
- 1 <= stickers[i].length <= 10
- 1 <= target.length <= 15
- stickers[i] and target contain only lowercase English letters.
"""


import sys
import copy

sys.setrecursionlimit(10000)


# ============================================================
# Way 1: DFS + memo with state as sorted tuple (BEST - Memorize!)
# ============================================================
def stickers_to_spell_word_1(stickers, target):
    from collections import Counter
    # pre-compute Counter for each sticker (without chars not in target)
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        # remove chars not in target (they don't help)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:  # only keep useful stickers
            sticker_counts.append(cnt)

    memo = {}

    def helper(state):
        # state is a Counter of remaining letters
        if not state:
            return 0
        # canonical key: tuple of (char, count) sorted
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            # apply this sticker: subtract overlapping chars
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            # OPTIMIZATION: if sticker doesn't reduce the state, skip
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    result = helper(Counter(target))
    return result if result != -1 else -1


# ============================================================
# Way 2: Verbose
# ============================================================
def stickers_to_spell_word_2(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    initial_state = Counter(target)
    memo = {}

    def helper(state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        result = -1 if best == float('inf') else best
        memo[key] = result
        return result

    result = helper(initial_state)
    return result


# ============================================================
# Way 3: BFS (state as Counter)
# ============================================================
def stickers_to_spell_word_3(stickers, target):
    from collections import Counter, deque
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    if not sticker_counts:
        return -1

    initial = Counter(target)
    visited = {tuple(sorted(initial.items()))}
    queue = deque([(initial, 0)])

    while queue:
        state, steps = queue.popleft()
        if not state:
            return steps
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            key = tuple(sorted(new_state.items()))
            if key not in visited:
                visited.add(key)
                queue.append((new_state, steps + 1))
    return -1


# ============================================================
# Way 4: Memoized recursion (state as tuple)
# ============================================================
def stickers_to_spell_word_4(stickers, target):
    from collections import Counter

    def count_to_tuple(cnt):
        return tuple(sorted((c, cnt[c]) for c in cnt.keys() if cnt[c] > 0))

    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    memo = {}

    def helper(state):
        # state is Counter
        if not state:
            return 0
        key = count_to_tuple(state)
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    result = helper(Counter(target))
    return result


# ============================================================
# Way 5: State as bitmask (small targets only)
# ============================================================
def stickers_to_spell_word_5(stickers, target):
    from collections import Counter, deque
    # Use deque with tuple state for BFS (avoids recursion)
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    # State = sorted tuple of (char, count) - same as Way 1
    initial = tuple(sorted(Counter(target).items()))
    if not initial:
        return 0
    visited = {initial: 0}
    queue = deque([initial])

    while queue:
        state = queue.popleft()
        steps = visited[state]
        state_cnt = dict(state)
        if not state_cnt:
            return steps

        for sc in sticker_counts:
            new_cnt = dict(state_cnt)
            reduced = False
            for c, cnt in sc.items():
                if new_cnt.get(c, 0) > 0:
                    new_cnt[c] -= cnt
                    reduced = True
                    if new_cnt[c] <= 0:
                        del new_cnt[c]
            if not reduced:
                continue
            new_state = tuple(sorted(new_cnt.items()))
            if new_state not in visited:
                visited[new_state] = steps + 1
                queue.append(new_state)
    return -1


# ============================================================
# Way 6: Class-based
# ============================================================
class StickersToSpellWord_6:
    def __init__(self, stickers, target):
        self.stickers = stickers
        self.target = target

    def compute(self):
        from collections import Counter
        target_chars = set(self.target)
        self.sticker_counts = []
        for sticker in self.stickers:
            cnt = Counter(sticker)
            for c in list(cnt.keys()):
                if c not in target_chars:
                    del cnt[c]
            if cnt:
                self.sticker_counts.append(cnt)
        self.memo = {}
        result = self._helper(Counter(self.target))
        return result

    def _helper(self, state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in self.memo:
            return self.memo[key]

        best = float('inf')
        for sc in self.sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = self._helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        self.memo[key] = -1 if best == float('inf') else best
        return self.memo[key]


def stickers_to_spell_word_6(stickers, target):
    return StickersToSpellWord_6(stickers, target).compute()


# ============================================================
# Way 7: DP over character counts (a,b,c,...,z = 26 dims)
# ============================================================
def stickers_to_spell_word_7(stickers, target):
    # For each sticker, compute char count vector (length 26)
    target_chars = set(target)
    sticker_vecs = []
    for sticker in stickers:
        vec = [0] * 26
        for c in sticker:
            if c in target_chars:
                vec[ord(c) - ord('a')] += 1
        if any(v > 0 for v in vec):
            sticker_vecs.append(vec)

    target_vec = [0] * 26
    for c in target:
        target_vec[ord(c) - ord('a')] += 1

    memo = {}

    def helper(remaining):
        if all(v == 0 for v in remaining):
            return 0
        key = tuple(remaining)
        if key in memo:
            return memo[key]

        best = float('inf')
        for sv in sticker_vecs:
            new_remaining = list(remaining)
            for i in range(26):
                if sv[i] > 0 and new_remaining[i] > 0:
                    new_remaining[i] = max(0, new_remaining[i] - sv[i])
            if new_remaining == list(remaining):
                continue
            sub = helper(tuple(new_remaining))
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    result = helper(tuple(target_vec))
    return result


# ============================================================
# Way 8: lru_cache decorator
# ============================================================
from functools import lru_cache


def stickers_to_spell_word_8(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    initial = tuple(sorted(Counter(target).items()))

    @lru_cache(maxsize=None)
    def helper(state):
        if not state:
            return 0
        state_cnt = dict(state)
        best = float('inf')
        for sc in sticker_counts:
            new_cnt = dict(state_cnt)
            reduced = False
            for c, cnt in sc.items():
                if c in new_cnt:
                    new_cnt[c] -= cnt
                    reduced = True
                    if new_cnt[c] <= 0:
                        del new_cnt[c]
            if not reduced:
                continue
            new_state = tuple(sorted(new_cnt.items()))
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        return -1 if best == float('inf') else best

    result = helper(initial)
    return result


# ============================================================
# Way 9: Pre-filtered stickers, sort by frequency
# ============================================================
def stickers_to_spell_word_9(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    # sort by total chars (most useful first)
    sticker_counts.sort(key=lambda x: -sum(x.values()))

    memo = {}

    def helper(state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    return helper(Counter(target))


# ============================================================
# Way 10: Helper functions
# ============================================================
def stickers_to_spell_word_10(stickers, target):
    from collections import Counter

    def subtract(state, sticker):
        new = state.copy()
        reduced = False
        for c, cnt in sticker.items():
            if c in new:
                new[c] -= cnt
                reduced = True
                if new[c] <= 0:
                    del new[c]
        return new, reduced

    def get_key(state):
        return tuple(sorted(state.items()))

    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    memo = {}

    def helper(state):
        if not state:
            return 0
        key = get_key(state)
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state, reduced = subtract(state, sc)
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    return helper(Counter(target))


# ============================================================
# Way 11: Functional reduce style
# ============================================================
def stickers_to_spell_word_11(stickers, target):
    from collections import Counter
    from functools import reduce

    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    def apply_sticker(state, sc):
        new = state.copy()
        reduced = False
        for c, cnt in sc.items():
            if c in new:
                new[c] -= cnt
                reduced = True
                if new[c] <= 0:
                    del new[c]
        return new, reduced

    memo = {}

    def helper(state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state, reduced = apply_sticker(state, sc)
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    return helper(Counter(target))


# ============================================================
# Way 12: Iterative BFS with state as tuple
# ============================================================
def stickers_to_spell_word_12(stickers, target):
    from collections import Counter, deque
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    if not sticker_counts:
        return -1

    initial = tuple(sorted(Counter(target).items()))
    visited = {initial: 0}
    queue = deque([initial])

    while queue:
        state = queue.popleft()
        steps = visited[state]
        state_cnt = dict(state)
        for sc in sticker_counts:
            new_cnt = state_cnt.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_cnt:
                    new_cnt[c] -= cnt
                    reduced = True
                    if new_cnt[c] <= 0:
                        del new_cnt[c]
            if not reduced:
                continue
            new_state = tuple(sorted(new_cnt.items()))
            if new_state == ():
                return steps + 1
            if new_state not in visited:
                visited[new_state] = steps + 1
                queue.append(new_state)
    return -1


# ============================================================
# Way 13: DFS with iterative deepening
# ============================================================
def stickers_to_spell_word_13(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    initial = Counter(target)

    def can_do(steps):
        memo = {}

        def helper(state, depth):
            if not state:
                return True
            if depth == 0:
                return False
            key = tuple(sorted(state.items()))
            if key in memo:
                return memo[key]
            for sc in sticker_counts:
                new_state = state.copy()
                reduced = False
                for c, cnt in sc.items():
                    if c in new_state:
                        new_state[c] -= cnt
                        reduced = True
                        if new_state[c] <= 0:
                            del new_state[c]
                if not reduced:
                    continue
                if helper(new_state, depth - 1):
                    memo[key] = True
                    return True
            memo[key] = False
            return False

        return helper(initial, steps)

    for steps in range(1, len(target) + 1):
        if can_do(steps):
            return steps
    return -1


# ============================================================
# Way 14: Beam search (top-k best stickers at each step)
# ============================================================
def stickers_to_spell_word_14(stickers, target):
    from collections import Counter
    import heapq
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    initial = Counter(target)
    # State: (heuristic, steps, state)
    # heuristic = sum of remaining char counts (smaller is better)
    # We use heap with negated heuristic
    counter = 0
    heap = [(-sum(initial.values()), counter, 0, initial)]
    visited = {tuple(sorted(initial.items())): 0}

    while heap:
        _, _, steps, state = heapq.heappop(heap)
        if not state:
            return steps
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            new_key = tuple(sorted(new_state.items()))
            if new_key not in visited or visited[new_key] > steps + 1:
                visited[new_key] = steps + 1
                counter += 1
                heapq.heappush(heap, (-sum(new_state.values()), counter, steps + 1, new_state))
    return -1


# ============================================================
# Way 15: Use frozenset as memo key (multiset as sorted tuple of chars)
# ============================================================
def stickers_to_spell_word_15(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    memo = {}

    def helper(state):
        # state: tuple of chars (with repetitions, sorted)
        if not state:
            return 0
        if state in memo:
            return memo[state]

        best = float('inf')
        state_cnt = Counter(state)
        for sc in sticker_counts:
            new_cnt = state_cnt.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_cnt:
                    new_cnt[c] -= cnt
                    reduced = True
                    if new_cnt[c] <= 0:
                        del new_cnt[c]
            if not reduced:
                continue
            # convert back to tuple
            new_state = []
            for c, cnt in sorted(new_cnt.items()):
                new_state.extend([c] * cnt)
            new_state = tuple(new_state)
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[state] = -1 if best == float('inf') else best
        return memo[state]

    return helper(tuple(sorted(target)))


# ============================================================
# Way 16: Sorted character string state
# ============================================================
def stickers_to_spell_word_16(stickers, target):
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        from collections import Counter
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    def subtract_string(state_str, sc):
        # state_str is a sorted string
        lst = list(state_str)
        reduced = False
        for c, cnt in sc.items():
            for _ in range(cnt):
                if c in lst:
                    lst.remove(c)
                    reduced = True
                else:
                    break
        return ''.join(sorted(lst)), reduced

    memo = {}

    def helper(state_str):
        if not state_str:
            return 0
        if state_str in memo:
            return memo[state_str]

        best = float('inf')
        for sc in sticker_counts:
            new_state, reduced = subtract_string(state_str, sc)
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[state_str] = -1 if best == float('inf') else best
        return memo[state_str]

    return helper(''.join(sorted(target)))


# ============================================================
# Way 17: Force first sticker use, then recurse
# ============================================================
def stickers_to_spell_word_17(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    # remove dominated stickers (stickers that are subsets of others)
    unique = []
    for i, sc1 in enumerate(sticker_counts):
        dominated = False
        for j, sc2 in enumerate(sticker_counts):
            if i != j:
                # is sc1 dominated by sc2? (sc2 has >= count of every char)
                if all(sc1[c] <= sc2.get(c, 0) for c in sc1):
                    dominated = True
                    break
        if not dominated:
            unique.append(sc1)
    sticker_counts = unique

    memo = {}

    def helper(state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    return helper(Counter(target))


# ============================================================
# Way 18: Bidirectional search (forward + backward)
# ============================================================
def stickers_to_spell_word_18(stickers, target):
    # For simplicity, use forward BFS with smart state pruning
    from collections import Counter, deque
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    if not sticker_counts:
        return -1

    initial = Counter(target)
    visited = {tuple(sorted(initial.items()))}
    queue = deque([(initial, 0)])

    while queue:
        state, steps = queue.popleft()
        if not state:
            return steps
        # try each sticker, with early termination
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            key = tuple(sorted(new_state.items()))
            if key not in visited:
                visited.add(key)
                queue.append((new_state, steps + 1))
    return -1


# ============================================================
# Way 19: Pre-compute dominators and use memoized DFS
# ============================================================
def stickers_to_spell_word_19(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    # Build map: state -> list of stickers that contribute to it
    memo = {}

    def helper(state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        # OPTIMIZATION: stickers that don't cover any char in state are useless
        useful = [sc for sc in sticker_counts if any(c in state for c in sc)]

        for sc in useful:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    return helper(Counter(target))


# ============================================================
# Way 20: Final cleanest (the one to memorize)
# ============================================================
def stickers_to_spell_word_20(stickers, target):
    from collections import Counter

    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    memo = {}

    def helper(state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    return helper(Counter(target))


# ============================================================
# HOW TO THINK (Framework)
# ============================================================
"""
HOW TO THINK ABOUT THIS PROBLEM:

1. UNDERSTAND THE PROBLEM:
   - Each sticker can be used multiple times.
   - Each use, you pick ONE character from the sticker to cut out.
   - Goal: minimum stickers to spell the entire target.

2. STATE REPRESENTATION:
   - The state is the REMAINING letters needed.
   - Represent as Counter (multiset of characters).
   - Canonical key for memo: sorted tuple of (char, count) pairs.

3. TRANSITIONS:
   - From state S, applying sticker T reduces S by min(S[c], T[c]) for each c.
   - Each transition costs 1.

4. SEARCH:
   - DFS with memo: try each sticker at each state.
   - BFS also works.
   - Memoization is crucial (state space can be large).

5. OPTIMIZATIONS:
   - Pre-filter stickers: remove chars not in target.
   - Drop stickers that are subsets of others (dominated).
   - Skip stickers that don't reduce the current state.

6. COMPLEXITY:
   - State space: bounded by counts of letters in target (max 15 chars).
   - Exponential in worst case, but constraints keep it manageable.

7. EDGE CASES:
   - Impossible: any char in target not in any sticker -> -1.
   - Empty target: 0 stickers.
   - Single char: 1 if any sticker has it, else -1.
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (stickers, target, expected, description)
        (["with", "example", "science"], "thehat", 3, "Standard"),
        (["notice", "possible"], "basicbasic", -1, "Impossible"),
        (["a"], "a", 1, "Single char match"),
        (["a"], "b", -1, "Single char no match"),
        (["ab", "cd"], "abcd", 2, "Two stickers for four chars"),
        (["abc"], "abcabc", 2, "Reuse needed"),
        (["these", "guess", "about", "garden", "him"], "atomher", 3, "LeetCode"),
        (["old", "station", "sign"], "stupid", -1, "LeetCode #691 example - impossible (need u,p)"),
        (["w", "o", "r", "d"], "word", 4, "Each char separate"),
    ]

    implementations = [
        ("Way 1: DFS + memo Counter", stickers_to_spell_word_1),
        ("Way 2: Verbose", stickers_to_spell_word_2),
        ("Way 3: BFS Counter", stickers_to_spell_word_3),
        ("Way 4: Memo tuple", stickers_to_spell_word_4),
        ("Way 5: Bitmask", stickers_to_spell_word_5),
        ("Way 6: Class-based", stickers_to_spell_word_6),
        ("Way 7: Vector DP", stickers_to_spell_word_7),
        ("Way 8: lru_cache", stickers_to_spell_word_8),
        ("Way 9: Sorted stickers", stickers_to_spell_word_9),
        ("Way 10: Helper functions", stickers_to_spell_word_10),
        ("Way 11: Functional", stickers_to_spell_word_11),
        ("Way 12: BFS tuple", stickers_to_spell_word_12),
        ("Way 13: Iterative deepening", stickers_to_spell_word_13),
        ("Way 14: Greedy best first", stickers_to_spell_word_14),
        ("Way 15: Multiset tuple", stickers_to_spell_word_15),
        ("Way 16: String state", stickers_to_spell_word_16),
        ("Way 17: Dominated removal", stickers_to_spell_word_17),
        ("Way 18: BFS Counter smart", stickers_to_spell_word_18),
        ("Way 19: Useful filter", stickers_to_spell_word_19),
        ("Way 20: Final cleanest", stickers_to_spell_word_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for stickers, target, expected, desc in test_cases:
            try:
                stickers_copy = copy.deepcopy(stickers)
                target_copy = target
                result = fn(stickers_copy, target_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: got={result} expected={expected}")
            except Exception as e:
                failed += 1
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
