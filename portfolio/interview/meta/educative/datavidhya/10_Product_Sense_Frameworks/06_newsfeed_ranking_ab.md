# News Feed Ranking Change - A/B Design

## Problem
Design an A/B test for a News Feed ranking change.

## How to Think
1. **Hypothesis** – pre-register.
2. **Primary** – DAU, time spent.
3. **Secondary** – composition, creator-side engagement.
4. **Counter** – cannibalization of other surfaces, negative reactions.
5. **Experiment** – unit, MDE, power, duration.
6. **Analysis** – pre-registered subgroup plans.

## How to Remember
- **Pre-register everything.**
- **Watch cannibalization** across Reels / Stories / Marketplace.

## Hypothesis
H: Prioritizing friends+family in ranking -> +DAU without reducing total time.

## Metrics
| Tier | Metric |
|---|---|
| Primary | DAU, time spent / DAU |
| Secondary | Friend-impression share, creator engagement, D7 retention |
| Counter | Reels / Stories / Marketplace time, negative reactions, survey NPS |

## A/B Setup
- Unit: user_id
- Split: 50/50
- Duration: 4 weeks
- MDE: +0.5% relative DAU
- Power 0.8, alpha 0.05

## Code (Sample Size)
```python
import math

def sample_size_per_arm(p_dau=0.5, mde=0.005, alpha=0.05, power=0.8):
    z_a, z_b = 1.96, 0.84
    p1 = p_dau * (1 + mde)
    num = (z_a + z_b) ** 2 * (p1*(1-p1) + p_dau*(1-p_dau))
    den = (p1 - p_dau) ** 2
    return math.ceil(num / den)
```

## Common Mistakes
- Pre-registering AFTER seeing data (p-hacking).
- Too-small MDE -> experiment underpowered.
- Ignoring long-term effects (4 weeks is usually enough, but check 8).

## AI Use Cases
- Auto pre-registration template generation.
- Always-valid sequential testing.
- Cannibalization causal decomposition across surfaces.
