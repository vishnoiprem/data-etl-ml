-- sql_interviews/09_hard_practice/code/schema.sql
-- Schema and seed data for the M09 (Hard) practice module.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>

-- ============================================================
-- Problem 85: Median Finder per Group
-- ============================================================

CREATE TABLE Employee6 (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    salary        INTEGER NOT NULL,
    departmentId  INTEGER NOT NULL
);

INSERT INTO Employee6 (id, name, salary, departmentId) VALUES
    (1, 'Alice',   90000, 1),
    (2, 'Bob',     85000, 1),
    (3, 'Carol',   70000, 1),
    (4, 'Dan',     60000, 1),
    (5, 'Eve',    100000, 2),
    (6, 'Frank',   95000, 2),
    (7, 'Grace',   80000, 2),
    (8, 'Hank',    75000, 2);

-- ============================================================
-- Problem 86: Cumulative Sum with Reset
-- ============================================================

CREATE TABLE Events (
    id   INTEGER PRIMARY KEY,
    val  INTEGER NOT NULL,
    kind TEXT NOT NULL
);

INSERT INTO Events (id, val, kind) VALUES
    (1,  10, 'add'),
    (2,  20, 'add'),
    (3,   0, 'reset'),
    (4,  15, 'add'),
    (5,  25, 'add'),
    (6,   0, 'reset'),
    (7,   5, 'add');

-- ============================================================
-- Problem 87: Tournament Winners
-- ============================================================

CREATE TABLE Tournament (
    player_id INTEGER NOT NULL,
    group_id  INTEGER NOT NULL,
    score     INTEGER NOT NULL
);

INSERT INTO Tournament (player_id, group_id, score) VALUES
    (1, 1, 100),
    (2, 1,  90),
    (3, 1,  95),
    (4, 2,  80),
    (5, 2,  85),
    (6, 2,  92),
    (7, 3,  88),
    (8, 3,  77);

-- ============================================================
-- Problem 88: Department Salary Ranking w/ Tie-Breaking
-- ============================================================

CREATE TABLE Department4 (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Employee7 (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    salary        INTEGER NOT NULL,
    departmentId  INTEGER NOT NULL
);

INSERT INTO Department4 (id, name) VALUES
    (1, 'Engineering'),
    (2, 'Sales');

INSERT INTO Employee7 (id, name, salary, departmentId) VALUES
    (1, 'Alice', 90000, 1),
    (2, 'Bob',   90000, 1),  -- ties with Alice
    (3, 'Carol', 80000, 1),
    (4, 'Dan',   70000, 1),
    (5, 'Eve',   85000, 2),
    (6, 'Frank', 85000, 2),  -- ties with Eve
    (7, 'Grace', 75000, 2);

-- ============================================================
-- Problem 89: Stock Price Analysis
-- ============================================================

CREATE TABLE StockPrice (
    stock_id INTEGER NOT NULL,
    ts       TEXT NOT NULL,
    price    INTEGER NOT NULL
);

INSERT INTO StockPrice (stock_id, ts, price) VALUES
    (1, '2024-01-01', 100),
    (1, '2024-01-02', 110),
    (1, '2024-01-03', 105),
    (1, '2024-01-04', 115),
    (1, '2024-01-05', 120),
    (1, '2024-01-06', 95),
    (1, '2024-01-07', 90),
    (1, '2024-01-08', 100);

-- ============================================================
-- Problem 90: Employee Bonus Calculation
-- ============================================================

CREATE TABLE Employee8 (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    salary INTEGER NOT NULL,
    bonus INTEGER
);

INSERT INTO Employee8 (id, name, salary, bonus) VALUES
    (1, 'Alice', 50000, 5000),
    (2, 'Bob',   60000, NULL),
    (3, 'Carol', 70000, 7000),
    (4, 'Dan',   80000, NULL);

-- ============================================================
-- Problem 91: Consecutive Available Seats
-- ============================================================

CREATE TABLE Seats (
    seat_id INTEGER PRIMARY KEY,
    free    INTEGER NOT NULL
);

INSERT INTO Seats (seat_id, free) VALUES
    (1, 1),
    (2, 0),
    (3, 1),
    (4, 1),
    (5, 0),
    (6, 1),
    (7, 1),
    (8, 1),
    (9, 0);

-- ============================================================
-- Problem 92: Rank Scores
-- ============================================================

CREATE TABLE Scores (
    id    INTEGER PRIMARY KEY,
    score INTEGER NOT NULL
);

INSERT INTO Scores (id, score) VALUES
    (1, 100),
    (2, 90),
    (3, 90),
    (4, 80),
    (5, 75);

-- ============================================================
-- Problem 93: Department Salary Stats
-- ============================================================

CREATE TABLE Department5 (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Employee9 (
    id            INTEGER PRIMARY KEY,
    departmentId  INTEGER NOT NULL,
    salary        INTEGER NOT NULL
);

INSERT INTO Department5 (id, name) VALUES
    (1, 'Engineering'),
    (2, 'Sales'),
    (3, 'Marketing');

INSERT INTO Employee9 (id, departmentId, salary) VALUES
    (1, 1, 90000),
    (2, 1, 85000),
    (3, 1, 70000),
    (4, 2, 95000),
    (5, 2, 80000),
    (6, 3, 60000);

-- ============================================================
-- Problem 94: Trip Cancellation Rate by Day
-- ============================================================

CREATE TABLE Trips2 (
    id         INTEGER PRIMARY KEY,
    status     TEXT NOT NULL,
    request_at TEXT NOT NULL
);

INSERT INTO Trips2 (id, status, request_at) VALUES
    (1, 'completed', '2024-01-01'),
    (2, 'cancelled', '2024-01-01'),
    (3, 'cancelled', '2024-01-01'),
    (4, 'completed', '2024-01-02'),
    (5, 'completed', '2024-01-02'),
    (6, 'cancelled', '2024-01-03'),
    (7, 'completed', '2024-01-03'),
    (8, 'cancelled', '2024-01-03'),
    (9, 'cancelled', '2024-01-03');

-- ============================================================
-- Problem 95: Market Analysis II
-- ============================================================

CREATE TABLE Users3 (
    user_id  INTEGER PRIMARY KEY,
    name     TEXT NOT NULL
);

CREATE TABLE Items (
    item_id  INTEGER PRIMARY KEY,
    item_brand TEXT NOT NULL
);

CREATE TABLE Orders3 (
    order_id   INTEGER PRIMARY KEY,
    seller_id  INTEGER NOT NULL,
    buyer_id   INTEGER NOT NULL,
    item_id    INTEGER NOT NULL,
    order_date TEXT NOT NULL
);

INSERT INTO Users3 (user_id, name) VALUES
    (1, 'Alice'),
    (2, 'Bob'),
    (3, 'Carol'),
    (4, 'Dan');

INSERT INTO Items (item_id, item_brand) VALUES
    (1, 'Apple'),
    (2, 'Samsung'),
    (3, 'Apple'),
    (4, 'Sony');

INSERT INTO Orders3 (order_id, seller_id, buyer_id, item_id, order_date) VALUES
    (1, 1, 2, 1, '2024-01-15'),  -- buyer 2 bought Apple (item 1)
    (2, 1, 3, 3, '2024-02-10'),  -- buyer 3 bought Apple (item 3)
    (3, 2, 4, 2, '2024-01-20'),  -- buyer 4 bought Samsung (item 2)
    (4, 4, 1, 4, '2024-02-05'),  -- buyer 1 bought Sony (item 4)
    (5, 3, 2, 2, '2024-02-20'),  -- buyer 2 also bought Samsung (item 2)
    (6, 4, 3, 2, '2024-03-01'),  -- buyer 3 also bought Samsung
    (7, 3, 4, 1, '2024-03-05'),  -- buyer 4 also bought Apple (item 1)
    (8, 2, 1, 3, '2024-03-10'),  -- buyer 1 also bought Apple (item 3)
    (9, 1, 2, 3, '2024-03-15'),  -- buyer 2 also bought Apple (item 3) → 2 Apple for buyer 2
    (10, 4, 3, 4, '2024-03-20'); -- buyer 3 also bought Sony

-- ============================================================
-- Problem 96: Sales Analysis by Year
-- ============================================================

CREATE TABLE Sales3 (
    sale_id   INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    sale_date TEXT NOT NULL,
    amount    INTEGER NOT NULL
);

INSERT INTO Sales3 (sale_id, product_id, sale_date, amount) VALUES
    (1, 1, '2022-06-15', 100),
    (2, 1, '2023-06-15', 200),
    (3, 2, '2022-07-01', 150),
    (4, 2, '2023-07-01', 250),
    (5, 2, '2024-07-01', 180);

-- ============================================================
-- Problem 97: Number of Transactions per Visit
-- ============================================================

CREATE TABLE Visits (
    user_id    INTEGER NOT NULL,
    visit_date TEXT NOT NULL
);

CREATE TABLE Transactions (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    visit_date TEXT NOT NULL,
    amount     INTEGER NOT NULL
);

INSERT INTO Visits (user_id, visit_date) VALUES
    (1, '2024-01-01'),
    (1, '2024-01-02'),
    (1, '2024-01-04'),
    (2, '2024-01-01'),
    (3, '2024-01-02');

INSERT INTO Transactions (id, user_id, visit_date, amount) VALUES
    (1, 1, '2024-01-01', 100),
    (2, 1, '2024-01-01', 150),
    (3, 1, '2024-01-02',  80),
    (4, 2, '2024-01-01', 200),
    (5, 3, '2024-01-02', 300);

-- ============================================================
-- Problem 98: Last Person to Fit in the Bus
-- ============================================================

CREATE TABLE Bus (
    person_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    weight    INTEGER NOT NULL,
    turn      INTEGER NOT NULL
);

INSERT INTO Bus (person_id, name, weight, turn) VALUES
    (1, 'Alice',  300, 1),
    (2, 'Bob',    400, 2),
    (3, 'Carol',  500, 3),
    (4, 'Dan',    200, 4),
    (5, 'Eve',    350, 5);

-- Bus capacity = 1000.
