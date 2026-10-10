# L8.1: The infrastructure stack — the 4 pillars and the 6 layers

> **FDE framing in one line:** the agent infrastructure stack is 4 pillars (deployment, observability, message broker, security) across 6 layers (compute, storage, network, identity, observability, integration). The FDE who can draw this stack on a whiteboard in 5 minutes is the FDE who can own a production agent.

## The 3 things you'll learn

1. The 4 pillars of agent infrastructure: deployment (where it runs), observability (how you know it's healthy), message broker (how it scales), security (how it's protected). The pillars are independent; the FDE picks the right tool for each.
2. The 6 layers of the stack: compute (CPU/memory), storage (Postgres/Redis/S3), network (HTTP/gRPC/VPC), identity (auth/authz/credentials), observability (logs/metrics/traces), integration (the customer's tech stack). The layers are interdependent; the FDE picks the right tool for each.
3. The "infrastructure as the contract" pattern: the agent's SLOs (latency, uptime, cost) are the contract; the infrastructure is the implementation; the on-call is the gate. The FDE ships the SLOs first, then the infra that meets them.

## Concept

The agent doesn't run in a vacuum. The agent runs on infrastructure: a container in a Kubernetes pod, behind a load balancer, talking to a database, emitting logs to CloudWatch, and accepting requests from the customer's API. The infrastructure is the platform layer; it's the FDE's responsibility to pick the right tool for each pillar, deploy the agent, observe it, secure it, and own the 3am page when it breaks. **The agent is the application; the infrastructure is the platform; the FDE owns both.**

The 4 pillars:

1. **Deployment.** Where the agent runs. The FDE picks from Kubernetes (most flexible, most complex), serverless (Lambda, Cloud Run; least complex, least flexible), dedicated VM (EC2, Compute Engine; full control, manual operations), or a PaaS (Render, Fly.io, Railway; the middle ground). The right choice depends on the customer's scale, the team's engineering depth, and the latency requirements.
2. **Observability.** How the FDE knows the agent is healthy. The 3 pillars of observability: logs (discrete events), metrics (aggregated numbers), traces (the full request lifecycle). The FDE picks the tool: Datadog (managed, $$$), Grafana + Prometheus + Loki (open-source, $), Honeycomb (managed, $$), or cloud-native (CloudWatch, Azure Monitor, GCP Cloud Monitoring).
3. **Message broker.** How the agent scales. The FDE picks from synchronous (request/response, easy), async with queue (SQS, Kafka, RabbitMQ, Redis Streams), or event-driven (Kafka, NATS, Kinesis). The right choice depends on the request volume, the latency requirement, and the durability requirement.
4. **Security.** How the agent is protected. The 5 layers: API gateway (rate limit, auth), mTLS (encrypt in transit), secrets management (Vault, AWS Secrets Manager), audit log (who did what when), and identity (OAuth, JWT, API key). The FDE picks the tool that matches the customer's compliance requirements.

The 6 layers of the stack:

1. **Compute.** The CPU + memory the agent runs on. The FDE picks: container (Kubernetes, ECS, Cloud Run), VM (EC2, Compute Engine), serverless (Lambda, Cloud Functions), or PaaS (Render, Fly.io). The layer is the foundation; the FDE sizes the compute to the workload.
2. **Storage.** The data the agent needs. The FDE picks: relational (Postgres, MySQL), document (MongoDB, DynamoDB), vector (Pinecone, Qdrant, pgvector), cache (Redis, Memcached), object (S3, GCS), and queue (SQS, Kafka, Redis Streams). The FDE picks the right tool for each access pattern.
3. **Network.** The path the agent's traffic takes. The FDE picks: HTTP/REST (most common), gRPC (high-performance), GraphQL (flexible queries), WebSocket (streaming), VPC peering (private network), and CDN (CloudFront, Cloudflare). The layer is the carrier; the FDE picks the protocol that matches the workload.
4. **Identity.** Who can call the agent. The FDE picks: API key (simple), OAuth 2.0 (delegated auth), JWT (self-contained), mTLS (machine-to-machine), and OIDC (federated). The layer is the gate; the FDE picks the protocol that matches the customer's identity provider.
5. **Observability.** What the FDE sees. The FDE picks: logs (CloudWatch, Loki, Datadog), metrics (Prometheus, CloudWatch, Datadog), traces (OpenTelemetry, Jaeger, Honeycomb), and dashboards (Grafana, Datadog, CloudWatch). The layer is the dashboard; the FDE picks the tool that matches the team's skill.
6. **Integration.** The customer's tech stack. The FDE integrates with: CRM (Salesforce, HubSpot), ticketing (Jira, Linear, Zendesk), communication (Slack, Teams, email), database (Postgres, Snowflake, BigQuery), and the customer's internal APIs. The layer is the bridge; the FDE picks the integration that matches the customer's stack.

The "infrastructure as the contract" pattern is the recognition that the agent's SLOs are the contract with the customer. The SLOs are: latency (p95 < 2s), uptime (99.9%), error rate (< 0.5%), cost ($200/month). The infrastructure is the implementation; the FDE picks the tools that meet the SLOs. **The FDE ships the SLOs first, then the infra that meets them. The SLO is the contract; the infra is the implementation; the on-call is the gate.**

## The pattern

The 4 pillars × 6 layers matrix (the FDE's reference):

```python
INFRASTRUCTURE_MATRIX = {
    "deployment": {
        "compute": ["Kubernetes (EKS, GKE, AKS)", "ECS", "Cloud Run", "Lambda", "EC2"],
        "best_for": {"k8s": "high scale + engineering team", "serverless": "spiky workloads", "vm": "stateful + on-prem"},
        "decision_factors": "scale, latency, engineering depth, on-prem requirement",
    },
    "observability": {
        "compute": ["Prometheus + Grafana + Loki", "Datadog", "Honeycomb", "CloudWatch"],
        "best_for": {"prom_grafana": "open-source + engineering team", "datadog": "managed + budget", "honeycomb": "traces + budget"},
        "decision_factors": "skill, budget, scale, cloud provider",
    },
    "message_broker": {
        "compute": ["SQS", "Kafka", "Redis Streams", "RabbitMQ", "NATS"],
        "best_for": {"sqs": "managed + simple", "kafka": "high-throughput + event sourcing", "redis": "low-latency + existing Redis", "rabbitmq": "complex routing", "nats": "lightweight + pub-sub"},
        "decision_factors": "volume, latency, durability, ordering",
    },
    "security": {
        "compute": ["API gateway (Kong, AWS API GW)", "Vault", "AWS Secrets Manager", "OAuth (Auth0, Cognito)", "mTLS"],
        "best_for": {"api_gw": "rate limit + auth", "vault": "secrets + rotation", "oauth": "federated identity", "mtls": "service-to-service"},
        "decision_factors": "compliance, customer identity, multi-tenancy",
    },
}
```

The 6 layers (the FDE's whiteboard):

```python
SIX_LAYERS = {
    "L1_compute": {
        "description": "The CPU + memory the agent runs on",
        "tools": ["Kubernetes pod", "ECS task", "Lambda function", "EC2 instance", "Cloud Run service"],
        "decision": "scale, latency, cost, engineering depth",
    },
    "L2_storage": {
        "description": "The data the agent needs",
        "tools": ["Postgres (relational)", "Redis (cache + queue)", "S3 (object)", "Pinecone (vector)", "SQS (queue)"],
        "decision": "access pattern, consistency, durability, scale",
    },
    "L3_network": {
        "description": "The path the agent's traffic takes",
        "tools": ["HTTP/REST", "gRPC", "GraphQL", "WebSocket", "VPC peering", "CDN"],
        "decision": "protocol, performance, security, geographic distribution",
    },
    "L4_identity": {
        "description": "Who can call the agent",
        "tools": ["API key", "OAuth 2.0", "JWT", "mTLS", "OIDC"],
        "decision": "customer identity, compliance, multi-tenancy",
    },
    "L5_observability": {
        "description": "What the FDE sees",
        "tools": ["CloudWatch/Loki (logs)", "Prometheus/CloudWatch (metrics)", "OpenTelemetry/Jaeger (traces)", "Grafana/Datadog (dashboards)"],
        "decision": "skill, budget, scale, cloud provider",
    },
    "L6_integration": {
        "description": "The customer's tech stack",
        "tools": ["CRM (Salesforce, HubSpot)", "Ticketing (Jira, Linear)", "Comms (Slack, Teams)", "DB (Postgres, Snowflake)"],
        "decision": "customer's existing stack + the FDE's integration map",
    },
}
```

The SLO contract (the FDE ships first):

```python
AGENT_SLO_CONTRACT = {
    "latency": {
        "p50_target_s": 1.0,
        "p95_target_s": 2.0,
        "p99_target_s": 5.0,
        "measured_by": "Prometheus histogram agent_latency_per_run_s",
    },
    "uptime": {
        "monthly_target": 0.999,  # 99.9%
        "monthly_error_budget_minutes": 43.2,
        "measured_by": "uptime monitor (Pingdom, UptimeRobot, CloudWatch Synthetics)",
    },
    "error_rate": {
        "target": 0.005,  # 0.5%
        "alert_threshold": 0.01,  # 1%
        "measured_by": "Prometheus counter agent_error_total / agent_run_total",
    },
    "cost": {
        "monthly_target_usd": 200,
        "per_run_target_usd": 0.001,
        "alert_threshold": 0.8 * 200,  # $160
        "measured_by": "Cloud cost allocation tags + cost dashboard",
    },
    "capacity": {
        "concurrent_runs_target": 50,
        "burst_target": 200,  # 4x burst for 1 minute
        "measured_by": "load test (k6, Locust, Gatling)",
    },
}
```

The reference architecture (the FDE's diagram):

```
                          ┌─────────────────┐
                          │   API Gateway   │
                          │ (rate limit,    │
                          │  auth, audit)   │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  Load Balancer  │
                          │  (ALB, Nginx)   │
                          └────────┬────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
          ┌──────────┐       ┌──────────┐       ┌──────────┐
          │ Agent    │       │ Agent    │       │ Agent    │
          │ Pod 1    │       │ Pod 2    │       │ Pod 3    │
          └────┬─────┘       └────┬─────┘       └────┬─────┘
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  │
        ┌──────────────────┬──────┴──────┬──────────────────┐
        ▼                  ▼             ▼                  ▼
   ┌─────────┐       ┌──────────┐  ┌─────────┐       ┌──────────┐
   │ Postgres│       │  Redis   │  │ Pinecone│       │   SQS    │
   │ (data)  │       │ (cache)  │  │ (vector)│       │ (queue)  │
   └─────────┘       └──────────┘  └─────────┘       └──────────┘
                                  │
                                  ▼
                          ┌─────────────────┐
                          │ Observability   │
                          │ (Prom + Grafana)│
                          └─────────────────┘
```

The pattern that wins interviews is the "4 pillars × 6 layers + SLO contract" pattern. The candidate who says "I think about infrastructure as 4 pillars (deployment, observability, message broker, security) across 6 layers (compute, storage, network, identity, observability, integration). I ship the SLOs first (latency, uptime, error rate, cost, capacity), then the infra that meets them. The on-call is the gate; the dashboard is the artifact; the SLO is the contract. The wrong choice is to over-engineer for scale the customer doesn't have. The right choice is the SLOs first, then the infra" is the candidate who demonstrates the infra-mindset.

## Code or example

The 4-pillar decision rubric (the FDE's tool picker):

```python
def pick_infra_stack(requirements: dict) -> dict:
    """Pick the 4-pillar stack based on the requirements."""
    scale = requirements.get("concurrent_runs", 50)
    latency_p95_s = requirements.get("latency_p95_s", 2.0)
    monthly_budget_usd = requirements.get("monthly_budget_usd", 200)
    team_engineering_first = requirements.get("team_engineering_first", True)
    on_prem = requirements.get("on_prem", False)

    stack = {}

    # Deployment pillar
    if on_prem:
        stack["deployment"] = "Kubernetes (self-hosted on bare metal / VM)"
    elif scale > 100 or not team_engineering_first is False:
        stack["deployment"] = "Kubernetes (EKS/GKE/AKS)"
    elif scale < 50 and team_engineering_first is False:
        stack["deployment"] = "Serverless (Lambda + API Gateway)"
    else:
        stack["deployment"] = "Container (ECS or Cloud Run)"

    # Observability pillar
    if monthly_budget_usd > 500:
        stack["observability"] = "Datadog (managed, $$$)"
    elif team_engineering_first:
        stack["observability"] = "Prometheus + Grafana + Loki (open-source, $)"
    else:
        stack["observability"] = "CloudWatch (managed, $$)"

    # Message broker pillar
    if scale > 1000:
        stack["message_broker"] = "Kafka (high-throughput)"
    elif scale > 100:
        stack["message_broker"] = "SQS (managed) or Redis Streams (low-latency)"
    else:
        stack["message_broker"] = "Synchronous HTTP (no broker needed)"

    # Security pillar
    if requirements.get("compliance", "none") in ("soc2", "hipaa", "pci"):
        stack["security"] = "API Gateway + Vault + mTLS + audit log"
    else:
        stack["security"] = "API Gateway + AWS Secrets Manager + OAuth 2.0"

    return stack
```

The AtlasMart stack (the case study):

```python
ATLASMART_STACK = {
    "scale": "5,000 requests/day = 200/hour = 3-4/second peak",
    "latency_target": "p95 2s",
    "uptime_target": "99.9%",
    "monthly_cost_target": "$200",
    "team": "5 engineers + 10 ops; engineering-first",
    "deployment": {
        "platform": "Kubernetes (EKS on AWS)",
        "replicas": "3 pods, auto-scale to 10",
        "node_type": "t3.medium (2 vCPU, 4GB RAM)",
        "monthly_cost": "$80 (EKS) + $40 (EC2) = $120",
    },
    "observability": {
        "logs": "CloudWatch Logs",
        "metrics": "Prometheus + Grafana",
        "traces": "OpenTelemetry + Jaeger",
        "alerting": "Alertmanager + PagerDuty",
        "monthly_cost": "$30",
    },
    "message_broker": {
        "platform": "SQS (standard queue)",
        "use_case": "Async processing of long-running tasks (>5s)",
        "monthly_cost": "$5",
    },
    "security": {
        "api_gateway": "AWS API Gateway (rate limit, auth, audit)",
        "secrets": "AWS Secrets Manager (OpenAI key, DB credentials)",
        "identity": "OAuth 2.0 with customer-specific scopes",
        "mTLS": "Not required (internal only)",
        "monthly_cost": "$25",
    },
    "storage": {
        "primary_db": "Postgres (RDS, db.t3.medium)",
        "cache": "Redis (ElastiCache, cache.t3.medium)",
        "vector": "pgvector (in the same Postgres)",
        "object": "S3 (logs, backups, model artifacts)",
        "monthly_cost": "$20",
    },
    "total_monthly_cost": "$200 (within budget)",
    "total_p95_latency": "1.8s (within SLA)",
    "total_uptime": "99.95% (within SLA)",
}
```

The FDE's 5-minute whiteboard (the interview exercise):

```markdown
# FDE's 5-Minute Whiteboard: Agent Infrastructure

## Layer 1: Compute
- Kubernetes pod (3 replicas, auto-scale to 10)
- Why: high scale, engineering team, sub-second p95
- Alternative: Lambda (if <100 concurrent), ECS (if simple)

## Layer 2: Storage
- Postgres (relational, source of truth)
- Redis (cache, idempotency, rate limit)
- pgvector (in Postgres, <1M vectors)
- S3 (logs, backups, model artifacts)
- SQS (queue for long-running tasks)
- Why: customer's existing Postgres, no separate vector DB

## Layer 3: Network
- HTTP/REST (most common, customer-friendly)
- VPC peering (private network for DB)
- CloudFront (CDN for static assets)
- Why: standard, simple, customer understands

## Layer 4: Identity
- API Gateway (rate limit, auth, audit)
- OAuth 2.0 (customer's identity provider)
- mTLS (service-to-service, internal only)
- Why: customer's existing OAuth, compliance

## Layer 5: Observability
- Prometheus (metrics)
- Grafana (dashboards)
- OpenTelemetry (traces)
- CloudWatch Logs (logs)
- Alertmanager (alerts)
- Why: open-source, engineering team, customer can self-serve

## Layer 6: Integration
- HubSpot (CRM)
- Slack (notifications)
- Postgres (customer's DB)
- Why: customer's existing stack
```

## Production addendum

The infrastructure stack question is the answer to "what is the agent infrastructure stack." The 60-second script:

> "4 pillars (deployment, observability, message broker, security) across 6 layers (compute, storage, network, identity, observability, integration). I ship the SLOs first (latency, uptime, error rate, cost, capacity), then the infra that meets them. The reference architecture: API Gateway → Load Balancer → Agent Pods → Postgres + Redis + Vector + Queue, with observability on the side. The wrong choice is to over-engineer for scale the customer doesn't have. The right choice is the SLOs first, then the infra, with the 4 × 6 matrix as the tool picker."

This is the difference between a candidate who says "I deployed to Kubernetes" and a candidate who says "4 pillars × 6 layers, SLO contract first, reference architecture, the 4-pillar decision rubric, the 5-minute whiteboard." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/infra/` — the infrastructure reference.
- **Reference implementation**: `course/hardcode/level-6-production-systems/13-autoscaling-llm-service.py` — the canonical infrastructure stack.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — infrastructure as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — multi-agent requires per-agent deployment.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — infrastructure as a system design topic.

## The 3 questions this lecture preps you for

1. **"What is the agent infrastructure stack?"** Answer: 4 pillars (deployment, observability, message broker, security) across 6 layers (compute, storage, network, identity, observability, integration). The FDE picks the right tool for each pillar + each layer based on the SLOs. The wrong choice is to over-engineer for scale the customer doesn't have. The right choice is the SLOs first, then the infra.
2. **"What are the 4 pillars?"** Answer: deployment (where it runs: Kubernetes, serverless, VM, PaaS), observability (how you know it's healthy: logs, metrics, traces), message broker (how it scales: SQS, Kafka, Redis, sync), security (how it's protected: API gateway, secrets, identity, audit). Each pillar is independent; the FDE picks the right tool.
3. **"What is the SLO contract?"** Answer: the FDE ships the SLOs first (latency p95, uptime %, error rate, cost, capacity), then the infrastructure that meets them. The SLO is the contract with the customer; the infrastructure is the implementation; the on-call is the gate. The SLO is the artifact that turns an agent into a product.

## Read next

`L8-2-deployment-platforms.md` — the 3 deployment patterns in production-grade detail: Kubernetes (the FDE's default), serverless (the cost optimizer), dedicated VM (the stateful + on-prem choice). The deployment decision rubric.
