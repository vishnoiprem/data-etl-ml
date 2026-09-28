# Top 50 Apache Spark Data Engineering Interview Questions and Answers

**Source attribution:** This article was originally published on Data Vidhya
(https://datavidhya.com/) by **Darshil Parmar (Founder, Data Vidhya)**:
"70 Spark Interview Questions for Data Engineers (Real Asks, 2026)"
— Jan 25, 2025, updated Mar 18, 2026.

Reproduced in `data-enginnering-cloudvala/` as interview-prep reference material.
Authored Q&A content; no editorial wrapping added.

---

Mastering big data requires a solid grasp of distributed computing, and at the heart of modern data pipelines sits Apache Spark. As companies move away from traditional MapReduce toward faster, in-memory processing, the demand for engineers who can build, optimize, and troubleshoot Spark applications has skyrocketed. Whether you are just finishing a data engineering bootcamp or are looking to level up your career, mastering these apache spark data engineering interview questions is a crucial step in proving your technical expertise.

In this guide, we dive directly into the technical questions you are likely to encounter in a screening or technical round, covering everything from core architecture to complex performance tuning scenarios.

## Core Concepts & Architecture

### 1. What is Apache Spark, and how does it differ from Hadoop MapReduce?

Apache Spark is an open-source, distributed computing system designed for fast, in-memory data processing. The primary difference lies in how they handle data: MapReduce is disk-based, writing intermediate results to the file system after every Map and Reduce phase, which causes significant I/O overhead. Spark, however, keeps data in RAM whenever possible, making it up to 100x faster for iterative algorithms and machine learning. Furthermore, Spark provides a unified engine for SQL, streaming, and graph processing, whereas Hadoop requires different frameworks (like Hive or Storm) for these tasks.

### 2. Explain the components of the Spark Ecosystem.

The Spark ecosystem is a collection of libraries built on top of the Spark Core engine:

- **Spark Core:** Provides the basic functionality of Spark, including task scheduling, memory management, and fault recovery.
- **Spark SQL:** Allows users to query structured data using SQL or the DataFrame API, integrating relational processing with Spark's functional programming.
- **Spark Streaming / Structured Streaming:** Enables scalable and fault-tolerant processing of live data streams.
- **MLlib:** A built-in library for machine learning that includes common algorithms like classification, regression, and clustering.
- **GraphX:** A library for manipulating graphs and performing graph-parallel computation.

### 3. What is an RDD (Resilient Distributed Dataset)?

RDD is the fundamental data structure of Spark. It is an immutable, partitioned collection of objects that can be processed in parallel across a cluster. It is "Resilient" because it tracks its own "lineage" (the sequence of operations used to create it), allowing it to automatically recompute data in case of node failure. It is "Distributed" because the data is split into partitions across multiple nodes.

### 4. What is a Spark Driver?

The Driver is the central "brain" of a Spark application. It is the process where the main() method runs and where the SparkSession (or SparkContext) is created. Its responsibilities include converting the user's code into a logical DAG (Directed Acyclic Graph), splitting that graph into stages and tasks, and scheduling those tasks on the Executors. It also collects the results of actions (like count() or collect()) and returns them to the user.

### 5. What is an Executor?

Executors are worker processes that run on individual nodes in the cluster. Their sole purpose is to execute the tasks assigned to them by the Driver and store the resulting data in-memory or on disk. Each application has its own set of executors that persist for the entire lifetime of the application. If an executor fails, the Driver can re-launch tasks on other available executors.

### 6. Explain the concept of a DAG (Directed Acyclic Graph).

A DAG is a representation of the series of transformations applied to the data. In Spark, every time you call a transformation, the Driver adds it to the DAG. It is "Directed" because the operations move in a specific order, and "Acyclic" because the flow does not loop back on itself. When an action is called, Spark submits this DAG to the DAG Scheduler, which optimizes the plan by collapsing transformations into stages.

### 7. What are Transformations in Spark?

Transformations are operations that take an existing RDD or DataFrame and produce a new one. Crucially, transformations are "lazy," meaning they aren't executed immediately; Spark simply remembers the operation. Examples include map(), filter(), flatMap(), and groupByKey(). Transformations are further categorized into "narrow" (no data movement) and "wide" (requires a shuffle).

### 8. What are Actions in Spark?

Actions are operations that trigger the actual computation of the transformations recorded in the DAG. When an action is called, Spark processes the data and returns a result to the Driver or writes the data to an external storage system. Common actions include collect(), count(), take(n), first(), and saveAsTextFile().

### 9. What is Lazy Evaluation?

Lazy evaluation means that Spark delays the execution of transformations until an action is invoked. Instead of executing each line of code as it is encountered, Spark builds up a lineage of transformations. This allows the Catalyst Optimizer to look at the entire chain of events and optimize the physical execution, for example, by combining filters or skipping unnecessary data reads, before any processing actually begins.

### 10. What is a SparkSession?

Introduced in Spark 2.0, the SparkSession is a unified entry point for interacting with Spark. Prior to 2.0, developers had to manage different contexts (SparkContext for RDDs, SQLContext for SQL, and HiveContext for Hive). SparkSession encapsulates all these functionalities into a single object, making the API cleaner and easier to use while maintaining backward compatibility.

## Data Structures & APIs

### 11. What is the difference between RDD, DataFrame, and Dataset?

- **RDD:** Provides the most control but has no built-in schema, meaning Spark doesn't know the structure of the data inside. This makes it harder for Spark to optimize.
- **DataFrame:** A distributed collection of data organized into named columns, similar to a table in a relational database. It is much faster than RDDs because it uses the Catalyst Optimizer and Tungsten execution engine.
- **Dataset:** An extension of DataFrames that provides type-safety (available in Scala/Java). It allows you to use strongly typed objects while still benefiting from the performance optimizations of the DataFrame engine.

### 12. How do you create a DataFrame in PySpark?

There are several ways to create a DataFrame:

- **From a file:** `spark.read.csv("file.csv")`, `spark.read.json()`, or `spark.read.parquet()`.
- **From an existing RDD:** By calling `rdd.toDF()` if the RDD contains Row objects or tuples.
- **Programmatically:** Using `spark.createDataFrame(data, schema)`, where `data` is a list of tuples or rows and `schema` is either a list of column names or a `StructType` object.

### 13. What is the difference between map and flatMap?

`map()` transforms each element of the input into exactly one element in the output. For example, if you map a list of strings to their lengths, a 5-element list remains a 5-element list. `flatMap()`, however, can return zero, one, or many elements for each input element because it "flattens" the resulting collection. A common use case for `flatMap()` is a word count where one line (one element) is broken into multiple words (multiple elements).

### 14. What are Narrow and Wide Transformations?

- **Narrow Transformations:** These occur when each partition of the parent RDD is used by at most one partition of the child RDD (e.g., filter, map). Since the data stays within the same partition, no network shuffle is required.
- **Wide Transformations:** These occur when data from multiple parent partitions is needed to calculate a single child partition (e.g., groupByKey, reduceByKey, join). This triggers a "Shuffle," where data is moved across the network between executors.

### 15. What is a Shuffle operation?

A shuffle is a mechanism for redistributing data across executors so that it's grouped differently across partitions. It is often triggered by operations like join or groupBy. Shuffles are the most expensive operations in Spark because they involve disk I/O, data serialization, and network transmission. Minimizing shuffles is a key part of Spark performance tuning.

### 16. How does Spark handle missing or null data?

Spark provides the `DataFrame.na` functions specifically for this. You can use `df.na.drop()` to remove rows containing null values, `df.na.fill(value)` to replace nulls with a specific constant, or `df.na.replace()` to swap specific values. You can also target specific columns for these operations to avoid losing valuable data in other columns.

### 17. What is a Schema, and why should you define it explicitly?

A schema is the metadata that defines the column names and data types of a DataFrame. While Spark can "infer" the schema by reading a portion of the data, this is often slow and prone to errors (e.g., a column of integers being read as strings). Defining a schema explicitly using `StructType` and `StructField` is a best practice because it makes the data loading process faster and ensures data integrity.

### 18. Explain the difference between repartition and coalesce.

- **repartition:** Reshuffles the data across the cluster to create a specific number of partitions. It can increase or decrease the number of partitions but always performs a full shuffle.
- **coalesce:** Specifically used to decrease the number of partitions. It avoids a full shuffle by merging local partitions together on the same executor, making it much more efficient than repartition for reducing file counts before saving data.

### 19. What are Spark Accumulators?

Accumulators are variables that are used for aggregating information from executors back to the Driver. They are "write-only" from the perspective of the executors; executors can add to them, but they cannot read their values. Only the Driver can read the final accumulated value. They are most commonly used for implementing counters (e.g., counting the number of corrupted records in a dataset).

### 20. What are Broadcast Variables?

Broadcast variables allow the programmer to keep a read-only variable cached on each machine rather than shipping a copy of it with every task. They are incredibly useful when you have a large dataset (like a fact table) that needs to be joined with a small lookup table (the broadcast variable). This prevents the "Wide Transformation" shuffle that would normally occur during a join.

## Performance Tuning & Optimization

### 21. What is Data Skew, and how do you handle it?

Data skew happens when a few partitions have a disproportionately large amount of data compared to others. This causes "straggler" tasks where most executors finish quickly but one or two take hours. To fix this, you can use "salting" (adding a random prefix to the join keys to spread them out) or use a Broadcast Join if one of the tables is small enough to fit in memory.

### 22. Explain the Catalyst Optimizer.

Catalyst is the optimization engine for Spark SQL. It uses advanced programming features to build an extensible query optimizer. When you submit a query, Catalyst goes through four phases: Analysis (resolving references), Logical Optimization (rule-based optimizations like constant folding), Physical Planning (generating multiple physical plans and picking the best one based on cost), and Code Generation (generating Java bytecode to run on the JVM).

### 23. What is Project Tungsten?

Project Tungsten is an initiative to improve the efficiency of Spark's memory and CPU usage. It introduces "Off-Heap Memory Management" to bypass the overhead of Java's Garbage Collection and uses "Whole-Stage Code Generation" to collapse multiple operations into a single function, reducing the number of virtual function calls and improving CPU cache locality.

### 24. What is Caching/Persistence?

Caching is a technique used to store the results of an expensive DataFrame or RDD computation in memory so it can be reused in future actions without being recomputed. `df.cache()` uses the default storage level (Memory only). `df.persist(storageLevel)` gives you more control, allowing you to store data on disk, in memory, or a combination of both (e.g., `MEMORY_AND_DISK`).

### 25. When should you use a Broadcast Join?

A Broadcast Join should be used when you are joining a very large DataFrame with a small one (typically under 100MB, though this is configurable). Instead of shuffling both tables based on the join key, Spark "broadcasts" the entire small table to every executor. This turns a wide transformation into a narrow one, significantly speeding up the join.

### 26. How do you identify a bottleneck in a Spark job?

The primary way to identify bottlenecks is by using the Spark UI. You should look for:

- **Stages with high shuffle read/write:** Indicates heavy data movement.
- **Max task time vs. Median task time:** A large gap here indicates data skew.
- **Garbage Collection (GC) time:** High GC time means the executors are struggling with memory management.
- **Spill to Disk:** Indicates that the executor memory is insufficient for the data being processed.

### 27. What is Predicate Pushdown?

Predicate pushdown is an optimization where the filtering of data (the `WHERE` clause) is moved as close to the data source as possible. For example, if you are reading from a Parquet file, Spark will only read the rows that match your filter criteria rather than loading the whole file into memory and filtering it afterward. This drastically reduces I/O and memory usage.

### 28. How does Spark handle Out of Memory (OOM) errors?

OOM errors can occur at the Driver (if you `collect()` too much data) or at the Executor (if partitions are too large). To resolve these:

- **Driver OOM:** Avoid using `collect()` on large datasets; write to a file instead.
- **Executor OOM:** Increase `spark.executor.memory`, increase the number of partitions to make each task smaller, or reduce the number of `spark.executor.cores` to allow more memory per running task.

### 29. What is the significance of the Parquet file format in Spark?

Parquet is a columnar storage format that is highly optimized for big data processing. Its advantages include:

- **Column Pruning:** Spark only reads the columns required for the query.
- **Schema Evolution:** You can add new columns over time.
- **Compression:** Columnar data compresses much better than row-based data.
- **Metadata:** Parquet stores statistics like min/max values, allowing Spark to skip entire blocks of data (statistics-based skipping).

### 30. How do you tune the number of partitions?

The goal is to have enough partitions to utilize all available cores but not so many that the overhead of managing tasks outweighs the benefits of parallelism. A common rule is 2–4 partitions per CPU core. For shuffle operations, you can tune `spark.sql.shuffle.partitions`, which defaults to 200. If your data is small, 200 is too many; if your data is in the terabytes, 200 is far too few.

## Operations & Deployment

### 31. What are the different Cluster Managers supported by Spark?

Spark supports several cluster managers to allocate resources:

- **Standalone:** A simple cluster manager included with Spark.
- **Hadoop YARN:** The resource manager in Hadoop 2 and 3. Most common in enterprise environments.
- **Apache Mesos:** A general cluster manager that can also run Hadoop MapReduce and other applications.
- **Kubernetes:** An open-source system for automating deployment, scaling, and management of containerized applications.

### 32. Explain "Client Mode" vs. "Cluster Mode."

- **Client Mode:** The Driver process runs on the host machine where the job was submitted. This is useful for interactive work (like using a Jupyter notebook) because you can see the output immediately, but it is risky for long-running jobs if the host machine loses connectivity.
- **Cluster Mode:** The Driver process runs on one of the worker nodes inside the cluster. This is the standard for production jobs because it makes the application more robust against network issues between the client and the cluster.

### 33. What is a Lineage Graph?

A Lineage Graph (also known as the RDD Operator Graph) is a record of all the parent RDDs used to create a child RDD. Since RDDs are immutable, Spark doesn't change data; it creates new RDDs. If a node fails and a partition of data is lost, Spark looks at the lineage graph to see exactly which transformations were applied to the original data source and re-runs them to recover the lost partition.

### 34. How do you achieve fault tolerance in Spark?

Spark achieves fault tolerance through two main methods:

- **Lineage:** As mentioned, Spark can recompute lost partitions using the lineage graph.
- **Checkpointing:** For applications with very long or complex lineages (like streaming or iterative ML), Spark can save the RDD's state to a reliable storage system (like S3 or HDFS). This "cuts" the lineage, so if a failure occurs, Spark only has to recompute from the last checkpoint.

### 35. What is spark-submit?

`spark-submit` is the command-line utility used to launch Spark applications. It allows you to configure various parameters such as the master URL (e.g., `yarn`), the deploy mode (client or cluster), executor memory, number of cores, and any external jars or Python files your application needs to run.

### 36. Explain the concept of Window Functions.

Window functions allow you to perform calculations across a set of rows that are related to the current row. Unlike aggregate functions (like `SUM`), which collapse rows into a single value, window functions keep the original rows while adding the calculation. Common examples include `ROW_NUMBER()` for ranking, `RANK()`, and `LAG()` or `LEAD()` for comparing a row's value to the previous or next row.

### 37. What is Structured Streaming?

Structured Streaming is a stream processing engine built on the Spark SQL engine. It allows you to express streaming computations the same way you would express batch computations on static data. The system treats the live data stream as an "unbounded table" that is constantly being appended to, and Spark automatically handles the incremental processing and fault tolerance.

### 38. What is a "Stage" in a Spark job?

A stage is a physical unit of execution. Spark breaks a job into stages based on shuffle boundaries. Any set of transformations that can be performed without moving data across the network (narrow transformations) are grouped into a single stage. When a wide transformation (like a join) is required, Spark finishes the current stage, shuffles the data, and starts a new stage.

### 39. What is the role of spark.executor.memoryOverhead?

This setting defines the amount of additional memory to be allocated per executor process. It is used for VM overhead, interned strings, and other native code requirements. By default, it is about 10% of the executor memory. If your Spark job uses native libraries (like Python or C++ libraries via JNI), you may need to increase this to avoid the cluster manager killing your containers.

### 40. How do you handle data serialization in Spark?

Serialization is used to convert objects into a format that can be stored or transmitted over the network. Spark supports two libraries:

- **Java Serialization:** The default, which is flexible but very slow and produces large objects.
- **Kryo Serialization:** Much faster and more compact than Java serialization. It is highly recommended for production Spark applications, though it requires you to register custom classes for the best performance.

## Advanced Scenarios & Coding Logic

### 41. How would you join two very large tables?

Joining two massive tables usually requires a Sort-Merge Join. Spark first shuffles both tables so that rows with the same join key end up in the same partition. Then, it sorts the data within each partition and merges them. To optimize this, ensure that both tables are "bucketed" and sorted on the join key in advance. This allows Spark to skip the shuffle and sort phases entirely during the join.

### 42. What is an "Action" that does not return data to the Driver?

Actions like `saveAsTextFile()`, `write.parquet()`, or `write.jdbc()` do not bring the data back to the Driver. Instead, each executor writes its own partition of data directly to the external storage system (e.g., S3, HDFS, or a database). This is much more efficient than bringing data to the Driver first, as it utilizes the combined bandwidth of the entire cluster.

### 43. How do you read data from a JDBC source?

You use `spark.read.format("jdbc")` and provide the connection URL, table name, and credentials. Crucially, to avoid reading the whole table through a single connection (which is a bottleneck), you should provide `partitionColumn`, `lowerBound`, `upperBound`, and `numPartitions`. This tells Spark to open multiple concurrent connections to the database and read data in parallel.

### 44. What is the difference between reduceByKey and groupByKey?

`reduceByKey` is significantly more efficient because it performs a "map-side combine." It merges values locally on each executor before the shuffle occurs, drastically reducing the amount of data sent over the network. `groupByKey`, on the other hand, sends every single record over the network to group them, which can easily lead to Out of Memory errors if a single key has millions of records.

### 45. Explain "Dynamic Allocation" in Spark.

Dynamic allocation allows Spark to adjust the number of executors assigned to an application based on the workload. If tasks are waiting in the queue, Spark requests more executors from the cluster manager. If executors have been idle for a certain period, Spark releases them back to the cluster. This is vital for shared clusters to ensure that resources aren't being wasted by idle applications.

### 46. How do you prevent "Small File Problem" in Spark?

The small file problem occurs when Spark writes thousands of tiny files to storage, making future reads very slow. To fix this:

- Use `coalesce(n)` or `repartition(n)` before writing to reduce the number of output partitions.
- Use a file compaction utility to merge small files after the job finishes.
- If using Spark 3.0+, enable Adaptive Query Execution (AQE), which can automatically coalesce small partitions during the shuffle phase.

### 47. What is "Speculative Execution"?

Speculative execution is a health-check mechanism. If Spark detects that one task is running significantly slower than the average (due to faulty hardware or network issues on a specific node), it will launch a duplicate "speculative" copy of that task on a different node. Spark then uses the result from whichever task finishes first and kills the other one.

### 48. How do you implement a UDF (User Defined Function)?

In PySpark, you define a standard Python function and then register it using `pyspark.sql.functions.udf(func, returnType)`. However, UDFs should be a last resort. Because they run in a Python process outside the JVM, Spark has to serialize data, send it to Python, and then bring it back. Whenever possible, use built-in Spark SQL functions, which are written in Scala and run directly on the JVM.

### 49. What is the purpose of checkpoint()?

`checkpoint()` is used to save the RDD to a reliable storage system and completely remove its lineage. This is different from `cache()`, which keeps the lineage. Checkpointing is essential for long-running streaming jobs or iterative algorithms (like GraphX or ALS) where the DAG could grow so large that it causes a stack overflow or makes recovery from failure take too long.

### 50. How would you count unique values in a column?

There are two main ways:

- `df.select("column").distinct().count()` — This performs a distinct operation (wide transformation) and then counts the rows.
- `from pyspark.sql.functions import countDistinct; df.select(countDistinct("column")).show()` — This uses an optimized aggregate function to calculate the count of unique values. For very large datasets where an exact count isn't needed, you can use `approx_count_distinct()` to get a result much faster.

---

Preparing for a career in big data is about more than just memorizing definitions; it's about understanding how to handle data at scale efficiently. These apache spark data engineering interview questions cover the foundational pillars and the complex edge cases you'll face in the field. The best way to master Spark is through hands-on practice — build pipelines, break them, and use the Spark UI to understand why they failed.

## Frequently asked questions

**What are the key features of Apache Spark?**
In-memory processing (10-100× faster than disk-based MapReduce), unified API for batch + streaming via Structured Streaming, lazy evaluation with the Catalyst query optimizer, language support for Scala/Python/SQL/R, and a rich ecosystem (MLlib for ML, GraphX for graphs, Spark SQL for analytics). Spark runs on Kubernetes, YARN, Mesos, or standalone clusters.

**What is the difference between transformations and actions in Spark?**
Transformations (map, filter, join, groupBy) are lazy — they build a logical execution plan but don't trigger computation. Actions (count, collect, write, show) materialize results and trigger the entire DAG to execute. This lazy evaluation lets Catalyst optimize the full plan before running, which is why Spark is fast despite the verbose API.

**How does Spark handle data partitioning?**
Spark splits data into partitions — the unit of parallelism. By default it uses HashPartitioner (200 shuffle partitions). Bad partitioning causes skew (one task takes 10× longer than others). Fix: use `repartition()` to balance, or `partitionBy()` in writes for predicate pushdown. Adaptive Query Execution (AQE) auto-coalesces small partitions and handles skew in joins.

**What is a broadcast join and when should you use it?**
A broadcast join sends a small table to every executor's memory, avoiding the network shuffle a normal join requires. Spark auto-broadcasts tables under `spark.sql.autoBroadcastJoinThreshold` (default 10MB). For larger tables you know will fit, hint it explicitly: `F.broadcast(small_df)`. Use when the smaller side is under ~100MB and the larger side is huge.

**How do you optimize Spark performance?**
Top six levers: (1) enable Adaptive Query Execution (AQE), (2) broadcast small tables, (3) cache reused DataFrames, (4) partition large datasets by the most-filtered column, (5) avoid wide transformations where narrow ones work (filter before join), (6) right-size cluster — more workers isn't always better; more memory per worker often is. Read the Spark UI's Stages tab to find the slow stage before tuning.

**What is the difference between cache() and persist() in Spark?**
`cache()` is shorthand for `persist(MEMORY_AND_DISK)`. `persist()` lets you choose the storage level: `MEMORY_ONLY` (fastest, fails if memory short), `MEMORY_AND_DISK` (spills to disk), `DISK_ONLY`, plus serialized and replicated variants. Use `cache()` for the common case. Use `persist(MEMORY_ONLY_SER)` when memory is tight and CPU is cheap.

**What causes data skew in Spark and how do you fix it?**
Skew happens when one partition has way more data than others (e.g., joining on a column with one dominant value). Fixes: enable AQE (handles skew automatically in 3.0+), use salting (append random prefix to skewed key then aggregate twice), or filter the skewed key out and join it separately. The Spark UI shows skewed stages as one task taking far longer than median.
