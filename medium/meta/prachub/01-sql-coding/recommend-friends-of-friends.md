# Recommend Friends-of-Friends

## 1. Simple way to think
- This is the same shape as "two-hop follows" but framed as a friend graph.
- Given `graph = {A: [B, C], B: [C, D], C: [E]}`, for user U return everyone followed by U's followees, minus U and minus people U already follows.
- Same dedup and sort requirements.
- The only difference is the framing — make sure you call it out so the interviewer sees you recognized the overlap.

## 2. Interview write-up (how to solve it)
```python
def recommend_friends(graph, user):
    """
    graph: {user: [followees]}
    Returns: sorted list of people followed by user's followees, excluding
             the user themselves and people the user already follows.
    """
    already = set(graph.get(user, []))
    fofs = set()
    for followee in already:
        fofs.update(graph.get(followee, []))
    fofs.discard(user)
    fofs -= already
    return sorted(fofs)
```

Walk-through: `already = {B, C}`. For B, candidates = {C, D}. For C, candidates = {E}. Union = {C, D, E}. Remove already-followed {B, C} → {D, E}.

## 3. Best optimized solution
```python
def recommend_friends(graph, user):
    already = set(graph.get(user, ()))
    fofs = set().union(*(graph.get(f, ()) for f in already))
    fofs.discard(user)
    fofs -= already
    return sorted(fofs)


# --- tests ---
g = {"A": ["B", "C"], "B": ["C", "D"], "C": ["E"], "D": [], "E": ["A"]}
assert recommend_friends(g, "A") == ["D", "E"]
assert recommend_friends(g, "D") == []
assert recommend_friends(g, "E") == ["B", "C"]
print("ok")
```

### Why it's optimal
- `set().union(*iterables)` is C-level — faster than a Python `for` loop with `update`.
- Single pass over followees, set ops are O(1) average.
- Sorting at the end is O(k log k) where k = number of recommendations, usually tiny.

### Common mistakes & interviewer tips
- Including the user themselves in the result (the user might appear as someone's followee).
- Counting mutual friendships differently (e.g., weighted by number of paths) — clarify with the interviewer.
- Tip: if recommendations should be ranked, sort by "number of common followees." That's a one-line addition: count how many of the user's followees follow each candidate.
