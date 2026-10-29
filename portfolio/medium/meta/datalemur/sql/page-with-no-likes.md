## Problem
**Page With No Likes [Easy]** — Facebook wants to know which pages have zero likes.

**Schema:**
- `pages(page_id, name)`
- `page_likes(user_id, page_id, liked_date)`

Return the `page_id`s (or `name`s) of pages that have **no likes at all**.

---

## 1. Simple way to think
- You have two tables: a list of pages and a list of likes.
- We want pages that nobody liked.
- Think of it like a guest book: which people never got a single signature?
- The simplest move is to scan every page and ask "did this page_id show up in the likes table?"
- If a page_id never appears in `page_likes`, it's a page with zero likes.
- This is a classic "anti-join" pattern — pages that DON'T match anything in the other table.

## 2. Interview write-up (how to solve it)
I'll use a LEFT JOIN from `pages` to `page_likes`. The LEFT JOIN keeps every page on the left even if there's no match on the right — unmatched rows get NULLs. Then I filter where the right-side column is NULL.

```sql
SELECT p.page_id
FROM pages p
LEFT JOIN page_likes pl
  ON p.page_id = pl.page_id
WHERE pl.page_id IS NULL;
```

Why this works: the LEFT JOIN guarantees every page is in the result. Pages with at least one like will have a non-NULL `pl.page_id`. Pages with zero likes will have NULL because there's no row to join to. The `WHERE pl.page_id IS NULL` keeps only those unmatched pages.

Alternative using `NOT IN`:
```sql
SELECT page_id FROM pages
WHERE page_id NOT IN (SELECT page_id FROM page_likes WHERE page_id IS NOT NULL);
```

I'd pick the LEFT JOIN version in an interview because `NOT IN` can misbehave when NULLs are present.

## 3. Best optimized solution
```sql
SELECT page_id
FROM pages
LEFT JOIN page_likes USING (page_id)
WHERE page_id IS NULL;
```

Or with `NOT EXISTS`, which many engines optimize well:
```sql
SELECT page_id
FROM pages p
WHERE NOT EXISTS (
  SELECT 1 FROM page_likes pl WHERE pl.page_id = p.page_id
);
```

### Why it's optimal
- A single scan of `pages` and a single scan of `page_likes` via the join — no nested loop explosion.
- LEFT JOIN with anti-join filter is usually the fastest pattern; the planner can use a hash anti-join.
- `NOT EXISTS` short-circuits per outer row and is NULL-safe.

### Common mistakes & interviewer tips
A common mistake is using `NOT IN` without filtering NULLs — if any `page_likes.page_id` is NULL, the whole query returns empty. Prefer LEFT JOIN or NOT EXISTS. Interviewers love hearing "I'll use an anti-join because it's NULL-safe and typically uses a hash join under the hood." Mention indexing on `page_likes.page_id` if asked about scale.