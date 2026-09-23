"""
REORGANIZE STRING — LeetCode 767
===============================
Rearrange a string so that no two ADJACENT characters are equal. If
impossible, return the empty string. Otherwise any valid arrangement
suffices.

Pattern: MAX-heap of (count, character), plus a COOL-DOWN QUEUE.
    1. Always pop the most frequent remaining char, append it.
    2. Push back the previously-used char (with its count - 1) — but
       only AFTER one step, so the same char can't repeat.

Why a queue? Because if we push the char back IMMEDIATELY, we'd pop
the same char again and place it adjacent to itself.

Special case: if a single char appears more than (n+1)/2 times, no
rearrangement exists.
"""

from collections import Counter, deque
import heapq
from typing import Dict


def reorganize_string(s: str) -> str:
    n = len(s)
    counts: Dict[str, int] = Counter(s)

    # Feasibility check — the most frequent char can't exceed half (rounded up).
    if max(counts.values()) > (n + 1) // 2:
        return ""

    # Max-heap keyed on (-count, char) for stable deterministic output.
    heap = [(-c, ch) for ch, c in counts.items()]
    heapq.heapify(heap)
    wait = deque()                                 # pairs of (entry, char)
    out = []

    while heap:
        neg_c, ch = heapq.heappop(heap)
        out.append(ch)
        wait.append((neg_c + 1, ch))               # decrement count

        # Only release an entry back into the heap after one step,
        # unless the heap is empty (we'd lose the last char).
        if len(wait) > 1 or not heap:
            neg_c2, ch2 = wait.popleft()
            if neg_c2 < 0:                          # still has remaining count
                heapq.heappush(heap, (neg_c2, ch2))
    return "".join(out)


if __name__ == "__main__":
    print(reorganize_string("aab"))           # "aba"
    print(reorganize_string("aaab"))          # ""  (impossible)
    print(reorganize_string("vvvlo"))         # "vlvov" or similar
