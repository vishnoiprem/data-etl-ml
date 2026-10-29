"""Word Ladder — shortest transformation sequence length.

Time:  O(n² · L) — naive neighbors; can be improved with wildcard buckets
Space: O(n · L) — visited set
"""

from collections import deque


def solve_word_ladder(begin_word, end_word, word_list):
    """Return the length of the shortest transformation, or 0 if none.

    >>> solve_word_ladder("hit", "cog", ["hot","dot","dog","lot","log","cog"])
    5
    """
    word_set = set(word_list)
    if end_word not in word_set:
        return 0
    queue = deque([(begin_word, 1)])
    visited = {begin_word}
    L = len(begin_word)
    while queue:
        word, depth = queue.popleft()
        if word == end_word:
            return depth
        for i in range(L):
            for c in "abcdefghijklmnopqrstuvwxyz":
                if c == word[i]:
                    continue
                candidate = word[:i] + c + word[i + 1:]
                if candidate in word_set and candidate not in visited:
                    visited.add(candidate)
                    queue.append((candidate, depth + 1))
    return 0


if __name__ == "__main__":
    print(solve_word_ladder("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]))
