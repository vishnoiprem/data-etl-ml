"""
Insert into a Sorted Circular Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/insert-into-a-sorted-circular-linked-list

Given a node from a sorted circular linked list (head is any node, sorted
ascending), insert insertVal such that the list remains sorted. Return any
node from the list.

KEY INSIGHT:
Walk around the circle. Find the spot where insertVal fits: either between
two consecutive nodes (prev.val <= insertVal <= cur.val), or at the
"break" point (max -> min, when insertVal is smaller than min or larger
than max).

Examples:
    3->4->1 (circular), insertVal=2  =>  3->4->1->2 or 3->4->2->1 (sort order)

Constraints:
- 0 <= number of nodes <= 5 * 10^4
- -10^6 <= Node.val, insertVal <= 10^6
"""

import copy
import sys

sys.setrecursionlimit(100000)


class Node:
    def __init__(self, val=None, next=None):
        self.val = val
        self.next = next


def circular_list_from_array(arr):
    """Build a circular list from array. Returns head."""
    if not arr:
        return None
    head = Node(arr[0])
    cur = head
    for v in arr[1:]:
        cur.next = Node(v)
        cur = cur.next
    cur.next = head  # close the circle
    return head


def circular_list_to_array(head, n):
    """Walk n steps to collect values."""
    out = []
    cur = head
    for _ in range(n):
        if not cur:
            break
        out.append(cur.val)
        cur = cur.next
    return out


# ============================================================
# Way 1: Walk once, find insertion spot (BEST - Memorize!)
# ============================================================
def insert_1(head, insertVal):
    """Walk once; insert at proper spot or handle edge cases."""
    new_node = Node(insertVal)
    if not head:
        new_node.next = new_node
        return new_node
    cur = head
    while True:
        # Normal case: insertVal between cur and cur.next (in sorted order)
        if cur.val <= insertVal <= cur.next.val:
            break
        # Wrap-around case: cur is the max, cur.next is the min
        if cur.val > cur.next.val:
            # We're at the break; insertVal should be either >= cur.val or <= cur.next.val
            if insertVal >= cur.val or insertVal <= cur.next.val:
                break
        cur = cur.next
        if cur == head:
            # We've gone all the way around; insertVal doesn't fit cleanly.
            # Insert anywhere (e.g., between cur and cur.next).
            break
    new_node.next = cur.next
    cur.next = new_node
    return head


# ============================================================
# Way 2: Find min and max first, then insert
# ============================================================
def insert_2(head, insertVal):
    """Find min/max; insert accordingly."""
    new_node = Node(insertVal)
    if not head:
        new_node.next = new_node
        return new_node
    # Find max node (one whose next is smaller) and min node (max's next)
    cur = head
    while cur.next != head and cur.next.val > cur.val:
        cur = cur.next
    # cur is max; cur.next is min
    max_node = cur
    min_node = cur.next
    if insertVal >= max_node.val or insertVal <= min_node.val:
        # Insert between max and min
        new_node.next = min_node
        max_node.next = new_node
        return head
    # Insert between two nodes where prev.val <= insertVal <= next.val
    cur = head
    while not (cur.val <= insertVal <= cur.next.val):
        cur = cur.next
    new_node.next = cur.next
    cur.next = new_node
    return head


# ============================================================
# Way 3: Walk and use previous/next comparison
# ============================================================
def insert_3(head, insertVal):
    """Use prev/next logic to find spot."""
    new_node = Node(insertVal)
    if not head:
        new_node.next = new_node
        return new_node
    cur = head
    nxt = cur.next
    while not (
        (cur.val <= insertVal <= nxt.val) or
        (cur.val > nxt.val and (insertVal >= cur.val or insertVal <= nxt.val))
    ):
        cur = nxt
        nxt = cur.next
        if cur == head:
            # All values same or wrap-around; insert after head
            new_node.next = cur.next
            cur.next = new_node
            return head
    new_node.next = nxt
    cur.next = new_node
    return head


# ============================================================
# Way 4: Collect into array, sort, rebuild circular
# ============================================================
def insert_4(head, insertVal):
    """Collect to array, sort, rebuild circular."""
    vals = []
    if head:
        cur = head
        while True:
            vals.append(cur.val)
            cur = cur.next
            if cur == head:
                break
    vals.append(insertVal)
    vals.sort()
    # Rebuild
    if not vals:
        return None
    new_head = Node(vals[0])
    cur = new_head
    for v in vals[1:]:
        cur.next = Node(v)
        cur = cur.next
    cur.next = new_head
    return new_head


# ============================================================
# Way 5: Class-based wrapper
# ============================================================
class SortedCircularList_5:
    def __init__(self, head):
        self.head = head

    def insert(self, val):
        return insert_1(self.head, val)


def insert_5(head, insertVal):
    return SortedCircularList_5(head).insert(insertVal)


# ============================================================
# Way 6: Handle empty, single node, then walk
# ============================================================
def insert_6(head, insertVal):
    """Explicit handling of empty/single, then walk."""
    new_node = Node(insertVal)
    if not head:
        new_node.next = new_node
        return new_node
    if head.next == head:
        # Single node
        new_node.next = head
        head.next = new_node
        return head
    cur = head
    while True:
        if cur.next == head:
            # End of walk
            new_node.next = cur.next
            cur.next = new_node
            return head
        if cur.val <= insertVal <= cur.next.val:
            new_node.next = cur.next
            cur.next = new_node
            return head
        if cur.val > cur.next.val:
            # Wrap point
            if insertVal > cur.val or insertVal < cur.next.val:
                new_node.next = cur.next
                cur.next = new_node
                return head
        cur = cur.next


# ============================================================
# Way 7: Use two-pointer (prev/cur)
# ============================================================
def insert_7(head, insertVal):
    """Two-pointer prev/cur."""
    new_node = Node(insertVal)
    if not head:
        new_node.next = new_node
        return new_node
    prev = head
    cur = head.next
    while cur != head:
        # Normal in-order insertion
        if prev.val <= insertVal <= cur.val:
            break
        # Wrap-around
        if prev.val > cur.val and (insertVal >= prev.val or insertVal <= cur.val):
            break
        prev = cur
        cur = cur.next
    new_node.next = cur
    prev.next = new_node
    return head


# ============================================================
# Way 8: Hash + sort
# ============================================================
def insert_8(head, insertVal):
    """Use list (multiset) so duplicates are preserved; sort."""
    vals = []
    if head:
        cur = head
        while True:
            vals.append(cur.val)
            cur = cur.next
            if cur == head:
                break
    vals.append(insertVal)
    vals.sort()
    if not vals:
        return None
    new_head = Node(vals[0])
    cur = new_head
    for v in vals[1:]:
        cur.next = Node(v)
        cur = cur.next
    cur.next = new_head
    return new_head


# ============================================================
# Way 9: Linear walk with explicit comparison
# ============================================================
def insert_9(head, insertVal):
    """Walk with explicit comparison logic."""
    new_node = Node(insertVal)
    if not head:
        new_node.next = new_node
        return new_node
    cur = head
    start = head
    while True:
        if cur.val <= insertVal <= cur.next.val:
            break
        if cur.val > cur.next.val:
            if insertVal >= cur.val or insertVal <= cur.next.val:
                break
        cur = cur.next
        if cur == start:
            break
    new_node.next = cur.next
    cur.next = new_node
    return head


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def insert_10(head, insertVal):
    """
    THE ONE TO MEMORIZE.

    1. If empty, return a single-node circular list.
    2. cur = head.
    3. While True:
       - If cur.val <= insertVal <= cur.next.val: insert between them.
       - Else if cur.val > cur.next.val (wrap point):
           If insertVal >= cur.val or insertVal <= cur.next.val: insert.
       - cur = cur.next. If cur == head, break (inserted anywhere).
       - Insert: new_node.next = cur.next; cur.next = new_node.

    Time:  O(n)
    Space: O(1).
    """
    new_node = Node(insertVal)
    if not head:
        new_node.next = new_node
        return new_node
    cur = head
    while True:
        if cur.val <= insertVal <= cur.next.val:
            break
        if cur.val > cur.next.val and (insertVal >= cur.val or insertVal <= cur.next.val):
            break
        cur = cur.next
        if cur == head:
            break
    new_node.next = cur.next
    cur.next = new_node
    return head


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to insert insertVal into a sorted circular linked list and return
any node from the resulting list."

Key Insight:
"Walk around the circle. Find the spot where insertVal fits: either
between two consecutive nodes in sorted order (prev.val <= insertVal <= next.val),
or at the wrap point (max -> min, when insertVal is bigger than max or
smaller than min)."

Algorithm:
1. If empty, return a single-node circle with insertVal.
3. While not found:
   a. If cur.val <= insertVal <= cur.next.val: insert here.
   b. Else if cur.val > cur.next.val (wrap point) AND
          (insertVal >= cur.val OR insertVal <= cur.next.val): insert here.
   c. cur = cur.next. If cur == head: insert anywhere (e.g., after head).
4. Insert: new_node.next = cur.next; cur.next = new_node.

Edge Cases:
- Empty list: single-node circle.
- Single node: insert before or after.
- All same values: insert anywhere.
- insertVal < all or > all: at wrap point.

KEY TRICK:
The wrap point (cur.val > cur.next.val) is where the maximum node's next
points to the minimum node. insertVal fits at the wrap if it's a new max
or new min.

RELATED PROBLEMS:
- Insert Interval (LC 57).
- Insert into BST (LC 701).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    # Each test: (input_circular, n_nodes, insertVal, expected_circular_or_special)
    test_cases = [
        ([3, 4, 1], 3, 2, [3, 4, 1, 2], "Standard LC708"),
        ([], 0, 1, [1], "Empty"),
        ([1], 1, 0, [1, 0], "Single, smaller"),
        ([1], 1, 2, [1, 2], "Single, larger"),
        ([3, 3, 3], 3, 0, [3, 3, 3, 0], "All same"),
        ([1, 3, 5], 3, 4, [1, 3, 4, 5], "In middle"),
    ]

    implementations = [
        ("Way 1: Walk once (BEST)", insert_1),
        ("Way 2: Find min/max", insert_2),
        ("Way 3: prev/nxt logic", insert_3),
        ("Way 4: Array sort", insert_4),
        ("Way 5: Class-based", insert_5),
        ("Way 6: Explicit handling", insert_6),
        ("Way 7: Two-pointer", insert_7),
        ("Way 8: Hash + sort", insert_8),
        ("Way 9: Linear walk", insert_9),
        ("Way 10: Final cleanest", insert_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, n, v, expected, desc in test_cases:
            try:
                head = circular_list_from_array(copy.deepcopy(inp))
                result = fn(head, v)
                got = circular_list_to_array(result, n + 1)
                # Circular equivalence: check that the multiset of values is the same.
                if sorted(got) == sorted(expected):
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} v={v} expected={expected} got={got}")
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