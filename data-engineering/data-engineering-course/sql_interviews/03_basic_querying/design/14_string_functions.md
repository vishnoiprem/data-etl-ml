# Lesson 14 — String Functions: CONCAT, SUBSTRING, LENGTH

> **Goal:** the string functions you'll actually use in
> data cleaning and ETL.

---

## CONCAT

Joins strings. In standard SQL, `||` is the concat operator.
In MySQL and SQLite, `CONCAT(...)` is the function form.

```sql
-- Standard SQL
SELECT first_name || ' ' || last_name AS full_name
FROM   Employee;

-- MySQL / SQLite
SELECT CONCAT(first_name, ' ', last_name) AS full_name
FROM   Employee;
```

NULL handling: `CONCAT` returns NULL if any argument is NULL.
In MySQL, `CONCAT` skips NULLs. In PostgreSQL, use
`CONCAT_WS(' ', first_name, last_name)` (with separator)
which also skips NULLs.

---

## SUBSTRING (or SUBSTR)

Extract a portion of a string. 1-indexed.

```sql
SELECT SUBSTRING(name, 1, 3)   -- first 3 characters
FROM   Employee;

SELECT SUBSTRING(name, 5)      -- from position 5 to the end
FROM   Employee;
```

In MySQL it's `SUBSTRING` or `SUBSTR`; in PostgreSQL it's
`SUBSTRING`; in SQLite it's `SUBSTR`. All work the same way.

The third argument is the length. `SUBSTRING(s FROM n FOR
len)` is the standard form (SQLite also supports it).

---

## LENGTH

Number of characters in a string.

```sql
SELECT LENGTH(name) FROM Employee;
```

Some databases have `CHAR_LENGTH` (character count, not byte
count) and `OCTET_LENGTH` (byte count). For ASCII they are
identical; for Unicode they differ.

In SQLite, `LENGTH` returns the character count. In
PostgreSQL, `LENGTH` returns the character count and
`OCTET_LENGTH` returns bytes.

---

## UPPER, LOWER

```sql
SELECT UPPER(name), LOWER(email) FROM Customer;
```

Case conversion. Useful for case-insensitive comparisons
when the database doesn't have `ILIKE`.

---

## TRIM, LTRIM, RTRIM

Remove whitespace (or another character) from the edges.

```sql
SELECT TRIM(name) FROM Employee;             -- both sides
SELECT LTRIM(name) FROM Employee;            -- left only
SELECT RTRIM(name) FROM Employee;            -- right only
SELECT TRIM('*' FROM name) FROM Employee;    -- custom char
```

Common in ETL: source data often has trailing whitespace
from fixed-width files.

---

## REPLACE

Replace all occurrences of a substring.

```sql
SELECT REPLACE(phone, '-', '') FROM Customer;   -- 555-1234 -> 5551234
```

Three arguments: the string, the search, the replacement.
Returns NULL if the input is NULL.

---

## COALESCE (with strings)

`COALESCE` is the standard "first non-null" function. With
strings, it lets you substitute a default:

```sql
SELECT name, COALESCE(nickname, name) AS display_name
FROM   Customer;
```

If `nickname` is NULL, fall back to `name`.

---

## POSITION (or INSTR, or CHARINDEX)

Find the position of a substring. 1-indexed; 0 if not found.

```sql
SELECT POSITION('@' IN email) FROM Customer;  -- standard SQL
SELECT INSTR(email, '@') FROM Customer;       -- SQLite, MySQL
```

`POSITION` returns the position. Combine with `SUBSTRING` and
`LENGTH` to split a string:

```sql
-- Split email at '@'
SELECT
  SUBSTRING(email, 1, POSITION('@' IN email) - 1) AS local_part,
  SUBSTRING(email, POSITION('@' IN email) + 1)    AS domain
FROM   Customer;
```

In production, prefer the regex or proper parsing if your
database has it.

---

## Common interview answers

- "Extract the domain from an email" — `SUBSTRING` + `POSITION`
  or regex.
- "Find rows where the name contains 'Smith'" — `LIKE '%Smith%'`.
- "Normalize phone numbers to digits only" — nested
  `REPLACE` calls.
- "Capitalize the first letter of a name" — `UPPER(SUBSTRING(name,
  1, 1)) || LOWER(SUBSTRING(name, 2))`.

---

## Try it

Given `Customer(id, name, email, country, phone)`:

1. Build a "display name" as `name` uppercased.
2. Extract the domain from `email`.
3. Strip non-digit characters from `phone` (use nested
   `REPLACE` calls, or a CTE with a regex if your database
   supports it).
