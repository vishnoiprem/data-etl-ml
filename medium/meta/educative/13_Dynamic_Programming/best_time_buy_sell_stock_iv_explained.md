# Best Time to Buy and Sell Stock IV

## Problem
Given `prices[i]` for each day and an integer `k`, return the maximum profit
achievable with **at most `k` transactions**. A transaction = buy + later sell.
You can hold at most one stock at a time.

## Approach: DP with two states per transaction

### Key Insight
For each transaction count `t` (0..k), we track two states:
- `sell[t]` = max profit up to today, ending **without a stock**, having
  completed at most `t` transactions.
- `hold[t]` = max profit up to today, ending **holding a stock**, having
  completed at most `t` transactions.

### Transitions (each day)
```
new_sell[t] = max(sell[t],           # did nothing today
                  hold[t] + price)   # sold today: complete a transaction

new_hold[t] = max(hold[t],           # did nothing today
                  sell[t-1] - price) # bought today: start a new transaction
```

### Initialization
- `hold[0] = -prices[0]` (bought on day 0, no completed transactions)
- `sell[t] = 0` for all `t`
- `hold[t] = -prices[0]` for all `t` (could have bought on day 0)

### Answer
`sell[k]` (we want to end with no stock).

### Big-k Optimization
If `k >= n // 2`, we can't possibly need more than `n // 2` transactions
(you can do at most one buy+sell per ~2 days). In that case, just sum
every consecutive upward move greedily for `O(n)` time.

## Walkthrough: `k=2, prices=[3,2,6,5,0,3]`

Following the DP, the answer is **7** (e.g., buy 2 sell 6 = +4, buy 0 sell 3 = +3).

## Complexity
- **Time:** `O(n * k)` in the general case, `O(n)` when `k >= n // 2`
- **Space:** `O(k)`

## Edge Cases
- `k = 0` → `0` profit
- `n < 2` → `0` profit
- `k >= n // 2` → greedy solution (no transaction-count limit matters)
