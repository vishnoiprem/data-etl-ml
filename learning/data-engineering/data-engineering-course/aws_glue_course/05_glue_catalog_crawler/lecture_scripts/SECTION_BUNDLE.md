# Section 5 — Glue Resources SetUp Part 3: Glue Catalog, Crawler (L21–L35, 58 min)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> This is the section bundle. Each lecture is also published as its own file in this directory.

---

## L21 — Section Overview (1:38)

> "Section 5 is the heart of the course. The Glue Data Catalog is the central metadata store. The Crawler automatically infers schemas from data in S3. The Glue Job is what actually runs the ETL. By the end of this section, you'll have 5 Crawlers running, 1 Glue Job, 1 Trigger (4 types covered), and 1 Workflow. The Job will read `city_temperature.csv`, aggregate by country, and write Parquet to the target bucket."

---

## L22 — AWS Glue Catalog 101 (3:28)

> "The Glue Data Catalog is a managed Hive Metastore. It stores: database (a logical namespace), table (a schema + location), partition (a sub-directory in the table's location), column (a field in the table's schema). The Catalog is the *metadata*; the *data* itself stays in S3. The Catalog is shared across Athena, EMR, Redshift Spectrum, and Glue Jobs. So when you create a table in the Catalog, you can query it from any of those services."

Key bullets: database / table / partition / column; Catalog is metadata; shared across services.

---

## L23 — AWS Glue Database 101 (creating a database by hand) (3:30)

> "A Glue Database is a logical namespace for tables. You create one in the console: Glue → Databases → Add database. Name: `glue_course_db`. Description: 'Database for the AWS Glue masterclass'. Location: optional — S3 prefix for the database's tables. The location is *metadata*; the data itself stays in the S3 paths declared per table. The 2 ways to create a database: by hand (this lecture) or implicitly via a Crawler (a Crawler that has no database configured will create one). For this course, we'll create the database by hand so we have a stable target for our Crawlers."

Lab: Glue → Databases → Add database. Name: `glue_course_db`. Create.

Key bullets: namespace; by hand vs Crawler-implicit; location is metadata.

---

## L24 — AWS Glue Table 101 (creating a table in the catalog) (3:30)

> "A Glue Table is a schema + a location. You create one in the console: Glue → Tables → Add table. Step 1: name (`city_temperature`). Step 2: database (`glue_course_db`). Step 3: data store (S3). Step 4: classification (CSV). Step 5: column schema — 10 columns matching `city_temperature.csv`. Step 6: partition keys (none for now). Step 7: review and create. The table is now in the Catalog. You can query it from Athena with `SELECT * FROM city_temperature LIMIT 10;`."

Lab: Glue → Tables → Add table. Add 10 columns. Verify in Athena.

Key bullets: schema + location; 7-step add-table wizard; Athena query works.

---

## L25 — AWS Glue Crawler 101 (6:03)

> "A Crawler connects to a data store (S3, JDBC, DynamoDB), inspects the data, infers the schema, and creates or updates tables in the Data Catalog. The Crawler is *incremental* — on each run, it only inspects new or modified files. The Crawler uses *classifiers* to determine the file type and parse the schema. Built-in classifiers: CSV, JSON, Parquet, ORC, Avro. You can write a *custom classifier* (grok pattern or XML tag) for non-standard formats. The Crawler writes a table per *data store* (S3 prefix), partitioned by the directory structure. So if your S3 path is `s3://bucket/year=2026/month=01/data.csv`, the Crawler creates a table with `year` and `month` as partition columns."

Key bullets: data store; incremental; classifiers; partitioned by directory structure.

---

## L26 — AWS Glue Crawler Classifier 101 (3:16)

> "Classifiers tell the Crawler how to parse your data. The built-in classifiers cover CSV, JSON, Parquet, ORC, and Avro. For custom formats (e.g., a log file with a specific structure), you write a *grok classifier* — a pattern that matches each line. The Crawler tries classifiers in order; the first one that matches wins. Custom classifiers are useful but rare. For this course, the built-in CSV classifier is enough."

Key bullets: built-in classifiers; grok for custom; first-match-wins.

---

## L27 — Crawler Lab: First Glue Crawler Creation (4:17)

> "Create the first Crawler. Glue → Crawlers → Add crawler. Name: `crawler-source-csv`. Data store: S3. Path: `s3://<your-source-bucket>/input/`. IAM role: `GlueJobRole`. Schedule: on demand. Database: `glue_course_db`. Output: prefix. Create. The Crawler is ready to run."

Lab: create the Crawler, leave in READY state.

---

## L28 — First Glue Crawler Running (4:19)

> "Run the Crawler. Click 'Run crawler'. Wait 1-2 minutes. The Crawler creates a table named `input` in the `glue_course_db` database. Open the table: the schema has 10 columns (region, country, city, latitude, longitude, year, month, day, avg_temperature, avg_temperature_uncertainty). The table's location is `s3://<your-source-bucket>/input/`. The Crawler also detected 0 partitions (the file is at the root of the prefix, not in `year=X/month=Y/` sub-directories). To add partitioning, we'd need to re-write the data with a partitioned directory structure — we'll do that in Lecture L32."

---

## L29 — Crawler Lab: Second Glue Crawler Creation (5:24)

> "Create a second Crawler for the target bucket. This Crawler is post-Job: it runs after the Glue Job writes Parquet to the target bucket. The Crawler will discover the partitioned Parquet output and create a table with `year` and `month` as partition columns. Name: `crawler-target-parquet`. Path: `s3://<your-target-bucket>/output/`. Same IAM role, same database."

---

## L30 — Crawler Lab: Third Glue Crawler Creation (2:26)

> "Third Crawler: a Crawler for the Glue script bucket. This Crawler will scan the `scripts/` prefix where we upload the Glue Job Python script. It creates a table for the script (text format). This is mostly a convenience — it lets you query the script's last-modified time from Athena. Not strictly necessary, but a good practice."

---

## L31 — Crawler Lab: Fourth Glue Crawler Creation (7:04)

> "Fourth Crawler: a Crawler that crawls *both* the source and target buckets. Glue Crawlers can have multiple data store paths. This is a single Crawler that creates 2 tables — one for each prefix. Useful when you want one Crawler to manage the schema for the whole pipeline."

---

## L32 — Crawler Lab: Fifth Glue Crawler Creation And Running (2:54)

> "Fifth Crawler: a Crawler for the *partitioned* output. After the Glue Job runs, the output is at `s3://<target>/output/by_country_year_month/year=YYYY/month=MM/`. This Crawler creates a table with `year` and `month` as partition columns. To make the Crawler pick up the partitions, you click 'Sync partitions' in the table view after the Crawler runs. The Crawler does *not* automatically populate the partition metadata in the Catalog; you have to sync."

---

## L33 — AWS Glue Job 101 (7:21)

> "The Glue Job is the ETL itself. Two flavors: Spark (Python or Scala) and Python Shell. Spark Jobs run on a managed Spark cluster — they auto-scale, they handle the data partitioning, they read/write to S3. Python Shell Jobs run on a single instance — they're for short scripts (<= 1 hour) that don't need Spark. **Glue Studio** is the *visual* way to build a Glue Job — drag-and-drop transforms, no Python required. We'll cover Glue Studio in the next subsection. The 6 key Job properties: Name, Role (`GlueJobRole`), Glue Version (4.0 = Spark 3.3, Python 3.10), Worker Type (G.025X = 1 DPU, G.1X = 4 DPU, G.2X = 8 DPU, G.4X = 16 DPU, G.8X = 32 DPU), Number of Workers, Script Location (an S3 path). The 3 default arguments you'll use: `--job-language python`, `--source_bucket`, `--target_bucket`. The script reads them via `getResolvedOptions(sys.argv, ['source_bucket', 'target_bucket', 'source_key'])` — keys must match *exactly* (Glue 4.0 does not auto-convert dashes to underscores)."

Key bullets: Spark vs Python Shell; **Glue Studio** (visual, drag-and-drop); Glue version; Worker types; default arguments.

**Glue Studio 101 (5 min, mini-lecture inside L33).** Open Glue Studio from the Glue console (`AWS Glue → ETL jobs → Studio`). Click 'Create job' → 'Visual with a blank canvas'. You'll see a canvas with a Source node, a Transform node (ApplyMapping, Filter, Join, Aggregate, etc.), and a Target node. Drag a Source node → S3 → select the `input/city_temperature.csv` file → the source is configured. Drag a Transform node → ApplyMapping → rename the columns → the transform is configured. Drag a Target node → S3 Parquet → the target is configured. Connect Source → Transform → Target. Click 'Run'. The Job runs. **Glue Studio generates the PySpark script for you** — click the 'Script' tab to see it. This is the fastest way to build a Glue Job when you don't want to write Python by hand. The trade-off: you give up fine-grained control over the script.

---

## L34 — AWS Glue Trigger 101 — Scheduled, Conditional, On-Demand, EventBridge (4:18)

> "A Trigger is what starts a Glue Job. **4 types** — this is critical, get these right: 1) **Scheduled** — runs the Job on a cron schedule (e.g., every day at 2am UTC). 2) **Conditional** — runs Job B if Job A succeeds (or fails). 3) **On-Demand** — manual trigger, started by clicking 'Run' in the console or by calling `StartJobRun` from the API. 4) **EventBridge** — runs the Job in response to an EventBridge event (e.g., an S3 PUT event). The most common pattern is a Scheduled Trigger that runs the Job every day at 2am UTC. The second most common is a Conditional Trigger that runs Job B if Job A succeeds. For our first pipeline, we'll use an On-Demand Trigger (run from the console). The 4 types are configured the same way in the console: Glue → Triggers → Add trigger → pick the type → fill in the schedule/predicate/event pattern."

Key bullets: **4 types** (Scheduled / Conditional / On-Demand / EventBridge); cron syntax for Scheduled; predicate syntax for Conditional; event-pattern JSON for EventBridge.

---

## L35 — AWS Glue Workflow 101 + Section Recap (2:52)

> "A Workflow is a collection of Triggers, Jobs, and Crawlers, all in one named entity. A Workflow gives you a single view of the whole pipeline in the console: 'this Job feeds this Crawler feeds this Dashboard'. You can start a Workflow manually or on a schedule. Workflows also have a run history: 'the last run of this Workflow at 2am UTC succeeded in 4 minutes, 12 seconds'. For our first pipeline, we'll skip the Workflow — the Job runs on-demand. We'll add a Workflow in Section 7 (the pipeline lab)."

> "Section 5 recap: 5 things to remember. One: the Glue Data Catalog is metadata, not data. Two: a Crawler creates tables by inspecting files; a Crawler is incremental. Three: built-in classifiers handle CSV, JSON, Parquet, ORC, Avro. Four: a Glue Job has 6 properties — Name, Role, Glue Version, Worker Type, Number of Workers, Script Location. Five: Triggers start Jobs; there are 4 types (Scheduled / Conditional / On-Demand / EventBridge); Workflows orchestrate Triggers. In Section 6, we move to CloudFormation — same resources, but as code."

---

## Section 5 Quiz

5 questions, see `quizzes/section_5.md`.
