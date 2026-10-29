-- sql_interviews/07_easy_practice/code/schema.sql
-- Schema and seed data for the M07 (Easy) practice module.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- This file is the single source of truth for the M07 schema.
-- The test file runs the contents of this file before each
-- test, so adding a new column here updates every test that
-- uses it.

-- ============================================================
-- Schema: Employee / Department
-- ============================================================

CREATE TABLE Department (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Employee (
    id            INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    salary        INTEGER NOT NULL,
    departmentId  INTEGER REFERENCES Department(id),
    managerId     INTEGER REFERENCES Employee(id),
    hireDate      TEXT
);

INSERT INTO Department (id, name) VALUES
    (1, 'Engineering'),
    (2, 'Sales'),
    (3, 'Marketing'),
    (4, 'Finance');

INSERT INTO Employee (id, name, salary, departmentId, managerId, hireDate) VALUES
    (1, 'Alice',   120000, 1, NULL, '2020-01-15'),
    (2, 'Bob',      95000, 1, 1,    '2020-03-22'),
    (3, 'Carol',   150000, 1, 1,    '2019-06-10'),
    (4, 'Dan',     110000, 2, NULL, '2021-09-01'),
    (5, 'Eve',      85000, 2, 4,    '2022-02-14'),
    (6, 'Frank',   130000, 2, 4,    '2021-11-30'),
    (7, 'Grace',    78000, 3, NULL, '2023-04-05'),
    (8, 'Hank',     92000, 3, 7,    '2023-08-12'),
    (9, 'Ivy',     105000, 4, NULL, '2022-07-19'),
    (10, 'Judy',    88000, 4, 9,    '2023-01-25');

-- ============================================================
-- Schema: Customer / Orders
-- ============================================================

CREATE TABLE Customer (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT
);

CREATE TABLE Orders (
    id         INTEGER PRIMARY KEY,
    customerId INTEGER REFERENCES Customer(id),
    total      INTEGER,
    status     TEXT,
    orderDate  TEXT
);

INSERT INTO Customer (id, name, email) VALUES
    (1, 'Karen',  'karen@example.com'),
    (2, 'Leo',    'leo@example.com'),
    (3, 'Mia',    'mia@example.com'),
    (4, 'Nate',   'nate@example.com'),
    (5, 'Olive',  'olive@example.com'),
    (6, 'Paul',   'paul@example.com');

INSERT INTO Orders (id, customerId, total, status, orderDate) VALUES
    (1, 1, 100, 'delivered', '2024-01-15'),
    (2, 1, 200, 'delivered', '2024-02-20'),
    (3, 1, 150, 'shipped',   '2024-03-10'),
    (4, 2, 300, 'delivered', '2024-01-22'),
    (5, 2, 250, 'cancelled', '2024-02-05'),
    (6, 3,  50, 'delivered', '2024-03-12'),
    (7, 4, 400, 'delivered', '2024-02-28'),
    (8, 4, 175, 'delivered', '2024-04-03'),
    (9, 5, 220, 'pending',   '2024-04-15');

-- ============================================================
-- Schema: Person (for "remove duplicate emails")
-- ============================================================

CREATE TABLE Person (
    id    INTEGER PRIMARY KEY,
    email TEXT NOT NULL
);

INSERT INTO Person (id, email) VALUES
    (1, 'a@example.com'),
    (2, 'b@example.com'),
    (3, 'a@example.com'),
    (4, 'c@example.com'),
    (5, 'b@example.com'),
    (6, 'a@example.com'),
    (7, 'd@example.com');

-- ============================================================
-- Schema: Weather (for "rising temperature")
-- ============================================================

CREATE TABLE Weather (
    id          INTEGER PRIMARY KEY,
    recordDate  TEXT NOT NULL,
    temperature INTEGER NOT NULL
);

INSERT INTO Weather (id, recordDate, temperature) VALUES
    (1, '2024-01-01', 10),
    (2, '2024-01-02', 15),
    (3, '2024-01-03', 12),
    (4, '2024-01-04', 20),
    (5, '2024-01-05', 18),
    (6, '2024-01-06', 25);

-- ============================================================
-- Schema: Country (for "big countries")
-- ============================================================

CREATE TABLE Country (
    name       TEXT PRIMARY KEY,
    population INTEGER NOT NULL,
    area       INTEGER NOT NULL
);

INSERT INTO Country (name, population, area) VALUES
    ('USA',       330000000,  9834000),
    ('China',    1400000000,  9597000),
    ('India',    1380000000,  3287000),
    ('Brazil',    215000000,  8516000),
    ('Monaco',       39000,       2),
    ('Vatican',        800,       0);

-- ============================================================
-- Schema: ProductSales
-- ============================================================

CREATE TABLE ProductSales (
    id        INTEGER PRIMARY KEY,
    productId INTEGER,
    saleDate  TEXT,
    amount    INTEGER
);

INSERT INTO ProductSales (id, productId, saleDate, amount) VALUES
    (1, 1, '2024-01-15', 100),
    (2, 1, '2024-02-20', 200),
    (3, 1, '2024-03-10', 150),
    (4, 2, '2024-01-22', 300),
    (5, 2, '2024-02-05', 250),
    (6, 3, '2024-03-12',  50);

-- ============================================================
-- Schema: Course (for "classes more than 5 students")
-- ============================================================

CREATE TABLE Course (
    student TEXT NOT NULL,
    class   TEXT NOT NULL
);

INSERT INTO Course (student, class) VALUES
    ('A', 'Math'),
    ('B', 'Math'),
    ('C', 'Math'),
    ('D', 'Math'),
    ('E', 'Math'),
    ('F', 'Math'),
    ('G', 'English'),
    ('H', 'English'),
    ('I', 'English'),
    ('J', 'English'),
    ('K', 'Physics'),
    ('L', 'Physics'),
    ('M', 'Physics'),
    ('N', 'Physics'),
    ('O', 'Physics'),
    ('P', 'Physics'),
    ('Q', 'History'),
    ('R', 'History'),
    ('S', 'History'),
    ('T', 'History');

-- ============================================================
-- Schema: TestScore (for "calculate test scores")
-- ============================================================

CREATE TABLE TestScore (
    student TEXT NOT NULL,
    subject TEXT NOT NULL,
    score   INTEGER  -- nullable
);

INSERT INTO TestScore (student, subject, score) VALUES
    ('A', 'Math',    90),
    ('A', 'English', 85),
    ('A', 'Math',    95),
    ('B', 'Math',    78),
    ('B', 'English', NULL),
    ('C', 'Math',    NULL),
    ('C', 'English', 88),
    ('D', 'Science', 92),
    ('D', 'Science', NULL);

-- ============================================================
-- Schema: InstagramPost (for "monthly post success")
-- ============================================================

CREATE TABLE InstagramPost (
    id       INTEGER PRIMARY KEY,
    userId   INTEGER,
    postDate TEXT,
    likes    INTEGER,
    comments INTEGER
);

INSERT INTO InstagramPost (id, userId, postDate, likes, comments) VALUES
    (1, 1, '2024-01-05', 100, 20),
    (2, 1, '2024-01-15', 150, 30),
    (3, 1, '2024-02-01', 200, 50),
    (4, 1, '2024-02-20', 180, 45),
    (5, 2, '2024-01-10',  50, 10),
    (6, 2, '2024-02-15',  75, 15),
    (7, 2, '2024-03-01', 100, 25),
    (8, 3, '2024-01-12', 300, 60);
