# Best Time to Buy and Sell Stock — 10 Solutions + Interview Thinking

## Problem
Given an array `prices` where `prices[i]` is the stock price on day `i`,
find the maximum profit from one transaction (buy one day, sell a later
day). Return 0 if no profit is possible.

Reference: LeetCode #121 / Educative Grokking — "Best Time to Buy and
Sell Stock".

---

## Interview Talking Points

Lead with the **invariant**: "Track the minimum price seen so far.
For each day, profit = today − min so far. Keep the max."

Then mention why this works: the best sell day is paired with the best
buy day that came BEFORE it.

---

## 10-Step Thinking Process

### 1. Understand
"One buy + one sell. Buy must be BEFORE sell. Maximize sell − buy."

### 2. Key Insight
For each day `i`, the best profit ending at `i` is
`prices[i] - min(prices[0..i])`. Track the maximum of this.

### 3. Pattern Recognition
Single-pass with two variables:
- `min_price`: lowest price seen so far (best buy day)
- `max_profit`: best profit seen so far (best sell day)

### 4. Edge Cases
- `len(prices) == 1` → 0 (can't sell).
- Strictly decreasing prices → 0.
- All same prices → 0.
- Profit only at end → returned correctly.

### 5. Tricky Detail — Order of Updates

There are two natural orders:
1. **Update min first, then compute profit**:
   ```
   if p < min_price: min_price = p
   else if p - min_price > max_profit: max_profit = ...
   ```
2. **Compute profit first, then update min**:
   ```
   max_profit = max(max_profit, p - min_price)
   min_price = min(min_price, p)
   ```

Both work. The second is cleaner but be careful: when `p < min_price`,
we don't want `p - min_price = p - p = 0` to be recorded as a "profit"
(this is fine since 0 is the floor).

### 6. Algorithm
```
min_price = inf
max_profit = 0
for p in prices:
    max_profit = max(max_profit, p - min_price)
    min_price = min(min_price, p)
return max_profit
```

### 7. Why It Works
For any pair `(buy_day, sell_day)` with `buy_day < sell_day`:
- `prices[buy_day]` is some past price.
- At iteration `i = sell_day`, `min_price = min(prices[0..sell_day])`
  which is ≤ `prices[buy_day]`.
- So `prices[sell_day] - min_price >= prices[sell_day] - prices[buy_day]`.

We track `max_profit` across all `sell_day`, so we find the maximum.

### 8. Complexity
- **Time**: O(n) — single pass.
- **Space**: O(1) — only two scalars.

### 9. Code Structure
1. Edge case: empty / single element.
2. Initialize min_price (inf or prices[0]).
3. Single loop updating both.
4. Return max_profit.

### 10. Mental Trace
`prices = [7, 1, 5, 3, 6, 4]`:
- p=7: min=7. profit=0. max=0.
- p=1: min=1. profit=0. max=0.
- p=5: min=1. profit=4. max=4.
- p=3: min=1. profit=2. max=4.
- p=6: min=1. profit=5. max=5.
- p=4: min=1. profit=3. max=5.
- Returns 5. ✓

`prices = [7, 6, 4, 3, 1]`:
- p=7: min=7. profit=0. max=0.
- p=6: min=6. profit=0. max=0.
- ... (all decreasing).
- Returns 0. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Track min_price (BEST)                | O(n)    | O(1)  | canonical |
| 2  | Same with reversed update order       | O(n)    | O(1)  | cleaner |
| 3  | Brute force O(n²)                     | O(n²)   | O(1)  | educational |
| 4  | enumerate + min tracking              | O(n)    | O(1)  | pythonic |
| 5  | Kadane on differences                 | O(n)    | O(1)  | alt view |
| 6  | itertools.accumulate                  | O(n)    | O(n)  | functional |
| 7  | numpy                                 | O(n)    | O(n)  | extra dep |
| 8  | Recursive                             | O(n)    | O(n)  | call stack |
| 9  | Sorted max-min (WRONG)                | O(n log n) | O(n)  | doesn't enforce order |
| 10 | Explicit min/max loop                 | O(n)    | O(1)  | readable |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal, idiomatic:

```python
def max_profit(prices):
    min_price = float('inf')
    max_profit = 0
    for p in prices:
        if p < min_price:
            min_price = p
        elif p - min_price > max_profit:
            max_profit = p - min_price
    return max_profit
```

Or more concise:

```python
def max_profit(prices):
    min_price = float('inf')
    max_profit = 0
    for p in prices:
        max_profit = max(max_profit, p - min_price)
        min_price = min(min_price, p)
    return max_profit
```

---

## Common Pitfalls

1. **Forgetting that buy < sell** — the sorted approach (V9) fails
   this. Always enforce order via the running minimum.
2. **Initializing min_price to 0** — for prices like `[5, 4, 3]`, you'd
   get min=0 and profit=5 (wrong). Use `float('inf')` or `prices[0]`.
3. **Using `max` on negative profit and forgetting to floor at 0** —
   if no profit is possible, return 0.
4. **Confusing with multi-transaction variant (LC #122)** — different
   problem. Here, only ONE transaction.
5. **Off-by-one in brute force** — buy at `i`, sell at `j > i`. Loop
   `j in range(i+1, n)`.

---

## Talking Points — Interview Cheat Sheet

If asked "why does tracking the minimum work?":
> "For any sell day `i`, the best buy day is the minimum price before
> `i`. We track this running minimum, and for each day compute the
> profit if we sold today. Take the max over all days."

If asked "what's the alternative approach?":
> "Kadane's algorithm on price differences. But that doesn't buy/sell
> in the right order intuitively — it just gives the same answer
> via a different lens (max sum subarray)."

If asked "how does this extend to multiple transactions?":
> "LC #122: with multiple transactions, the answer is sum of all
> positive price differences. Same greedy principle."

If asked "what if there are transaction fees?":
> "LC #714: subtract the fee from each profitable transaction.
> Otherwise same approach."

---

## Related Problems

- **Best Time to Buy and Sell Stock II** (LC #122) — multiple
  transactions allowed.
- **Best Time to Buy and Sell Stock with Transaction Fee** (LC #714).
- **Best Time to Buy and Sell Stock with Cooldown** (LC #309).
- **Best Time to Buy and Sell Stock IV** (LC #188) — at most K
  transactions.

---

## Variants

- **Multiple transactions**: sum of all `max(0, prices[i+1] - prices[i])`.
- **At most K transactions**: dynamic programming (different problem).
- **With cooldown**: DP with state (holding, not-holding-with-cooldown).
- **With transaction fee**: greedy with profit > fee threshold.