# 07 — When to Use What: The 30-Second Architecture Decision

> **Lesson 7 of 7 — Technical Questions for SAs** · ~15 min

A real decision tree (mermaid `graph TD`) for "given X
requirement, use Y service." The decision tree covers the
6 most common service categories from Lesson 02: compute,
storage, database, networking, messaging, and security.

This lesson is the *practice* of Lesson 06. The framework
is the theory; the decision tree is the application.

---

## 1. The decision tree (compute)

```mermaid
graph TD
    A[What's the workload?] --> B{Long-running<br/>> 1 hour?}
    B -->|Yes| C{Need custom OS<br/>or runtime?}
    B -->|No| D{Event-driven<br/>spiky traffic?}

    C -->|Yes| E[VM<br/>EC2 / Compute Engine / Azure VMs]
    C -->|No| F{Stateful connections<br/>to databases?}

    F -->|Yes| G[Containers<br/>ECS/EKS / GKE / AKS]
    F -->|No| H[Serverless or Containers<br/>depending on team skills]

    D -->|Yes| I[Serverless<br/>Lambda / Cloud Functions / Azure Functions]
    D -->|No| J{Multi-cloud<br/>portability?}

    J -->|Yes| K[Containers<br/>on multi-cloud K8s]
    J -->|No| L[VM or Containers<br/>depending on team skills]
```

The compute decision tree has 3 main branches:
- **Long-running** → VM or Containers.
- **Event-driven, spiky** → Serverless.
- **Mid-range, multi-cloud** → Containers.

The decision at each node is a 1-question test:
"Long-running? Stateful? Spiky? Multi-cloud?" The
combination of answers points to the right compute model.

---

## 2. The decision tree (database)

```mermaid
graph TD
    A[What's the workload?] --> B{Need SQL<br/>and joins?}

    B -->|Yes| C{Strong consistency<br/>required?}
    B -->|No| D{Sub-10ms<br/>latency required?}

    C -->|Yes| E{Scale?<br/>> 10TB?}
    C -->|No| F[RDS / Cloud SQL / Azure SQL<br/>single-region]

    E -->|Yes| G[Aurora / Spanner / Cosmos DB<br/>multi-region capable]
    E -->|No| H[RDS / Cloud SQL / Azure SQL<br/>with read replicas]

    D -->|Yes| I{Throughput?<br/>> 100k reads/sec?}

    I -->|Yes| J[DynamoDB / Cosmos DB / Firestore<br/>global tables for multi-region]
    I -->|No| K[ElastiCache Redis<br/>or DynamoDB on-demand]

    D -->|No| L{Time-series<br/>write-heavy?}

    L -->|Yes| M[Wide-column<br/>Cassandra / Bigtable / HBase]
    L -->|No| N[Document DB<br/>MongoDB / DocumentDB / Firestore]
```

The database decision tree has 3 main branches:
- **SQL + strong consistency** → RDS / Aurora.
- **Sub-10ms latency, no SQL** → DynamoDB / Redis.
- **Time-series** → Cassandra / Bigtable.

---

## 3. The decision tree (storage)

```mermaid
graph TD
    A[What kind of data?] --> B{Unstructured<br/>files?}
    B -->|Yes| C{Access pattern?}
    B -->|No| D{Database<br/>storage?}

    C -->|Frequent reads<br/>global access| E[Object + CDN<br/>S3 + CloudFront]
    C -->|Archival<br/>rare access| F[Object Cold Tier<br/>S3 Glacier / Archive]
    C -->|Shared filesystem<br/>multi-VM| G[File<br/>EFS / Filestore / Azure Files]

    D -->|Single VM<br/>OS disk| H[Block<br/>EBS / Persistent Disk / Managed Disks]
    D -->|Database<br/>storage| I[Managed DB<br/>Aurora / RDS / Cloud SQL]
    D -->|Shared<br/>database| J[Shared Block<br/>EBS multi-attach / Premium SSD v2]
```

The storage decision tree has 3 main branches:
- **Unstructured files** → Object (S3) + optional CDN.
- **Database storage** → Managed DB or block storage.
- **Shared filesystem** → File storage (EFS).

---

## 4. The decision tree (messaging)

```mermaid
graph TD
    A[What's the use case?] --> B{Decouple producer<br/>from consumer?}

    B -->|Yes| C{Ordering<br/>required?}

    C -->|Yes| D{Replay<br/>required?}
    C -->|No| E[Queue<br/>SQS / Service Bus Queue]

    D -->|Yes| F[Streaming<br/>Kinesis / Pub/Sub / Event Hubs]
    D -->|No| G[Queue with FIFO<br/>SQS FIFO / Pub/Sub ordering]

    B -->|No| H{Multiple<br/>consumers?}

    H -->|Yes| I[Topic<br/>SNS / Pub/Sub / Service Bus Topic]
    H -->|No| J[Direct API call<br/>or HTTP request]
```

The messaging decision tree has 4 main branches:
- **Decouple + ordering + replay** → Streaming (Kinesis).
- **Decouple + no ordering** → Queue (SQS).
- **Fan-out to multiple consumers** → Topic (SNS).
- **No decoupling needed** → Direct API call.

---

## 5. The decision tree (networking)

```mermaid
graph TD
    A[What do you need?] --> B{Network isolation<br/>required?}

    B -->|Yes| C[VPC / VNet<br/>with subnets]
    B -->|No| D{Public-facing<br/>HTTP service?}

    C --> E{Multi-region<br/>connectivity?}

    E -->|Yes| F[Transit Gateway<br/>or Interconnect]
    E -->|No| G[VPC Peering<br/>or Private Link]

    D -->|Yes| H{Need path-based<br/>routing?}

    H -->|Yes| I[L7 Load Balancer<br/>ALB / App Gateway]
    H -->|No| J[L4 Load Balancer<br/>NLB / TCP LB]

    D -->|No| K{Global static<br/>asset distribution?}

    K -->|Yes| L[CDN<br/>CloudFront / Cloud CDN / Azure CDN]
    K -->|No| M[No networking needed<br/>direct service call]
```

The networking decision tree has 3 main branches:
- **Network isolation** → VPC + subnets.
- **Public HTTP service** → L7 or L4 load balancer.
- **Global static distribution** → CDN.

---

## 6. The decision tree (security)

```mermaid
graph TD
    A[What do you need to protect?] --> B{Data at rest?}

    B -->|Yes| C{Compliance<br/>requirement?}

    C -->|FIPS 140-2<br/>Level 3| D[HSM<br/>CloudHSM / Azure Dedicated HSM]
    C -->|Standard<br/>FIPS 140-2 Level 2| E[KMS<br/>AWS KMS / Cloud KMS / Key Vault]

    B -->|No| F{Secrets<br/>management?}

    F -->|Yes| G[Secrets Manager<br/>AWS / Azure Key Vault / Secret Manager]
    F -->|No| H{PII detection?}

    H -->|Yes| I[Macie / Cloud DLP / Purview]
    H -->|No| J{IAM<br/>only?}

    J -->|Yes| K[IAM<br/>AWS / GCP / Entra ID]
    J -->|No| L[Multiple services<br/>based on workload]
```

The security decision tree has 3 main branches:
- **Data at rest + high compliance** → HSM.
- **Data at rest + standard compliance** → KMS.
- **Secrets management** → Secrets Manager.

---

## 7. The 30-second decision process

The decision tree is the *reference*. The 30-second
decision process is the *practice*. For any architecture
decision in an interview, the 5-step process:

1. **Identify the category.** (Compute, database,
   storage, networking, messaging, or security.)
2. **Identify the constraints.** (Latency, consistency,
   scale, cost, compliance.)
3. **Walk the decision tree.** (Follow the branches
   from the constraint to the service.)
4. **Name the alternative.** (What would you have used
   if the constraint was different?)
5. **Name the tradeoff.** (What's given up by choosing
   this service?)

The 5-step process takes 30-45 seconds in an interview.
The candidate who can produce it consistently passes
the round.

---

## 8. A worked example: 30-second decision

The question: "We're building a real-time fraud detection
pipeline with 1M transactions/day, 100ms p99 latency
requirement, and the data must be encrypted at rest with
FIPS 140-2 Level 3 compliance for our financial services
customer."

### Step 1: Identify the category

Multiple categories. The architecture has:
- Compute (for the fraud detection model)
- Database (for the transaction history and the feature
  store)
- Messaging (for the event stream)
- Security (for the encryption)

### Step 2: Identify the constraints

- **Latency:** 100ms p99 (sub-100ms end-to-end).
- **Consistency:** Strong consistency for the
  transaction history.
- **Compliance:** FIPS 140-2 Level 3 (HSM).
- **Scale:** 1M transactions/day = ~12 transactions/sec
  average, ~100/sec peak (manageable).

### Step 3: Walk the decision tree

- **Compute:** 100ms p99 latency, custom ML model → EKS
  with the model deployed as a service.
- **Database (transaction history):** SQL + strong
  consistency → RDS or Aurora with KMS encryption.
- **Database (feature store):** Sub-10ms latency →
  DynamoDB with on-demand mode.
- **Messaging:** Real-time, ordered, replayable → Kinesis
  or Pub/Sub.
- **Security (encryption at rest):** FIPS 140-2 Level 3 →
  CloudHSM, not just KMS.

### Step 4: Name the alternative

- If the latency requirement was 1s instead of 100ms,
  Lambda could replace EKS for the model.
- If the consistency was eventual, DynamoDB alone (no
  RDS) could handle the transaction history.

### Step 5: Name the tradeoff

- CloudHSM is more expensive than KMS. If the customer
  doesn't need FIPS 140-2 Level 3, KMS is sufficient.
- EKS has more operational overhead than Lambda. If the
  latency budget allowed 1s, Lambda would be cheaper
  and simpler.

The 5-step answer takes 30-45 seconds. The candidate who
can produce it consistently is the senior SA.

---

## 9. The 6 questions to ask before any decision

For any architecture decision, ask these 6 questions
first. The answers drive the decision tree:

1. **What's the latency requirement?** (Sub-millisecond,
   milliseconds, seconds, minutes?)
2. **What's the consistency requirement?** (Strong,
   eventual, read-after-write?)
3. **What's the scale?** (Requests/sec, data volume,
   growth rate?)
4. **What's the cost ceiling?** (Dollars/month,
   dollars/million requests?)
5. **What are the compliance requirements?** (PCI, HIPAA,
   FIPS 140-2 Level X, GDPR?)
6. **What's the team's operational capacity?** (How many
   SREs? What's their skill set?)

The 6 questions are the *checklist* before any decision.
The decision tree is the *output* of the checklist.

---

## 10. The 5 things the decision tree signals

If you use this decision tree in an interview, the 5
things you signal:

1. **You have a framework.** You can produce a consistent
   answer across categories.
2. **You know the services.** You can map any constraint
   to a specific service.
3. **You think about tradeoffs.** You name the alternative
   and the tradeoff.
4. **You think about constraints first.** The decision
   is driven by the customer's needs, not by your
   preference.
5. **You can adapt.** When the customer introduces a new
   constraint, you can re-walk the tree.

The 5 signals are the senior SA move. The decision tree
is the *practice*; the signals are the *outcome*.

---

## Try it

For each of the 6 service categories, pick a 2-3
paragraph scenario and walk the decision tree:

1. **Compute:** "Design the compute layer for a video
   transcoding service with 10k videos/day, each 1-hour
   long, 4K resolution, processed in batch at midnight."
2. **Database:** "Design the database for a social media
   app with 10M users, 1M posts/day, sub-50ms read
   latency for the home feed."
3. **Storage:** "Design the storage for a photo backup
   service with 1M users, 100GB/user, accessed
   infrequently."
4. **Messaging:** "Design the messaging for an order
   processing pipeline with 100k orders/day, ordered
   by customer_id, replayable for 30 days for audit."
5. **Networking:** "Design the networking for a multi-
   region SaaS with users in US, EU, Asia, 99.99%
   availability."
6. **Security:** "Design the encryption for a healthcare
   data lake with HIPAA-adjacent data, accessed by
   internal data scientists only."

Run each 2-3 times. By the 3rd time, the decision tree
will be in muscle memory. That's the 30-second decision
round of any architecture interview.
