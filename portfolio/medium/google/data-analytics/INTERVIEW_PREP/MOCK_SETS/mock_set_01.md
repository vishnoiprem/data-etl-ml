# Mock Interview Set 1 - Full Simulation
## Round 1: Recruiter Screen (30 min)

### Interviewer: Technical Recruiter
### Focus: Baseline fit, motivation, communication

---

### Questions & Expected Answers

#### Q1: "Walk me through your background - 3 minutes."
**Expected:** 3-minute narrative covering: Current role, scale, key achievements, why Google Cloud Consulting, why now. Quantified metrics throughout.

#### Q2: "Describe your most complex migration project."
**Expected:** STAR - 140TB Teradata/Hadoop→BigQuery, 22 weeks, 16-person team, 62% cost reduction, 12 ML models enabled.

#### Q3: "BigQuery architecture in 2 minutes."
**Expected:** Serverless, storage/compute separation, Colossus/Dremel/Borg, slots, editions, partitioning/clustering, streaming.

#### Q4: "How do you handle a client who says GCP is too expensive?"
**Expected:** TCO framework, decompose hidden costs, Pilot with cost criteria, reference customer.

#### Q5: "What's your experience with SI partners?"
**Expected:** Co-delivery model, governance (scorecards, escalation), enablement (certification), commercial models.

#### Q6: "Why this role? Why Singapore?"
**Expected:** MAS-TRM expertise, APAC hub, FinServ focus, partner ecosystem, regulatory laboratory.

#### Q7: "Salary expectations / Notice period / Location preference"
**Expected:** Market-aligned, flexible on location (Singapore-based), standard notice.

---

### Recruiter Evaluation Criteria
| Dimension | Pass Signal |
|-----------|-------------|
| **Communication** | Clear, structured, quantified, consultative tone |
| **Technical Baseline** | BQ architecture correct, migration phases named |
| **Consulting DNA** | Client-first language, Pilot approach, partner awareness |
| **Motivation** | Specific to Google Cloud Consulting, not generic |
| **Culture Fit** | Humility, learning agility, "I don't know but..." |

---

## Round 2: Technical Deep-Dive (60 min)

### Interviewer: Senior Data Architect
### Focus: Technical depth at scale, architecture decisions, tradeoffs

---

### Part A: Live Coding - SQL (20 min)

#### Challenge 1: Customer 360 Query
```sql
-- Tables: customers (10M), orders (500M), events (2B)
-- Requirements: Latest order per customer, event count last 30d, handle late events
-- Optimize for 500M+ rows

WITH latest_orders AS (
  SELECT customer_id, order_id, order_ts, order_value,
         ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_ts DESC) AS rn
  FROM `project.dataset.orders`
  WHERE order_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 YEAR)
),
recent_events AS (
  SELECT customer_id, COUNT(*) AS event_count_30d
  FROM `project.dataset.events`
  WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    AND _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY customer_id
)
SELECT c.customer_id, c.email, c.tier,
       o.order_id, o.order_ts, o.order_value,
       COALESCE(e.event_count_30d, 0) AS event_count_30d
FROM `project.dataset.customers` c
LEFT JOIN latest_orders o ON c.customer_id = o.customer_id AND o.rn = 1
LEFT JOIN recent_events e ON c.customer_id = e.customer_id
WHERE c.status = 'ACTIVE';
```

**Optimization Discussion:** Partition by order_ts/event_ts, cluster by customer_id, MATERIALIZED VIEW for latest_orders, BI Engine for dashboard.

#### Challenge 2: Deduplication with Late Data
```sql
-- Events table with duplicates, late-arriving data
-- Deduplicate by event_id, keep latest, handle 10min late arrival

SELECT * EXCEPT(rn)
FROM (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY event_id 
           ORDER BY event_ts DESC, _PARTITIONTIME DESC
         ) AS rn
  FROM `project.dataset.events`
  WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY)  -- 2-day lookback for late data
)
WHERE rn = 1;
```

---

### Part B: Live Coding - Python/Beam (15 min)

#### Challenge: Dataflow DoFn for Pub/Sub → BigQuery with Dead Letter
```python
import apache_beam as beam
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.io.gcp.pubsub import ReadFromPubSub
import json
import logging

class ValidateAndEnrich(beam.DoFn):
    def __init__(self, schema, side_input_ref):
        self.schema = schema
        self.side_input_ref = side_input_ref
    
    def process(self, element, reference_data=beam.pvalue.AsDict(side_input_ref)):
        try:
            record = json.loads(element.decode('utf-8'))
            
            # Schema validation
            for field in self.schema:
                if field['name'] not in record:
                    raise ValueError(f"Missing field: {field['name']}")
            
            # Enrichment with side input
            customer_id = record.get('customer_id')
            if customer_id in reference_data:
                record['customer_tier'] = reference_data[customer_id]['tier']
                record['customer_region'] = reference_data[customer_id]['region']
            
            # Add processing metadata
            record['_processed_ts'] = beam.utils.timestamp.Timestamp.now().to_rfc3339()
            record['_source'] = 'pubsub'
            
            yield beam.pvalue.TaggedOutput('valid', record)
            
        except Exception as e:
            yield beam.pvalue.TaggedOutput('dead_letter', {
                'original_message': element.decode('utf-8'),
                'error': str(e),
                'timestamp': beam.utils.timestamp.Timestamp.now().to_rfc3339()
            })

# Pipeline
with beam.Pipeline(options=options) as p:
    reference_data = (
        p 
        | 'Read Reference' >> beam.io.ReadFromBigQuery(query='SELECT customer_id, tier, region FROM `project.ref.customers`')
        | 'To Dict' >> beam.Map(lambda x: (x['customer_id'], x))
    )
    
    (p 
     | 'Read PubSub' >> ReadFromPubSub(topic='projects/project/topics/events')
     | 'Validate & Enrich' >> beam.ParDo(ValidateAndEnrich(SCHEMA, reference_data)).with_outputs('valid', 'dead_letter')
     | 'Write Valid to BQ' >> WriteToBigQuery(
            'project:dataset.events',
            schema=BQ_SCHEMA,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
            method="STREAMING_INSERTS"
        )
    )
    # Dead letter to separate table
    dead_letters | 'Write DLQ' >> WriteToBigQuery('project:dataset.events_dlq', ...)
```

---

### Part C: System Design (25 min)

#### Prompt: "Design real-time fraud detection on GCP"
**Requirements:**
- 100K events/sec, <100ms latency
- Features from BigQuery (customer profile) + Firestore (real-time balance)
- Model in Vertex AI, explainable predictions
- Audit trail for compliance

#### Expected Architecture:
```
Kafka/Event Source → Pub/Sub → Dataflow Streaming → Vertex AI Online Prediction → BigQuery → Alerting
                                    ↓                              ↓
                              Feature Store (online)          Audit Logs → Chronicle
                                    ↓
                              BigQuery (offline features) ← Dataflow batch feature refresh
```

**Key Discussion Points:**
- Pub/Sub partitioning by customer_id for ordering
- Dataflow: Fixed windows (1min) + allowed lateness (5min) for exactly-once
- Feature Store: Online serving (<10ms), offline for training, sync via Dataflow
- Vertex AI: Online endpoint (autoscaling, A/B), Model Monitoring (drift)
- BigQuery: Partition by event_date, cluster by customer_id, audit table
- Compliance: VPC-SC, CMEK, Column-level lineage, RLS for PII

---

### Technical Evaluation Rubric
| Dimension | 1 - Below | 2 - Meets | 3 - Exceeds | 4 - Exceptional |
|-----------|-----------|-----------|-------------|-----------------|
| **SQL Fluency** | Syntax errors, no optimization | Works, basic partition | Clean, partitioned, clustered, EXPLAIN analysis | Innovative patterns, teaches interviewer |
| **Beam/Python** | Doesn't compile, no dead letter | Works, basic validation | Clean DoFn, side inputs, tagged outputs, error handling | Production patterns, monitoring built-in |
| **Architecture** | Missing components, no tradeoffs | Complete, standard patterns | Scalable, cost-aware, security baked in | Novel approach, anticipates scale issues |
| **GCP Services** | Names services only | Knows config options | Knows limits, quotas, integration points | Contributes to product feedback |

---

## Round 3: Consulting Simulation (45 min)

### Interviewer: Practice Lead
### Focus: Client-facing, stakeholder management, negotiation

---

### Scenario 1: Executive Presentation (15 min)
> **"You have 10 minutes to present a $2M migration proposal to a skeptical CFO. They're worried about: security, cost overrun, team capability. Your slides: 3 max. Go."**

**Evaluation:**
- Executive summary FIRST (business outcomes > technical details)
- Addresses all 3 objections proactively
- Confident but not arrogant
- Clear ask (Pilot, 4 weeks, Go/No-Go)

---

### Scenario 2: Scope Creep Negotiation (15 min)
> **"Customer adds 5 new requirements mid-project. Timeline fixed. Budget fixed. Roleplay: I'm the customer PM. Convince me to defer or pay more."**

**Evaluation:**
- Data-driven (impact analysis)
- MoSCoW prioritization
- Alternative proposals (Phase 2, descoping)
- Preserves relationship
- Clear escalation path

---

### Scenario 3: Technical Disagreement (15 min)
> **"Your architect recommends Dataflow for streaming. Customer's lead engineer insists on self-managed Kafka on GKE. You have 10 minutes to align."**

**Evaluation:**
- Seeks to understand FIRST ("Help me understand your constraints...")
- Presents tradeoffs objectively (table: ops burden, cost, exactly-once, TCO)
- Finds common ground (Pilot both? Hybrid?)
- Documents decision (ADR)

---

## Round 4: Presentation (30 min + 15 Q&A)

### Interviewer: Panel (Architect + Practice Lead + Customer-facing)
### Focus: Presentation delivery, architecture clarity, Q&A composure

---

### Presentation Topic: "Enterprise Data Platform Migration - Lessons from 140TB FinServ Migration"

**Structure (20 min):**
1. Business Context (2 min) - Pain, drivers, mandates
2. Current State (2 min) - Architecture diagram (draw live)
3. Target State (3 min) - Architecture diagram (draw live)
4. Migration Approach (3 min) - 4 phases, timeline, validation
5. Security/Governance (2 min) - VPC-SC, CMEK, Dataplex, MAS-TRM
6. Challenges & Solutions (3 min) - Top 3 technical challenges
7. Results (3 min) - Quantified metrics (cost, performance, adoption)
8. Reusable IP (2 min) - Runbook, Terraform, Templates, Packs

**Whiteboard (5 min):** Draw target architecture from memory

**Q&A (15 min):** See qa_prep.md for anticipated questions

---

### Presentation Evaluation
| Dimension | Weight | Pass Signal |
|-----------|--------|-------------|
| **Storytelling** | 25% | Business outcomes first, technical depth on demand |
| **Whiteboard** | 20% | Clear, labeled, correct services, tradeoffs noted |
| **Technical Depth** | 25% | Accurate services, configs, limits, integration |
| **Business Acumen** | 15% | TCO, ROI, partner model, scaling delivery |
| **Q&A Composure** | 15% | Structured answers, evidence, "I don't know but..." |

---

## Round 5: Cognitive/Behavioral (60 min)

### Interviewer: Cross-functional (Director + HR + Peer)
### Focus: Googleyness, leadership, Singapore context, technical fundamentals

---

### Googleyness (15 min) - See star_answers.md STAR 1-6
1. "Tell me about a time you failed."
2. "How do you handle not knowing an answer?"
3. "Describe influencing without authority."
4. "How do you prioritize when everything is urgent?"
5. "What does 'focus on the user' mean in consulting?"

### Leadership/Strategy (15 min)
1. "How do you build a high-performing consulting team?"
2. "How do you scale delivery through partners?"
3. "Walk me through your practice P&L thinking."

### Singapore/APAC Context (10 min) - See singapore_context.md
1. "How does MAS-TRM affect your architecture?"
2. "Data residency strategy for multi-country?"
3. "Partner ecosystem in Singapore?"

### Technical Fundamentals (10 min) - See technical_fundamentals.md
Rapid-fire: BQ, Dataflow, Dataproc, Composer, Vertex AI, Security

### Objection Handling (10 min) - See objection_handling.md
Roleplay 2 scenarios from: Cost, Security, Lock-in, Timeline, Partner, DIY

---

## Overall Mock Set 1 Scoring

| Round | Weight | Pass Threshold |
|-------|--------|----------------|
| Round 1: Recruiter | 10% | Strong Hire / Hire |
| Round 2: Technical | 30% | ≥3.0 avg (1-4 scale) |
| Round 3: Consulting | 20% | ≥3.0 avg |
| Round 4: Presentation | 25% | ≥3.5 avg |
| Round 5: Cognitive | 15% | No values veto, ≥3.0 avg |

**Overall: Hire if all rounds pass, no values veto, technical ≥3.0**

---

## Debrief Template (Post-Mock)

### Strengths Observed:
1. ________________________________________
2. ________________________________________
3. ________________________________________

### Development Areas:
1. ________________________________________
2. ________________________________________
3. ________________________________________

### Specific Action Items:
1. ________________________________________ (Owner: You, Due: _____)
2. ________________________________________ (Owner: You, Due: _____)
3. ________________________________________ (Owner: You, Due: _____)

### Next Mock Focus: ________________________________________

---

*Run this mock with a colleague. Record yourself. Debrief honestly. Repeat until consistent pass.*