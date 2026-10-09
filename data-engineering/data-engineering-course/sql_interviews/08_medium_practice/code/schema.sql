-- sql_interviews/08_medium_practice/code/schema.sql
-- Schema and seed data for the M08 (Medium) practice module.
-- Author: Prem Vishnoi <prem.vishnoi@example.com>

-- ============================================================
-- Problem 54: Consecutive Numbers
-- ============================================================

CREATE TABLE Logs (
    id  INTEGER PRIMARY KEY,
    num INTEGER NOT NULL
);

INSERT INTO Logs (id, num) VALUES
    (1, 1),
    (2, 1),
    (3, 1),
    (4, 2),
    (5, 1),
    (6, 2),
    (7, 2);

-- ============================================================
-- Problem 55: Nth Highest Salary
-- ============================================================

CREATE TABLE Employee2 (
    id     INTEGER PRIMARY KEY,
    salary INTEGER NOT NULL
);

INSERT INTO Employee2 (id, salary) VALUES
    (1, 100),
    (2, 200),
    (3, 300);

-- ============================================================
-- Problem 56: Department Top 3 Salaries
-- ============================================================

CREATE TABLE Department2 (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Employee3 (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    salary        INTEGER NOT NULL,
    departmentId  INTEGER REFERENCES Department2(id)
);

INSERT INTO Department2 (id, name) VALUES
    (1, 'Engineering'),
    (2, 'Sales');

INSERT INTO Employee3 (id, name, salary, departmentId) VALUES
    (1, 'Alice',   90000, 1),
    (2, 'Bob',     85000, 1),
    (3, 'Carol',   70000, 1),
    (4, 'Dan',     60000, 1),
    (5, 'Eve',    100000, 2),
    (6, 'Frank',   95000, 2),
    (7, 'Grace',   80000, 2);

-- ============================================================
-- Problem 57: Friend Requests II
-- ============================================================

CREATE TABLE FriendRequest (
    sender_id  INTEGER NOT NULL,
    send_to_id INTEGER NOT NULL,
    date       TEXT
);

INSERT INTO FriendRequest (sender_id, send_to_id, date) VALUES
    (1, 2, '2024-01-01'),
    (1, 3, '2024-01-02'),
    (1, 4, '2024-01-03'),
    (2, 3, '2024-01-04'),
    (3, 4, '2024-01-05');

CREATE TABLE RequestAccepted (
    requester_id INTEGER NOT NULL,
    accepter_id  INTEGER NOT NULL,
    date         TEXT
);

INSERT INTO RequestAccepted (requester_id, accepter_id, date) VALUES
    (1, 2, '2024-01-10'),
    (1, 3, '2024-01-11'),
    (2, 3, '2024-01-12'),
    (3, 4, '2024-01-13'),
    (4, 1, '2024-01-14');

-- ============================================================
-- Problem 58-61: Game Play Analysis
-- ============================================================

CREATE TABLE Activity (
    player_id    INTEGER NOT NULL,
    device_id    INTEGER NOT NULL,
    event_date   TEXT NOT NULL,
    games_played INTEGER NOT NULL
);

INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES
    (1, 2, '2024-01-01', 5),
    (1, 2, '2024-01-02', 6),
    (1, 3, '2024-01-03', 7),
    (2, 1, '2024-01-01', 4),
    (2, 1, '2024-01-05', 3),
    (3, 2, '2024-01-02', 8),
    (3, 2, '2024-01-04', 9);

-- ============================================================
-- Problem 62: Sales Analysis III
-- ============================================================

CREATE TABLE Product (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT,
    unit_price   INTEGER
);

CREATE TABLE Sales (
    seller_id  INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    buyer_id   INTEGER NOT NULL,
    sale_date  TEXT NOT NULL,
    quantity   INTEGER NOT NULL,
    price      INTEGER NOT NULL
);

INSERT INTO Product (product_id, product_name, unit_price) VALUES
    (1, 'Widget A', 100),
    (2, 'Widget B', 200),
    (3, 'Widget C', 300);

INSERT INTO Sales (seller_id, product_id, buyer_id, sale_date, quantity, price) VALUES
    (1, 1, 1, '2024-01-15', 2, 200),
    (1, 2, 2, '2024-03-10', 1, 200),
    (2, 2, 3, '2024-04-05', 3, 600),
    (3, 3, 4, '2024-02-20', 1, 300);

-- ============================================================
-- Problem 63: Tree Node
-- ============================================================

CREATE TABLE Tree (
    id   INTEGER PRIMARY KEY,
    p_id INTEGER
);

INSERT INTO Tree (id, p_id) VALUES
    (1, NULL),
    (2, 1),
    (3, 1),
    (4, 2),
    (5, 2);

-- ============================================================
-- Problem 64: Median Employee Salary
-- ============================================================

CREATE TABLE Employee4 (
    id            INTEGER PRIMARY KEY,
    company       TEXT NOT NULL,
    salary        INTEGER NOT NULL
);

INSERT INTO Employee4 (id, company, salary) VALUES
    (1, 'A', 2341),
    (2, 'A', 1534),
    (3, 'A', 2241),
    (4, 'A', 3701),
    (5, 'A', 4021),
    (6, 'B', 8213),
    (7, 'B', 9432),
    (8, 'B', 5423),
    (9, 'B', 6321),
    (10, 'C', 1023),
    (11, 'C', 5500),
    (12, 'C', 3000);

-- ============================================================
-- Problem 65: Swap Salary
-- ============================================================

CREATE TABLE Salary (
    id  INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    sex  TEXT NOT NULL,
    salary INTEGER NOT NULL
);

INSERT INTO Salary (id, name, sex, salary) VALUES
    (1, 'Alice', 'm', 50000),
    (2, 'Bob',   'f', 60000),
    (3, 'Carol', 'm', 55000),
    (4, 'Dan',   'f', 70000);

-- ============================================================
-- Problem 66: Trips and Users
-- ============================================================

CREATE TABLE Trips (
    id         INTEGER PRIMARY KEY,
    client_id  INTEGER,
    driver_id  INTEGER,
    city_id    INTEGER,
    status     TEXT,
    request_at TEXT
);

CREATE TABLE Users (
    users_id  INTEGER PRIMARY KEY,
    banned    TEXT,
    role      TEXT
);

INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES
    (1, 1, 10, 1, 'completed',  '2024-01-01'),
    (2, 2, 11, 1, 'cancelled',  '2024-01-01'),
    (3, 3, 12, 1, 'completed',  '2024-01-02'),
    (4, 4, 13, 1, 'cancelled',  '2024-01-02'),
    (5, 1, 10, 1, 'completed',  '2024-01-03');

INSERT INTO Users (users_id, banned, role) VALUES
    (1,  'No', 'client'),
    (2,  'No', 'client'),
    (3,  'No', 'client'),
    (4,  'Yes', 'client'),
    (10, 'No', 'driver'),
    (11, 'No', 'driver'),
    (12, 'Yes', 'driver'),
    (13, 'No', 'driver');

-- ============================================================
-- Problem 67: Human Traffic of Stadium
-- ============================================================

CREATE TABLE Stadium (
    id         INTEGER PRIMARY KEY,
    visit_date TEXT NOT NULL,
    people     INTEGER NOT NULL
);

INSERT INTO Stadium (id, visit_date, people) VALUES
    (1, '2024-01-01', 10),
    (2, '2024-01-02', 25),
    (3, '2024-01-03', 105),
    (4, '2024-01-04', 200),
    (5, '2024-01-05', 90),
    (6, '2024-01-06', 300),
    (7, '2024-01-07', 50);

-- ============================================================
-- Problem 68: Department Highest Salary (revisited)
-- ============================================================

CREATE TABLE Department3 (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Employee5 (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    salary        INTEGER NOT NULL,
    departmentId  INTEGER REFERENCES Department3(id)
);

INSERT INTO Department3 (id, name) VALUES
    (1, 'Engineering'),
    (2, 'Sales');

INSERT INTO Employee5 (id, name, salary, departmentId) VALUES
    (1, 'Alice', 90000, 1),
    (2, 'Bob',   80000, 1),
    (3, 'Carol', 95000, 2),
    (4, 'Dan',   85000, 2);

-- ============================================================
-- Problem 69: Exchange Seats
-- ============================================================

CREATE TABLE Seat (
    id      INTEGER PRIMARY KEY,
    student TEXT NOT NULL
);

INSERT INTO Seat (id, student) VALUES
    (1, 'Alice'),
    (2, 'Bob'),
    (3, 'Carol'),
    (4, 'Dan'),
    (5, 'Eve');

-- ============================================================
-- Problem 70: Customers Who Bought All Products
-- ============================================================

CREATE TABLE Customer2 (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Product2 (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Orders2 (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id  INTEGER NOT NULL
);

INSERT INTO Customer2 (id, name) VALUES
    (1, 'Alice'),
    (2, 'Bob'),
    (3, 'Carol');

INSERT INTO Product2 (id, name) VALUES
    (1, 'Widget'),
    (2, 'Gadget'),
    (3, 'Doohickey');

INSERT INTO Orders2 (id, customer_id, product_id) VALUES
    (1, 1, 1),
    (2, 1, 2),
    (3, 1, 3),
    (4, 2, 1),
    (5, 2, 2),
    (6, 3, 1);

-- ============================================================
-- Problem 71-73: Product Sales Analysis
-- ============================================================

CREATE TABLE ProductSales2 (
    product_id   INTEGER NOT NULL,
    sale_date    TEXT NOT NULL,
    units_sold   INTEGER NOT NULL
);

INSERT INTO ProductSales2 (product_id, sale_date, units_sold) VALUES
    (1, '2024-01-15', 100),
    (1, '2024-02-20', 200),
    (1, '2024-03-10', 150),
    (2, '2024-01-22', 300),
    (2, '2024-02-05', 250);

-- ============================================================
-- Problem 74: Daily Leads and Partners
-- ============================================================

CREATE TABLE DailySales (
    date_id   TEXT NOT NULL,
    make_name TEXT NOT NULL,
    lead_id   INTEGER NOT NULL,
    partner_id INTEGER NOT NULL
);

INSERT INTO DailySales (date_id, make_name, lead_id, partner_id) VALUES
    ('2024-01-01', 'Toyota', 1, 1),
    ('2024-01-01', 'Toyota', 2, 2),
    ('2024-01-01', 'Toyota', 3, 3),
    ('2024-01-02', 'Toyota', 1, 1),
    ('2024-01-02', 'Toyota', 4, 4),
    ('2024-01-01', 'Honda',  1, 1),
    ('2024-01-02', 'Honda',  2, 2),
    ('2024-01-02', 'Honda',  3, 3);

-- ============================================================
-- Problem 75: Number of Comments per Post
-- ============================================================

CREATE TABLE Posts2 (
    id      INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL
);

CREATE TABLE Comments (
    id      INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT
);

INSERT INTO Posts2 (id, user_id) VALUES
    (1, 100),
    (2, 101),
    (3, 102);

INSERT INTO Comments (id, post_id, user_id, content) VALUES
    (1, 1, 200, 'Great post'),
    (2, 1, 201, 'Thanks for sharing'),
    (3, 2, 202, 'I agree');

-- ============================================================
-- Problem 76: Page Recommendations
-- ============================================================

CREATE TABLE Friendship (
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL
);

CREATE TABLE Likes (
    user_id  INTEGER NOT NULL,
    page_id  INTEGER NOT NULL
);

INSERT INTO Friendship (user1_id, user2_id) VALUES
    (1, 2),
    (1, 3),
    (1, 4),
    (2, 3);

INSERT INTO Likes (user_id, page_id) VALUES
    (2, 100),
    (3, 100),
    (3, 200),
    (4, 200);

-- ============================================================
-- Problem 77: Capital Gain/Loss
-- ============================================================

CREATE TABLE Stocks (
    stock_name    TEXT NOT NULL,
    operation     TEXT NOT NULL,
    operation_day INTEGER NOT NULL,
    price         INTEGER NOT NULL
);

INSERT INTO Stocks (stock_name, operation, operation_day, price) VALUES
    ('AAPL', 'Buy',  1, 100),
    ('AAPL', 'Sell', 5, 200),
    ('AAPL', 'Buy',  10, 50),
    ('AAPL', 'Sell', 15, 150),
    ('GOOG', 'Buy',  2, 500),
    ('GOOG', 'Sell', 8, 600);

-- ============================================================
-- Problem 78: Winners of Each Group
-- ============================================================

CREATE TABLE Contest (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Users2 (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE Score (
    contest_id INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    score      INTEGER NOT NULL
);

INSERT INTO Contest (id, name) VALUES
    (1, 'Contest A'),
    (2, 'Contest B'),
    (3, 'Contest C');

INSERT INTO Users2 (id, name) VALUES
    (1, 'Alice'),
    (2, 'Bob'),
    (3, 'Carol');

INSERT INTO Score (contest_id, user_id, score) VALUES
    (1, 1, 100),
    (1, 2, 90),
    (1, 3, 95),
    (2, 1, 80),
    (2, 2, 95),
    (2, 3, 70),
    (3, 1, 85),
    (3, 2, 70),
    (3, 3, 100);

-- ============================================================
-- Problem 79: Confirmation Rate
-- ============================================================

CREATE TABLE Signups (
    user_id     INTEGER PRIMARY KEY,
    time_stamp  TEXT NOT NULL
);

CREATE TABLE Confirmations (
    user_id     INTEGER NOT NULL,
    time_stamp  TEXT NOT NULL,
    action      TEXT NOT NULL
);

INSERT INTO Signups (user_id, time_stamp) VALUES
    (1, '2024-01-01'),
    (2, '2024-01-02'),
    (3, '2024-01-03');

INSERT INTO Confirmations (user_id, time_stamp, action) VALUES
    (1, '2024-01-01 10:00', 'confirmed'),
    (1, '2024-01-01 11:00', 'confirmed'),
    (1, '2024-01-01 12:00', 'timeout'),
    (2, '2024-01-02 10:00', 'confirmed'),
    (3, '2024-01-03 10:00', 'timeout');

-- ============================================================
-- Problem 80: Students and Examinations
-- ============================================================

CREATE TABLE Students (
    student_id   INTEGER PRIMARY KEY,
    student_name TEXT NOT NULL
);

CREATE TABLE Subjects (
    subject_name TEXT PRIMARY KEY
);

CREATE TABLE Examinations (
    student_id    INTEGER NOT NULL,
    subject_name  TEXT NOT NULL
);

INSERT INTO Students (student_id, student_name) VALUES
    (1, 'Alice'),
    (2, 'Bob'),
    (3, 'Carol');

INSERT INTO Subjects (subject_name) VALUES
    ('Math'),
    ('Physics'),
    ('Chemistry');

INSERT INTO Examinations (student_id, subject_name) VALUES
    (1, 'Math'),
    (1, 'Physics'),
    (2, 'Math');

-- ============================================================
-- Problem 81: User Activity Past 30 Days
-- ============================================================

CREATE TABLE Activity2 (
    user_id     INTEGER NOT NULL,
    session_id  INTEGER NOT NULL,
    activity_date TEXT NOT NULL,
    activity_type TEXT NOT NULL
);

INSERT INTO Activity2 (user_id, session_id, activity_date, activity_type) VALUES
    (1, 10, '2024-01-01', 'open'),
    (1, 10, '2024-01-01', 'scroll'),
    (1, 10, '2024-01-01', 'click'),
    (1, 11, '2024-01-05', 'open'),
    (2, 12, '2024-01-15', 'open'),
    (2, 12, '2024-01-15', 'click'),
    (3, 13, '2024-01-20', 'open');

-- ============================================================
-- Problem 82: Immediate Food Delivery
-- ============================================================

CREATE TABLE Delivery (
    delivery_id                    INTEGER PRIMARY KEY,
    customer_id                    INTEGER NOT NULL,
    order_date                     TEXT NOT NULL,
    customer_pref_delivery_date    TEXT NOT NULL
);

INSERT INTO Delivery (delivery_id, customer_id, order_date, customer_pref_delivery_date) VALUES
    (1, 1, '2024-01-01', '2024-01-02'),
    (2, 1, '2024-01-05', '2024-01-05'),
    (3, 2, '2024-01-10', '2024-01-10'),
    (4, 2, '2024-01-15', '2024-01-16'),
    (5, 3, '2024-01-20', '2024-01-20');

-- ============================================================
-- Problem 83: Sales Analysis I
-- ============================================================

CREATE TABLE Sales2 (
    sale_id     INTEGER PRIMARY KEY,
    product_id  INTEGER NOT NULL,
    year        INTEGER NOT NULL,
    quantity    INTEGER NOT NULL,
    price       INTEGER NOT NULL
);

INSERT INTO Sales2 (sale_id, product_id, year, quantity, price) VALUES
    (1, 1, 2022, 10, 100),
    (2, 1, 2023, 12, 110),
    (3, 2, 2022, 5,  50),
    (4, 2, 2024, 8,  80);

-- ============================================================
-- Problem 84: Daily Active Users
-- ============================================================

CREATE TABLE DAU_Logins (
    user_id    INTEGER NOT NULL,
    login_date TEXT NOT NULL
);

INSERT INTO DAU_Logins (user_id, login_date) VALUES
    (1, '2024-01-01'),
    (2, '2024-01-01'),
    (1, '2024-01-02'),
    (3, '2024-01-02'),
    (1, '2024-01-03'),
    (2, '2024-01-03'),
    (3, '2024-01-03');
