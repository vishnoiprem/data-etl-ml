-- Problem 5 — Total authors, % with .com URL, % never made a sale
-- Difficulty: Easy-Medium | Round: Screening | Pattern: multiple aggregates in one pass

-- Goal
-- ----
-- Three numbers, one row:
--   1) Total number of authors
--   2) Percentage of authors whose website_url contains ".com"
--   3) Percentage of authors who have ZERO transactions on any of their books

-- Interview script
-- ----------------
-- "Two independent boolean conditions on authors. The cleanest pattern is
--  one CTE that flags each author, then a single SELECT aggregating
--  counts. LIKE '%\.com%' is portable; I'd note the ESCAPE clause for
--  hygiene. The 'never made a sale' check needs an anti-join: an author
--  whose books appear in NO transaction."

-- Solution
-- --------
WITH author_flags AS (
    SELECT
        a.author_id,
        CASE WHEN a.website_url LIKE '%.com%'           THEN 1 ELSE 0 END AS has_com_url,
        CASE WHEN NOT EXISTS (
            SELECT 1
            FROM books      AS b
            JOIN transactions AS t ON t.book_id = b.book_id
            WHERE b.author_id = a.author_id
        )                                                  THEN 1 ELSE 0 END AS no_sale
    FROM authors AS a
)
SELECT
    COUNT(*)                                           AS total_authors,
    100.0 * SUM(has_com_url) / NULLIF(COUNT(*), 0)     AS pct_with_com_url,
    100.0 * SUM(no_sale)      / NULLIF(COUNT(*), 0)     AS pct_no_sale
FROM author_flags;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- Authors (6 total): Alice, Brandon, Carla, Dmitri, Esha, Feng.
-- .com URLs: Alice (alice.com YES), Brandon (kim.io NO), Carla (NULL NO),
--   Dmitri (volkov.net NO), Esha (esha.com YES), Feng (NULL NO).
--   -> 2 of 6 = 33.33%
-- No sales: Feng's book 115 is never bought; every other author has at
--   least one book that appears in transactions.
--   -> 1 of 6 = 16.67%
--
-- Talk-track follow-ups
-- ---------------------
-- "What if URL has 'COM' (uppercase)?"
--   -> LIKE is case-insensitive in SQLite by default for ASCII; in
--      Postgres you'd use ILIKE; in MySQL you'd lowercase both sides.
-- "What if the URL contains a path like '/about.com'?"
--   -> My LIKE '%\.com%' uses a literal dot, so '/about.com' WOULD match.
--      Be honest about this in the interview.
