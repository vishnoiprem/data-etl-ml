"""
Intersection of Two Linked Lists - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/intersection-of-two-linked-lists

Given the heads of two singly linked lists, return the node at which the
two lists intersect, or None if they do not intersect.

Two lists intersect if they share the SAME NODE in memory (not just nodes
with equal values).

KEY INSIGHT:
Two-pointer "switch heads" trick. Walk both lists; when a pointer reaches
the end, jump it to the other list's head. By the time both pointers have
traversed the same total length, they'll meet at the intersection (or
both reach None together if no intersection).

Examples:
    A: 4 -> 1 -> 8 -> 4 -> 5
    B: 5 -> 6 -> 1 -> 8 -> 4 -> 5
       (intersection at node with val 8)
    -> Return the node with val 8.

    A: 2 -> 6 -> 4
    B: 1 -> 5
       (no intersection)
    -> Return None.

Constraints:
- 1 <= node.val <= 10^5
- 1 <= m, n <= 10^3  (lengths of the two lists)
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Linked List Node Definition
# ============================================================
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def list_from_array(arr):
    """Build a linked list from an array. Returns head."""
    if not arr:
        return None
    head = ListNode(arr[0])
    cur = head
    for v in arr[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


def array_from_list(head):
    """Convert linked list to array."""
    arr = []
    while head:
        arr.append(head.val)
        head = head.next
    return arr


# ============================================================
# Helper to build intersecting lists from LeetCode-style inputs
# ============================================================
def build_intersect(intersect_val, listA, listB, skipA, skipB):
    """Build two lists that intersect at the node with value intersect_val.
    skipA = number of nodes to skip in A (0-indexed) to reach the
    intersection node. Same for skipB.

    Construction:
    - Shared tail = listA[skipA:] (built first as a separate list).
    - A's prefix = listA[:skipA]; tail of prefix points to shared tail.
    - B's prefix = listB[:skipB]; tail of prefix points to shared tail.
    - Both prefixes' tails reference the SAME shared_tail node(s).
    """
    if intersect_val == 0:
        # No intersection — independent lists
        return list_from_array(listA), list_from_array(listB)

    # Build the shared tail
    shared_tail = list_from_array(listA[skipA:])

    # Build A prefix + shared tail
    prefixA = list_from_array(listA[:skipA])
    if prefixA:
        cur = prefixA
        while cur.next:
            cur = cur.next
        cur.next = shared_tail
        headA = prefixA
    else:
        headA = shared_tail

    # Build B prefix + shared tail
    prefixB = list_from_array(listB[:skipB])
    if prefixB:
        cur = prefixB
        while cur.next:
            cur = cur.next
        cur.next = shared_tail
        headB = prefixB
    else:
        headB = shared_tail

    return headA, headB


# ============================================================
# Way 1: Two-pointer switch heads (BEST - Memorize!)
# ============================================================
def get_intersection_node_1(headA, headB):
    """When a pointer reaches end, jump to the other list's head.
    Both pointers traverse A+B length; they meet at intersection (or None)."""
    if not headA or not headB:
        return None
    pA, pB = headA, headB
    # Stop when pA == pB (either the intersection node or both None).
    while pA != pB:
        pA = headB if pA is None else pA.next
        pB = headA if pB is None else pB.next
    return pA


# ============================================================
# Way 2: Hash set of nodes from one list
# ============================================================
def get_intersection_node_2(headA, headB):
    """Walk one list, store all node ids in a set. Walk the other and check."""
    seen = set()
    cur = headA
    while cur:
        seen.add(id(cur))
        cur = cur.next
    cur = headB
    while cur:
        if id(cur) in seen:
            return cur
        cur = cur.next
    return None


# ============================================================
# Way 3: Length difference then align
# ============================================================
def get_intersection_node_3(headA, headB):
    """Compute lengths; advance the longer one by the difference; then walk together."""
    def length(head):
        n = 0
        while head:
            n += 1
            head = head.next
        return n

    lenA, lenB = length(headA), length(headB)
    # Advance the longer one
    pA, pB = headA, headB
    for _ in range(lenA - lenB):
        pA = pA.next
    for _ in range(lenB - lenA):
        pB = pB.next
    while pA and pB:
        if pA is pB:
            return pA
        pA = pA.next
        pB = pB.next
    return None


# ============================================================
# Way 4: Brute force O(m*n)
# ============================================================
def get_intersection_node_4(headA, headB):
    """For each node in B, scan all of A."""
    curB = headB
    while curB:
        curA = headA
        while curA:
            if curA is curB:
                return curA
            curA = curA.next
        curB = curB.next
    return None


# ============================================================
# Way 5: Hash map of node -> count
# ============================================================
def get_intersection_node_5(headA, headB):
    """Use a dict to count occurrences. The intersection node appears in both."""
    from collections import Counter
    counter = Counter()
    cur = headA
    while cur:
        counter[id(cur)] += 1
        cur = cur.next
    cur = headB
    while cur:
        if counter[id(cur)] > 0:
            return cur
        cur = cur.next
    return None


# ============================================================
# Way 6: Stack-based (find tails, walk back)
# ============================================================
def get_intersection_node_6(headA, headB):
    """Push all nodes from both lists onto two stacks. Pop and compare from
    the back; the last common node is the intersection."""
    stackA, stackB = [], []
    cur = headA
    while cur:
        stackA.append(cur)
        cur = cur.next
    cur = headB
    while cur:
        stackB.append(cur)
        cur = cur.next
    intersection = None
    while stackA and stackB and stackA[-1] is stackB[-1]:
        intersection = stackA.pop()
        stackB.pop()
    return intersection


# ============================================================
# Way 7: Mark visited nodes
# ============================================================
def get_intersection_node_7(headA, headB):
    """Tag nodes of listA by setting a visited attribute; walk listB."""
    cur = headA
    while cur:
        cur.visited = True
        cur = cur.next
    cur = headB
    while cur:
        if getattr(cur, 'visited', False):
            return cur
        cur = cur.next
    # Clean up (avoid mutating shared nodes permanently for next call)
    cur = headA
    while cur:
        if hasattr(cur, 'visited'):
            del cur.visited
        cur = cur.next
    return None


# ============================================================
# Way 8: Cycle trick
# ============================================================
def get_intersection_node_8(headA, headB):
    """Connect tail of A to head (forming a cycle), then use two-pointer
    cycle detection (Floyd's) starting from headB. The meeting point
    lies on the cycle, and we can derive the intersection.
    Simpler: if both A and B point into a shared tail, we can detect this
    by walking both lists twice with switch."""
    # This is essentially Way 1 but with explicit bookkeeping.
    pA, pB = headA, headB
    count = 0
    while pA != pB:
        if pA is None:
            pA = headB
        else:
            pA = pA.next
        if pB is None:
            pB = headA
        else:
            pB = pB.next
        count += 1
        if count > 10000:
            # Safety: lists don't intersect and we've looped too many times
            return None
    return pA


# ============================================================
# Way 9: Class-based
# ============================================================
class IntersectionFinder_9:
    def __init__(self, headA, headB):
        self.headA = headA
        self.headB = headB

    def find(self):
        pA, pB = self.headA, self.headB
        while pA != pB:
            pA = self.headB if pA is None else pA.next
            pB = self.headA if pB is None else pB.next
        return pA


def get_intersection_node_9(headA, headB):
    return IntersectionFinder_9(headA, headB).find()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def get_intersection_node_10(headA, headB):
    """
    THE ONE TO MEMORIZE.

    1. pA = headA, pB = headB.
    2. While pA != pB:
       - pA = headB if pA is None else pA.next
       - pB = headA if pB is None else pB.next
    3. Return pA (intersection node or None).

    Both pointers walk A+B length. If they intersect, they meet at the
    intersection. Otherwise, both end at None simultaneously.

    Time:  O(m + n)
    Space: O(1)
    """
    pA, pB = headA, headB
    while pA != pB:
        pA = headB if pA is None else pA.next
        pB = headA if pB is None else pB.next
    return pA


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the intersection node of two singly linked lists, or
None if they don't intersect. Lists intersect when they share a node in
memory, not just when values match."

Key Insight:
"Two-pointer switch-heads trick. Walk both lists. When a pointer hits
the end, jump it to the OTHER list's head. After both pointers have
walked A+B total length, they'll either meet at the intersection node
or both become None (no intersection)."

Algorithm:
1. pA = headA, pB = headB.
2. While pA != pB:
   a. pA = headB if pA is None else pA.next
   b. pB = headA if pB is None else pB.next
3. Return pA.

Edge Cases:
- No intersection: both pointers end at None; loop exits; return None.
- Identical lists: pA == pB from the start.
- One list is None: short-circuit; return None.
- Intersect at first node: return headA (or headB).

Why does it work?
- pA walks: A then B (total m+n).
- pB walks: B then A (total n+m).
- If they share a tail, after the switch they're aligned.
- If not, both end at None simultaneously.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Switch hds| O(m+n) | O(1)   |
| Hash set  | O(m+n) | O(m)   |
| Length    | O(m+n) | O(1)   |
| Brute     | O(m*n) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
Each pointer walks exactly m+n nodes total — the trick is the switch
at the end of each list. This is more elegant than computing lengths.

RELATED PROBLEMS:
- Linked List Cycle (LC 141): Floyd's algorithm.
- Linked List Cycle II (LC 142): cycle entry.
- Merge Two Sorted Lists (LC 21): pointer walk.
"""


# ============================================================
# TEST CASES (LeetCode-style with intersectVal, skipA, skipB)
# ============================================================
def run_tests():
    # Test case: (intersectVal, listA, listB, skipA, skipB, expected_intersect_val_or_None)
    test_cases = [
        # Standard LeetCode examples
        (8, [4, 1, 8, 4, 5], [5, 6, 1, 8, 4, 5], 2, 3, 8),
        # No intersection
        (0, [2, 6, 4], [1, 5], 3, 2, None),
        # Intersect at second node of A (index 1)
        (9, [4, 9, 1, 2, 4], [3, 9, 1, 2, 4], 1, 1, 9),
        # Intersect at second node of A
        (2, [1, 2], [3, 2], 1, 1, 2),
        # B is prefix of A
        (1, [1, 2, 3], [1], 0, 0, 1),
        # Single node intersect
        (7, [7], [7], 0, 0, 7),
        # Single node no intersect
        (0, [7], [8], 1, 1, None),
        # Both empty (length 1 each, different vals)
        (0, [1], [2], 1, 1, None),
        # Intersect at last node of both
        (5, [1, 2, 3, 4, 5], [6, 7, 5], 4, 2, 5),
        # Intersect at second node of A
        (3, [1, 3, 5, 7, 9], [2, 3, 5, 7, 9], 1, 1, 3),
    ]

    implementations = [
        ("Way 1: Switch heads (BEST)", get_intersection_node_1),
        ("Way 2: Hash set", get_intersection_node_2),
        ("Way 3: Length difference", get_intersection_node_3),
        ("Way 4: Brute O(m*n)", get_intersection_node_4),
        ("Way 5: Counter", get_intersection_node_5),
        ("Way 6: Stack-based", get_intersection_node_6),
        ("Way 7: Mark visited", get_intersection_node_7),
        ("Way 8: Cycle trick", get_intersection_node_8),
        ("Way 9: Class-based", get_intersection_node_9),
        ("Way 10: Final cleanest", get_intersection_node_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for case_idx, (intersect_val, listA, listB, skipA, skipB, expected_val) in enumerate(test_cases):
            try:
                headA, headB = build_intersect(intersect_val, listA, listB, skipA, skipB)
                result = fn(headA, headB)
                result_val = result.val if result else None
                if result_val == expected_val:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] case {case_idx}: expected={expected_val} got={result_val}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] case {case_idx}: {type(e).__name__}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
