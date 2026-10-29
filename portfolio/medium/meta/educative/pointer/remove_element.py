"""
Remove Element
Easy | 15 min

Given an integer array nums and an integer val, remove all occurrences
of val in-place. The order of elements may be changed. Return the
number of elements in nums which are not equal to val.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/remove-element

Examples:
    nums=[3,2,2,3], val=3 -> 2, nums=[2,2,_,_]
    nums=[0,1,2,2,3,0,4,2], val=2 -> 5, nums=[0,1,3,0,4,_,_,_]

Constraints:
- 0 <= nums.length <= 100
- 0 <= nums[i] <= 50
- 0 <= val <= 100

KEY INSIGHT:
Two-pointer technique:
- i walks through nums.
- j tracks position to write next "kept" element.
- When nums[i] != val: nums[j] = nums[i]; j += 1.
- Final count = j.

Time:  O(n) — single pass.
Space: O(1) — in-place.
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT REMOVE ELEMENT:

1. UNDERSTAND THE PROBLEM:
   "Remove all occurrences of val from nums in-place.
   Return the count of remaining (non-val) elements."

2. KEY OBSERVATION:
   "We don't need to actually DELETE elements — just move 'kept' elements
   to the front. The leftover positions can contain anything."

3. TWO-POINTER PATTERN:
   - i = read pointer (walks through array).
   - j = write pointer (tracks position of next kept element).
   - If nums[i] != val: copy to nums[j], j++.
   - Skip if nums[i] == val.
   - Final count = j.

4. WHY IN-PLACE:
   "We overwrite elements we want to remove with elements we keep.
   Beyond j, the array contents don't matter."

5. EDGE CASES:
   - All elements equal val: return 0.
   - No element equals val: return len(nums).
   - Empty array: return 0.
   - val not in array: return len(nums).

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Two ptr  | O(n)   | O(1)   |
   | Brute pop| O(n^2) | O(1)   |
   | New arr  | O(n)   | O(n)   |
   +----------+--------+--------+

7. WHY TWO POINTERS:
   - Single pass: O(n).
   - O(1) extra space.
   - Stable: preserves relative order of kept elements.
"""


# =============================================================================
# WAY 1: Two-pointer (BEST - Memorize!)
# =============================================================================
def remove_element_1(nums, val):
    """
    Two-pointer: read and write.
    Move non-val elements forward.
    """
    j = 0
    for i in range(len(nums)):
        if nums[i] != val:
            nums[j] = nums[i]
            j += 1
    return j


# =============================================================================
# WAY 2: Two-pointer from both ends (swap with end)
# =============================================================================
def remove_element_2(nums, val):
    """
    Swap val elements with end elements.
    Reduces array size implicitly.
    """
    i = 0
    n = len(nums)
    while i < n:
        if nums[i] == val:
            nums[i] = nums[n - 1]
            n -= 1
        else:
            i += 1
    return n


# =============================================================================
# WAY 3: List comprehension + mutation
# =============================================================================
def remove_element_3(nums, val):
    """Filter non-val, then write back."""
    kept = [x for x in nums if x != val]
    for i in range(len(kept)):
        nums[i] = kept[i]
    return len(kept)


# =============================================================================
# WAY 4: While loop with explicit index
# =============================================================================
def remove_element_4(nums, val):
    """Same as Way 1 but with while loop."""
    i = 0
    j = 0
    while i < len(nums):
        if nums[i] != val:
            nums[j] = nums[i]
            j += 1
        i += 1
    return j


# =============================================================================
# WAY 5: Remove with built-in count
# =============================================================================
def remove_element_5(nums, val):
    """Use list.remove in a loop. Less efficient but readable."""
    while val in nums:
        nums.remove(val)
    return len(nums)


# =============================================================================
# WAY 6: Use pop in loop
# =============================================================================
def remove_element_6(nums, val):
    """Pop elements equal to val. O(n^2) but educational."""
    i = 0
    while i < len(nums):
        if nums[i] == val:
            nums.pop(i)
        else:
            i += 1
    return len(nums)


# =============================================================================
# WAY 7: Filter then extend (functional)
# =============================================================================
def remove_element_7(nums, val):
    """Use filter() and reset array."""
    result = list(filter(lambda x: x != val, nums))
    count = len(result)
    nums.clear()
    nums.extend(result)
    return count


# =============================================================================
# WAY 8: New array, copy back
# =============================================================================
def remove_element_8(nums, val):
    """Build new array, then copy. O(n) space."""
    kept = []
    for x in nums:
        if x != val:
            kept.append(x)
    count = len(kept)
    for i in range(count):
        nums[i] = kept[i]
    return count


# =============================================================================
# WAY 9: Counter-based approach
# =============================================================================
def remove_element_9(nums, val):
    """Use Counter to find count of non-val, then overwrite."""
    from collections import Counter
    c = Counter(nums)
    non_val_count = sum(v for k, v in c.items() if k != val)
    j = 0
    for x in nums:
        if x != val:
            nums[j] = x
            j += 1
    return j


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def remove_element_10(nums, val):
    """
    THE ONE TO MEMORIZE.

    Two-pointer: read pointer walks array, write pointer tracks next kept.
    Skip elements equal to val, copy others forward.

    Time:  O(n).
    Space: O(1).
    """
    j = 0
    for i in range(len(nums)):
        if nums[i] != val:
            nums[j] = nums[i]
            j += 1
    return j


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two-pointer (BEST)", remove_element_1),
        ("Way 2: Two-pointer swap end", remove_element_2),
        ("Way 3: List comprehension", remove_element_3),
        ("Way 4: While loop", remove_element_4),
        ("Way 5: Built-in remove", remove_element_5),
        ("Way 6: Pop in loop", remove_element_6),
        ("Way 7: Filter + clear", remove_element_7),
        ("Way 8: New array copy", remove_element_8),
        ("Way 9: Counter approach", remove_element_9),
        ("Way 10: Final cleanest", remove_element_10),
    ]

    def run_test(name, func, inp, val, expected_count):
        """Run a single test, copying input so we don't mutate original."""
        nums_copy = list(inp)
        result_count = func(nums_copy, val)
        # Check count.
        if result_count != expected_count:
            return False, f"count={result_count}, expected={expected_count}, nums={nums_copy}"
        # Check that first `count` elements are all not val.
        kept = nums_copy[:expected_count]
        if any(x == val for x in kept):
            return False, f"val still in kept: {kept}, nums={nums_copy}"
        return True, ""

    test_cases = [
        # (nums, val, expected_count)
        ([3, 2, 2, 3], 3, 2),
        ([0, 1, 2, 2, 3, 0, 4, 2], 2, 5),
        ([], 1, 0),
        ([1], 1, 0),
        ([1], 2, 1),
        ([2, 2, 2], 2, 0),
        ([1, 2, 3, 4], 5, 4),
        ([1, 1, 1, 1], 1, 0),
        ([4, 5], 4, 1),
        ([3, 3], 5, 2),
    ]

    print("=" * 70)
    print("REMOVE ELEMENT - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/remove-element")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for inp, val, expected_count in test_cases:
            try:
                ok, msg = run_test(name, func, inp, val, expected_count)
                if not ok:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: inp={inp}, val={val}, {msg}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: inp={inp}, val={val}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
