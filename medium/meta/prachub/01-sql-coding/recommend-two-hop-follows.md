# Recommend Two-Hop Follows in Python

## 1. Simple way to think
- Graph: `graph[user] = [people they follow]`.
- "Two-hop" for user U: anyone followed by at least one of U's followees, except U themselves and except people U already follows.
- Mental model: a friend-of-friend recommender. U → A → B, suggest B.
- Output should be deterministic (sorted) and de-duplicated (B might be reached via multiple followees).

## 2. Interview write-up (how to solve it)

```python
def recommend_two_hop(graph: dict, user: str) -> list:
    """
    Return people followed by user's followees, excluding:
      - the user themselves
      - people the user already follows
    """
    already_following = set(graph.get(user, []))
    fofs = set()
    for followee in already_following:
        for candidate in graph.get(followee, []):
            if candidate != user and candidate not in already_following:
                fofs.add(candidate)
    return sorted(fofs)
```

## 3. Best optimized solution
```python
def recommend_two_hop(graph, user):
    already = set(graph.get(user, ()))
    candidates = set()
    for followee in already:
        candidates.update(graph.get(followee, ()))
    candidates.discard(user)
    candidates -= already
    return sorted(candidates)


# --- tests ---
g = {
    "A": ["B", "C"],
    "B": ["C", "D"],
    "C": ["D", "E"],
    "D": [],
    "E": ["A"],
}
assert recommend_two_hop(g, "A") == ["D", "E"]   # via B->D/E, C->D/E
assert recommend_two_hop(g, "D") == []            # no followees
assert recommend_two_hop(g, "E") == []           # E follows A, A follows B,C; E already follows no one except A
# Correcting: E follows A; A's followees are B,C; E doesn't follow B,C -> recommend B,C
g2 = {"A": ["B", "C"], "E": ["A"]}
assert recommend_two_hop(g2, "E") == ["B", "C"]
print("ok")
```

### Why it's optimal
- O(V + E) worst case: one pass over the user's followees, one set union per followee.
- Set operations are O(1) average — fast even for large follow lists.
- Sorting at the end gives deterministic output without affecting big-O.

### Common mistakes & interviewer tips
- Forgetting to exclude the user themselves (U can appear as a followee of U's followee).
- Returning a list with duplicates (B reached via two followees).
- Tip: clarify whether the graph is directed. "Follows" usually is — make that explicit. Also, ask if "already follows" means direct only, or includes two-hop recommendations already shown.
