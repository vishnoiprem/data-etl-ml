"""
FIND THE TOWN JUDGE — LeetCode 997
==================================
In a town there are n people labelled 1..n. `trust[i] = [a, b]` means
person `a` trusts person `b`. A town judge is a person who:
  • trusts nobody (out-degree == 0), AND
  • is trusted by EVERYONE else (in-degree == n - 1).

Return the judge's label, or -1.

Trick: compute in-degree − out-degree for each person.
The judge is the UNIQUE node with score n − 1. If no such node exists
the answer is -1.

Why interviewers ask it
-----------------------
It tests whether you reach for a graph when one isn't strictly needed —
the structure is so simple a counter does the job. Always simplify.
"""

from typing import List


def find_judge(n: int, trust: List[List[int]]) -> int:
    score = [0] * (n + 1)              # index 1..n
    for a, b in trust:
        score[a] -= 1                  # a trusts someone → loses a point
        score[b] += 1                  # b is trusted by someone → gains
    for i in range(1, n + 1):
        if score[i] == n - 1:          # unique judge if such a person exists
            return i
    return -1


if __name__ == "__main__":
    print(find_judge(2, [[1, 2]]))             # 2
    print(find_judge(3, [[1,3],[2,3]]))        # 3
    print(find_judge(3, [[1,3],[2,3],[3,1]]))  # -1
