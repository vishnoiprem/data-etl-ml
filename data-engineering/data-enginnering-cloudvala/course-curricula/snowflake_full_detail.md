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
> Optimization). The remaining articles are JS-rendered and require a
> logged-in browser session to extract.

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
