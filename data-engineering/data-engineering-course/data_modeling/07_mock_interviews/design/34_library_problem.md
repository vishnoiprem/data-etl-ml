# Lesson 34 — Practice: Library Management System

> **Format:** problem statement. Time-box: 30 minutes.
> Read the prompt, draw the schema, then read the
> solution in [`code/solutions.py`](../code/solutions.py).

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

## The prompt

Design a data warehouse for a **public library
management system**. The library has multiple branches,
each with thousands of books. Patrons (library members)
borrow and return books. The library wants to report
on:

1. **Circulation** — how many books are borrowed per
   branch per month.
2. **Overdue rate** — what % of borrowings are returned
   late.
3. **Popularity** — which books and authors are most
   borrowed.
4. **Patron engagement** — active patrons, retention,
   segments (students / adults / seniors).
5. **Collection health** — which books are never
   borrowed, which are damaged / lost.

The OLTP source tracks: books (title, author, ISBN,
genre), patrons (id, name, type, signup_date, branch_id),
branches (id, name, city), and loans (loan_id, book_id,
patron_id, branch_id, checkout_date, due_date,
return_date, status).

---

## What to produce

1. **Discovery questions** — at least five you'd ask
   the interviewer before drawing anything.
2. **Requirements doc** — the consumers, use cases,
   sources, and key facts.
3. **Star schema** — at least one fact table, with all
   dimensions, marked with grain.
4. **SCD choices** — for each dim, which SCD type.
5. **Three SQL queries** — circulation, overdue rate,
   popularity.
6. **Tradeoffs** — at least two you'd call out.

---

## Hints

- The grain is most likely *one row per loan* — a
  loan has a checkout and a return.
- Books are typically SCD 1 (an ISBN's title and
  author don't usually change). But what about
  *editions* and *reprints*? Worth asking.
- Patrons might be SCD 2 if their *type* (student /
  adult / senior) changes and we want to attribute
  Q1 loans to Q1 type.
- Branches are usually SCD 1 (a branch doesn't
  change attributes often).
- A "reservation" or "hold" is a separate concept
  from a loan. Worth asking if the brief covers
  holds.
- Damaged / lost is a *status*, not a fact. Could be
  a flag on the book dim or a separate factless fact
  for "damage events."

---

## Sample discovery questions

1. Is a "loan" a checkout event or the full
   open-to-close cycle? If the latter, do we need a
   separate fact for the return event?
2. Can a patron have multiple simultaneous loans?
3. Can a single book be borrowed multiple times in
   its lifetime (i.e., is `book_id` a specific copy
   or a title)?
4. Is "patron type" a slowly changing attribute? If
   a student turns adult in June, do Q1 loans
   attribute to student or adult?
5. What is "overdue"? Returned after `due_date`?
   Returned more than N days after `due_date`?
6. Are reservations / holds in scope?
7. Are digital loans (e-books) in scope? They have
   no physical branch.
8. Do we report on fines collected? If so, that's
   a separate fact.
9. What is the data refresh frequency? Daily loan
   snapshot or transactional?
10. Is there an inter-library loan (ILL) flow?

---

## Sample star schema (one possible answer)

```
fact_loans
   grain: one row per loan (checkout to return cycle)
   measures: loan_duration_days, days_overdue, fine_amount
   dimensions:
     dim_book      (SCD 1; attributes: title, author, isbn, genre, format)
     dim_patron    (SCD 2; attributes: name, type, signup_date, branch_id)
     dim_branch    (SCD 1; attributes: name, city, region)
     dim_date      (conformed; role-played for checkout_date_key, due_date_key, return_date_key)
   degenerate: loan_id
```

Optionally, a separate `fact_damage_events` for
"book was marked damaged or lost" (factless, with
`damage_date_key` and `damage_type_key`).

---

## Sample SQL queries

**Circulation per branch per month:**

```sql
SELECT b.branch_name, d.month,
       COUNT(*) AS loans
FROM fact_loans f
JOIN dim_branch b ON f.branch_key = b.branch_key
JOIN dim_date   d ON f.checkout_date_key = d.date_key
WHERE d.year = 2024
GROUP BY b.branch_name, d.month;
```

**Overdue rate per branch:**

```sql
SELECT b.branch_name,
       100.0 * SUM(CASE WHEN f.return_date_key > f.due_date_key
                        THEN 1 ELSE 0 END) / COUNT(*) AS overdue_pct
FROM fact_loans f
JOIN dim_branch b ON f.branch_key = b.branch_key
WHERE f.return_date_key IS NOT NULL
GROUP BY b.branch_name;
```

**Top 10 most-borrowed books:**

```sql
SELECT b.title, b.author, COUNT(*) AS borrow_count
FROM fact_loans f
JOIN dim_book b ON f.book_key = b.book_key
GROUP BY b.book_key, b.title, b.author
ORDER BY borrow_count DESC
LIMIT 10;
```

---

## Tradeoffs to call out

1. **One fact for the whole loan lifecycle vs
   separate facts for checkout and return.** I
   picked one fact because the loan is the natural
   unit of analysis and the return is a *completion*
   of the loan, not a separate event.
2. **SCD 2 on patron vs SCD 1.** SCD 2 enables
   historical attribution of Q1 loans to Q1 patron
   type. SCD 1 is simpler but loses that.
3. **Books as a dim with multiple copies vs a
   separate copy dim.** A library has 5 copies of
   "1984" — is the grain "one row per copy" or "one
   row per title"? Per-copy lets us track which
   physical copy is damaged. Per-title is simpler.
   The answer depends on whether the OLTP tracks
   copies.

---

## Try it

Set a 30-minute timer. Work the problem cold. Then
read [`code/solutions.py`](../code/solutions.py) and
[`tests/test_solutions.py`](../tests/test_solutions.py)
to see the working answer.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
