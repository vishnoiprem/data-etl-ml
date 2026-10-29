-- sql_interviews/tests/fixtures/capstone.sql
-- Minimal seed data for the capstone exercise. One file
-- covers all 5 capstone questions (with overlapping
-- tables).
-- Author: Prem Vishnoi <pvishnoi@avilx.com>

CREATE TABLE Customers (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    country TEXT
);

CREATE TABLE Orders (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES Customers(id),
    total       INTEGER,
    order_date  TEXT
);

CREATE TABLE Logins (
    user_id    INTEGER NOT NULL,
    login_date TEXT NOT NULL
);

INSERT INTO Customers (id, name, country) VALUES
    (1, 'Alice',   'US'),
    (2, 'Bob',     'US'),
    (3, 'Carol',   'UK'),
    (4, 'Dan',     'UK'),
    (5, 'Eve',     'DE'),
    (6, 'Frank',   'DE'),
    (7, 'Grace',   'US');

INSERT INTO Orders (id, customer_id, total, order_date) VALUES
    (1, 1, 100, '2024-01-15'),
    (2, 1, 200, '2024-02-20'),
    (3, 2, 300, '2024-01-22'),
    (4, 2, 150, '2024-03-10'),
    (5, 3, 250, '2024-01-25'),
    (6, 3, 100, '2024-02-28'),
    (7, 4, 400, '2024-02-15'),
    (8, 5,  50, '2024-03-05'),
    (9, 6, 175, '2024-01-30'),
    (10, 7, 220, '2024-02-10'),
    (11, 7, 280, '2024-03-15');

INSERT INTO Logins (user_id, login_date) VALUES
    (1, '2024-01-01'),
    (1, '2024-01-02'),
    (1, '2024-01-03'),
    (1, '2024-01-04'),
    (1, '2024-01-05'),
    (1, '2024-01-06'),
    (1, '2024-01-07'),
    (2, '2024-01-01'),
    (2, '2024-01-05'),
    (2, '2024-01-06'),
    (2, '2024-01-07'),
    (2, '2024-01-08'),
    (2, '2024-01-09'),
    (2, '2024-01-10'),
    (3, '2024-01-01'),
    (3, '2024-01-02');
