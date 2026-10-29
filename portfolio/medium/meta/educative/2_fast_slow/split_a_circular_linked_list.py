"""
Split a Circular Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/split-a-circular-linked-list

Given a circular linked list (last node points back to head), split it into
two equal circular linked lists. If the length is odd, the first list gets
the extra element.

KEY INSIGHT:
Use slow/fast pointers. After the loop, slow is at the end of the first
half. Break its next pointer; the next node becomes the head of the second
half.

Examples:
    1 -> 2 -> 3 -> 4 -> 1  =>  1 -> 2 -> 1   AND   3 -> 4 -> 3
    1 -> 2 -> 3 -> 1      =>  1 -> 2 -> 1   AND   3 -> 3

Constraints:
- 0 <= list length <= 10^4
"""

import copy
import sys

sys.setrecursionlimit(100000)


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def build_circular(arr):
    """Build a circular linked list from array values."""
    if not arr:
        return None
    nodes = [ListNode(v) for v in arr]
    n = len(nodes)
    for i in range(n - 1):
        nodes[i].next = nodes[i + 1]
    nodes[n - 1].next = nodes[0]  # circular
    return nodes[0]


def list_to_circular_array(head, max_steps=100):
    """Walk a circular list and return values (bounded)."""
    if not head:
        return []
    out = []
    cur = head
    for _ in range(max_steps):
        out.append(cur.val)
        cur = cur.next
        if cur == head:
            break
    return out


# ============================================================
# Way 1: Fast/slow + split (BEST - Memorize!)
# ============================================================
def split_circular_1(head):
    """Use slow/fast. Slow ends at end of first half. Break there."""
    if not head or head.next == head:
        return head, None
    slow = head
    fast = head
    while fast.next != head and fast.next.next != head:
        slow = slow.next
        fast = fast.next.next
    # slow is at the end of first half
    head1 = head
    head2 = slow.next
    # Make head1 circular: find end of head1 and link to head.
    # slow is already at end of head1; set slow.next = head1.
    slow.next = head1
    # Make head2 circular: find end of head2 and link to head2.
    if head2:
        cur = head2
        while cur.next != head:
            cur = cur.next
        cur.next = head2
    return head1, head2


# ============================================================
# Way 2: Count + walk + split
# ============================================================
def split_circular_2(head):
    """Count length. Walk half; split; relink."""
    if not head or head.next == head:
        return head, None
    # Count length
    n = 1
    cur = head.next
    while cur != head:
        n += 1
        cur = cur.next
    # Walk half - 1 steps (slow lands on last node of first half)
    mid = (n + 1) // 2  # number of nodes in first half (extra for odd)
    cur = head
    for _ in range(mid - 1):
        cur = cur.next
    head1 = head
    head2 = cur.next
    cur.next = head1
    # Find end of second half
    if head2:
        walker = head2
        for _ in range(n - mid - 1):
            walker = walker.next
        walker.next = head2
    return head1, head2


# ============================================================
# Way 3: Slow/fast + manual relink
# ============================================================
def split_circular_3(head):
    """Same as Way 1 but with helper functions."""
    if not head:
        return None, None
    if head.next == head:
        return head, None
    slow = head
    fast = head
    prev_slow = None
    while fast.next != head and fast.next.next != head:
        prev_slow = slow
        slow = slow.next
        fast = fast.next.next
    head1 = head
    head2 = slow.next
    slow.next = head1
    # Relink second half
    if head2:
        end2 = head2
        while end2.next != head:
            end2 = end2.next
        end2.next = head2
    return head1, head2


# ============================================================
# Way 4: Array-based
# ============================================================
def split_circular_4(head):
    """Convert to array of values, split, rebuild."""
    if not head:
        return None, None
    vals = []
    cur = head
    while True:
        vals.append(cur.val)
        cur = cur.next
        if cur == head:
            break
    n = len(vals)
    mid = (n + 1) // 2
    first = vals[:mid]
    second = vals[mid:]
    return build_circular(first), build_circular(second)


# ============================================================
# Way 5: Slow/fast with explicit "stop condition"
# ============================================================
def split_circular_5(head):
    """Same logic as Way 1, different naming."""
    if not head or head.next == head:
        return head, None
    slow = head
    fast = head
    while True:
        if fast.next == head:
            break
        if fast.next.next == head:
            break
        slow = slow.next
        fast = fast.next.next
    head1 = head
    head2 = slow.next
    slow.next = head1
    if head2:
        cur = head2
        while cur.next != head:
            cur = cur.next
        cur.next = head2
    return head1, head2


# ============================================================
# Way 6: Find length then walk half
# ============================================================
def split_circular_6(head):
    """Find length, walk half - 1, split."""
    if not head or head.next == head:
        return head, None
    # Find length
    n = 1
    cur = head.next
    while cur is not head:
        n += 1
        cur = cur.next
    # Walk half
    half = (n + 1) // 2
    cur = head
    for _ in range(half - 1):
        cur = cur.next
    head1 = head
    head2 = cur.next
    cur.next = head1
    # Find end of second half
    end2 = head2
    for _ in range(n - half - 1):
        end2 = end2.next
    if end2:
        end2.next = head2
    return head1, head2


# ============================================================
# Way 7: Recursive
# ============================================================
def split_circular_7(head):
    """Recursive length + iterative split."""
    if not head or head.next == head:
        return head, None

    def get_length(node):
        length = 1
        cur = node.next
        while cur is not node:
            length += 1
            cur = cur.next
        return length

    n = get_length(head)
    half = (n + 1) // 2
    cur = head
    for _ in range(half - 1):
        cur = cur.next
    head1 = head
    head2 = cur.next
    cur.next = head1
    if head2:
        end2 = head2
        for _ in range(n - half - 1):
            end2 = end2.next
        end2.next = head2
    return head1, head2


# ============================================================
# Way 8: Use index counter
# ============================================================
def split_circular_8(head):
    """Walk with index; track middle."""
    if not head or head.next == head:
        return head, None
    # First pass: count
    n = 0
    cur = head
    while True:
        n += 1
        cur = cur.next
        if cur == head:
            break
    # Second pass: walk to mid-1
    half = (n + 1) // 2
    cur = head
    for _ in range(half - 1):
        cur = cur.next
    head1 = head
    head2 = cur.next
    cur.next = head1
    # Find end of head2
    end2 = head2
    while end2.next is not head:
        end2 = end2.next
    end2.next = head2
    return head1, head2


# ============================================================
# Way 9: Class-based
# ============================================================
class CircularSplitter_9:
    def __init__(self, head):
        self.head = head

    def split(self):
        if not self.head or self.head.next == self.head:
            return self.head, None
        slow = self.head
        fast = self.head
        while fast.next != self.head and fast.next.next != self.head:
            slow = slow.next
            fast = fast.next.next
        head1 = self.head
        head2 = slow.next
        slow.next = head1
        if head2:
            end2 = head2
            while end2.next != self.head:
                end2 = end2.next
            end2.next = head2
        return head1, head2


def split_circular_9(head):
    return CircularSplitter_9(head).split()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def split_circular_10(head):
    """
    THE ONE TO MEMORIZE.

    1. Use slow/fast; stop when fast.next == head or fast.next.next == head.
    2. slow is at the end of the first half.
    3. head2 = slow.next; slow.next = head (closes first half as circular).
    4. Walk second half to find its end; point it to head2.

    Time:  O(n)
    Space: O(1).
    """
    if not head or head.next == head:
        return head, None
    slow = head
    fast = head
    while fast.next != head and fast.next.next != head:
        slow = slow.next
        fast = fast.next.next
    head1 = head
    head2 = slow.next
    slow.next = head1
    if head2:
        end2 = head2
        while end2.next != head:
            end2 = end2.next
        end2.next = head2
    return head1, head2


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to split a circular linked list into two equal circular linked lists.
If the length is odd, the first list gets the extra element."

Key Insight:
"Use slow/fast pointers. After the loop, slow is at the end of the first
half. Set slow.next = head (closes first half as circular), and walk the
second half to close it as a circular list pointing to its own head."

Algorithm:
1. slow = fast = head.
2. While fast.next != head and fast.next.next != head:
     slow = slow.next
     fast = fast.next.next
3. head2 = slow.next
4. slow.next = head   (close first half)
5. Walk head2 to find end; end.next = head2  (close second half)
6. Return head, head2.

Edge Cases:
- Empty / single node (head.next == head): return (head, None).
- Two nodes: return (head, head.next).

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Slow/fast | O(n)   | O(1)   |
| Count+walk| O(n)   | O(1)   |
| Array     | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
The stop condition `fast.next != head and fast.next.next != head` is what
makes this work for circular lists. The standard `fast and fast.next` would
not detect the cycle correctly.

RELATED PROBLEMS:
- Middle of Linked List (LC 876).
- Palindrome Linked List (LC 234).
- Split Linked List in Parts (LC 725).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    # Each test: (input, expected_first, expected_second, description)
    test_cases = [
        ([1, 2, 3, 4], [1, 2], [3, 4], "Even: 4 nodes"),
        ([1, 2, 3], [1, 2], [3], "Odd: 3 nodes"),
        ([1, 2], [1], [2], "Two nodes"),
        ([1], [1], None, "Single node"),
        ([1, 2, 3, 4, 5, 6], [1, 2, 3], [4, 5, 6], "Six nodes"),
        ([1, 2, 3, 4, 5], [1, 2, 3], [4, 5], "Five nodes"),
        ([], None, None, "Empty"),
    ]

    implementations = [
        ("Way 1: Fast/slow split (BEST)", split_circular_1),
        ("Way 2: Count + walk", split_circular_2),
        ("Way 3: Slow/fast manual", split_circular_3),
        ("Way 4: Array-based", split_circular_4),
        ("Way 5: Slow/fast stop cond", split_circular_5),
        ("Way 6: Find length walk", split_circular_6),
        ("Way 7: Recursive", split_circular_7),
        ("Way 8: Index counter", split_circular_8),
        ("Way 9: Class-based", split_circular_9),
        ("Way 10: Final cleanest", split_circular_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for arr, exp_first, exp_second, desc in test_cases:
            try:
                head = build_circular(copy.deepcopy(arr))
                h1, h2 = fn(head)
                got1 = list_to_circular_array(h1) if h1 else None
                got2 = list_to_circular_array(h2) if h2 else None
                if got1 == exp_first and got2 == exp_second:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: arr={arr} expected=({exp_first},{exp_second}) got=({got1},{got2})")
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
