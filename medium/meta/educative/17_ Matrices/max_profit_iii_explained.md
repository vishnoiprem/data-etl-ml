# Best Time to Buy and Sell Stock III — 0.0001% Expert Guide

> **LeetCode 123** | **Difficulty:** Hard | **Avg Solve Time:** 40 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/best-time-to-buy-and-sell-stock-iii
> **Problem:** `maxProfit(prices)` — max profit with at most 2 transactions.

---

## 📋 WHAT THE QUESTION ASKS

Given `prices[]`, find the maximum profit with at most 2 buy-sell transactions. Each transaction = buy + sell. Must sell before next buy. Hold at most one stock at a time.

### Constraints
- `1 <= prices.length <= 10^5`
- `0 <= prices[i] <= 10^5`

### Examples
```
prices=[3,3,5,0,0,3,1,4] -> 6   (buy 0, sell 3, buy 1, sell 4 = 3+3)
prices=[1,2,3,4,5]      -> 4   (one tx: buy 1, sell 5)
prices=[7,6,4,3,1]      -> 0   (no profitable tx)
prices=[1,5,2,8]        -> 10  ((5-1) + (8-2))
prices=[2,1,4,5,2,9,7]  -> 11  ((5-1) + (9-2))
prices=[]               -> 0
```

### Why This Is "Hard"
- Multi-transaction tracking.
- State machine with 4 variables.
- LC 123 (Stock III) is the k=2 case of LC 188 (Stock IV).

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (2 min)
> "Max profit, at most 2 transactions, sequential, hold ≤ 1 stock."

### Step 2: KEY INSIGHT — 4-State Machine (5 min)
> "Track 4 states per day:
> - buy1: max profit holding 1st stock (negative cost)
> - sell1: max profit after selling 1st stock
> - buy2: max profit holding 2nd stock
> - sell2: max profit after selling 2nd stock [ANSWER]
>
> Each day, update IN ORDER so transitions use latest values:
>   buy1  = max(buy1, -p)
>   sell1 = max(sell1, buy1 + p)
>   buy2  = max(buy2, sell1 - p)
>   sell2 = max(sell2, buy2 + p)"

### Step 3: Why Order Matters (3 min)
> "Each transition's right side must use the OLD state for the
> same day. If we wrote buy2 = max(buy2, sell1 - p) before
> updating sell1, we'd use stale sell1. But updating buy2 AFTER
> sell1 means sell1 is from today, but buy1 in sell1 uses buy1
> from yesterday — wait, sell1 = max(sell1, buy1 + p) is correct.
>
> Actually each line's RHS references the CURRENT day's already-updated
> vars for EARLIER transitions and OLD vars for SAME/SELF transition.
> Order matters."

### Step 4: Algorithm (3 min)
```
1. buy1 = -prices[0], buy2 = -prices[0].
2. sell1 = sell2 = 0.
3. For each p in prices[1:]:
     buy1  = max(buy1,  -p)
     sell1 = max(sell1, buy1 + p)
     buy2  = max(buy2,  sell1 - p)
     sell2 = max(sell2, buy2 + p)
4. Return sell2.
```

### Step 5: Edge Cases (2 min)
- Empty / single: 0.
- All decreasing: 0.
- Two ascents: 2 transactions sum.

### Step 6: Code It (3 min)

```python
def maxProfit(prices):
    if not prices: return 0
    buy1 = buy2 = -prices[0]
    sell1 = sell2 = 0
    for p in prices[1:]:
        buy1 = max(buy1, -p)
        sell1 = max(sell1, buy1 + p)
        buy2 = max(buy2, sell1 - p)
        sell2 = max(sell2, buy2 + p)
    return sell2
```

### Step 7: Verify (2 min)
For `[1,2,3,4,5]`:
- Init: buy1=-1, buy2=-1, sell1=0, sell2=0.
- p=2: buy1=-1, sell1=max(0,-1+2)=1, buy2=max(-1,1-2)=-1, sell2=max(0,-1+2)=1.
- p=3: buy1=-1, sell1=2, buy2=-1, sell2=2.
- p=4: sell1=3, sell2=3.
- p=5: sell1=4, sell2=4.
- Return 4. ✓

For `[3,3,5,0,0,3,1,4]`:
- p=3: buy1=-3, sell1=0; buy2=max(-3, 0-3)=-3; sell2=max(0,-3+3)=0.
- p=5: sell1=max(0,-3+5)=2; buy2=max(-3,2-5)=-3; sell2=max(0,-3+5)=2.
- p=0: buy1=max(-3,0)=-0; sell1=max(2,-0+0)=2; buy2=max(-3,2-0)=2; sell2=max(2,2+0)=2.
- p=0: sell1=max(2,0+0)=2; buy2=max(2,2-0)=2; sell2=max(2,2+0)=2.
- p=3: sell1=max(2,0+3)=3; buy2=max(2,2-3)=2; sell2=max(2,2+3)=5.
- p=1: sell1=max(3,0+1)=3; buy2=max(2,3-1)=2; sell2=max(5,2+1)=5.
- p=4: sell1=max(3,0+4)=4; buy2=max(2,3-4)=2; sell2=max(5,2+4)=6.
- Return 6. ✓

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **State DP (4 vars):** O(n) time, O(1) space. **BEST**.
> 2. **Split Point:** O(n) time, O(n) space. Cleaner to explain.
> 3. **Generalized k-tx:** O(n × k) time. For k=2, same as #1.
>
> I'll use State DP."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need max profit with at most 2 transactions.

KEY INSIGHT: 4-state machine.
- buy1:  max profit while holding stock #1.
- sell1: max profit after selling stock #1.
- buy2:  max profit while holding stock #2.
- sell2: max profit after selling stock #2 [ANSWER].

Each day, update in order:
  buy1  = max(buy1,  -p)
  sell1 = max(sell1, buy1 + p)
  buy2  = max(buy2,  sell1 - p)
  sell2 = max(sell2, buy2 + p)

ALGORITHM:
1. buy1 = buy2 = -prices[0], sell1 = sell2 = 0.
2. For each p in prices[1:]: update 4 states.
3. Return sell2.

COMPLEXITY: O(n) time, O(1) space.

EDGE CASES:
- Empty / single: 0.
- All decreasing: 0.
- One rising then falling: 1 tx.

ALTERNATE: Split Point — max over i of (best 1-tx in [0..i]
                                       + best 1-tx in [i..n-1]).
Compute left[] and right[] arrays.

RELATED:
- Stock I (LC 121): 1 tx.
- Stock II (LC 122): unlimited tx.
- Stock IV (LC 188): at most k tx.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: State DP (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | 4-state DP | O(n) | O(1) | **THE ANSWER** |
| 11 | 1D K=2 | O(n) | O(1) | Variant |
| 17 | Iterative state machine | O(n) | O(1) | Educational |
| 20 | Final cleanest | O(n) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Split Point DP

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | Split (L+R arrays) | O(n) | O(n) | Educational |
| 5 | Forward+backward | O(n) | O(n) | Educational |
| 10 | Two sweeps | O(n) | O(n) | Educational |
| 15 | Split arrays | O(n) | O(n) | Educational |

### 🟠 TIER 3: Generalized K Transactions

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | K=2 generalized | O(n×k) | O(k) | Extensible to k |
| 6 | 2D DP dp[k][d] | O(n×k) | O(n×k) | Educational |
| 7 | Rolling 2-row | O(n×k) | O(n) | Educational |
| 18 | LC classic 'best' | O(n×k) | O(n×k) | Educational |

### 🔵 TIER 4: Memoization / DFS / Brute

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Top-down memo (3D) | O(n) | O(n) | Top-down |
| 8 | Class OOP | O(n) | O(1) | Reusable |
| 9 | Min/Max tracked | O(n) | O(n) | Variant |
| 12 | Memo dict | O(n) | O(n) | Educational |
| 13 | Brute split | O(n^3) | O(1) | Reference |
| 14 | Numpy | O(n) | O(n) | Vectorized |
| 16 | Recursive no memo | O(2^n) | O(n) | Bad |
| 19 | Pure recursive | O(2^n) | O(n) | Bad |

---

## 💎 THE 9-LINE SOLUTION (Memorize!)

```python
def maxProfit(prices):
    if not prices:
        return 0
    buy1 = buy2 = -prices[0]
    sell1 = sell2 = 0
    for p in prices[1:]:
        buy1 = max(buy1, -p)
        sell1 = max(sell1, buy1 + p)
        buy2 = max(buy2, sell1 - p)
        sell2 = max(sell2, buy2 + p)
    return sell2
```

**Time:** `O(n)`
**Space:** `O(1)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Order of Updates is Critical

> Each `sell1 = max(sell1, buy1 + p)` uses the FRESH `buy1` from
> the same day. But `buy2 = max(buy2, sell1 - p)` uses the FRESH
> `sell1` from today (which is fine — buy2 means we just sold #1
> and bought #2 today, allowing back-to-back transactions).

**Connection to:**
- **State machine:** Update in topological order.
- **Concurrent updates:** Critical sequencing.

### Insight 2: K=2 is a Special Case of LC 188

> LC 188 (Stock IV) is at most K tx. K=2 gives LC 123.
> General solution: for each k, maintain buy[k], sell[k].

**Connection to:**
- **Problem family:** Stock problems.
- **Code reuse:** Adapt Stock IV template.

### Insight 3: Why 4 States, Not 2

> 2 states (hold, not-hold) suffice for unlimited txs (Stock II).
> With K txs cap, we need to TRACK how many txs done: 2K states.

**Connection to:**
- **State explosion:** K multiplies state space.
- **DP design:** #states = O(K).

### Insight 4: Negative Initialization is Key

> `buy1 = -prices[0]` represents "we already bought at prices[0]".
> Without this, `buy1 = max(0, -p)` would let us "sell" without buying.

**Connection to:**
- **Base cases:** Init is critical.
- **Subtle bugs:** Easy to miss.

### Insight 5: Split Point Alternative

> For each split day i: total = (best 1-tx in [0..i]) +
>                              (best 1-tx in [i..n-1]).
> Two linear passes to fill left[] and right[], then combine.

**Connection to:**
- **Preprocessing:** Linear passes.
- **Divide and conquer:** Split.

### Insight 6: Connection to Stock II

> Stock II (unlimited txs): 2-state machine.
> Stock III (≤2 txs): 4-state machine.
> Stock IV (≤k txs): 2k-state machine.

**Connection to:**
- **Generalization:** K is parameter.
- **Reusable code:** Same skeleton.

### Insight 7: Why sell1 = 0 Initially

> sell1 = 0 means "we sold 1st tx with zero profit". Allows
> not-doing any transaction in 1st slot.

**Connection to:**
- **Edge cases:** Allow skip.
- **Mathematical identity:** 0 is neutral profit.

### Insight 8: Generalization to K Transactions

```python
buy = [0] * (K + 1)   # buy[k] = profit after k buys
sell = [0] * (K + 1)  # sell[k] = profit after k sells
for k in range(1, K+1):
    buy[k] = -prices[0]
for p in prices[1:]:
    for k in range(1, K+1):
        sell[k] = max(sell[k], buy[k] + p)
        buy[k]  = max(buy[k], sell[k-1] - p)
return sell[K]
```

**Connection to:**
- **Extensibility:** K-tx template.
- **DP patterns:** Reusable.

### Insight 9: Real-World Applications

| Application | Use |
|-------------|-----|
| **Algorithmic trading** | Multi-trade strategies |
| **Portfolio rebalancing** | Sequential buy/sell |
| **Real estate** | 2 deals (buy-sell-buy-sell) |
| **Forex trading** | Multi-currency tx |
| **Inventory turnover** | Multiple purchase cycles |
| **Crypto trading** | Multi-tx profit |

**Algorithmic trading** is the canonical use case.

### Insight 10: Why buy1 + p (Not buy1 - p)

> `sell1 = max(sell1, buy1 + p)`: if buy1 is negative cost and we
> sell at p, profit = buy1 + p. Example: bought at 5 (buy1=-5),
> sell at 8, profit = -5 + 8 = 3. Correct.

**Connection to:**
- **Sign convention:** Negative = held cost.
- **Arithmetic:** Always check signs.

### Insight 11: State Updates in One Pass

> Single pass over prices, O(1) space. No need for DP tables.

**Connection to:**
- **Memory efficiency:** Constant space.
- **Streaming:** Process online.

### Insight 12: Connection to Subarray Sum Variants

> Max profit in [i..j] = max difference. Same as max subarray
> (with rearrangement).

**Connection to:**
- **Array algorithms:** Subarray max.
- **Problem reduction:** Convert.

### Insight 13: When State DP Beats Split

> State DP: O(1) space, O(n) time.
> Split: O(n) space, O(n) time.
> For interviews, state DP wins.

**Connection to:**
- **Memory:** State DP is optimal.
- **Trade-offs:** Space vs clarity.

### Insight 14: 4-State is the Minimal

> Can we do it with fewer? No — need to track 2 buy + 2 sell.

**Connection to:**
- **Lower bound:** Cannot reduce.
- **Optimal state count:** Proven minimal.

### Insight 15: Connection to Coin Change

> Same DP structure: linear scan, state transitions.

**Connection to:**
- **DP family:** Linear scan + transitions.
- **Pattern reuse:** Common.

### Insight 16: Edge: All Same Prices

> All equal: profit = 0 (no tx). Verify.

**Connection to:**
- **Edge testing:** Equal values.
- **Boundary:** Degenerate.

---

## 🧪 TEST CASES

| `prices` | Expected | Note |
|----------|----------|------|
| `[3,3,5,0,0,3,1,4]` | 6 | Standard |
| `[1,2,3,4,5]` | 4 | Single tx |
| `[7,6,4,3,1]` | 0 | Decreasing |
| `[1,5,2,8]` | 10 | Two txs |
| `[2,1,4,5,2,9,7]` | 11 | Two txs |
| `[3,2,6,5,0,3]` | 7 | Two txs |
| `[]` | 0 | Empty |
| `[1]` | 0 | Single |
| `[0,0,0,0]` | 0 | All zero |
| `[1,2,4,2,5,7,2,4,8,9]` | 13 | Complex |
| `[1,2]` | 1 | Simple |
| `[2,1]` | 0 | Reverse |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **4-state DP** | **O(n)** | **O(1)** | **✅ BEST** |
| Split Point | O(n) | O(n) | ✅ Alternative |
| 2D DP | O(n×k) | O(n×k) | ✅ Educational |
| Top-down memo | O(n) | O(n) | ✅ Top-down |
| Brute | O(n^3) | O(1) | ❌ Too slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Stock I (LC 121) | 2-state, 1 tx | https://leetcode.com/problems/best-time-to-buy-and-sell-stock/ |
| Stock II (LC 122) | 2-state, unlimited | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/ |
| Stock IV (LC 188) | 2k-state, k tx | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iv/ |
| Stock with Cooldown (LC 309) | State with cooldown | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/ |
| Stock with Fee (LC 714) | State with fee | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-transaction-fee/ |
| Stock III (LC 123) | **This problem** | https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **4-state DP** is optimal: O(n) time, O(1) space.
2. **Update in order**: buy1 → sell1 → buy2 → sell2.
3. **Initialize** buy1 = buy2 = -prices[0].
4. **sell2 is the answer**.
5. **K=2 special case** of Stock IV.
6. **Split-point** is O(n) space alternative.
7. **State count = 2k** for at most k transactions.
8. **Trading** is the canonical application.
9. **Same skeleton** as LC 121, 122, 188.
10. **Negative initialization** prevents phantom sells.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Algorithmic trading** | Multi-tx strategies |
| **Portfolio mgmt** | Sequential rebalancing |
| **Real estate** | 2 deals (buy-sell-buy-sell) |
| **Forex** | Multi-currency |
| **Inventory** | Multiple cycles |
| **Crypto** | Multi-tx profit |
| **Risk management** | Tx limits |
| **Backtesting** | Strategy evaluation |
| **Optimization** | Constrained max |
| **Time series** | Sequential decisions |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the 4-state DP in 90 seconds
- [x] Can code the 9-line solution in 90 seconds
- [x] Know complexity: O(n) time, O(1) space
- [x] Know why update order matters
- [x] Know why initialize buy with -prices[0]
- [x] Know split-point alternative
- [x] Know K-transaction generalization
- [x] Know related problems (LC 121, 122, 188, 309, 714)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 15 minutes.
**Lines of code to write:** 9.
**Insight:** "4-state DP: buy1, sell1, buy2, sell2. Update in order. sell2 is the answer."
