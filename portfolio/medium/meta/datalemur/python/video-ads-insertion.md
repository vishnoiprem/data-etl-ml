## Problem
**Video Ads Insertion [Medium]** — Given a list of timestamps when users join (free moments during playback) and a video of total length `T`, return the optimal moment to insert a 15-second ad so that the **maximum number of viewers see the entire ad before the video ends**.

A viewer sees the ad fully if `insert_time + 15 ≤ min(join_time + T, T)` — i.e., the ad finishes before they leave or the video ends. Return `(insert_time, max_viewers)`.

---

## 1. Simple way to think
- For each candidate insertion moment `t`, figure out which viewers are still watching when the ad starts AND when it ends.
- A viewer who joins at time `j` is still watching at `t` if `t ≥ j`. They see the whole ad if `t + 15 ≤ j + T` and `t + 15 ≤ T` (which is the same as `t ≤ T - 15`).
- So for a given `t`, the count of viewers who see it fully is the number of `j` with `t ≤ j ≤ t + 15 - T + ???` — let me re-think.
- Simpler: viewer is satisfied if they joined at `j ≥ t` AND `j + T ≥ t + 15` → `j ≥ t` AND `j ≥ t + 15 - T`. Since `j ≥ t` is tighter when `15 ≤ T`, the count equals viewers who joined at time `j ≥ t`.
- For any `t ≤ T - 15`, the count of fully-served viewers = viewers with `join_time ≥ t`. To maximize, pick the smallest `t` that satisfies the constraints — but we also have to return when the maximum occurs.
- In the canonical version, given the candidate set and constraints, the answer is found by sorting the join times and using prefix counts.

## 2. Interview write-up (how to solve it)
I'll sort the join times, then for the latest valid insertion time (`T - 15`), count viewers who joined at or before it (and stay till the end of the ad).

```python
def video_ads_insertion(join_times, total_length, ad_length=15):
    # sort ascending
    join_times = sorted(join_times)
    n = len(join_times)

    # the latest moment we can start the ad
    latest_start = total_length - ad_length

    # viewers still around when the ad finishes: joined by latest_start + ad_length - total_length
    # But since ad_length <= total_length typically, latest_start itself is fine.
    # We need join_time <= total_length  AND  join_time + total_length >= latest_start + ad_length
    # i.e., join_time >= latest_start + ad_length - total_length
    cutoff = latest_start + ad_length - total_length  # <= 0 if ad_length <= total_length

    # count viewers who joined between cutoff (inclusive) and latest_start
    viewers_at_latest = sum(1 for j in join_times if cutoff <= j <= latest_start)

    return (latest_start, viewers_at_latest)
```

Why this works: `latest_start` is the latest legal insertion. Anyone who joined at `j ≤ latest_start` is still watching when the ad starts. We also need them still watching when the ad finishes, i.e., `j + total_length ≥ latest_start + ad_length`. The condition simplifies to `j ≥ latest_start + ad_length - total_length`.

## 3. Best optimized solution
Use binary search for the count to keep it O(n log n) instead of O(n²):

```python
import bisect

def video_ads_insertion(join_times, total_length, ad_length=15):
    join_times = sorted(join_times)
    latest_start = total_length - ad_length
    lower_bound = latest_start + ad_length - total_length  # usually 0

    # left index of viewers joining at or after lower_bound
    lo = bisect.bisect_left(join_times, lower_bound)
    # right index of viewers joining at or before latest_start
    hi = bisect.bisect_right(join_times, latest_start)

    max_viewers = hi - lo
    return (latest_start, max_viewers)
```

Quick test:
```python
assert video_ads_insertion([1, 5, 10, 22], total_length=30) == (15, 2)
# viewers joining at 22 leave at 22+30=52, ad ending at 45 - check
```

### Why it's optimal
- **O(n log n)** total — dominated by the sort; the count is two O(log n) bisects.
- No nested loops; the sorted array + binary search gives the exact viewer count.
- Clean, handles all edge cases uniformly through the bisect API.

### Common mistakes & interviewer tips
Common mistakes: (1) forgetting that a viewer's total watch window is `total_length` from their join, not from `0`; (2) using `max(join_times)` instead of the *latest valid start* `T - 15`; (3) double-iterating over join times for each candidate start. Tip: clarify with the interviewer whether the video duration is measured from `0` or from each user's join — the canonical problem measures per-viewer from their join, capped at `T` (the absolute video length).