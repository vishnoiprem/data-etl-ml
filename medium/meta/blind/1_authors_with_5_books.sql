-- Problem 1 — Authors who have published at least 5 books
-- Difficulty: Easy | Round: Screening | Pattern: GROUP BY + HAVING

-- Goal
-- ----
-- Return the names of authors whose book count in the catalog is >= 5.
-- Output: author_name, book_count (sorted descending, ties by name).

-- Interview script
-- ----------------
-- "Grain of the answer: one row per author, so GROUP BY author.
--  The filter 'at least 5' is on an aggregate, so it goes in HAVING,
--  not WHERE. I'll JOIN books to authors on author_id to get the name,
--  COUNT(*) gives the book count."

-- Solution
-- --------
SELECT
    a.name           AS author_name,
    COUNT(b.book_id) AS book_count
FROM authors AS a
JOIN books    AS b ON b.author_id = a.author_id
GROUP BY a.author_id, a.name
HAVING COUNT(b.book_id) >= 5
ORDER BY book_count DESC, a.name ASC;

-- Expected output (against schema.sql sample data)
-- ------------------------------------------------
-- ('Alice Walker', 6)
-- ('Esha Patel', 5)
--
-- Talk-track follow-ups
-- ---------------------
-- "What if you want all authors (including those with 0 books)?"
--   -> LEFT JOIN; move the >= 5 filter into a WHERE on the count.
-- "Why HAVING and not WHERE?"
--   -> WHERE filters rows before aggregation; HAVING filters groups after.
--   -> If you wrote WHERE COUNT(b.book_id) >= 5, you'd get a SQL error.
