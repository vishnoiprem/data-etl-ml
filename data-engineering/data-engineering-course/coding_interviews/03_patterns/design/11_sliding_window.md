# 11 — Sliding Window

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

Use when you need a contiguous subarray / substring of dynamic length that satisfies a constraint (sum, distinct count, etc.).

## Template

```python
left = 0
state = {}
for right in range(len(arr)):
    # add arr[right] to state
    while not valid(state):
        # remove arr[left] from state
        left += 1
    # answer = max(answer, right - left + 1)
```

## Examples in this course

- 33 Longest Substring Without Repeating
- 50 Longest Substring with At Most K Distinct
- 78 Sliding Window Maximum
