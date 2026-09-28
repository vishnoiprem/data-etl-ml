# Snowflake (Hands-On) — Full-Detail Course Content

**Source attribution:** Course content from Data Vidhya (https://datavidhya.com/)
by **Darshil Parmar (Founder & Lead Instructor, Data Vidhya)**.
Course URL: https://datavidhya.com/learn/snowflake/

**Coverage:** 5 modules • 39 lessons
**Last updated on Data Vidhya:** Jul 8, 2026
**Reproduced in `data-enginnering-cloudvala/course-curricula/`** as a
study-path reference. Full-detail versions of the deep-dive articles
are included where the full body was extractable from the public page.

> **Note on coverage:** This file contains the complete 39-lesson
> curriculum plus the full article bodies for the lessons that were
> extractable from the public pages (Stages & Data Loading, Performance
> Optimization, Types of Tables, Streams & Tasks). The remaining
> articles are JS-rendered and require a logged-in browser session to
> extract.

---

## Module 1: Getting Started — 7 lessons

1. Snowflake DB Overview — *Article*
2. Snowflake Account Creation — *Article*
3. Snowflake UI Basics — *Article*
4. Snowflake Hands-On SQL — *Article*
5. Snowflake Architecture (Video) — *Video*
6. Snowflake Architecture — *Article*  *(JS-rendered, full body not extractable)*
7. Module Quiz — *Article*

## Module 2: Data Loading & Formats — 11 lessons

1. Stages & Data Loading (Video) — *Video*
2. **Stages & Data Loading — *Article*  *(full body included below)***
3. File Formats (Video) — *Video*
4. File Formats — *Article*
5. Handling JSON Data (Video) — *Video*
6. Handling JSON Data — *Article*
7. Snowpipe (Video) — *Video*
8. Snowpipe — *Article*
9. Storage Integration (Video) — *Video*
10. Storage Integration — *Article*
11. Module Quiz — *Article*

## Module 3: Performance & Optimization — 5 lessons

1. Performance Optimization (Video) — *Video*
2. **Performance Optimization — *Article*  *(full body included below)***
3. Caching & Clustering (Video) — *Video*
4. Caching & Clustering — *Article*
5. Module Quiz — *Article*

## Module 4: Tables, Time Travel & Sharing — 14 lessons

1. Types of Tables (Video) — *Video*
2. Types of Tables — *Article*
3. Time Travel (Video) — *Video*
4. Time Travel — *Article*
5. Restore & Undrop (Video 1) — *Video*
6. Restore & Undrop (Video 2) — *Video*
7. Restore & Undrop — *Article*
8. Cloning & Data Sharing (Video 1) — *Video*
9. Cloning & Data Sharing (Video 2) — *Video*
10. Cloning & Data Sharing — *Article*
11. Views & Dynamic Masking (Video 1) — *Video*
12. Views & Dynamic Masking (Video 2) — *Video*
13. Views & Dynamic Masking — *Article*
14. Module Quiz — *Article*

## Module 5: Streams & Tasks — 2 lessons

1. Streams & Tasks — *Article*
2. Module Quiz — *Article*

---

# Full Article Bodies

## Module 2 · Lesson 2: Stages & Data Loading

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Jul 8, 2026.
Course URL: https://datavidhya.com/learn/snowflake/data-loading-and-formats/stages-and-data-loading/*

One of the key features of Snowflake is the ability to load data from
external sources into tables using **stages** and the `COPY` command.
This is how data gets into your warehouse, whether from S3, Azure Blob
Storage, or Google Cloud Storage.

### What are Stages in Snowflake?

Stages are named locations that provide a way to access files from
Snowflake. They act as a bridge between your external storage (like an
S3 bucket) and your Snowflake tables.

There are two types:

- **Internal stages**: Created and managed within Snowflake. Files are
  uploaded directly to Snowflake's internal storage.
- **External stages**: Point to locations outside Snowflake (S3, GCS,
  Azure Blob). Snowflake reads files from these locations without
  moving them.

### Setting Up the Environment

First, create a database and schema to manage your stage objects and
file formats:

```sql
CREATE OR REPLACE DATABASE MANAGE_DB;

CREATE OR REPLACE SCHEMA external_stages;
```

### Creating Stages

#### Internal Stage

```sql
CREATE STAGE my_internal_stage;
```

#### External Stage (S3)

Create an external stage pointing to your S3 bucket:

```sql
CREATE OR REPLACE STAGE MANAGE_DB.external_stages.aws_stage
    url='s3://dw-snowflake-course-darshil'
    credentials=(aws_key_id='' aws_secret_key='');
```

You can also use publicly accessible buckets (no credentials needed):

```sql
CREATE OR REPLACE STAGE MANAGE_DB.external_stages.aws_stage
    url='s3://bucketsnowflakes3';
```

#### Useful Stage Commands

```sql
-- Describe the stage to see its properties
DESC STAGE MANAGE_DB.external_stages.aws_stage;

-- List files in the stage
LIST @aws_stage;

-- Update stage credentials
ALTER STAGE aws_stage
    SET credentials=(aws_key_id='XYZ_DUMMY_ID' aws_secret_key='987xyz');
```

### Loading Data with COPY

#### Basic COPY Command

First, create the target table:

```sql
CREATE OR REPLACE TABLE MANAGE_DB.PUBLIC.ORDERS (
    ORDER_ID VARCHAR(30),
    AMOUNT INT,
    PROFIT INT,
    QUANTITY INT,
    CATEGORY VARCHAR(30),
    SUBCATEGORY VARCHAR(30)
);
```

Then load data from the stage using `COPY INTO`:

```sql
COPY INTO MANAGE_DB.PUBLIC.ORDERS
FROM @aws_stage
file_format = (type = csv field_delimiter = ',' skip_header=1)
files=('OrderDetails.csv');
```

```sql
SELECT * FROM MANAGE_DB.PUBLIC.ORDERS;
```

The `file_format` parameter tells Snowflake how to parse the file, CSV
format, comma-delimited, skip the header row. The `files` parameter
specifies which file(s) to load.

### Transformations During Loading

One of Snowflake's powerful features is the ability to **transform
data while loading**. Instead of loading raw data and transforming
later, you can select specific columns and apply logic during the
`COPY` command.

#### Select Specific Columns

Load only the first two columns from the CSV:

```sql
CREATE OR REPLACE TABLE MANAGE_DB.PUBLIC.ORDERS_EX (
    ORDER_ID VARCHAR(30),
    AMOUNT INT
);

COPY INTO MANAGE_DB.PUBLIC.ORDERS_EX
FROM (SELECT s.$1, s.$2 FROM @MANAGE_DB.external_stages.aws_stage s)
file_format = (type = csv field_delimiter = ',' skip_header=1)
files=('OrderDetails.csv');

SELECT * FROM MANAGE_DB.PUBLIC.ORDERS_EX;
```

The `s.$1`, `s.$2` syntax references columns by position in the CSV
file. `$1` is the first column, `$2` is the second, and so on.

#### Apply CASE Logic During Loading

You can even apply transformations like CASE statements while loading:

```sql
CREATE OR REPLACE TABLE MANAGE_DB.PUBLIC.ORDERS_EX1 (
    ORDER_ID VARCHAR(30),
    AMOUNT INT,
    PROFIT INT,
    PROFITABILITY VARCHAR(255)
);

COPY INTO MANAGE_DB.PUBLIC.ORDERS_EX1
FROM (SELECT
        s.$1,
        s.$2,
        s.$3,
        CASE WHEN CAST(s.$3 as int) < 0 THEN 'not profitable' ELSE 'profitable' END
      FROM @MANAGE_DB.external_stages.aws_stage s)
file_format = (type = csv field_delimiter=',' skip_header=1)
files=('OrderDetails.csv');

SELECT * FROM MANAGE_DB.PUBLIC.ORDERS_EX1;
```

This loads order data and adds a computed `PROFITABILITY` column based
on whether the profit value is negative or positive, all in a single
COPY command.

> **Transform During Load vs After Load** — Transforming during COPY is
> useful for simple operations like column selection, type casting, and
> CASE logic. For complex transformations (joins, aggregations, window
> functions), load the raw data first and transform using SQL views or
> dbt models. The COPY command is optimized for bulk loading, not
> complex query logic.

> **File Formats** — Instead of specifying file format inline, you can
> create a reusable file format object:
>
> ```sql
> CREATE OR REPLACE FILE FORMAT csv_file_format
> TYPE = 'CSV'
> FIELD_DELIMITER = ','
> SKIP_HEADER = 1
> FIELD_OPTIONALLY_ENCLOSED_BY = '"';
>
> -- Then reference it in COPY
> COPY INTO my_table
> FROM @my_stage/file.csv
> FILE_FORMAT = (FORMAT_NAME = 'csv_file_format');
> ```
>
> This keeps your COPY commands cleaner and ensures consistent parsing
> across multiple loads.

---

## Module 3 · Lesson 2: Performance Optimization

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Jul 8, 2026.
Course URL: https://datavidhya.com/learn/snowflake/performance-and-optimization/performance-optimization/*

Performance optimization in Snowflake boils down to two goals: "make
queries run faster" and "save costs". In traditional databases, you
would add indexes, create table partitions, analyze query execution
plans, and remove unnecessary full table scans. In Snowflake, most of
this is handled automatically through "micro-partitions", but there
are still important decisions you need to make.

### What is Our Job?

Snowflake automates a lot, but you are still responsible for:

- "Assigning appropriate data types": Smaller types use less storage
  and scan faster
- "Sizing virtual warehouses": Right-sizing compute for different
  workloads
- "Cluster keys": Helping Snowflake organize data for frequently
  filtered columns

### Performance Aspects

There are five key areas for performance optimization in Snowflake:

| Aspect | When to Use |
|--------|-------------|
| **Dedicated virtual warehouses** | Separate workloads (ETL, BI, data science) |
| **Scaling Up** | Known patterns of high workload, complex queries |
| **Scaling Out** | Unknown/fluctuating patterns, many concurrent users |
| **Maximize Cache Usage** | Automatic: ensure similar queries hit the same warehouse |
| **Cluster Keys** | For very large tables with specific filter patterns |

### Dedicated Virtual Warehouses

Different teams have different workload patterns. ETL jobs run heavy
transformations, BI dashboards run many small queries, data scientists
run complex ad-hoc queries. Mixing these on one warehouse causes
contention.

The solution: "identify and classify groups of workloads/users", then
create dedicated virtual warehouses for each.

#### Create Warehouses for Different Teams

```sql
-- Data Scientists: need more compute for complex queries
CREATE WAREHOUSE DS_WH
WITH WAREHOUSE_SIZE = 'SMALL'
WAREHOUSE_TYPE = 'STANDARD'
AUTO_SUSPEND = 300
AUTO_RESUME = TRUE
MIN_CLUSTER_COUNT = 1
MAX_CLUSTER_COUNT = 1
SCALING_POLICY = 'STANDARD';

-- DBAs: lighter workload, smaller warehouse
CREATE WAREHOUSE DBA_WH
WITH WAREHOUSE_SIZE = 'XSMALL'
WAREHOUSE_TYPE = 'STANDARD'
AUTO_SUSPEND = 300
AUTO_RESUME = TRUE
MIN_CLUSTER_COUNT = 1
MAX_CLUSTER_COUNT = 1
SCALING_POLICY = 'STANDARD';
```

#### Create Roles and Assign Users

```sql
-- Create roles
CREATE ROLE DATA_SCIENTIST;
GRANT USAGE ON WAREHOUSE DS_WH TO ROLE DATA_SCIENTIST;

CREATE ROLE DBA;
GRANT USAGE ON WAREHOUSE DBA_WH TO ROLE DBA;

-- Create Data Scientist users
CREATE USER DS1 PASSWORD = 'DS1' LOGIN_NAME = 'DS1'
    DEFAULT_ROLE = 'DATA_SCIENTIST' DEFAULT_WAREHOUSE = 'DS_WH'
    MUST_CHANGE_PASSWORD = FALSE;
CREATE USER DS2 PASSWORD = 'DS2' LOGIN_NAME = 'DS2'
    DEFAULT_ROLE = 'DATA_SCIENTIST' DEFAULT_WAREHOUSE = 'DS_WH'
    MUST_CHANGE_PASSWORD = FALSE;
CREATE USER DS3 PASSWORD = 'DS3' LOGIN_NAME = 'DS3'
    DEFAULT_ROLE = 'DATA_SCIENTIST' DEFAULT_WAREHOUSE = 'DS_WH'
    MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE DATA_SCIENTIST TO USER DS1;
GRANT ROLE DATA_SCIENTIST TO USER DS2;
GRANT ROLE DATA_SCIENTIST TO USER DS3;

-- Create DBA users
CREATE USER DBA1 PASSWORD = 'DBA1' LOGIN_NAME = 'DBA1'
    DEFAULT_ROLE = 'DBA' DEFAULT_WAREHOUSE = 'DBA_WH'
    MUST_CHANGE_PASSWORD = FALSE;
CREATE USER DBA2 PASSWORD = 'DBA2' LOGIN_NAME = 'DBA2'
    DEFAULT_ROLE = 'DBA' DEFAULT_WAREHOUSE = 'DBA_WH'
    MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE DBA TO USER DBA1;
GRANT ROLE DBA TO USER DBA2;
```

#### Considerations

- "Don't create too many warehouses": Avoid underutilization. If a
  warehouse sits idle most of the day, consolidate it.
- "Refine classifications over time": Work patterns change. Revisit
  your warehouse assignments periodically.
- "Enterprise Edition and above": All warehouses should be Multi-Cluster.
  Minimum cluster count defaults to 1, maximum can be set high.

### Scaling Up / Down

Scaling up means "changing the size of the virtual warehouse", from
XSMALL to SMALL, MEDIUM, LARGE, etc. More compute power for more
complex queries.

**Use cases:**

- ETL jobs that run at certain times (e.g., between 6pm and 8pm):
  scale up during the window, scale back down after
- Special business events with higher workload (Black Friday,
  quarter-end reporting)

A common scenario is increased query complexity, the queries
themselves are heavier. That is a scaling **up** problem. But if you
have **more users** running the same queries concurrently, scaling
**out** (multi-cluster) is the better solution.

### Scaling Out (Multi-Cluster)

| Scaling Up | Scaling Out |
|------------|-------------|
| Increasing the size of virtual warehouses | Using additional warehouses / Multi-Cluster |
| More complex queries | More concurrent users/queries |

Scaling out handles performance related to "large numbers of concurrent
users". Multi-cluster warehouses automatically spin up additional
clusters when demand increases and shut them down when it drops.

- Handles fluctuating number of users automatically
- Requires Enterprise Edition or higher

### The Right Strategy for Each Problem

Performance optimization is not one-size-fits-all. Match the solution
to the problem:

- "Queries too slow?" → Scale up (bigger warehouse) or add cluster keys
- "Too many concurrent users?" → Scale out (multi-cluster)
- "Different teams competing for resources?" → Dedicated virtual
  warehouses
- "Same queries running repeatedly?" → Leverage caching by routing to
  the same warehouse

### Cleanup

```sql
DROP USER DBA1;
DROP USER DBA2;
DROP USER DS1;
DROP USER DS2;
DROP USER DS3;

DROP ROLE DATA_SCIENTIST;
DROP ROLE DBA;

DROP WAREHOUSE DS_WH;
DROP WAREHOUSE DBA_WH;
```

---

## Module 4 · Lesson 2: Types of Tables — Permanent, Transient, Temporary

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Mar 23, 2026.
Course URL: https://datavidhya.com/learn/snowflake/tables-time-travel-sharing/types-of-tables/*

Snowflake has three types of tables, each with different persistence,
Time Travel, and Fail-safe behavior. Choosing the right type affects both
cost and data protection.

### Comparison

| Feature | Permanent | Transient | Temporary |
|---|---|---|---|
| **Persistence** | Until explicitly dropped | Until explicitly dropped | Deleted when session ends |
| **Time Travel** | Up to 90 days (Enterprise) | 0 or 1 day only | 0 or 1 day only |
| **Fail-safe** | 7 days | No | No |
| **Visible to other sessions** | Yes | Yes | No |
| **Storage cost** | Highest | Medium | Lowest |

### Permanent Tables

Permanent tables are the default. They persist until explicitly dropped
and have full Time Travel (up to 90 days) and Fail-safe (7 days of
recovery by Snowflake support).

```sql
CREATE OR REPLACE DATABASE PDB;

CREATE OR REPLACE TABLE PDB.public.customers (
    id INT,
    first_name STRING,
    last_name STRING,
    email STRING,
    gender STRING,
    Job STRING,
    Phone STRING
);
```

Load data and verify:

```sql
CREATE OR REPLACE FILE FORMAT MANAGE_DB.file_formats.csv_file
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1;

CREATE OR REPLACE STAGE MANAGE_DB.external_stages.time_travel_stage
    URL = 's3://data-snowflake-fundamentals/time-travel/'
    file_format = MANAGE_DB.file_formats.csv_file;

COPY INTO PDB.public.customers
FROM @MANAGE_DB.external_stages.time_travel_stage
files = ('customers.csv');

SELECT * FROM PDB.public.customers;

-- SHOW TABLES confirms it's a permanent table
SHOW TABLES;
```

**Use when:** Data is frequently accessed, modified, and queried. You
need full Time Travel and Fail-safe protection.

### Transient Tables

Transient tables persist until dropped (like permanent tables) but have
**no Fail-safe** and **limited Time Travel** (0 or 1 day max). This saves
storage costs for data that doesn't need long-term protection.

```sql
CREATE OR REPLACE DATABASE TDB;

CREATE OR REPLACE TRANSIENT TABLE TDB.public.customers_transient (
    id INT,
    first_name STRING,
    last_name STRING,
    email STRING,
    gender STRING,
    Job STRING,
    Phone STRING
);

INSERT INTO TDB.public.customers_transient
SELECT t1.* FROM OUR_FIRST_DB.public.customers t1
CROSS JOIN (SELECT * FROM OUR_FIRST_DB.public.customers) t2;

SHOW TABLES;
```

#### Time Travel on Transient Tables

You can set retention to 0 or 1 day only:

```sql
ALTER TABLE TDB.public.customers_transient
SET DATA_RETENTION_TIME_IN_DAYS = 0;
```

With retention set to 0, UNDROP will not work:

```sql
DROP TABLE TDB.public.customers_transient;

-- This will FAIL: no Time Travel history
UNDROP TABLE TDB.public.customers_transient;
```

#### Transient Schemas

You can also create transient schemas; any table created inside a
transient schema is automatically transient:

```sql
CREATE OR REPLACE TRANSIENT SCHEMA TDB.TRANSIENT_SCHEMA;

SHOW SCHEMAS;

-- This table is automatically transient (inherits from schema)
CREATE OR REPLACE TABLE TDB.TRANSIENT_SCHEMA.new_table (
    id INT,
    first_name STRING,
    last_name STRING,
    email STRING,
    gender STRING,
    Job STRING,
    Phone STRING
);

-- Can set up to 1 day retention (not more)
ALTER TABLE TDB.TRANSIENT_SCHEMA.new_table
SET DATA_RETENTION_TIME_IN_DAYS = 2;
-- This will fail: transient tables can only have 0 or 1 day retention

SHOW TABLES;
```

**Use when:** Staging tables, intermediate ETL results, large datasets
that can be easily recreated from source.

### Temporary Tables

Temporary tables exist only for the **duration of the session**. They
are not visible to other sessions or users. When you disconnect, the
table is automatically deleted.

```sql
-- Create a permanent table first
CREATE OR REPLACE TABLE PDB.public.customers (
    id INT,
    first_name STRING,
    last_name STRING,
    email STRING,
    gender STRING,
    Job STRING,
    Phone STRING
);

INSERT INTO PDB.public.customers
SELECT t1.* FROM OUR_FIRST_DB.public.customers t1;

-- Create a temporary table
CREATE OR REPLACE TEMPORARY TABLE PDB.public.temp_table (
    id INT,
    first_name STRING,
    last_name STRING,
    email STRING,
    gender STRING,
    Job STRING,
    Phone STRING
);

INSERT INTO PDB.public.temp_table
SELECT * FROM PDB.public.customers;

SELECT * FROM PDB.public.temp_table;

SHOW TABLES;
```

**Use when:** Intermediate results for complex queries, working datasets
within a session, ad-hoc analysis that doesn't need to persist.

---

### Choosing the Right Table Type

- **Permanent**: Default choice. Use for anything important: fact tables,
  dimension tables, reference data.
- **Transient**: Use for staging/landing tables, ETL intermediates. Saves
  ~30-50% on storage vs permanent tables.
- **Temporary**: Use for session-scoped work: ad-hoc analysis, intermediate
  query results, scratch tables.

### Transient Databases

You can also create transient databases with `CREATE TRANSIENT DATABASE`.
Every schema and table created inside will inherit the transient property.

---

## Module 5 · Lesson 1: Streams & Tasks — Native CDC and Scheduling

*Written by Darshil Parmar, Founder & Lead Instructor, Data Vidhya.
Published Mar 23, 2026.
Course URL: https://datavidhya.com/learn/snowflake/automation/streams-and-tasks/*

Most warehouses need outside help for two jobs: noticing what changed
(Debezium, Kafka) and running things on a schedule (Airflow, cron).
Snowflake ships both as SQL objects. **Streams** are change data capture
built into the table; **Tasks** are a scheduler built into the warehouse.

### Streams: a change log you can SELECT

Creating one takes a single statement:

```sql
CREATE OR REPLACE STREAM customer_changes ON TABLE customer;
```

From that moment, every insert, update, and delete on `customer` is
visible in the stream:

```sql
INSERT INTO customer VALUES (101, 'Anna', 'Engineer');
UPDATE customer SET job = 'Manager' WHERE id = 42;
DELETE FROM customer WHERE id = 7;

SELECT * FROM customer_changes;
```

The result contains the changed rows plus metadata columns that say what
happened to each. One logical UPDATE arrives as **two rows**, the DELETE
of the old image and the INSERT of the new one, both flagged
`METADATA$ISUPDATE = TRUE`.

#### The rule that surprises everyone

A stream is not a growing log you clean up. It is an **offset** that
advances when consumed:

- A plain `SELECT * FROM customer_changes` **peeks**: the stream still
  holds everything.
- Using the stream inside a DML statement (`MERGE ... USING customer_changes`,
  `INSERT ... SELECT FROM customer_changes`) **consumes**: the offset
  advances, and the stream shows empty until new changes arrive.

### Tasks: cron that lives in the warehouse

A stream captures changes; something still has to process them regularly:

```sql
CREATE OR REPLACE TASK process_customer_changes
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '1 minute'
    WHEN SYSTEM$STREAM_HAS_DATA('customer_changes')
AS
    MERGE INTO customer_current c
    USING customer_changes s ON c.id = s.id
    WHEN MATCHED AND s.METADATA$ACTION = 'DELETE' AND s.METADATA$ISUPDATE = 'FALSE'
        THEN DELETE
    WHEN MATCHED AND s.METADATA$ACTION = 'INSERT'
        THEN UPDATE SET c.name = s.name, c.job = s.job
    WHEN NOT MATCHED AND s.METADATA$ACTION = 'INSERT'
        THEN INSERT (id, name, job) VALUES (s.id, s.name, s.job);

ALTER TASK process_customer_changes RESUME;
```

Key operational details:

- **Tasks are born suspended.** Nothing runs until `ALTER TASK ... RESUME`.
- **`WHEN SYSTEM$STREAM_HAS_DATA(...)`** makes the schedule cheap: the
  task skips without spinning up the warehouse.
- **Tasks chain.** `CREATE TASK child ... AFTER parent` builds small
  DAGs entirely inside Snowflake.

```sql
SELECT name, state, scheduled_time
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
ORDER BY scheduled_time DESC;
```

### The trio, assembled

Snowpipe loads files into staging; a Stream captures changes; a Task
running every minute MERGEs them onward; the history table stays fresh.
Ingestion, CDC, and scheduling without a single external tool.

### Common mistakes

- **SELECTing a stream and wondering why it never empties.** Only DML
  consumes.
- **Forgetting RESUME.** Tasks are created suspended.
- **Skipping `WHEN SYSTEM$STREAM_HAS_DATA`.**
- **Letting a stream go stale.** If a stream is never consumed within
  the table's Time Travel retention, it goes stale.
- **Treating update pairs as two changes.** DELETE + INSERT with
  `ISUPDATE = TRUE` is one logical update.
