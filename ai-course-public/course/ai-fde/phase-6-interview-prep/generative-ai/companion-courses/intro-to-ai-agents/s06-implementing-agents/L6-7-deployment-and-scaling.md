# L6.7: Deployment and scaling — serverless, container, dedicated VM

> **FDE framing in one line:** the deployment pattern is a tradeoff between cost, latency, and operational overhead. Serverless for spiky workloads; container for predictable traffic; dedicated VM for stateful agents with large memory backends. The FDE picks the pattern that matches the customer's traffic profile.

## The 3 things you'll learn

1. The 3 deployment patterns: serverless (Lambda, Cloud Functions), container (Docker + ECS / Cloud Run), dedicated VM (EC2, Compute Engine). The cost-latency-operations tradeoff.
2. The 3 scaling levers: horizontal (more replicas), vertical (bigger model), cost-aware routing (use the cheap model for routine steps).
3. The "deploy behind a circuit breaker" pattern: the agent is stateless; the state lives in a database; the deployment is idempotent. The 3am recovery is a single command.

## Concept

Deployment and scaling is the 7th layer of the shipping agent. The deployment pattern is a tradeoff between cost, latency, and operational overhead. The scaling levers are the FDE's response to traffic growth. **The FDE picks the deployment pattern that matches the customer's traffic profile; the scaling levers are the operational toolkit.**

The 3 deployment patterns:

1. **Serverless (Lambda, Cloud Functions, Cloud Run Jobs).** Pay per invocation; auto-scales from 0 to 1000s; cold start latency ~1s. Best for: spiky workloads, low-traffic agents, event-driven triggers (e.g., an email arrives → invoke the drafter). Cost: $0.20 per 1M requests + $0.0000166667 per GB-second. The cold start is the latency tax.
2. **Container (Docker + ECS / Cloud Run / Kubernetes).** Pay per CPU/memory per second; auto-scales from 1 to 100s; cold start < 100ms (warm). Best for: predictable traffic, latency-sensitive agents, stateful backends. Cost: $0.0000166667 per GB-second + load balancer. The operational overhead is the tax.
3. **Dedicated VM (EC2, Compute Engine, on-prem).** Pay per hour; no auto-scaling; full control. Best for: stateful agents with large memory backends (vector DB in-process), on-prem deployments, regulated industries. Cost: $0.04-$0.50 per hour depending on size. The operational overhead is the highest tax.

The 3 scaling levers:

1. **Horizontal scaling (more replicas).** Add more containers / serverless instances; the load balancer distributes traffic. The lever for: traffic growth (10× more requests/day). The cost: linear with traffic. The complexity: stateless agents only; stateful agents need a shared database.
2. **Vertical scaling (bigger model).** Switch from gpt-5-mini to gpt-5, or from gpt-5 to claude-opus. The lever for: accuracy demand (the customer's eval set requires a more capable model). The cost: 5-15× per token. The complexity: the same agent class; just change the model constructor arg.
3. **Cost-aware routing (cheap model for routine steps).** The orchestrator dispatches routine steps to gpt-5-mini; hard steps to gpt-5. The lever for: cost ceiling (the customer's monthly budget is binding). The cost: 5-10× reduction. The complexity: the orchestrator + the per-step model router.

The "deploy behind a circuit breaker" pattern is the recognition that the agent is stateless; the state lives in a database; the deployment is idempotent. **The 3am recovery is a single command.** The agent service is behind a load balancer; the load balancer is behind a circuit breaker; the circuit breaker trips when the downstream service fails. The on-call recovers by restarting the service; the state is preserved in the database; the in-flight requests are retried.

## The pattern

The deployment pattern decision rubric:

```python
def pick_deployment_pattern(requirements: dict) -> str:
    """Pick serverless, container, or VM based on the requirements."""
    traffic = requirements.get("traffic_profile", "spiky")  # spiky | steady | bursty
    latency_sensitivity = requirements.get("latency_p95_s", 5.0)
    stateful = requirements.get("stateful", False)  # vector DB in-process?
    on_prem_required = requirements.get("on_prem_required", False)
    cost_per_month = requirements.get("cost_per_month_usd", 100.0)

    if on_prem_required or stateful:
        return "vm"
    if traffic == "spiky" and latency_sensitivity > 2.0 and cost_per_month < 50:
        return "serverless"
    if traffic in ("steady", "bursty") and latency_sensitivity < 1.0:
        return "container"
    return "container"  # default
```

The 3-pattern deployment compared:

```python
# Serverless (AWS Lambda)
# - Trigger: SNS topic (email arrives) or API Gateway (HTTP request)
# - Cold start: ~1s; warm: ~100ms
# - Cost: $0.20 per 1M requests + compute time
# - Scaling: auto, 0 to 1000s
# - State: must be external (DynamoDB, S3)
LAMBDA_DEPLOYMENT = """
import boto3
def handler(event, context):
    email = event["email"]
    result = run_agent(email, AGENT)
    return {"statusCode": 200, "body": json.dumps(result)}
"""

# Container (Docker + ECS)
# - Trigger: ALB (HTTP request)
# - Cold start: < 100ms (warm)
# - Cost: $0.0000166667 per GB-second
# - Scaling: auto, 1 to 100s
# - State: can be in-process (Redis, vector DB)
DOCKER_DEPLOYMENT = """
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY service/ /app/service/
WORKDIR /app
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# VM (EC2, on-prem)
# - Trigger: ALB or direct
# - Cold start: N/A (always running)
# - Cost: $0.04-$0.50/hour
# - Scaling: manual (or ASG)
# - State: full control
VM_DEPLOYMENT = """
# systemd unit file
[Unit]
Description=PacificFreight Agent
[Service]
ExecStart=/usr/bin/python3 -m uvicorn service.app:app --host 0.0.0.0 --port 8000
Restart=always
[Install]
WantedBy=multi-user.target
"""
```

The cost-aware router (the scaling lever for cost):

```python
def cost_aware_route(step_kind: str, cost_tracker: CostCeiling) -> str:
    """Pick the model based on the step and the remaining budget."""
    remaining = cost_tracker.max_run_usd - cost_tracker.run_cost
    if remaining < 0.01:
        return "gpt-5-mini"  # Budget exhausted; cheapest option
    if step_kind in ("planning", "synthesis", "final_answer") and remaining > 0.05:
        return "gpt-5"  # Hard step with budget
    return "gpt-5-mini"  # Default: cost-quality crossover
```

The 3am recovery (the deployment safety net):

```bash
# The 3am recovery is a single command
# 1. SSH to the VM (or kubectl exec into the container)
# 2. Check the circuit breaker state
kubectl get pods -l app=pf-agent
# 3. If the pods are unhealthy, restart them
kubectl rollout restart deployment/pf-agent
# 4. The state is preserved in PostgreSQL / Redis
# 5. The in-flight requests are retried by the load balancer
# 6. The on-call checks the audit log to see what failed
```

The pattern that wins interviews is the "3 deployment patterns + 3 scaling levers + 3am recovery" pattern. The candidate who says "I pick serverless for spiky workloads, container for predictable traffic, VM for stateful backends or on-prem. The 3 scaling levers are horizontal (more replicas), vertical (bigger model), cost-aware routing (cheap model for routine steps). The agent is stateless; the state is in the database; the 3am recovery is a single command. The wrong choice is serverless for a stateful vector DB (cold start + state loss). The right choice is the pattern that matches the traffic profile + the state requirements" is the candidate who demonstrates the deployment-mindset.

## Code or example

The 3 scaling levers in action:

```python
# Lever 1: Horizontal scaling
# 10× traffic growth → 10× replicas
# Before: 1 container, 100 RPS, p95 800ms
# After: 10 containers, 1000 RPS, p95 800ms (same latency)
# Cost: 10× the per-container cost
# Complexity: stateless agent (state in Redis/PostgreSQL)

# Lever 2: Vertical scaling
# Accuracy demand → bigger model
# Before: gpt-5-mini, 75% eval accuracy, $0.005/run
# After: gpt-5, 85% eval accuracy, $0.05/run
# Cost: 10× per run
# Complexity: just change the model constructor arg

# Lever 3: Cost-aware routing
# Cost ceiling binding → cheap model for routine steps
# Before: gpt-5 for all 10 steps, $0.05/run
# After: gpt-5 for 2 hard steps + gpt-5-mini for 8 routine steps, $0.012/run
# Cost: 4× reduction
# Complexity: the orchestrator + the per-step model router (from L2.1)
```

The PacificFreight deployment (the canonical FDE use case):

```python
# PacificFreight runs on a dedicated VM (Daniel's box)
# - 4 vCPU, 16GB RAM, 100GB SSD = $80/month
# - 150 emails/day * 5 steps/email = 750 LLM calls/day
# - Cost: 750 * $0.005 = $3.75/day = $112/month (within budget)
# - Latency: p95 1.8s (good for non-urgent emails)
# - State: usage.jsonl on local disk, episodic memory in PostgreSQL

# Scaling plan:
# - 10× growth (5 customer teams, 1500 emails/day) → horizontal: 3 VM replicas
# - 100× growth (50 customer teams) → container + auto-scaling group
# - 1000× growth (500 customer teams) → serverless + cost-aware routing
```

## Production addendum

The deployment question is the answer to "how do you deploy and scale an agent." The 60-second script:

> "3 deployment patterns. Serverless (Lambda) for spiky workloads, cold start ~1s, pay per invocation. Container (Docker + ECS / Cloud Run) for predictable traffic, cold start < 100ms, pay per CPU/memory. Dedicated VM (EC2) for stateful backends or on-prem, pay per hour, full control. 3 scaling levers: horizontal (more replicas), vertical (bigger model), cost-aware routing (cheap model for routine steps). **The agent is stateless; the state is in the database; the 3am recovery is a single command.** The wrong choice is serverless for a stateful vector DB (cold start + state loss). The right choice is the pattern that matches the traffic profile + the state requirements."

This is the difference between a candidate who says "I deployed the agent" and a candidate who says "serverless for spiky, container for predictable, VM for stateful; horizontal + vertical + cost-aware routing; 3am recovery is a single command." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-applications/07-deployment.md` — the deployment patterns.
- **Reference implementation**: `course/ai-fde/phase-2-applications/service/` — the PacificFreight production deployment.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/12-deployment.md` — the deployment as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/03-distilled-slm/` — the SLM as the deployment-flexibility lever.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — deployment as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you deploy and scale an agent?"** Answer: 3 deployment patterns — serverless for spiky (Lambda, cold start ~1s), container for predictable (Docker + ECS, cold start < 100ms), VM for stateful or on-prem. 3 scaling levers — horizontal (more replicas), vertical (bigger model), cost-aware routing (cheap model for routine steps). The wrong choice is serverless for stateful; the right choice is the pattern that matches the traffic profile.
2. **"What is the 3am recovery pattern?"** Answer: the agent is stateless; the state lives in a database (PostgreSQL, Redis); the deployment is behind a load balancer + circuit breaker. The 3am recovery is a single command: `kubectl rollout restart deployment/pf-agent`. The state is preserved; the in-flight requests are retried; the on-call checks the audit log to see what failed.
3. **"When do you use horizontal vs vertical scaling?"** Answer: horizontal when traffic grows (10× more requests/day → 10× replicas). Vertical when accuracy demand grows (the eval set requires a more capable model → switch from gpt-5-mini to gpt-5). Cost-aware routing when the cost ceiling is binding (cheap model for routine steps, expensive model for hard steps). The 3 levers are orthogonal; the FDE picks the one that matches the bottleneck.

## Read next

`L6-8-monitoring-and-observability.md` — the 8th lecture. The 4 metrics, the 3 logs, the 2 traces, the alerts. The 3am dashboard that tells the on-call whether the agent is healthy.