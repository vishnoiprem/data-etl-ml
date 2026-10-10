# 92. Datadog

- **Role:** ML Engineer (Observability / AIOps)
- **Tech stack:** Python, Go, Java, PyTorch, TensorFlow, Kafka, Flink, Kubernetes
- **Comp band:** $200K-$600K (L3-L6)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds (5 stages)

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, team fit (AIOps, Log Analytics, Metrics, Watchdog). | 1 week | ~50% advance |
| 2. **Technical phone screen (60 min)** | 1 coding + 1 system design (observability). | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds in 1 day)** | 2 coding → 1 system design → 1 ML (forecasting/anomaly detection). | 1 day | ~30% advance |
| 4. **Hiring committee** | Packet + calibration. | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp negotiation. | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about a large-scale ML system you built."
**Answer:** STAR with scale numbers. Example: "I built a real-time anomaly detection system for a 10K-host infrastructure. It ingests 1M metrics/sec, uses a Prophet + LSTM ensemble, and pages on 0.1% false positive rate. The key technical decision: I moved from batch (5-min lag) to streaming (1-sec lag) using Kafka + Flink, which reduced the MTTD by 12×."
**Tip:** Datadog values scale + observability. Mention specific throughput, latency, and MTTD/MTTR numbers.

### Q1.2: "Why Datadog?"
**Answer:** Specific bet + test + disagreement. "I want to work on the Watchdog team because the AI for ops thesis is the most important bet in 2026. The bet: as systems get more complex, the human on-call needs an AI co-pilot, not just dashboards. The 1 thing I'd test: whether LLM-based root cause analysis (RCA) can match human accuracy on the top 100 incident types. The 1 thing I disagree with: I think Datadog is too conservative on the LLM side — the Bits AI assistant should be allowed to take actions (e.g., restart a service), not just suggest."
**Tip:** Reference Bits AI + Watchdog + the AI for ops roadmap.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Given a stream of (timestamp, metric_value) pairs, detect anomalies. The metric is CPU usage. Define a rolling baseline and flag points that deviate by >3 standard deviations."
**Answer:**
```python
import numpy as np
from collections import deque
class AnomalyDetector:
    def __init__(self, window=1000, threshold=3.0):
        self.window = window
        self.threshold = threshold
        self.buf = deque(maxlen=window)
    def add(self, value):
        if len(self.buf) < 30:  # warm-up
            self.buf.append(value); return False
        mean, std = np.mean(self.buf), np.std(self.buf)
        is_anomaly = abs(value - mean) > self.threshold * std
        self.buf.append(value)
        return is_anomaly
```
**Tip:** For Datadog, mention the seasonality handling (e.g., daily/weekly cycles), the streaming algorithm (Welford's online std), and the false positive control.

### Q2.2: "Design a metrics ingestion pipeline that handles 10M time series at 1-sec granularity. Total: 10B data points per second."
**Answer:** 4 components: (1) agents: lightweight collectors on each host. (2) intake: Kafka cluster with topic-per-metric-family, partitioned by host. (3) storage: time-series DB (Druid, TimescaleDB, or custom). (4) query: Presto + materialized rollups. Trade-off: write throughput vs. query latency.
**Tip:** Mention the cardinality problem (10M unique metric names), the use of dictionary encoding, the time-bucketed storage, and the rollup strategy (1-sec → 1-min → 1-hour).

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min, 2 problems)

### Q3.1.1: "Implement a time-series database with insert and range query. Support downsampling (avg, max, min) over arbitrary time windows."
**Answer:**
```python
import bisect
class TimeSeriesDB:
    def __init__(self):
        self.timestamps = []
        self.values = []
    def insert(self, ts, val):
        bisect.insort(self.timestamps, ts)
        idx = bisect.bisect_left(self.timestamps, ts)
        self.values.insert(idx, val)
    def range_query(self, t1, t2, agg='avg'):
        i = bisect.bisect_left(self.timestamps, t1)
        j = bisect.bisect_right(self.timestamps, t2)
        vals = self.values[i:j]
        if not vals: return None
        if agg == 'avg': return sum(vals) / len(vals)
        if agg == 'max': return max(vals)
        if agg == 'min': return min(vals)
```
**Tip:** Mention the use of columnar storage, Gorilla compression (Facebook's paper), and the use of pre-aggregated rollups for fast queries.

### Q3.1.2: "Given a log line, parse it into structured fields. The format is `timestamp LEVEL service message key=value key=value`."
**Answer:** Use regex with named groups. Example: `^(?P<ts>\S+)\s+(?P<level>\w+)\s+(?P<service>\w+)\s+(?P<msg>.*?)(\s+\S+=\S+)*$`. Then for kv pairs, split on whitespace and `=`.
**Tip:** For Datadog, mention the log pipeline (agent → intake → indexer → query), the structured logging standards (JSON, OpenTelemetry), and the trade-off between parsing on the agent vs. the server.

### Round 3.2: System design (60 min)

### Q3.2.1: "Design an alerting system that pages on-call engineers when a metric is anomalous. Minimize false positives, maximize recall."
**Answer:** 4 components: (1) detection: multiple algorithms (threshold, anomaly detection, forecasting) with voting. (2) routing: per-service escalation policies, on-call schedules. (3) silencing: maintenance windows, alert deduplication. (4) postmortem: incident timeline, RCA. Trade-off: false positive rate vs. recall. Use composite alerts (multiple conditions) to reduce false positives.
**Tip:** Mention the alert fatigue problem, the use of SLO-based alerting, and the importance of actionable alerts (every page should have a runbook).

### Q3.2.2: "Design a distributed tracing system. Spans come in from 100K services, must be queryable in <1s."
**Answer:** Use Jaeger / Zipkin / Datadog APM architecture. Components: agent (collects spans), intake (Kafka), storage (Cassandra / Elasticsearch), query (REST API with index). Each span has trace_id, span_id, parent_id, service, operation, duration, tags. Trade-off: storage cost vs. query performance.
**Tip:** Mention sampling (head-based vs. tail-based), the use of trace ID propagation (W3C Trace Context), and the importance of long-tail traces (rare slow ones).

### Round 3.3: ML deep-dive (60 min, forecasting/anomaly)

### Q3.3.1: "How would you forecast CPU usage 1 hour ahead, given 30 days of history at 1-min granularity?"
**Answer:** Multi-model ensemble: (1) Prophet (Facebook) for trend + seasonality. (2) LSTM or Transformer for residuals. (3) Confidence intervals via quantile regression. Use a walk-forward validation. Trade-off: model complexity vs. inference latency.
**Tip:** Mention the daily/weekly seasonality, the holiday handling, the changepoint detection (e.g., when a new deploy changes the baseline), and the importance of MAPE vs. RMSE for business stakeholders.

### Q3.3.2: "How would you detect anomalies in a multi-dimensional metric (e.g., p99 latency, error rate, request count)?"
**Answer:** Multi-signal approach: (1) per-signal anomaly detection (Prophet, Isolation Forest). (2) cross-signal correlation (PCA, autoencoder). (3) composite score with voting. Trade-off: per-signal precision vs. cross-signal recall.
**Tip:** Mention the root cause analysis (RCA) challenge: when 5 signals are anomalous simultaneously, which is the root? Use causal inference (Granger causality, do-calculus) or just a learned ranking model.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "Tell me about a time you shipped a system that had to scale 10×."
**Answer:** Use STAR. Situation (the product, the original scale), Task (your role), Action (the specific bottleneck, the redesign, the rollout), Result (the new throughput, the latency, the cost). Example: "I redesigned the metrics ingestion pipeline from batch to streaming, increasing throughput from 100K metrics/sec to 1M metrics/sec while reducing p99 latency from 5 sec to 200ms."
**Tip:** Datadog values scale + observability. Mention specific numbers, the failure modes you handled, and the monitoring you added.

## Stage 4: Hiring committee
The committee reviews the packet. The ML roles have a separate ML review. ~60% advance.

## Stage 5: Offer
Cash + RSU comp. Comp band L3-L6: $200K-$600K. Comp negotiation is real at L4+.

## Tips for the Datadog loop

1. **The observability domain is the signal.** Mention time-series databases, distributed tracing, log aggregation, alerting.
2. **Scale is the meta-rubric.** Every answer should include specific throughput, latency, and cardinality numbers.
3. **The AI for ops bet is the 2026 differentiator.** Watchdog + Bits AI + the AI for ops roadmap.
4. **System design is observability-themed.** Metrics ingestion, log aggregation, distributed tracing, alerting.
5. **The ML round is forecasting + anomaly detection, not generative AI.** Prophet, LSTM, Isolation Forest, multi-signal voting.

## Real candidate report

> "Datadog's loop is the most observability-focused of the monitoring companies. The coding round was standard LeetCode medium (LRU cache). The system design was a metrics pipeline at 10M time series. The ML round was forecasting + anomaly detection on time-series data. The behavioral round tested ownership and scale. If you've worked on monitoring or observability, this is the best-fit company in the space."
> — r/devops, on the Datadog loop

## Sources

- [Levels.fyi — Datadog compensation](https://www.levels.fyi/companies/datadog/salaries/software-engineer)
- [Datadog Engineering Blog](https://www.datadoghq.com/blog/engineering/) — the observability architecture posts
- [Datadog AI for Ops — Watchdog + Bits AI](https://www.datadoghq.com/product/ai/) — the AI for ops bet
- [r/devops — Datadog interview threads](https://www.reddit.com/r/devops/)
- [Gorilla: A Fast, Scalable, In-Memory Time Series Database (Facebook, 2015)](https://www.vldb.org/pvldb/vol8/p1816-teller.pdf) — the foundational TSDB paper
