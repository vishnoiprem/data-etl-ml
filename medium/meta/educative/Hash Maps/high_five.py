"""
High Five
Easy | 15 min

Given a list of [ID, score] pairs, compute the top 5 average score for each
student. Return result sorted by ID.

Top 5 average = sum of top 5 scores / 5 (integer division)

Constraints:
- 1 <= items.length <= 1000
- 1 <= ID <= 1000
- 0 <= score <= 100
- Each ID has at least 5 scores

Example:
    items = [[1,91],[1,92],[2,93],[2,97],[1,60],
             [2,77],[1,65],[1,87],[1,100],[2,100],[2,98]]
    Output: [[1,87],[2,93]]
"""

import heapq
from collections import defaultdict, Counter


# =============================================================================
# WAY 1: defaultdict + sort (Cleanest - Memorize!)
# =============================================================================
# THINKING: "Group by ID, then take top 5 from each group."
def high_five_1(items):
    scores = defaultdict(list)
    for item_id, score in items:
        scores[item_id].append(score)

    result = []
    for student_id in sorted(scores.keys()):
        top_five = sorted(scores[student_id], reverse=True)[:5]
        result.append([student_id, sum(top_five) // 5])

    return result


# =============================================================================
# WAY 2: Manual Dictionary
# =============================================================================
def high_five_2(items):
    scores = {}
    for item_id, score in items:
        if item_id not in scores:
            scores[item_id] = []
        scores[item_id].append(score)

    result = []
    for student_id in sorted(scores.keys()):
        top_five = sorted(scores[item_id], reverse=True)[:5]
        result.append([student_id, sum(top_five) // 5])

    return result


# =============================================================================
# WAY 3: Using heapq (Efficient for top-K)
# =============================================================================
def high_five_3(items):
    scores = defaultdict(list)
    for item_id, score in items:
        heapq.heappush(scores[item_id], score)
        # Keep only top 5 by popping smallest if we have more
        if len(scores[item_id]) > 5:
            heapq.heappop(scores[item_id])

    result = []
    for student_id in sorted(scores.keys()):
        top_five = scores[item_id]
        result.append([student_id, sum(top_five) // 5])

    return result


# =============================================================================
# WAY 4: Dict + min-heap per student
# =============================================================================
def high_five_4(items):
    scores = {}
    for item_id, score in items:
        if item_id not in scores:
            scores[item_id] = []
        heapq.heappush(scores[item_id], score)
        if len(scores[item_id]) > 5:
            heapq.heappop(scores[item_id])

    result = []
    for student_id in sorted(scores.keys()):
        result.append([student_id, sum(scores[item_id]) // 5])

    return result


# =============================================================================
# WAY 5: Counter-based
# =============================================================================
def high_five_5(items):
    scores = {}
    for item_id, score in items:
        if item_id not in scores:
            scores[item_id] = []
        scores[item_id].append(score)

    result = []
    for student_id in sorted(scores.keys()):
        student_scores = sorted(scores[item_id], reverse=True)[:5]
        avg = sum(student_scores) // 5
        result.append([student_id, avg])

    return result


# =============================================================================
# WAY 6: Using list comprehension
# =============================================================================
def high_five_6(items):
    scores = defaultdict(list)
    for item_id, score in items:
        scores[item_id].append(score)

    return [[student_id, sum(sorted(s, reverse=True)[:5]) // 5]
            for student_id in sorted(scores.keys())]


# =============================================================================
# WAY 7: Compact one-liner style
# =============================================================================
def high_five_7(items):
    d = defaultdict(list)
    for i, s in items:
        d[i].append(s)
    return [[k, sum(sorted(v, reverse=True)[:5]) // 5] for k in sorted(d)]


# =============================================================================
# WAY 8: With sorted and zip
# =============================================================================
def high_five_8(items):
    scores = defaultdict(list)
    for item_id, score in items:
        scores[item_id].append(score)

    result = []
    for student_id in sorted(scores):
        top_5 = sorted(scores[student_id], reverse=True)[:5]
        result.append([student_id, sum(top_5) // 5])
    return result


# =============================================================================
# WAY 9: Explicit top-5 calculation
# =============================================================================
def high_five_9(items):
    scores = {}
    for item_id, score in items:
        if item_id not in scores:
            scores[item_id] = []
        scores[item_id].append(score)

    result = []
    for student_id in sorted(scores.keys()):
        sorted_scores = sorted(scores[item_id], reverse=True)
        top_five_sum = sum(sorted_scores[:5])
        result.append([student_id, top_five_sum // 5])

    return result


# =============================================================================
# WAY 10: Most compact
# =============================================================================
def high_five_10(items):
    d = defaultdict(list)
    for i, s in items:
        d[i].append(s)
    return sorted([[k, sum(sorted(v, reverse=True)[:5]) // 5] for k, v in d.items()])


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to group scores by student ID, then for each student take
their top 5 scores and calculate the average."

Approach:
"I'll use a hashmap (defaultdict) to group scores by ID. Then for
each ID, I'll sort their scores in descending order, take the top 5,
sum them, and divide by 5."

Alternative (more efficient):
"If memory is a concern, I could use a min-heap of size 5 for each
student - this way I never store more than 5 scores per student."

Steps:
"1. Group scores by ID using hashmap
2. For each ID, sort scores descending and take top 5
3. Calculate average = sum(top 5) // 5
4. Sort result by ID and return"

Edge cases:
- Multiple students with same scores
- Student has exactly 5 scores
- Scores can be 0

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Sort      | O(nlogn)| O(n)    |
| Heap      | O(nlogk)| O(n)    |
+-----------+--------+----------+
where n = total items, k = 5
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: defaultdict sort", high_five_1),
        ("Way 2: Manual dict", high_five_2),
        ("Way 3: heapq", high_five_3),
        ("Way 4: Dict heap", high_five_4),
        ("Way 5: Counter", high_five_5),
        ("Way 6: List comp", high_five_6),
        ("Way 7: Compact", high_five_7),
        ("Way 8: sorted zip", high_five_8),
        ("Way 9: Explicit top5", high_five_9),
        ("Way 10: Most compact", high_five_10),
    ]

    test_cases = [
        ([[1,91],[1,92],[2,93],[2,97],[1,60],
          [2,77],[1,65],[1,87],[1,100],[2,100],[2,98]],
         [[1,87],[2,93]]),
        ([[1,90],[1,80],[1,70],[1,60],[1,50]], [[1,70]]),
        ([[1,100],[1,90],[1,80],[1,70],[1,60],
          [2,100],[2,90],[2,80],[2,70],[2,60]], [[1,80],[2,80]]),
    ]

    print("=" * 70)
    print("HIGH FIVE - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for items, expected in test_cases:
            try:
                result = func(items)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                status = "✓" if result == expected else "✗"
                print(f"  {status} {name}: {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: ERROR - {e}")
        print(f"  Overall: {'PASS' if all_test_pass else 'FAIL'}\n")

    print("=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS! 🎉")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
