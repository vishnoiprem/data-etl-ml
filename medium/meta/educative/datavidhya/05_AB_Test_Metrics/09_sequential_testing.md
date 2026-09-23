# Sequential Testing / Always-Valid p-Values

## Problem
Avoid inflating Type I error when peeking at A/B results over time.

## How to Think
1. Standard fixed-horizon test inflates false positives with peeking.
2. Always-valid p-values (mSPRT, confidence sequences) maintain Type I at all t.
3. Approximately: p_always_valid ~ p_fixed / sqrt(t_fraction).

## How to Remember
- **Pattern**: "p_av ~ p_fixed / sqrt(t_fraction)."
- Pre-register t (planned sample size) and t_fraction = current_n / planned_n.

## Code (Python)
```python
import math
def always_valid_p(z, t_fraction):
    p_fixed = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return min(1.0, p_fixed / math.sqrt(t_fraction))
```

## Common Mistakes
- Using a fixed-horizon p-value and peeking — false positives.
- Forgetting to specify t_fraction.

## AI Use Cases
- Continuous monitoring of live experiments.
- Auto-stop experiments when significance is reached.
- Real-time dashboards.
