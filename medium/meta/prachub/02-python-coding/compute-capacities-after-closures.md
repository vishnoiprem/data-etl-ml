# Compute Capacities After Site Closures

## 1. Simple way to think
- You have a nested dict `redistribution[closed_site][dest_site] = added_capacity`.
- The input also gives the current capacity of each site, e.g. `capacity[site] = n`.
- For each site that closes, the added capacity flows into the destination. Final capacity = current capacity + sum of additions from any closed site pointing to it.
- The catch: a destination site itself might close, in which case its incoming additions get re-routed to *its* destinations (transitively).
- Mental model: this is a graph where edges represent capacity flow. If a node is removed, walk its outgoing edges and propagate.

## 2. Interview write-up (how to solve it)
Use BFS / DFS to traverse the closure graph. Each closed site contributes its entire current capacity (plus anything routed to it from other closed sites) to its destinations.

```python
from collections import defaultdict

def final_capacities(capacity: dict, redistribution: dict, closed: list) -> dict:
    """
    capacity:        {site: current_capacity}
    redistribution:  {closed_site: {dest_site: added_capacity}}
    closed:          [list of site ids being closed]
    Returns {site: final_capacity} for every site.
    """
    final = dict(capacity)  # start with current

    # Walk the closure graph: each closed site routes its capacity
    def flow(site, amount):
        """Recursively distribute `amount` from `site` to its destinations."""
        for dest, add in redistribution.get(site, {}).items():
            final[dest] = final.get(dest, 0) + add * (amount / capacity[site])
            # If dest is also closing, keep propagating
            if dest in closed_set:
                flow(dest, add)

    closed_set = set(closed)
    for s in closed:
        if s in capacity and capacity[s] > 0:
            flow(s, capacity[s])
            final[s] = 0  # closed site ends with zero

    return final
```

A cleaner version uses a stack to avoid Python recursion limits on deep closure chains.

## 3. Best optimized solution
```python
def final_capacities(capacity, redistribution, closed):
    final = dict(capacity)
    closed_set = set(closed)
    # Aggregate total incoming flow per dest
    incoming = defaultdict(float)
    for src, dests in redistribution.items():
        for d, amt in dests.items():
            incoming[d] += amt

    # Closed sites get redistributed; if a dest is also closed, re-aggregate
    # iteratively until fixed point.
    changed = True
    while changed:
        changed = False
        for site in list(closed_set):
            if site not in redistribution:
                continue
            outgoing = redistribution[site]
            for d, amt in outgoing.items():
                if d in closed_set:
                    # roll into its destinations
                    for d2, amt2 in redistribution.get(d, {}).items():
                        incoming[d2] += amt * (amt2 / sum(outgoing.values()))
                        changed = True
                else:
                    final[d] = final.get(d, 0) + amt
        closed_set -= {site for site in closed_set if site not in redistribution}

    for s in closed_set:
        final[s] = 0
    return final
```

### Why it's optimal
- O(V + E) per iteration of the fixed-point loop; usually converges in 1–2 passes because the closure graph is a DAG.
- Iterative approach avoids recursion depth issues.
- Using `defaultdict` makes aggregation O(1) per update.

### Common mistakes & interviewer tips
- Forgetting that a destination might also be in the closed set.
- Double-counting when a closed site routes to another closed site.
- Tip: clarify whether capacity is conserved (sum of inputs == sum of outputs). If yes, the answer can be sanity-checked instantly.
