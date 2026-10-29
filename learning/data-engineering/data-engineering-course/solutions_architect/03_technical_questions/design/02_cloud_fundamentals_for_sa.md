# 02 — Cloud Fundamentals for Solutions Architects

> **Lesson 2 of 7 — Technical Questions for SAs** · ~30 min

The 6 service categories every SA must know, the AWS/GCP/
Azure comparison, and the 5 things that differ between
hyperscalers in practice. This is reference material —
read it once, then come back as needed.

---

## 1. The 6 service categories

Every cloud service falls into one of 6 categories. Every
SA interview, regardless of company, tests the candidate's
fluency in at least 4 of the 6.

| # | Category | What it is | Examples (AWS / GCP / Azure) |
|---|---|---|---|
| 1 | **Compute** | Virtual machines, containers, serverless | EC2 / Compute Engine / Azure VMs; Lambda / Cloud Functions / Azure Functions; ECS/EKS / GKE / AKS |
| 2 | **Storage** | Object, block, file storage | S3 / Cloud Storage / Blob Storage; EBS / Persistent Disk / Managed Disks; EFS / Filestore / Azure Files |
| 3 | **Database** | Relational, NoSQL, in-memory | RDS/Aurora / Cloud SQL / Azure Database; DynamoDB / Firestore / Cosmos DB; ElastiCache / Memorystore / Cache for Redis |
| 4 | **Networking** | VPC, load balancing, CDN | VPC / VPC / VNet; ALB/NLB / Cloud Load Balancing / Azure Load Balancer; CloudFront / Cloud CDN / Azure CDN |
| 5 | **Messaging** | Queues, topics, event buses | SQS/SNS / Pub/Sub / Service Bus; EventBridge / Eventarc / Event Grid; Kinesis / Pub/Sub / Event Hubs |
| 6 | **Security & Identity** | IAM, KMS, secrets | IAM / IAM / Entra ID; KMS / Cloud KMS / Key Vault; Secrets Manager / Secret Manager / Key Vault |

The 6 categories are the *spine* of the cloud. Every
architecture you design uses 4-6 of the 6 categories.
Every tradeoff question is about choosing between
options in one of the 6 categories.

---

## 2. The compute comparison

The 3 compute models and how they differ:

| Model | When to use | Pros | Cons | Examples |
|---|---|---|---|---|
| **Virtual machines** | Long-running workloads, custom OS, custom runtime | Full control; predictable cost; any OS/runtime | You manage the OS, scaling, patching | EC2, Compute Engine, Azure VMs |
| **Containers** | Microservices, multi-cloud portability, complex runtime | Portable; consistent across environments; orchestrators handle scaling | You manage the orchestrator (or pay for managed) | ECS, EKS, GKE, AKS |
| **Serverless** | Event-driven, spiky workloads, short-lived tasks | Auto-scaling; pay per invocation; no ops | Cold start; runtime limits; vendor lock-in | Lambda, Cloud Functions, Azure Functions |

The 3 models are not interchangeable. The choice depends
on the workload:

- **Long-running, stateful, custom runtime** → VMs.
- **Microservices, multi-cloud, complex runtime** → Containers.
- **Event-driven, spiky, short-lived** → Serverless.

The interview question is usually: "Given [workload],
which model and why?" The answer is the model that
matches the workload's characteristics, with the
tradeoff named.

---

## 3. The storage comparison

The 3 storage types and how they differ:

| Type | When to use | Pros | Cons | Examples |
|---|---|---|---|---|
| **Object** | Unstructured data, backups, data lakes, static assets | Cheap; virtually unlimited; durable | Higher latency; no filesystem semantics | S3, Cloud Storage, Blob Storage |
| **Block** | Database storage, OS disks | Low latency; consistent performance | Limited size; tied to a single VM | EBS, Persistent Disk, Managed Disks |
| **File** | Shared filesystem, lift-and-shift apps | POSIX semantics; shared access | More expensive than object; less scalable than object | EFS, Filestore, Azure Files |

The interview question is usually: "Given [workload],
which type and why?" The answer:

- **Unstructured, accessed by many services, infrequently
  read** → Object.
- **Database, OS disk, single-VM-attached** → Block.
- **Shared filesystem, multi-VM-attach, lift-and-shift**
  → File.

---

## 4. The database comparison

The 4 database types and how they differ:

| Type | When to use | Pros | Cons | Examples |
|---|---|---|---|---|
| **Relational (RDBMS)** | Transactional, structured, strong consistency | ACID; SQL; mature tooling | Hard to scale horizontally; fixed schema | RDS/Aurora, Cloud SQL, Azure SQL |
| **Key-value / Document (NoSQL)** | High-throughput, flexible schema, low latency | Horizontally scalable; flexible schema | No SQL; eventual consistency by default; no joins | DynamoDB, Firestore, Cosmos DB |
| **Wide-column** | Time-series, write-heavy, very high scale | Massive scale; cheap writes | Limited query patterns; complex ops | Cassandra, Bigtable, HBase |
| **In-memory** | Caching, session, real-time | Sub-millisecond latency; high throughput | Volatile (unless persisted); expensive | ElastiCache, Memorystore, Cache for Redis |

The interview question is usually: "Given [workload],
which type and why?" The answer:

- **Transactional, structured, strong consistency, complex
  queries** → RDBMS.
- **High-throughput, flexible schema, single-digit-ms
  latency** → Key-value / Document.
- **Time-series, write-heavy, massive scale** → Wide-column.
- **Caching, session, sub-millisecond** → In-memory.

---

## 5. The networking comparison

The 4 networking primitives and how they differ:

| Primitive | When to use | Examples |
|---|---|---|
| **VPC / VNet** | Network isolation; private subnets; service-to-service communication | VPC, VPC, VNet |
| **Load balancer (L7)** | HTTP/HTTPS routing, path-based routing, SSL termination | ALB, Cloud Load Balancing (HTTP), App Gateway |
| **Load balancer (L4)** | TCP/UDP routing, low-latency, high-throughput | NLB, TCP/UDP Load Balancing, Load Balancer (Standard) |
| **CDN** | Static asset caching, edge acceleration, global distribution | CloudFront, Cloud CDN, Azure CDN |

The interview question is usually: "Given [workload],
which primitives and why?" The answer:

- **Private network for service-to-service** → VPC.
- **HTTP routing with SSL termination** → L7 LB.
- **TCP/UDP routing with low latency** → L4 LB.
- **Global static asset distribution** → CDN.

---

## 6. The messaging comparison

The 3 messaging primitives and how they differ:

| Primitive | When to use | Pros | Cons | Examples |
|---|---|---|---|---|
| **Queue** | Decoupling producers and consumers; load leveling; async work | Reliable delivery; consumer-side scaling | No broadcasting; no replay | SQS, Pub/Sub (with subscription), Service Bus Queue |
| **Topic / Pub-Sub** | Fan-out to multiple consumers; event-driven architectures | Multiple consumers; loose coupling | No ordering guarantee (depending); consumer must handle duplicates | SNS, Pub/Sub, Service Bus Topic |
| **Event bus / streaming** | Event sourcing, real-time processing, replay | Ordering; replay; long retention | More complex; higher cost | EventBridge, Eventarc, Event Grid; Kinesis, Pub/Sub (with retention), Event Hubs |

The interview question is usually: "Given [workload],
which primitive and why?" The answer:

- **Decouple producer from consumer, async work** → Queue.
- **Fan-out to multiple consumers, event-driven** → Topic.
- **Real-time processing, event sourcing, replay** →
  Event bus / streaming.

---

## 7. The 5 things that differ between hyperscalers

The 5 things that AWS, GCP, and Azure do *differently* in
practice — beyond the service-name translations.

| # | Difference | What it means in practice |
|---|---|---|
| 1 | **Pricing model** | AWS charges per-second for Lambda (after the first second), GCP charges per-100ms. Azure has hybrid benefit for Windows licenses. The 10-20% cost differences are real. |
| 2 | **Service depth** | AWS has more services (~200+ vs ~100+ at GCP, ~200+ at Azure). GCP tends to be deeper in data/ML. Azure tends to be deeper in enterprise integration. |
| 3 | **Identity model** | AWS uses IAM with policies. GCP uses IAM with roles. Azure uses Entra ID (was Azure AD) with role-based access. The mental models differ enough that a multi-cloud architect needs to know all 3. |
| 4 | **Networking model** | AWS uses VPC with private subnets, NAT gateways, internet gateways. GCP uses VPC with shared VPC, private Google access. Azure uses VNet with subnets, NSGs, service endpoints. |
| 5 | **Compliance posture** | AWS has the most certifications (FedRAMP High, IL5, etc.). Azure is the natural choice for Microsoft-heavy enterprises. GCP is strong in healthcare (HIPAA) and data analytics. |

The 5 differences are *real* and matter for design
decisions. A senior SA who claims "all clouds are the
same" is signaling inexperience.

---

## 8. The "compare X vs Y" interview pattern

A common SA interview question: "Compare S3 vs Cloud
Storage vs Blob Storage for [workload]." The 4-part
answer structure:

1. **The basic comparison.** "All three are object
   storage with 11 nines of durability and similar
   pricing."
2. **The differentiation.** "S3 has the deepest feature
   set (S3 Glacier, S3 Intelligent-Tiering, etc.). Cloud
   Storage has simpler IAM and tighter integration with
   BigQuery. Blob Storage has tight integration with
   Azure services and hybrid benefits."
3. **The choice for the workload.** "For a data lake
   with multi-cloud replication, S3 is the standard. For
   a GCP-native analytics stack, Cloud Storage is the
   natural choice. For a Microsoft-heavy enterprise,
   Blob Storage is the natural choice."
4. **The tradeoff.** "S3 has the highest feature ceiling
   but the steepest learning curve. Cloud Storage is
   simpler but has fewer features. Blob Storage is the
   most enterprise-friendly but the most expensive."

The 4-part answer is the senior SA move. A junior SA
gives 1-2 parts; a senior SA gives all 4.

---

## 9. The 6 service categories in an architecture

A typical architecture uses 4-6 of the 6 service
categories. The example below (a real-time analytics
pipeline) uses all 6:

| Category | Service | Why |
|---|---|---|
| **Compute** | Lambda for ingestion, ECS for the streaming service | Lambda for spiky event ingestion; ECS for the long-running service |
| **Storage** | S3 for the data lake, EBS for the streaming service | S3 for cheap, durable storage; EBS for low-latency block storage |
| **Database** | DynamoDB for the feature store, RDS for the metadata | DynamoDB for low-latency feature lookup; RDS for relational metadata |
| **Networking** | VPC, ALB, CloudFront | VPC for network isolation; ALB for L7 routing; CloudFront for global distribution |
| **Messaging** | Kinesis for the streaming pipeline, SQS for the async work | Kinesis for ordered, replayable events; SQS for decoupled async work |
| **Security & Identity** | IAM, KMS, Secrets Manager | IAM for access control; KMS for encryption; Secrets Manager for credentials |

The 6 categories are the *checklist* for any architecture
design. A senior SA runs through the checklist mentally
on every design.

---

## Try it

For each of the 6 service categories, write down:

1. **The 2-3 services in this category you'd use for a
   real-time analytics pipeline.**
2. **The 1 service you'd avoid and why.**
3. **The tradeoff you'd name to the customer.**

The 6 categories × 3 answers = 18 specific things to
know. The investment is 30-60 minutes; the return is the
ability to design any architecture in your sleep.

After you've written the 18 answers, do the same
exercise for a different architecture (e.g., a batch
processing pipeline, a transactional e-commerce system).
The second pass will surface the patterns that apply
across architectures — those are the durable things to
internalize.
