"""
Remove Duplicates from Sorted List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/remove-duplicates-from-sorted-list

Given the head of a sorted singly linked list, delete all duplicates such
that each element appears only once. Return the head of the resulting list.

KEY INSIGHT:
Walk with cur. If cur.next.val == cur.val, skip cur.next; otherwise advance.
Single pass, in place.

Examples:
    1->1->2  =>  1->2
    1->1->2->3->3  =>  1->2->3

Constraints:
- 0 <= number of nodes <= 300
- List is sorted
"""

import copy
import sys

sys.setrecursionlimit(100000)


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def list_from_array(arr):
    if not arr:
        return None
    head = ListNode(arr[0])
    cur = head
    for v in arr[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


def list_to_array(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


# ============================================================
# Way 1: Single pass with cur.next check (BEST - Memorize!)
# ============================================================
def delete_duplicates_1(head):
    """Walk; if cur.next has same val, skip it."""
    cur = head
    while cur and cur.next:
        if cur.next.val == cur.val:
            cur.next = cur.next.next
        else:
            cur = cur.next
    return head


# ============================================================
# Way 2: Walk with prev and cur
# ============================================================
def delete_duplicates_2(head):
    """Track prev; if cur is dup, prev.next = cur.next."""
    prev = None
    cur = head
    while cur:
        if prev and prev.val == cur.val:
            prev.next = cur.next
        else:
            prev = cur
        cur = cur.next
    return head


# ============================================================
# Way 3: Build into set, rebuild
# ============================================================
def delete_duplicates_3(head):
    """Use set to track seen values; rebuild."""
    seen = set()
    out = []
    cur = head
    while cur:
        if cur.val not in seen:
            seen.add(cur.val)
            out.append(cur.val)
        cur = cur.next
    return list_from_array(out)


# ============================================================
# Way 4: Recursive
# ============================================================
def delete_duplicates_4(head):
    """Recursively drop duplicates."""
    if not head or not head.next:
        return head
    head.next = delete_duplicates_4(head.next)
    if head.next and head.next.val == head.val:
        return head.next
    return head


# ============================================================
# Way 5: Class-based wrapper
# ============================================================
class DuplicateRemover_5:
    def __init__(self, head):
        self.head = head

    def remove(self):
        return delete_duplicates_1(self.head)


def delete_duplicates_5(head):
    return DuplicateRemover_5(head).remove()


# ============================================================
# Way 6: In-place with prev tracker
# ============================================================
def delete_duplicates_6(head):
    """Track prev; skip dups in-place."""
    if not head:
        return head
    prev = head
    cur = head.next
    while cur:
        if cur.val == prev.val:
            prev.next = cur.next
        else:
            prev = cur
        cur = cur.next
    return head


# ============================================================
# Way 7: Use sorted set to rebuild
# ============================================================
def delete_duplicates_7(head):
    """Walk and track unique values in a list (sorted)."""
    if not head:
        return head
    vals = []
    cur = head
    while cur:
        if not vals or vals[-1] != cur.val:
            vals.append(cur.val)
        cur = cur.next
    return list_from_array(vals)


# ============================================================
# Way 8: Hash map by value -> count
# ============================================================
def delete_duplicates_8(head):
    """Count occurrences; rebuild only with count==1 values (since sorted, count>1 are consecutive)."""
    if not head:
        return head
    counts = {}
    cur = head
    while cur:
        counts[cur.val] = counts.get(cur.val, 0) + 1
        cur = cur.next
    vals = []
    cur = head
    seen = set()
    while cur:
        if cur.val not in seen:
            vals.append(cur.val)
            seen.add(cur.val)
        cur = cur.next
    return list_from_array(vals)


# ============================================================
# Way 9: Walk and relink (keep one)
# ============================================================
def delete_duplicates_9(head):
    """Walk with prev; relink non-duplicate nodes."""
    if not head:
        return head
    prev = head
    cur = head.next
    while cur:
        if cur.val == prev.val:
            prev.next = cur.next
        else:
            prev = cur
        cur = cur.next
    return head


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def delete_duplicates_10(head):
    """
    THE ONE TO MEMORIZE.

    1. cur = head.
    2. While cur and cur.next:
       a. If cur.next.val == cur.val: cur.next = cur.next.next.
       b. Else: cur = cur.next.
    3. Return head.

    Time:  O(n)
    Space: O(1).
    """
    cur = head
    while cur and cur.next:
        if cur.next.val == cur.val:
            cur.next = cur.next.next
        else:
            cur = cur.next
    return head


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to delete duplicates from a sorted linked list, keeping only one
copy of each value, and return the head."

Key Insight:
"Since the list is sorted, duplicates are consecutive. Walk with cur.
If cur.next.val == cur.val, redirect cur.next to skip the duplicate.
Otherwise, advance cur."

Algorithm:
1. cur = head.
2. While cur and cur.next:
   a. If cur.next.val == cur.val: cur.next = cur.next.next.
   b. Else: cur = cur.next.
3. Return head.

Edge Cases:
- Empty / single: return as-is.
- All duplicates: return single node.
- No duplicates: return as-is.
- Two same: return one node.

KEY TRICK:
Don't advance cur when you delete cur.next — the new cur.next might also
be a duplicate. Only advance when cur.next.val != cur.val.

RELATED PROBLEMS:
- Remove Duplicates II (LC 82) — remove ALL duplicates.
- Delete Node in a Linked List (LC 237).
- Remove Linked List Elements (LC 203).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 1, 2], [1, 2], "Standard LC83"),
        ([1, 1, 2, 3, 3], [1, 2, 3], "Mixed"),
        ([], [], "Empty"),
        ([1], [1], "Single"),
        ([1, 1, 1], [1], "All dups"),
        ([1, 2, 3], [1, 2, 3], "No dups"),
    ]

    implementations = [
        ("Way 1: Single pass (BEST)", delete_duplicates_1),
        ("Way 2: prev + cur", delete_duplicates_2),
        ("Way 3: Set rebuild", delete_duplicates_3),
        ("Way 4: Recursive", delete_duplicates_4),
        ("Way 5: Class-based", delete_duplicates_5),
        ("Way 6: prev tracker", delete_duplicates_6),
        ("Way 7: Sorted list", delete_duplicates_7),
        ("Way 8: Hash map", delete_duplicates_8),
        ("Way 9: Dummy + walk", delete_duplicates_9),
        ("Way 10: Final cleanest", delete_duplicates_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(inp))
                result = fn(head)
                got = list_to_array(result)
                if got == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} expected={expected} got={got}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
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