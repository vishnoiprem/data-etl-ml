# Delta Sharing: The Protocol That Made Me Delete All Our Export Jobs

*How we went from a mess of exports to one source of truth  and why I am  never going back*


A while ago, we finally got our main Delta table into a really good place.

Clean schema.

Well maintained.

Fast queries.

It's your source of truth for customer data, and you have  spent months perfecting it.

Now, 40 different teams need access to this data.

What do you do?

If you are  like most data teams, you set up export jobs,  One for Partner A (they want CSV). One for Partner B (they need it in their S3 bucket). 
One for the analytics team (hourly refresh), One for the finance vendor (daily SFTP upload)  One for.. you get the idea.



Before you know it, you are  managing:
- 40 separate export jobs
- 40 different cloud storage locations  
- 40 potential points of failure
- 40 copies of data that can drift out of sync

And when something goes wrong and it always does you are the one debugging which export failed, which partner has stale data, and why the numbers do not match.

**This is the distributed synchronization problem ** and it's eating data teams alive.


## The Problem Nobody Wants to Talk About

Here's the dirty secret: exporting data is easy, *Keeping it in sync* is the nightmare.

Every time you export data, you create a copy, That copy immediately starts aging, By the time your partner imports it into their system, you have  already updated the source table three times.

Now multiply that by 40 partners.

```
Your Delta Table (The Truth)
        │
        ├──► Export Job 1 ──► Partner A's S3 ──► Their Database ──► ???
        │
        ├──► Export Job 2 ──► Partner B's S3 ──► Their Database ──► ???
        │
        ├──► Export Job 3 ──► SFTP Server ──► Vendor System ──► ???
        │
        ├──► Export Job 4 ──► Email (yes, really) ──► ???
        │
        └──► ... 36 more ...
        
Each arrow is a potential failure point.
Each destination is a diverging copy.
Each ??? is "who knows what state it's in."
```

The worst part? You have to track state for every single export. Did it succeed? Did it fail halfway through? Did the partner actually receive it? What happens when you need to replace corrupted data?

I spent a year of my career managing this mess. It was exhausting.

Then I found Delta Sharing.



## What Delta Sharing Actually Is

Delta Sharing flips the entire model.

Instead of **pushing** copies to partners, you let them **pull** directly from your table. No exports. No copies. No sync issues.

```
Your Delta Table (The Truth)
        │
        │
   Delta Sharing Server
        │
        ├──── Partner A reads directly
        ├──── Partner B reads directly
        ├──── Vendor reads directly
        └──── Analytics team reads directly

One table. One truth. Everyone in sync.
```

The protocol is:
- **Open** — Not tied to any vendor or cloud
- **Secure** — Token-based authentication with expiration
- **Simple** — REST API that any tool can implement
- **Live** — Partners read the current state, not a stale export

Let me show you how it works.



## The Three Players: Providers, Shares, and Recipients

Delta Sharing has three core concepts. Once you understand these, everything else clicks.

### 1. Data Provider (That's You)

You own the Delta tables. You decide who gets access to what. You run the sharing server.

### 2. Share

A share is a logical grouping that defines what data is accessible. Think of it as a "view" into your data lake.

Here's what a share configuration looks like:

```yaml
version: 1
shares:
  - name: "marketing_analysts_share"
    schemas:
      - name: "consumer"
        tables:
          - name: "clickstream_hourly"
            location: "s3://data-lake/consumer/clickstream_hourly"
            id: "eb6f82f5-a738-4bd8-943c-9cd8594b12ac"
          
          - name: "campaign_performance"
            location: "s3://data-lake/consumer/campaign_performance"
            id: "7a2b3c4d-5e6f-7890-abcd-ef1234567890"
```

This configuration says: *"The `marketing_analysts_share` gives access to two tables — `clickstream_hourly` and `campaign_performance`  both in the `consumer` schema."*

You can create multiple shares with different access levels:

```yaml
shares:
  # Marketing team gets consumer data
  - name: "marketing_share"
    schemas:
      - name: "consumer"
        tables: [clickstream_hourly, campaign_performance]
  
  # Finance team gets transaction data
  - name: "finance_share"
    schemas:
      - name: "transactions"
        tables: [daily_settlements, monthly_reconciliation]
  
  # Executive dashboard gets aggregates only
  - name: "executive_share"
    schemas:
      - name: "summaries"
        tables: [kpi_daily, revenue_weekly]
```

Different shares for different needs. All reading from the same source tables.

### 3. Recipient

A recipient is the identity receiving access. Could be a user, a team, a department, or an external partner.

Each recipient gets a **profile file**  a small JSON document containing everything they need to connect:

```json
{
  "shareCredentialsVersion": 1,
  "endpoint": "https://sharing.yourcompany.com/delta-sharing/",
  "bearerToken": "faaie590d541265bcab1f2de9813274bf233",
  "expirationTime": "2025-08-11T00:00:00.0Z"
}
```

Let me break this down:

| Field | What It Does |
|-------|--------------|
| `shareCredentialsVersion` | Version of the profile format (for compatibility) |
| `endpoint` | URL of your Delta Sharing server |
| `bearerToken` | Their authentication credential (keep this secret!) |
| `expirationTime` | When access expires (always set this!) |

You generate this profile, send it to the recipient securely, and they're ready to query.

>  ** Note:** The `expirationTime` field is optional, but please always set it. Long-lived or perpetual tokens are a security antipattern. Rotate your secrets. Keep them safe.

---

## The Delta Sharing Server

The server is the gatekeeper. It:
1. Authenticates recipients via their bearer token
2. Authorizes access based on share configuration
3. Returns presigned URLs to the actual Parquet files

You can think of it as both a **bouncer** (checking credentials) and a **broker** (connecting recipients to data).

### Running the Server

The Delta Sharing project provides a reference implementation. Getting started is straightforward:

```bash
# Clone the repo
git clone https://github.com/delta-io/delta-sharing.git

# Build and run
cd delta-sharing
sbt server/run --config /path/to/shares.yaml
```

Or use Docker:

```bash
docker run -p 8080:8080 \
  -v /path/to/shares.yaml:/config/shares.yaml \
  deltaio/delta-sharing-server:latest \
  --config /config/shares.yaml
```

Your server is now running at `http://localhost:8080`.

### Scaling with Prefixes

For larger deployments, you can route requests by data domain:

```
https://sharing.yourcompany.com/consumer/...
https://sharing.yourcompany.com/commercial/...
https://sharing.yourcompany.com/analytics/...
```

Each prefix can route to a different sharing instance, letting you scale by domain rather than arbitrarily.

The recipient's profile reflects this:

```json
{
  "shareCredentialsVersion": 1,
  "endpoint": "https://sharing.yourcompany.com/consumer/",
  "bearerToken": "<token>",
  "expirationTime": "2025-08-11T00:00:00.0Z"
}
```

---

## The REST API: How It All Works

Under the hood, Delta Sharing is a REST API. Let me walk you through the key endpoints.

### List Shares

*"What shares do I have access to?"*

```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://sharing.example.com/delta-sharing/shares"
```

Response:
```json
{
  "items": [
    {"name": "marketing_share"},
    {"name": "analytics_share"}
  ]
}
```

### Get Share Details

*"Tell me about this specific share."*

```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://sharing.example.com/delta-sharing/shares/marketing_share"
```

Response:
```json
{
  "share": {
    "name": "marketing_share",
    "id": "optional-unique-id"
  }
}
```

### List Schemas in a Share

*"What schemas are in this share?"*

```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://sharing.example.com/delta-sharing/shares/marketing_share/schemas"
```

Response:
```json
{
  "items": [
    {"name": "consumer", "share": "marketing_share"},
    {"name": "campaigns", "share": "marketing_share"}
  ]
}
```

### List Tables in a Schema

*"What tables are in this schema?"*

```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://sharing.example.com/delta-sharing/shares/marketing_share/schemas/consumer/tables"
```

Response:
```json
{
  "items": [
    {"name": "clickstream_hourly", "schema": "consumer", "share": "marketing_share"},
    {"name": "campaign_performance", "schema": "consumer", "share": "marketing_share"}
  ]
}
```

### List All Tables (Shortcut)

*"Just show me everything I can access."*

```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://sharing.example.com/delta-sharing/shares/marketing_share/all-tables"
```

Response:
```json
{
  "items": [
    {"name": "clickstream_hourly", "schema": "consumer", "share": "marketing_share"},
    {"name": "campaign_performance", "schema": "consumer", "share": "marketing_share"},
    {"name": "ad_spend", "schema": "campaigns", "share": "marketing_share"}
  ]
}
```

This is usually what you want  skip the hierarchy traversal and see everything at once.

### Pagination

For shares with many tables, responses are paginated:

```json
{
  "items": [...],
  "nextPageToken": "CgE0Eg1kZWx0YV9zaGFyaW5nGgdkZWZhdWx0"
}
```

Pass the token back to get the next page:

```bash
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "https://sharing.example.com/.../tables?maxResults=10&pageToken=CgE0Eg1..."
```

---

## Using the Delta Sharing Clients

The REST API is great, but you do not  need to use it directly. Delta Sharing has clients for every major platform.

### Python Client

Install it:
```bash
pip install delta-sharing
```

Use it:
```python
import delta_sharing

# Load the profile
profile_path = "/path/to/my-profile.share"
client = delta_sharing.SharingClient(profile_path)

# Explore what's available
shares = client.list_shares()
print(f"Available shares: {[s.name for s in shares]}")

# Get the first share
first_share = shares[0]
schemas = client.list_schemas(first_share)

# Get tables in the first schema
first_schema = schemas[0]
tables = client.list_tables(first_schema)

for table in tables:
    print(f"  📊 {table.share}.{table.schema}.{table.name}")
```

Output:
```
Available shares: ['marketing_share', 'analytics_share']
  📊 marketing_share.consumer.clickstream_hourly
  📊 marketing_share.consumer.campaign_performance
```

### Reading Data with Pandas

```python
# Build the table URL
table_url = f"{profile_path}#marketing_share.consumer.clickstream_hourly"

# Load as pandas DataFrame
df = delta_sharing.load_as_pandas(table_url)

# Now it's just pandas!
print(df.head())
print(f"Total rows: {len(df)}")
```

### Reading Data with PySpark

For larger datasets, use Spark:

```python
from pyspark.sql import SparkSession

# Create session with Delta Sharing support
spark = SparkSession.builder \
    .appName("DeltaSharingExample") \
    .config("spark.jars.packages", "io.delta:delta-sharing-spark_2.12:3.1.0") \
    .getOrCreate()

# Build the table URL
table_url = "/path/to/profile.share#marketing_share.consumer.clickstream_hourly"

# Read the shared table
df = spark.read \
    .format("deltaSharing") \
    .load(table_url)

# Use it like any DataFrame
df.filter("event_type = 'purchase'") \
  .groupBy("region") \
  .count() \
  .show()
```

### Reading Data with Spark SQL

```sql
-- Register the shared table
CREATE TABLE clickstream 
USING deltaSharing
LOCATION '/path/to/profile.share#marketing_share.consumer.clickstream_hourly';

-- Query it like any table
SELECT 
    DATE(event_time) as event_date,
    event_type,
    COUNT(*) as events
FROM clickstream
WHERE event_time >= '2024-01-01'
GROUP BY DATE(event_time), event_type
ORDER BY event_date DESC;
```

### Scala Client

```scala
import org.apache.spark.sql.functions.col

val profilePath = "/path/to/profile.share"
val tableUrl = s"$profilePath#marketing_share.consumer.clickstream_hourly"

val df = spark.read
  .format("deltaSharing")
  .load(tableUrl)
  .select("event_time", "event_type", "user_id", "region")
  .where(col("region").equalTo("US"))
  .limit(1000)

df.show()
```

---

## Time Travel: Reading Historical Versions

One of Delta Lake's killer features is time travel. Delta Sharing supports it too.

### By Version Number

```python
df = spark.read \
    .format("deltaSharing") \
    .option("versionAsOf", 10) \
    .load(table_url)
```

### By Timestamp

```python
df = spark.read \
    .format("deltaSharing") \
    .option("timestampAsOf", "2024-06-15 14:30:00") \
    .load(table_url)
```

This lets recipients query the table as it existed at a specific point in time — powerful for auditing, debugging, and reproducibility.

---

## Streaming: Real-Time Data Sharing

Here's where Delta Sharing gets really exciting.

Traditional exports give you snapshots. Stale the moment they're created.

Delta Sharing lets you **stream changes** in real-time:

```python
# Stream changes from a shared table
stream_df = spark.readStream \
    .format("deltaSharing") \
    .option("startingVersion", 0) \
    .option("skipChangeCommits", "true") \
    .load(table_url)

# Process the stream
query = stream_df.writeStream \
    .format("console") \
    .outputMode("append") \
    .start()

query.awaitTermination()
```

Your partner updates their table. You see the change immediately. Not in an hour. Not tomorrow. Now.

### Change Data Feed

For tables with Change Data Feed enabled (`delta.enableChangeDataFeed=true`), you can track exactly what changed:

```python
stream_df = spark.readStream \
    .format("deltaSharing") \
    .option("readChangeFeed", "true") \
    .option("startingVersion", 0) \
    .load(table_url)
```

This gives you INSERT, UPDATE, and DELETE events — perfect for keeping downstream systems in sync.

### All Streaming Options

| Option | Type | What It Does |
|--------|------|--------------|
| `startingVersion` | Int | Start reading from this table version |
| `endingVersion` | Int | Stop reading at this version (for bounded reads) |
| `startingTimestamp` | Timestamp | Start from the closest version to this time |
| `endingTimestamp` | Timestamp | Stop at the closest version to this time |
| `readChangeFeed` | Boolean | Enable CDC streaming |
| `maxFilesPerTrigger` | Int | Files per micro-batch (default: 1000) |
| `maxBytesPerTrigger` | String | Data per micro-batch (e.g., "10g") |
| `ignoreChanges` | Boolean | Skip UPDATE/DELETE operations |
| `ignoreDeletes` | Boolean | Skip DELETE operations only |
| `skipChangeCommits` | Boolean | Ignore data-modifying transactions |

---

## Community Connectors

Delta Sharing isn't just for Spark and Python. The community has built connectors for:

| Platform | Link | Status |
|----------|------|--------|
| **Power BI** | Databricks owned | ✅ Released |
| **Python** | delta-sharing (pip) | ✅ Released |
| **Node.js** | goodwillpunning/nodejs-sharing-client | ✅ Released |
| **Java** | databrickslabs/delta-sharing-java-connector | ✅ Released |
| **Rust** | r3stl355/delta-sharing-rust-client | ✅ Released |
| **Go** | magpierre/delta-sharing (golang) | ✅ Released |
| **C++** | magpierre/delta-sharing (cpp) | ✅ Released |

Your partners can consume shared data in whatever tool they prefer. The protocol is the same.

---

## What Changed For Us

Let me tell you what happened after we adopted Delta Sharing.

**Before:**
- 40 export jobs to manage
- Weekly "the data doesn't match" fires
- 3 engineers spending 20% of their time on data sharing
- Partners always working with stale data
- Schema changes breaking downstream pipelines

**After:**
- 0 export jobs
- 1 sharing server
- Partners reading live data
- Schema changes handled automatically
- Support tickets dropped 80%

The biggest change? **Trust.**

When partners know they're reading from the source of truth  not a copy of a copy  they trust the data. No more "can you verify this number?" No more "which export is the latest?"

There's only one version. The real one.



## Getting Started

Ready to try it? Here's your path:

### As a Provider:

1. **Set up the server**
   ```bash
   docker run -p 8080:8080 deltaio/delta-sharing-server:latest
   ```

2. **Create your share config** (start with one table)
   ```yaml
   version: 1
   shares:
     - name: "test_share"
       schemas:
         - name: "public"
           tables:
             - name: "sample_data"
               location: "s3://bucket/path/to/table"
   ```

3. **Generate a recipient profile** (set expiration!)

4. **Test it yourself** before sharing externally

### As a Recipient:

1. **Get the profile file** from your data provider

2. **Install the client**
   ```bash
   pip install delta-sharing
   ```

3. **Explore and query**
   ```python
   import delta_sharing
   client = delta_sharing.SharingClient("profile.share")
   print(client.list_shares())
   ```



## The Bottom Line

Data sharing doesn't have to be painful.

You do not  need 40 export jobs. You do not  need 40 S3 buckets. You do not  need to track which partner has which version of which data.

You need one table, one server, and a protocol that lets everyone read from the source of truth.

That's Delta Sharing.

It took us a week to set up. It saved us thousands of hours.

What are you waiting for?



*Still managing export jobs? Still emailing CSVs? Drop a comment  I have been there, and I'd love to help.*



**Resources:**
- [Delta Sharing Protocol Spec](https://github.com/delta-io/delta-sharing/blob/main/PROTOCOL.md)
- [Reference Server](https://github.com/delta-io/delta-sharing)
- [Python Client](https://pypi.org/project/delta-sharing/)



*Tags: #DeltaSharing #DataEngineering #DataMesh #Lakehouse #OpenSource #BigData*
