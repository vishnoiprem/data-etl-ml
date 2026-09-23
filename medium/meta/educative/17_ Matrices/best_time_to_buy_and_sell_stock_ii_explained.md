# Best Time to Buy and Sell Stock II — 0.0001% Expert Guide

> **LeetCode 122** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/best-time-to-buy-and-sell-stock-ii
> **Problem:** `maxProfit(prices)` — max profit with unlimited transactions, holding ≤ 1 share.

---

## 📋 WHAT THE QUESTION ASKS

Given an array `prices` where `prices[i]` is the price on day `i`, find the maximum profit from any sequence of buy/sell transactions. You may complete as many transactions as you like, but you must hold at most one share at any time.

### Constraints
- `1 <= prices.length <= 3 * 10^4`
- `0 <= prices[i] <= 10^4`

### Examples
```
prices=[7,1,5,3,6,4]  -> 7   (buy 1 sell 5, buy 3 sell 6 = 4+3 = 7)
prices=[1,2,3,4,5]    -> 4   (buy 1 sell 5)
prices=[7,6,4,3,1]    -> 0   (no profitable transactions)
prices=[1]            -> 0
prices=[]             -> 0
prices=[1,9,2,8,3,7]  -> 18  (9-1)+(8-2)+(7-3) = 8+6+4
```

### Why This Is "Medium"
- Greedy insight (sum of positive diffs).
- O(n) time, O(1) space.
- Foundation for stock variants.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Unlimited transactions, hold ≤ 1 share at a time."

### Step 2: KEY INSIGHT — Greedy on Consecutive Diffs (5 min)
> "Sum all positive (prices[i] - prices[i-1]).
>
> Why? An uptrend (a < b < c) can be split:
> (b-a) + (c-b) = c-a = single transaction profit.
> So multiple small transactions capture same profit as one big one,
> but with no risk of missing the peak."

### Step 3: Why Greedy = Optimal (3 min)
> "If price[i+1] > price[i], we can earn price[i+1] - price[i] by
> buying on day i and selling on day i+1. There's no penalty for
> more transactions, so always take every upward step."

### Step 4: Algorithm (3 min)
```
1. profit = 0.
2. For i in 1..n-1:
     if prices[i] > prices[i-1]:
       profit += prices[i] - prices[i-1].
3. Return profit.
```

### Step 5: Edge Cases (2 min)
- Empty: 0.
- Single price: 0.
- All decreasing: 0.
- All increasing: prices[-1] - prices[0].

### Step 6: Code It (3 min)

```python
def maxProfit(prices):
    profit = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            profit += prices[i] - prices[i - 1]
    return profit
```

### Step 7: Verify (2 min)
For `[7,1,5,3,6,4]`:
- i=1: 1-7 = -6 (skip)
- i=2: 5-1 = +4 (profit=4)
- i=3: 3-5 = -2 (skip)
- i=4: 6-3 = +3 (profit=7)
- i=5: 4-6 = -2 (skip)
- Total: 7 ✓

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **Greedy sum positive diffs:** O(n) time, O(1) space. **BEST**.
> 2. **DP cash/hold:** O(n) time, O(1) space. Same complexity.
> 3. **Brute force:** O(n!) or O(2^n). Too slow.
>
> I'll use greedy."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need max profit with unlimited transactions, holding at most 1 share."

KEY INSIGHT: Greedy — sum all positive price differences.
Every upward step captures profit we can lock in.

ALGORITHM:
1. profit = 0.
2. For i in 1..n-1:
     if prices[i] > prices[i-1]:
       profit += prices[i] - prices[i-1].
3. Return profit.

COMPLEXITY: O(n) time, O(1) space.

EDGE CASES:
- Empty: 0.
- Single: 0.
- All decreasing: 0.

WHY GREEDY = OPTIMAL:
- Up trend (a < b < c): (b-a) + (c-b) = c-a = single-tx profit.
- More transactions = same profit, less risk.
- Take every upward step.

THE TRICK:
- "Up step = profit" — sum all positive diffs.
- No penalty for many small transactions.

ALTERNATE: DP with cash/hold states.
- cash[i] = max profit NOT holding after day i.
- hold[i] = max profit HOLDING after day i (negative).
- cash[i] = max(cash[i-1], hold[i-1] + prices[i])
- hold[i] = max(hold[i-1], cash[i-1] - prices[i])

RELATED:
- Stock I (LC 121): 1 transaction → O(n) but different logic.
- Stock III (LC 123): 2 transactions → 4-state DP.
- Stock with Cooldown (LC 309): add cooldown state.
- Stock with Fee (LC 714): subtract fee per transaction.
- Stock IV (LC 188): K transactions.
"""
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Greedy Sum of Positive Diffs (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Sum of positive diffs | O(n) | O(1) | **THE ANSWER** |
| 2 | Greedy with explicit delta | O(n) | O(1) | Variant |
| 5 | One-pass with prev | O(n) | O(1) | Variant |
| 6 | Sum with generator | O(n) | O(1) | Variant |
| 7 | Reduce | O(n) | O(1) | Functional |
| 8 | Class OOP | O(n) | O(1) | Reusable |
| 9 | Zip | O(n) | O(1) | Variant |
| 10 | Sentinel | O(n) | O(1) | Variant |
| 15 | Concise | O(n) | O(1) | Educational |
| 17 | Math identity | O(n) | O(1) | Variant |
| 20 | Final cleanest | O(n) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: DP with States

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | DP cash/hold | O(n) | O(1) | **Alternative** |
| 12 | DP arrays | O(n) | O(n) | Educational |
| 13 | Recursive memo | O(n) | O(n) | Top-down |
| 14 | Iterative states | O(n) | O(n) | Educational |

### 🟠 TIER 3: Brute / Simulation

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Peak-valley | O(n) | O(1) | Educational |
| 11 | Brute O(n^3) | O(n^3) | O(1) | Small n |
| 16 | Itertools accumulate | O(n) | O(1) | Educational |
| 18 | Explicit sim | O(n) | O(1) | Educational |
| 19 | Numpy | O(n) | O(1) | Vectorized |

---

## 💎 THE 5-LINE SOLUTION (Memorize!)

```python
def maxProfit(prices):
    profit = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            profit += prices[i] - prices[i - 1]
    return profit
```

**Time:** `O(n)`
**Space:** `O(1)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Sum of Positive Diffs = Max Profit

> For unlimited transactions, every upward step is capturable profit.
> Sum of positive diffs = total capturable profit = max profit.

**Connection to:**
- **Greedy:** Local optimum = global.
- **Math identity:** Telescoping sum.

### Insight 2: Why Unlimited Transactions Are Free

> There's no transaction cost. So splitting one big transaction into
> many small ones has no downside. Take every upward step.

**Connection to:**
- **Costless:** Free transactions.
- **Greedy:** Always take.

### Insight 3: Telescoping Sum Property

> (b-a) + (c-b) + (d-c) = d-a.
> Many small transactions in an uptrend = one big transaction.

**Connection to:**
- **Math:** Telescoping.
- **Invariant:** Same total.

### Insight 4: Connection to Stock I

> Stock I: 1 transaction. Track min price, max profit.
> Stock II: unlimited. Just sum positive diffs.

Same family, different constraints.

**Connection to:**
- **Problem family:** Stock variants.
- **Different constraints:** Different solutions.

### Insight 5: DP cash/hold Alternative

> cash[i] = max profit NOT holding after day i.
> hold[i] = max profit HOLDING after day i.
> Transitions: cash → max(cash, hold+price), hold → max(hold, cash-price).

Same answer, different angle.

**Connection to:**
- **State machine:** 2 states.
- **Same result:** Greedy = DP.

### Insight 6: Real-World Applications

| Application | Use |
|-------------|-----|
| **Trading** | Day trading strategies |
| **Crypto** | High-frequency trading |
| **Pricing** | Inventory buy/sell |
| **Currency** | FX arbitrage |
| **Commodities** | Energy trading |
| **Inventory** | Stock rotation |

**Day trading** is canonical.

### Insight 7: Why DP cash[i-1] in hold transition

> To buy today, we sell (un-hold) yesterday's stock.
> cash[i-1] is the profit available for buying.

**Connection to:**
- **State machine:** Sequential.
- **Constraint:** One share.

### Insight 8: Why O(n) is Optimal

> Must examine every price (or every transition).
> Single pass achieves O(n).
> Can't do better.

**Connection to:**
- **Lower bound:** Must read input.
- **Optimal:** O(n).

### Insight 9: Compare to Peak-Valley

> Peak-valley: find local minima (buy) and maxima (sell).
> Greedy: just sum positive diffs.
> Both give same result; greedy is simpler.

**Connection to:**
- **Alternative:** Same result.
- **Simpler:** Greedy wins.

### Insight 10: Why Not 2^n Subset Approach

> 2^n subsets of transactions is exponential.
> Greedy/DP achieves O(n).

**Connection to:**
- **Brute:** Too slow.
- **Greedy:** Optimal.

### Insight 11: Recursive Memo Equivalence

> Bottom-up DP = top-down DFS with memo.
> Recurrence: best(i, holding) = max(skip, take action).

**Connection to:**
- **Two paradigms:** Same result.
- **Memoization:** Top-down.

### Insight 12: Edge Case All Equal

> All prices same: zero profit (no upward steps).
> Loop correctly returns 0.

**Connection to:**
- **Edge case:** Handled.
- **Identity:** All zeros.

### Insight 13: Why Not Sort Prices

> Sorted prices give max profit (last - first) but ignores order.
> We need to keep chronological order.
> Greedy preserves order.

**Connection to:**
- **Order matters:** Sequential.
- **Greedy:** Local decisions.

### Insight 14: Connection to Maximum Subarray

> Maximum subarray: max sum of contiguous subarray.
> Stock II: max sum of all positive diffs.
> Similar but different (Stock II has "free" skip).

**Connection to:**
- **Pattern:** Sum-related.
- **Difference:** Constraints.

### Insight 15: Why Negative Diffs Skipped

> Negative diff = loss. We never take losses.
> Greedy filters them out via max(0, ...).

**Connection to:**
- **Filter:** Loss-free.
- **Standard:** Only positive.

---

## 🧪 TEST CASES

| `prices` | Expected | Note |
|----------|----------|------|
| `[7,1,5,3,6,4]` | 7 | Standard |
| `[1,2,3,4,5]` | 4 | Monotonic up |
| `[7,6,4,3,1]` | 0 | Monotonic down |
| `[1]` | 0 | Single |
| `[]` | 0 | Empty |
| `[1,2]` | 1 | Two prices |
| `[2,1]` | 0 | Decreasing |
| `[1,5,2,8]` | 10 | Multiple swings |
| `[3,3,3,3]` | 0 | Flat |
| `[1,9,2,8,3,7]` | 18 | Many swings |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Greedy** | **O(n)** | **O(1)** | **✅ BEST** |
| DP cash/hold | O(n) | O(1) | ✅ Alternative |
| DP arrays | O(n) | O(n) | ✅ Educational |
| Brute recursion | O(n^2) | O(n) | ❌ Slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Stock I (LC 121) | Single transaction | https://leetcode.com/problems/best-time-to-buy-and-sell-stock/ |
| Stock II (LC 122) | **This problem** | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/ |
| Stock III (LC 123) | 2 transactions | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/ |
| Stock with Cooldown (LC 309) | 3-state DP | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/ |
| Stock with Fee (LC 714) | Subtract fee | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-transaction-fee/ |
| Stock IV (LC 188) | K transactions | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iv/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Sum of positive diffs** = max profit for unlimited transactions.
2. **O(n) time, O(1) space** — optimal.
3. **Telescoping sum**: many small = one big.
4. **No transaction cost** allows splitting.
5. **Day trading** is canonical use case.
6. **DP cash/hold** is alternative with same complexity.
7. **Peak-valley** gives same result but more complex.
8. **Stock I** = 1 transaction, **Stock II** = unlimited.
9. **Greedy = DP** for this problem.
10. **Empty/single/decreasing** all return 0.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Day trading** | High-frequency strategies |
| **Crypto** | Multi-pair arbitrage |
| **FX** | Currency trading |
| **Inventory** | Buy/sell rotation |
| **Commodities** | Energy trading |
| **Options** | Spread strategies |
| **Pricing** | Dynamic pricing |
| **Auctions** | Bid timing |
| **Logistics** | Route optimization |
| **Supply chain** | Stock management |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the greedy sum in 60 seconds
- [x] Can code the 5-line solution in 30 seconds
- [x] Know complexity: O(n) time, O(1) space
- [x] Know why greedy = optimal (telescoping)
- [x] Know DP cash/hold alternative
- [x] Know peak-valley alternative
- [x] Know related Stock problems (I, III, Cooldown, Fee, IV)
- [x] Know telescoping sum identity
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 5.
**Insight:** "Sum of positive price diffs. Every upward step is profit. Telescoping: many small = one big."
