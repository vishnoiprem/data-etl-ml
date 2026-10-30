# Compute Reservation Diff for Largest Member

## 1. Simple way to think
- `copies(copy_id, reserved_by_member_id)`: a copy is reserved by a member (or NULL if available).
- `members(member_id, referred_by_member_id)`: members can refer other members.
- "Largest member" almost certainly means the member with the maximum `member_id` (the question says "single result").
- The "diff" is likely: for that top member, count their reservations vs. something else (reservations by the member they referred, or reservations of all members they referred, etc.).
- Clarify with the interviewer — this question is under-specified and that itself is the trick.

## 2. Interview write-up (how to solve it)
The safest answer: return the top member's `member_id` and a count of copies they have reserved.

```sql
WITH top_member AS (
    SELECT MAX(member_id) AS member_id FROM members
)
SELECT tm.member_id,
       COUNT(c.copy_id) FILTER (WHERE c.reserved_by_member_id = tm.member_id) AS their_reservations,
       (SELECT COUNT(*) FROM copies WHERE reserved_by_member_id = tm.member_id)
         - (SELECT COUNT(*) FROM copies
            WHERE reserved_by_member_id IN (
                SELECT member_id FROM members WHERE referred_by_member_id = tm.member_id
            )) AS reservation_diff
FROM top_member tm
LEFT JOIN copies c ON c.reserved_by_member_id = tm.member_id
GROUP BY tm.member_id;
```

If "diff" is intended as "number of copies reserved by the top member vs. the member who referred them":
```sql
WITH top_member AS (SELECT MAX(member_id) AS member_id FROM members)
SELECT tm.member_id,
       (SELECT COUNT(*) FROM copies WHERE reserved_by_member_id = tm.member_id)
     - (SELECT COUNT(*) FROM copies
        WHERE reserved_by_member_id = (SELECT referred_by_member_id FROM members WHERE member_id = tm.member_id))
       AS reservation_diff
FROM top_member tm;
```

## 3. Best optimized solution
Reduce to a single aggregation, with a covering index.

```sql
CREATE INDEX idx_copies_reserved_by ON copies (reserved_by_member_id);
CREATE INDEX idx_members_referred_by ON members (referred_by_member_id, member_id);

WITH top AS (SELECT MAX(member_id) AS member_id FROM members),
     counts AS (
         SELECT reserved_by_member_id AS mid, COUNT(*) AS n
         FROM copies
         WHERE reserved_by_member_id IN (SELECT member_id FROM top
                                         UNION
                                         SELECT referred_by_member_id FROM members
                                         WHERE member_id = (SELECT member_id FROM top))
         GROUP BY 1
     )
SELECT t.member_id,
       COALESCE(MAX(c.n) FILTER (WHERE c.mid = t.member_id), 0)
     - COALESCE(MAX(c.n) FILTER (WHERE c.mid <> t.member_id), 0) AS reservation_diff
FROM top t LEFT JOIN counts c ON TRUE
GROUP BY t.member_id;
```

### Why it's optimal
- One scan of `copies` (filtered to two member ids), one scan of `members`.
- `FILTER` is planner-friendly for conditional aggregation.
- Indexes make the `IN` lookups an index probe.

### Common mistakes & interviewer tips
- "Largest" being ambiguous: it could mean largest `member_id` (numeric), or member with most reservations. Always ask.
- Forgetting that `MAX(member_id)` is the simplest "largest" — don't overthink it.
- Tip: in interviews, naming the ambiguity and proposing a sensible default is half the battle. Say: "I'm interpreting 'largest' as `MAX(member_id)`. If you meant 'most active', the query would change here."
