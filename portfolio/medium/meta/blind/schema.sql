-- schema.sql
-- Shared bookstore schema used by all SQL solutions in this folder.
-- Designed for the Meta Data Engineer 2025 interview questions.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS invitations;
DROP TABLE IF EXISTS payment_types;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS payment_types;

CREATE TABLE authors (
    author_id   INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    website_url TEXT                        -- nullable; some authors have no site
);

CREATE TABLE books (
    book_id    INTEGER PRIMARY KEY,
    author_id  INTEGER NOT NULL REFERENCES authors(author_id),
    title      TEXT NOT NULL,
    price      REAL NOT NULL
);

CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    registered_on   DATE NOT NULL,           -- signup date
    invited_by      INTEGER REFERENCES customers(customer_id)
);

CREATE TABLE payment_types (
    payment_type_id INTEGER PRIMARY KEY,
    name            TEXT NOT NULL            -- 'credit_card', 'paypal', etc.
);

CREATE TABLE transactions (
    transaction_id   INTEGER PRIMARY KEY,
    customer_id      INTEGER NOT NULL REFERENCES customers(customer_id),
    book_id          INTEGER NOT NULL REFERENCES books(book_id),
    payment_type_id  INTEGER NOT NULL REFERENCES payment_types(payment_type_id),
    purchase_date    DATE NOT NULL,
    amount           REAL NOT NULL
);

CREATE TABLE invitations (
    inviter_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    invitee_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    PRIMARY KEY (inviter_id, invitee_id)
);

-- Sample data
INSERT INTO authors VALUES
    (1, 'Alice Walker',    'https://alice.com'),
    (2, 'Brandon Kim',     'https://kim.io'),
    (3, 'Carla Diaz',      NULL),
    (4, 'Dmitri Volkov',   'volkov.net'),
    (5, 'Esha Patel',      'esha.com/about'),
    (6, 'Feng Liu',        NULL);

INSERT INTO books VALUES
    (101, 1, 'The Color Book',     12.50),
    (102, 1, 'Walking Tales',      9.99),
    (103, 1, 'Color Theory',       15.00),
    (104, 1, 'Sunrise Stories',    11.25),
    (105, 1, 'Letters Home',       8.00),
    (106, 1, 'Garden Essays',      14.75),
    (107, 2, 'Kim Recipes',        22.00),
    (108, 3, 'Diaz Diaries',       7.50),
    (109, 4, 'Volkov Voyages',     18.00),
    (110, 5, 'Patel Poems',        10.00),
    (111, 5, 'Indian Sunsets',     13.25),
    (112, 5, 'Monsoon Verses',     9.50),
    (113, 5, 'Spice Markets',      12.00),
    (114, 5, 'Temple Bells',       16.50),
    (115, 6, 'Liu Letters',        8.75);

INSERT INTO payment_types VALUES
    (1, 'credit_card'),
    (2, 'paypal'),
    (3, 'gift_card');

INSERT INTO customers VALUES
    (1001, 'Nina',    DATE('2024-01-15'), NULL),
    (1002, 'Oscar',   DATE('2024-02-01'), 1001),
    (1003, 'Priya',   DATE('2024-02-10'), 1001),
    (1004, 'Quentin', DATE('2024-03-05'), 1002),
    (1005, 'Rosa',    DATE('2024-04-12'), NULL),
    (1006, 'Sam',     DATE('2024-04-12'), NULL),    -- same-day-registered sales possible
    (1007, 'Tariq',   DATE('2024-05-20'), 1003),
    (1008, 'Uma',     DATE('2024-06-01'), 1001);

-- Transactions:
-- Nina (1001): buys books on 2024-03-01, 2024-06-15, 2024-12-01 (first, mid, last)
-- Oscar (1002): first day 2024-02-01 (registration day = same-day), also buys later
-- Priya (1003): first day 2024-02-10 (reg day), buys 3 books that day
-- Sam (1006): buys 3 books on 2024-04-12 (registration day) -- 3 rows, one day
-- Tariq (1007): buys 1 book on 2024-05-20 (reg day) -- only one transaction row
-- Quentin (1004): scattered buys
-- Rosa (1005): buys 4 books on first day, 4 books on last day
-- Uma (1008): one big purchase
INSERT INTO transactions VALUES
    (1,  1001, 101, 1, DATE('2024-03-01'), 12.50),
    (2,  1001, 102, 1, DATE('2024-03-01'),  9.99),
    (3,  1001, 103, 1, DATE('2024-06-15'), 15.00),
    (4,  1001, 104, 1, DATE('2024-12-01'), 11.25),
    (5,  1002, 105, 2, DATE('2024-02-01'),  8.00),    -- Oscar same-day
    (6,  1002, 106, 2, DATE('2024-02-01'), 14.75),
    (7,  1002, 107, 2, DATE('2024-08-15'), 22.00),
    (8,  1003, 108, 1, DATE('2024-02-10'),  7.50),    -- Priya same-day, 3 books
    (9,  1003, 109, 1, DATE('2024-02-10'), 18.00),
    (10, 1003, 110, 1, DATE('2024-02-10'), 10.00),
    (11, 1004, 111, 3, DATE('2024-03-15'), 13.25),
    (12, 1004, 112, 3, DATE('2024-07-20'),  9.50),
    (13, 1004, 113, 3, DATE('2024-09-10'), 12.00),
    (14, 1005, 114, 1, DATE('2024-04-15'), 16.50),    -- Rosa's first day: 4 books
    (15, 1005, 101, 1, DATE('2024-04-15'), 12.50),
    (16, 1005, 102, 1, DATE('2024-04-15'),  9.99),
    (17, 1005, 103, 1, DATE('2024-04-15'), 15.00),
    (18, 1005, 104, 1, DATE('2024-11-30'), 11.25),    -- Rosa's last day: 4 books
    (19, 1005, 105, 1, DATE('2024-11-30'),  8.00),
    (20, 1005, 106, 1, DATE('2024-11-30'), 14.75),
    (21, 1005, 107, 1, DATE('2024-11-30'), 22.00),
    (22, 1006, 108, 2, DATE('2024-04-12'),  7.50),    -- Sam same-day, 3 books (3 rows, one day)
    (23, 1006, 109, 2, DATE('2024-04-12'), 18.00),
    (24, 1006, 110, 2, DATE('2024-04-12'), 10.00),
    (25, 1007, 111, 1, DATE('2024-05-20'), 13.25),    -- Tariq same-day, but only 1 transaction row
    (26, 1008, 112, 1, DATE('2024-06-15'),  9.50),
    (27, 1008, 113, 1, DATE('2024-06-15'), 12.00),
    (28, 1008, 114, 1, DATE('2024-06-15'), 16.50);

-- Invitations: Nina invited Oscar and Priya and Uma; Oscar invited Quentin
INSERT INTO invitations VALUES
    (1001, 1002),
    (1001, 1003),
    (1001, 1008),
    (1002, 1004);
