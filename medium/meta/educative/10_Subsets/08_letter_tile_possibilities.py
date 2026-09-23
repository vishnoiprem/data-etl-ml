"""
LETTER TILE POSSIBILITIES — LeetCode 1079
You have `tiles` (letters, possibly repeated). Return the number of
NON-EMPTY sequences you can form.

Example
-------
tiles = "AAB"
Answer: 8  →  A, B, AA, AB, BA, AAB, ABA, BAA

This is the HARDEST problem in the folder. Two pitfalls:
  1. Duplicates in `tiles` → "AA" must be counted ONCE.
  2. Order matters ("AB" ≠ "BA") so it's NOT just subsets.
It is the UNION of "subsets" and "permutations": choose a subset of
tiles, then permute it. We can do this in ONE recursion by counting
how many of each letter we still have available.

Pattern: backtrack with a Counter (multi-set backtracking)
---------------------------------------------------------
At every step we pick any letter that still has remaining count > 0,
use one of it, recurse, and put it back. The recursion visits each
unique sequence exactly once, so we don't need an extra dedup set.
"""

from collections import Counter


def num_tile_possibilities(tiles: str) -> int:
    count = Counter(tiles)
    total = 0

    def backtrack():
        nonlocal total
        for ch in count:
            if count[ch] == 0:
                continue
            count[ch] -= 1
            total += 1                  # we just formed a new non-empty seq
            backtrack()                 # extend it further
            count[ch] += 1              # restore

    backtrack()
    return total


if __name__ == "__main__":
    print(num_tile_possibilities("AAB"))  # 8
    print(num_tile_possibilities("AAABBC"))  # 188
