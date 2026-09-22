# Number of Steps to Reduce a Binary Number to One

## Problem
Given a binary string `str`, count steps to reduce it to `1`:
- Even → divide by 2
- Odd → add 1

## Approach: Greedy with String Simulation

### Key Insight
- "Divide by 2" on a binary string = remove the last (rightmost) bit.
- "Add 1" = binary increment: propagate carry while LSB is 1.

So we simulate the operations directly on the binary representation.

### Algorithm
1. Reverse the string so the LSB is at index 0 (easy to drop / carry).
2. Convert each character to int.
3. While the number is not exactly `[1]`:
   - If LSB == 0 → pop the LSB (one division-by-2 step).
   - If LSB == 1 → add 1 by carry propagation.

## Walkthrough: `"1101"` (13)

```
1101 -> 1110 (add 1, carry)   step 1
1110 -> 111  (divide by 2)    step 2
111  -> 1000 (add 1, carry)   step 3
1000 -> 100  (divide by 2)    step 4
100  -> 10   (divide by 2)    step 5
10   -> 1    (divide by 2)    step 6
```

Total: **6 steps** ✓

## Complexity
- **Time:** `O(n²)` worst case (e.g., `"111...1"` causes a carry to propagate through every bit)
- **Space:** `O(n)` for the digit list

## Greedy Choice
At each step, we have no choice — the operation is forced by parity.
The "greedy" aspect is that we always take the only legal next step
and trust it leads to the optimal (minimum) count, which it does.

## Edge Cases
- Already `"1"` → 0 steps
- All `"1"`s → carry propagates to add one more bit, then divide-down
- Even number like `"10"` → 1 step
