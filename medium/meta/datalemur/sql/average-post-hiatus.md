## Problem
**Average Post Hiatus (Part 1) [Easy]** — Given a user's posts, find the number of days between each post and the **previous post** by the same user.

**Schema:**
- `posts(user_id, post_id, post_date)`

Return one row per post showing `(user_id, post_id, post_date, days_since_prev)`. The first post per user should return `NULL` (or 0) since there is no previous post.

---

## 1. Simple way to think
- For each user, walk their posts in time order.
- For every post except the very first, count the days between it and the post right before it.
- Think of it like measuring the gap between consecutive check-ins on a trip.
- SQL has a perfect feature for this: window functions. Specifically `LAG()`, which lets you peek at the previous row within the same partition (user).
- Once you have the previous date next to the current date, subtract — done.

## 2. Interview write-up (how to solve it)
I'll use `LAG()` partitioned by user and ordered by date. Then I subtract to get the day gap.

```sql
SELECT
  user_id,
  post_id,
  post_date,
  post_date - LAG(post_date) OVER (
    PARTITION BY user_id
    ORDER BY post_date
  ) AS days_between
FROM posts;
```

Notes:
- `LAG(post_date)` looks back one position inside the window. The first row per user gets NULL.
- Subtracting two dates in most SQL dialects returns an integer (days). In PostgreSQL you can use `post_date - LAG(post_date) ...`; in MySQL use `DATEDIFF(post_date, LAG(...))`.

## 3. Best optimized solution
```sql
SELECT
  user_id,
  post_id,
  post_date,
  DATEDIFF(
    post_date,
    LAG(post_date) OVER (PARTITION BY user_id ORDER BY post_date)
  ) AS days_between
FROM posts;
```

For PostgreSQL:
```sql
SELECT
  user_id,
  post_id,
  post_date,
  post_date - LAG(post_date) OVER (
    PARTITION BY user_id ORDER BY post_date
  ) AS days_between
FROM posts;
```

If the prompt wants the *average* hiatus per user, wrap with `AVG`:
```sql
SELECT user_id,
  AVG(post_date - LAG(post_date) OVER (PARTITION BY user_id ORDER BY post_date)) AS avg_hiatus
FROM posts
GROUP BY user_id;
```

### Why it's optimal
- Single pass over `posts` — no self-join, no correlated subquery.
- Window functions are streaming-friendly and avoid the O(n²) cost of comparing every pair.
- Index on `(user_id, post_date)` lets the engine partition + sort efficiently.

### Common mistakes & interviewer tips
A common mistake is doing a self-join like `posts a JOIN posts b ON a.user_id = b.user_id AND b.post_date < a.post_date` — that explodes rows and is hard to get exactly "previous." Always reach for `LAG()`. Also remember `LAG()` returns NULL for the first row, so don't accidentally turn that into `0` unless the prompt demands it. Interview tip: mention that window functions are evaluated after `WHERE`/`GROUP BY` but before `ORDER BY` of the outer query.