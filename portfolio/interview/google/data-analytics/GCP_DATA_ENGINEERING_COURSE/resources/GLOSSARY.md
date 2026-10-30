# Glossary

Every term the course uses, alphabetised. Terms specific to a service are marked with the service name.

## 📚 A

**Airflow** — An open-source workflow orchestrator built around DAGs. On Google Cloud it is managed as Cloud Composer.

**Alerting policy** — A monitoring rule that fires a notification when a metric crosses a threshold. Lives in Cloud Monitoring.

**Analytics Hub** — Bigtable's interface for running analytical queries over operational data, which normally would need to be copied into BigQuery first.

**API (Application Programming Interface)** — A defined contract that lets one program call another. On Google Cloud, most services are exposed through REST or gRPC APIs.

**Apache Beam** — The open-source unified programming model for batch and streaming pipelines. Google Cloud runs it as Dataflow.

**Apache Spark** — An open-source distributed compute engine for large-scale data processing. Google Cloud runs it as Dataproc.

**App Engine** — A managed platform-as-a-service for Python, Java, Go, Node.js and PHP applications, with automatic scaling.

**Archive storage class** — The cheapest Cloud Storage class at $0.0012 per GB-month, with a $0.05 per GB retrieval charge and an hours-long first-read latency.

**Autopilot** — A BigQuery mode that manages clusters, slots and billing automatically. You set a budget and a region; BigQuery sizes everything else.

## 📚 B

**Backfill** — Re-processing a historical data range that was missed, was wrong, or arrived late. A backfill re-runs the same logical dates with the same code.

**Batch processing** — Processing a bounded, finite set of data as one job. A nightly load of the previous day's files is a batch job.

**BigLake** — A managed lakehouse service that stores open-format tables in Cloud Storage and lets BigQuery query them directly, with no data movement.

**BigQuery Data Transfer Service** — A managed service that loads data from source systems into BigQuery on a schedule, including from Google Ads, YouTube, Salesforce and Google Sheets.

**BigQuery ML** — The facility to train and serve machine-learning models with SQL statements inside BigQuery, with no code and no model export.

**Bigtable** — A managed wide-column NoSQL database for large-scale key-value workloads, aimed at very high read throughput.

**Binding** — One line of an IAM policy: a principal, a role, and optionally a condition. A policy is a list of bindings.

**Bit** — A binary digit, the smallest unit of data. Eight bits make a byte.

**Blob** — A file object in Cloud Storage, addressed by a path within a bucket.

**Bucket** — The top-level container in Cloud Storage. Every object lives in exactly one bucket.

**Bus factor** — The number of people who would have to disappear before a project stalls. A bus factor of one is a risk.

## 📚 C

**CDC (Change Data Capture)** — The technique of reading the change log of a database to capture inserts, updates and deletes as a stream. Google Cloud offers it as Datastream.

**Catalog** — A metadata service that indexes datasets, tables, views and dashboards so they can be searched and governed. The course covers Data Catalog and Dataplex.

**Cloud Composer** — The managed, Google Cloud-hosted version of Apache Airflow, used for scheduling and orchestrating data workflows.

**Cloud Data Fusion** — A visual, low-code integration service for building data pipelines, supporting batch and streaming, with a code-free designer.

**Cloud Dataprep** — A browser-based visual data preparation service for exploring and cleaning data, using a row-limited, in-memory processing model.

**Cloud Functions** — An event-driven serverless compute service. Now called Cloud Run functions.

**Cloud Run** — A serverless container service billed per request and per CPU-second, with scale-to-zero.

**Cloud Scheduler** — A service that runs jobs on a cron or interval schedule by calling an authenticated HTTP endpoint.

**Cloud SQL** — A managed relational database offering MySQL, PostgreSQL and SQL Server, with automated backups and high availability.

**Cloud Spanner** — A globally consistent, horizontally partitioned relational database with strong consistency across regions.

**Cloud Storage** — Google Cloud's object storage service, with four storage classes, signed URLs, and integration with most other services.

**CMEK (Customer-Managed Encryption Key)** — A key you create and control in Cloud KMS, used to encrypt data at rest in a Google Cloud service.

**Cluster** — A grouping of nodes in GKE, Dataproc or BigQuery that run work together.

**Clustering (BigQuery)** — Sorting table rows by up to four columns so a query with a matching filter reads fewer bytes. See [CHEATSHEET.md](CHEATSHEET.md).

**Coldline** — A Cloud Storage class at $0.004 per GB-month with a $0.02 per GB retrieval charge, for data read about quarterly.

**Columnar storage** — Storing data by column rather than by row. Columnar layouts compress well and let a query read only the columns it needs.

**Composer environment** — A managed Airflow instance. It runs continuously and is billed per node-hour, so it costs money even when idle.

**Condition** — The optional expression attached to an IAM binding that limits when the role applies, such as requiring a request to come from a specific IP range.

**Conflict resolution** — The policy for handling two writers changing the same row in a replicated database. Common strategies are last-write-wins and optimistic concurrency.

**Continuous delivery** — Deploying to production automatically after a change passes its checks.

**Cost allocation** — Assigning cloud spend to teams, products or cost centres, usually with labels attached to resources.

**Custom role** — An IAM role you define yourself, containing only the permissions you choose.

## 📚 D

**DAG (Directed Acyclic Graph)** — The structure of an Airflow workflow: tasks connected by dependencies, with no cycles.

**Data Catalog** — A unified metadata and search service across the data estate. Now generally superseded by Dataplex.

**Data Cleansing** — Fixing or removing incorrect, incomplete or malformed data.

**Data Cubes** — Pre-aggregated structures built for fast reporting at the cost of flexibility.

**Data engineering** — The practice of designing and operating systems that move, transform and serve data reliably.

**Data interval** — The window of data an Airflow task run is responsible for, written `[logical_date, next_execution_date)`.

**Data lake** — A store of raw, unstructured files in object storage, kept in its original format.

**Data lakehouse** — A single platform that combines the flexibility of a data lake with the transaction and performance guarantees of a warehouse. BigLake is the course's example.

**Data line** — A single record moving through a pipeline, from source to sink.

**Data loss prevention (DLP)** — A class of service that finds sensitive data and can mask or redact it. See Sensitive Data Protection.

**Data model** — The definition of the fields in a dataset and their relationships.

**Data pipeline** — The full path data travels from source, through transformation, to a destination.

**Data residency** — The requirement that data stay within a particular country or jurisdiction.

**Data warehouse** — A store optimised for analytical queries over structured, historical data. BigQuery is the course's example.

**Dataplex** — A data management and governance service spanning lakes, warehouses and streaming, unifying metadata and governance.

**Datastream** — A change data capture service that reads from databases, SaaS sources and Kafka and writes to BigQuery, Cloud Storage or Pub/Sub.

**Dataform** — A service that treats SQL transformation logic as code, with version control, testing, lineage and dependency management.

**Dedup key** — The value used to identify a duplicate record. In this course, `dedup_key(event_id, partition)`.

**Delete-on-create** — Creating a resource and removing the default one with the same name, to avoid confusing names later.

**Deprecation** — The retirement of a feature on a published schedule. A deprecated API keeps working but is not updated.

**Deterministic** — A function that returns the same output for the same input, with no randomness or dependence on the clock. A deterministic pipeline can be replayed.

**Disaster recovery** — The plan for restoring service after a failure, measured by RPO and RTO.

**DLQ (Dead-Letter Queue)** — A queue holding messages that could not be processed successfully, so they can be inspected and replayed later.

**Domain** — A group of Google Cloud resources, used for DNS and service discovery.

## 📚 E

**Edge caching** — Storing content close to users to reduce latency and origin load.

**Egress** — Data leaving Google Cloud. Egress from Google Cloud to the internet is billed at $0.12 per GB.

**Elasticity** — The ability of a system to scale resources up and down with demand.

**Encryption at rest** — Data stored on disk is encrypted on the server, managed by Google.

**Encryption in transit** — Data moving between systems is encrypted, typically with TLS.

**ETL (Extract, Transform, Load)** — Copying data from sources, reshaping it, and writing it into a destination system.

**ELT (Extract, Load, Transform)** — Copying data into the warehouse first and transforming it with SQL inside the warehouse. This is the modern default.

**Exactly-once delivery** — A messaging guarantee that each message is processed exactly once. Available in Pub/Sub only for pull subscribers with an exactly-once-enabled subscription.

**Event time** — The time an event actually happened, carried in the payload. See processing time and watermark.

**Event-driven architecture** — A design where components react to events rather than being called synchronously.

**Exactly-once** — See Exactly-once delivery.

**Excess capacity** — Provisioned resources that are paid for but not used. The main source of waste in streaming systems.

## 📚 F

**Failover** — The automatic switch to a standby system when the primary fails.

**Fault tolerance** — The ability to keep operating despite the failure of individual components.

**Feature store** — A system serving consistent feature values to both training and online serving, preventing training/serving skew.

**Fine-tuning** — Continuing to train an existing model on a smaller, domain-specific dataset.

**Firestore** — A NoSQL document database for mobile and web applications, with offline sync and serverless operation.

**Folder** — A virtual container in the Google Cloud resource hierarchy, between an organization and a project.

**Function** — A piece of code deployed to Cloud Run functions and triggered by an event such as a Pub/Sub message.

**Fully managed service** — A service where Google Cloud runs the infrastructure, the scaling and the maintenance.

## 📚 G

**GKE (Google Kubernetes Engine)** — A managed Kubernetes control plane, with worker nodes you manage yourself or let Google manage.

**GDPR** — The European Union's General Data Protection Regulation, the main driver of data residency and de-identification requirements in Europe.

**gcloud CLI** — The command-line tool for managing Google Cloud resources. Every console action has an equivalent command.

**IAM (Identity and Access Management)** — The system that decides who can do what to which resource. On Google Cloud it is policy-based, not permission-based.

**IAM condition** — A binding attribute that restricts a role grant to requests matching an expression.

**Idempotent** — An operation that produces the same result whether it runs once or many times. Writing to a fixed partition with a deterministic key is idempotent.

**Incremental model** — A transformation that processes only new or changed data since the last run, using a high-water mark or a lookback window.

**Incremental load** — Moving only new data, rather than reloading everything.

**InfoType** — A Sensitive Data Protection detector for a category of sensitive data, such as email address or credit card number. `PERSON_NAME` and `EMAIL_ADDRESS` are common ones.

**Ingest** — Taking data into a system. `ingest_events()` in this course turns raw lines into validated event dictionaries.

**Instance** — A running virtual machine, or a managed database server.

**Internet-facing load balancer** — A load balancer that accepts traffic from the public internet.

**IAM binding condition** — See IAM condition.

**Isolated project** — A project deliberately separated from others to contain blast radius or satisfy a regulatory requirement.

## 📚 J

**JWT (JSON Web Token)** — A signed token that carries claims. Cloud Run and Cloud Functions use OIDC tokens to authenticate Pub/Sub push deliveries.

**Just-in-time (JIT) access** — Time-limited elevation of privileges, granted on request and expiring automatically.

## 📚 K

**Key ring** — A container in Cloud KMS holding crypto keys. A key ring is bound to a location.

**KMS (Key Management Service)** — The service that creates and manages encryption keys.

**Kubernetes** — An open-source container orchestrator. GKE is the managed version.

## 📚 L

**Lakehouse** — See Data lakehouse.

**Latency** — The delay between a request and its response.

**Least privilege** — Granting only the minimum permissions needed for a task, and no more.

**Lifecycle rule** — A Cloud Storage rule that automatically changes an object's storage class or deletes it as it ages.

**Lineage** — The record of where data came from and what was done to it. Dataform and Dataplex both produce it.

**Logical date** — The start of the data interval an Airflow run covers, not the wall-clock time it started. See [CHEATSHEET.md](CHEATSHEET.md).

**Looker** — A governed semantic layer and business-intelligence platform with its own modelling language.

**Looker Studio** — A browser-based dashboarding tool for building reports from BigQuery and other connectors.

## 📚 M

**Managed service** — A service where Google Cloud operates the infrastructure so you do not have to.

**Materialized view** — A pre-computed query result stored as a table, refreshed on a schedule or by streaming updates.

**Memorystore** — A managed in-memory Redis or Memcached cache for low-latency reads.

**Metadata** — Data about data: schemas, owners, lineage, freshness, row counts.

**Micro-batch** — A streaming pipeline that processes small batches of accumulated events together, trading latency for throughput.

**MLOps** — The practice of operating machine-learning systems: version control, testing, monitoring and retraining.

**Move to** — Cloud Storage's action that asynchronously copies or moves an object to another class, bucket or region.

**Multi-region** — A Cloud Storage location with three zones, offering higher availability at higher cost.

**Migrate to** — See Move to.

## 📚 N

**Nearline** — A Cloud Storage class at $0.010 per GB-month with a $0.01 per GB retrieval charge, for data read once or twice a month.

**Network latency** — The time for a packet to travel between two points.

**Network Private Access** — A way for VMs without public IPs to reach Google Cloud APIs through an internal route.

**Node pool** — A group of GKE nodes sharing a machine type and configuration.

**NoSQL** — A database category that does not use the relational table model, trading joins and constraints for horizontal scale.

## 📚 O

**OLAP (Online Analytical Processing)** — Queries that aggregate large historical datasets. Columnar warehouses are built for this.

**OLTP (Online Transaction Processing)** — Short, frequent, read-write operations on current data.

**Organization** — The top level of the Google Cloud resource hierarchy, governing one or many folders and projects.

**Org policy** — A constraint on where resources can be created and how they can be configured, applied at the organization or folder level.

**Organization policy constraint** — A single rule within an org policy, such as `constraints/gcp.resourceLocations` or `constraints/iam.disableServiceAccountKeyCreation`.

**Outlier** — A data point that differs markedly from the rest of the distribution, often from an error rather than real behaviour.

## 📚 P

**PCollection** — The Beam abstraction representing a distributed collection of elements. It is either bounded (batch) or unbounded (streaming).

**Partitioning (BigQuery)** — Dividing a table into date or timestamp segments so queries read only the segments they need.

**Personal Access Token (PAT)** — A long-lived token for the Cloud Logging API.

**PI (Personally Identifiable Information)** — Data that identifies a person: name, email, phone, address, national ID.

**PII** — See PI.

**Pipeline** — A sequence of connected processing steps that moves data from source to sink.

**Platform as a Service (PaaS)** — A managed application platform where the provider runs the infrastructure.

**PRunner** — The Beam runner. `DirectRunner` runs locally in one process; `DataflowRunner` runs the pipeline on Google Cloud.

**Predicate pushdown** — Pushing a filter down to the storage layer so unread rows are never fetched. BigQuery does this automatically for partition and clustering columns.

**PII redaction** — Replacing sensitive values with a mask or token. `redact_pii(value, keep_last=4)` in this course keeps the last four characters.

**Pub/Sub** — Google Cloud's managed publish/subscribe messaging service, used to decouple producers from consumers.

**Pull subscriber** — A consumer that polls for messages and acknowledges them. Required for exactly-once delivery.

**Push subscriber** — Pub/Sub delivers messages to an HTTPS endpoint you provide.

## 📚 Q

**Query plan** — The execution plan for a query, showing which stages read which bytes.

**Quota** — A limit on how much of a resource a project can consume, such as BigQuery slots per project or API requests per minute.

## 📚 R

**Reconciliation** — Comparing two sources of truth to confirm they agree, and repairing them when they do not.

**Region** — A geographic location containing multiple zones. Regional resources such as BigQuery datasets live in one.

**Regional** — A resource whose configuration applies across a whole region.

**Replication** — Keeping copies of data in more than one place for availability and performance.

**Residency** — See Data residency.

**Resource hierarchy** — The organization → folder → project structure that defines the blast radius of IAM and org policy.

**Retrospective** — A review after a launch that identifies what to keep, change and improve.

**Role** — A named bundle of permissions. IAM grants roles, not individual permissions.

**Row-level security** — Restricting which rows a user can see, based on a policy expression evaluated per row.

**RPO (Recovery Point Objective)** — The maximum acceptable amount of data loss, measured in time.

**RTO (Recovery Time Objective)** — The maximum acceptable time to restore service after a disruption.

**Runtime** — The execution environment for a container or function, such as Python 3.11.

## 📚 S

**Schema** — The definition of a table's columns and their types. It can be enforced or left flexible.

**Schema drift** — A change in the shape of incoming data, such as a new field or a changed type.

**Semantic layer** — A layer of business definitions, metrics and joins above the raw data. Looker is the course's example.

**Serverless** — A model where you deploy code without managing servers, and the platform scales it.

**Service account** — An identity that acts as a principal, used by workloads rather than people. Principals in IAM: `user:`, `group:`, `serviceAccount:`, `domain:`, `allUsers`, `allAuthenticatedUsers`.

**Service agent** — A service account that Google Cloud manages on your behalf to act as a service.

**Sink** — The destination of a data pipeline, such as a BigQuery table or a Pub/Sub topic.

**Slot** — A unit of BigQuery compute capacity, providing up to 5,000 queries per second. One slot-hour costs $0.06.

**Slot reservation** — A commitment to BigQuery capacity at a discount, in exchange for a minimum spend.

**Source** — Where data enters a pipeline.

**Split** — A parallel branch of a Dataflow pipeline.

**Streaming insert** — Writing rows into a BigQuery streaming buffer. Rows land in `_PARTITIONS` and are queryable within seconds.

**Streaming pipeline** — A pipeline that processes an unbounded, continuous flow of data.

**Synthetic data** — Artificially generated data used for testing or privacy, carrying the same statistical properties as real data.

## 📚 T

**Table** — A collection of rows with a defined schema in BigQuery.

**Task instance** — A single execution of one task in an Airflow DAG.

**Temporal table** — A table whose rows are versioned by a validity period, so a query can ask "what was true at time X".

**Terraform** — An infrastructure-as-code tool that declares Google Cloud resources in a configuration file. See the course's [chapter 2](../chapters/02-regions-zones-and-resource-hierarchy.md) for the resource hierarchy that Terraform manages.

**Throughput** — The volume of work completed per unit of time.

**Time to live (TTL)** — How long a resource or message survives before automatic deletion.

**Transaction** — A group of operations that either all succeed or all roll back.

**Trigger** — The event that causes a function or workflow to run.

**Type** — The kind of data a field holds: string, integer, boolean, timestamp, record, array.

## 📚 U

**Unified Billing** — Google Cloud's system that assigns every project's usage to a single billing account, with labels and budgets across projects.

**Unit of work** — A discrete amount of work that can be retried independently.

**Unpartitioned table** — A BigQuery table with no date partitions, where every query reads the whole table.

## 📚 V

**VPC (Virtual Private Cloud)** — A private network you define within a project, with its own subnets, routes and firewall rules.

**VPC-native** — A cluster where each node gets an IP from a VPC subnet rather than a range managed by the orchestrator.

**VPC Service Controls (VPC-SC)** — A perimeter that restricts which services and resources a principal can reach, preventing data exfiltration to outside the perimeter.

**Virtual Private Service Connect** — Connecting a VPC to a Google Cloud service without exposing traffic to the public internet.

**Vertex AI** — The managed platform for training, deploying and serving machine-learning models.

**Views** — A saved query that runs each time you reference it, reading the underlying table at query time.

## 📚 W

**Watermark** — The marker of how far a streaming pipeline believes it has processed a given event time. Data older than the watermark is late.

**Warm pool** — Pre-warmed Cloud Run instances that cut cold-start latency at the cost of idle capacity.

**Workflows** — A serverless, event-driven service for orchestrating API calls and Google Cloud services, each step defined in YAML.

**Write-ahead log** — A log of changes written before the change is applied, enabling replay and recovery.

## 📚 Z

**Zone** — A deployment location within a region, offering the lowest network latency between machines in it. `us-central1` has zones `us-central1-a`, `-b` and `-c`.

**Zonal** — A resource whose configuration applies to a single zone.

**Zero-downtime migration** — Moving a database or data set between systems without an interruption in service, often by replicating changes to the new target and cutting over.

**Zone-aware routing** — Sending traffic to the nearest healthy zone, and failing over when one becomes unavailable.

## 🔗 Related

| Document | Contents |
|---|---|
| [SETUP.md](SETUP.md) | Installation and the optional GCP path |
| [CHEATSHEET.md](CHEATSHEET.md) | Commands, cost formulas, decision tables |
| [FAQ.md](FAQ.md) | The questions students ask |
| [../interview/README.md](../interview/README.md) | The interview question bank |
