# L8.2: Deployment platforms — Kubernetes, serverless, dedicated VM

> **FDE framing in one line:** the deployment platform is a tradeoff between 4 axes: scale, latency, engineering depth, on-prem requirement. Kubernetes wins on scale + engineering depth; serverless wins on cost + low engineering depth; VM wins on stateful + on-prem. The FDE picks the platform that matches the customer's dominant axis.

## In 60 seconds

> "3 platforms. Kubernetes (100s-1000s concurrent + engineering team + sub-second p95 + on-prem). Serverless (spiky + <100 concurrent + low engineering + tolerance for cold start). VM (stateful + on-prem + budget). 4 axes: scale, latency, team depth, on-prem. The agent is stateless; the state is in Postgres + Redis + S3; the 3am recovery is a single `kubectl rollout restart`. The 4 K8s patterns: Deployment (agent), StatefulSet (DBs), DaemonSet (observability), Job/CronJob (batch). The wrong choice is Kubernetes for 10 concurrent runs (over-engineering). The right choice is the platform that matches the dominant axis."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The 3 deployment platforms in production detail: Kubernetes (EKS, GKE, AKS, self-hosted), serverless (Lambda, Cloud Run, ECS Fargate), dedicated VM (EC2, Compute Engine, on-prem). The right choice depends on the customer's scale + engineering depth + on-prem requirement.
2. The 4 Kubernetes patterns: Deployment (stateless pods), StatefulSet (databases, queues), DaemonSet (one per node), Job/CronJob (one-shot). The FDE uses Deployment for the agent; the other patterns are for the supporting infrastructure.
3. The "stateless agent, stateful data" pattern: the agent is stateless (the pod can be killed at any time); the state lives in Postgres + Redis + S3. The deployment is idempotent; the 3am recovery is a single `kubectl rollout restart`.

## Concept

The agent's deployment platform is the foundation of the infrastructure stack. The FDE picks the platform based on 4 axes: scale (concurrent runs), latency (p95 target), engineering depth (the team's Kubernetes skill), and on-prem requirement (regulated industries, customer requirement). **The wrong choice is to over-engineer (Kubernetes for 10 concurrent runs) or under-engineer (Lambda for 1000 concurrent runs). The right choice matches the dominant axis.**

The 3 deployment platforms:

1. **Kubernetes (EKS, GKE, AKS, self-hosted).** Container orchestration. The agent runs in a pod; the pod is managed by a Deployment; the Deployment is managed by a ReplicaSet; the ReplicaSet is managed by the controller. The FDE picks Kubernetes when the customer has an engineering team, needs 100+ concurrent runs, requires sub-second latency, or wants to run on-prem. The cost: $80-300/month for a small cluster; engineering overhead: significant (the FDE maintains the cluster).
2. **Serverless (Lambda, Cloud Run, ECS Fargate).** Pay per invocation; auto-scales from 0 to 1000s. The agent runs as a function or a container; the platform manages the lifecycle. The FDE picks serverless when the customer has spiky workloads, <100 concurrent runs, latency tolerance (>1s), or limited engineering depth. The cost: $0.20 per 1M requests + compute time; engineering overhead: minimal.
3. **Dedicated VM (EC2, Compute Engine, on-prem).** A long-running instance with full control. The agent runs as a systemd service; the VM is managed by the FDE or the customer's ops team. The FDE picks VM when the customer has stateful requirements (large in-memory vector DB), on-prem requirement (regulated industries), or budget constraints (VM is cheaper than Kubernetes for <3 replicas). The cost: $0.04-$0.50/hour; engineering overhead: manual (the FDE maintains the VM).

The 4 Kubernetes patterns:

1. **Deployment.** Stateless pods. The most common; the right pattern for the agent. The Deployment manages a ReplicaSet; the ReplicaSet manages N identical pods; the pods can be killed at any time without losing data. The FDE configures: replicas (3-10), resources (requests + limits), health checks (liveness + readiness), rolling update (max unavailable: 0, max surge: 1).
2. **StatefulSet.** Stateful pods. The right pattern for databases, queues, and other stateful services. The StatefulSet assigns a stable network identity (e.g., `postgres-0`, `postgres-1`); the pods persist data on attached volumes. The FDE uses StatefulSet for Postgres, Redis, Kafka — never for the agent.
3. **DaemonSet.** One pod per node. The right pattern for log collectors (Fluent Bit), monitoring agents (node-exporter), and CNI plugins. The FDE uses DaemonSet for observability infrastructure; never for the agent.
4. **Job / CronJob.** One-shot or scheduled. The right pattern for batch processing (re-index vectors, generate weekly reports). The FDE uses Job for one-time tasks; CronJob for scheduled tasks (e.g., weekly eval set run).

The "stateless agent, stateful data" pattern is the recognition that the agent is stateless. The agent's state (messages, tool calls, episodic memory) is in Postgres + Redis + the vector DB. **The agent pod can be killed at any time without losing data; the deployment is idempotent; the 3am recovery is a single `kubectl rollout restart deployment/agent`.** The pattern is the same as the FDE's first principle: the artifact is the data, not the process.

## The pattern

The 3 platforms compared (the FDE's reference):

```python
PLATFORM_COMPARISON = {
    "kubernetes": {
        "scale": "100s-1000s of pods; auto-scales to 1000s",
        "latency_p95": "<500ms (warm pod)",
        "cold_start_s": "0 (warm); 1-30s (cold)",
        "engineering_depth": "high (the team needs to manage the cluster)",
        "on_prem": "yes (self-hosted Kubernetes)",
        "cost_setup_usd": "200-500",
        "cost_per_month_usd": "100-300 (3-10 pods on t3.medium)",
        "best_for": "high scale + engineering team + on-prem",
        "weakness": "operational overhead; steep learning curve",
    },
    "serverless": {
        "scale": "0-1000s of concurrent invocations",
        "latency_p95": "1-5s (cold start); <500ms (warm)",
        "cold_start_s": "0.5-5s (depending on platform)",
        "engineering_depth": "low (the platform manages the lifecycle)",
        "on_prem": "no (cloud-only)",
        "cost_setup_usd": "0",
        "cost_per_month_usd": "10-100 (pay per use)",
        "best_for": "spiky workloads + low scale + low engineering depth",
        "weakness": "cold start; 15-minute timeout (Lambda); stateful limitations",
    },
    "vm": {
        "scale": "1 VM = 100s of concurrent (depending on size)",
        "latency_p95": "<500ms (always warm)",
        "cold_start_s": "0 (always running)",
        "engineering_depth": "medium (the team needs to manage the VM)",
        "on_prem": "yes (bare metal or VM)",
        "cost_setup_usd": "0-100",
        "cost_per_month_usd": "20-150 (depending on size)",
        "best_for": "stateful + on-prem + budget",
        "weakness": "manual scaling; single point of failure; operational overhead",
    },
}
```

The Kubernetes Deployment (the agent's manifest):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pf-agent
  labels:
    app: pf-agent
spec:
  replicas: 3  # 3 pods; auto-scale to 10
  selector:
    matchLabels:
      app: pf-agent
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0  # zero downtime
      maxSurge: 1  # one extra pod during the update
  template:
    metadata:
      labels:
        app: pf-agent
    spec:
      containers:
      - name: pf-agent
        image: pacificfreight/agent:v1.0.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "500m"  # 0.5 vCPU
            memory: "1Gi"
          limits:
            cpu: "1000m"  # 1 vCPU
            memory: "2Gi"
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: pf-agent-secrets
              key: openai-api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: pf-agent-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: pf-agent-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30  # check every 30s
          failureThreshold: 3  # restart after 3 failures
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10  # check every 10s
```

The Horizontal Pod Autoscaler (HPA):

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pf-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pf-agent
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # scale when CPU > 70%
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80  # scale when memory > 80%
```

The Lambda deployment (the serverless alternative):

```python
# AWS Lambda function for the agent
import json
from agent import run_agent

def handler(event, context):
    """The agent's Lambda handler."""
    body = json.loads(event["body"])
    result = run_agent(
        email=body["email"],
        tenant=body.get("tenant", "default"),
        request_id=context.aws_request_id,
    )
    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }

# Provisioned concurrency: 30  # keep 30 instances warm
# Memory: 2048 MB
# Timeout: 60 seconds
# Cold start: ~1 second
```

The 3am recovery (the deployment safety net):

```bash
# Kubernetes: restart the deployment
kubectl rollout restart deployment/pf-agent
# State is preserved in Postgres + Redis + S3
# In-flight requests are retried by the load balancer
# The on-call checks the audit log to see what failed

# Lambda: redeploy
aws lambda update-function-code \
  --function-name pf-agent \
  --image-uri pacificfreight/agent:v1.0.1
# State is preserved in DynamoDB
# No in-flight requests to retry (Lambda handles it)

# VM: restart the service
ssh daniel@pf-vm "sudo systemctl restart pf-agent"
# State is preserved on disk + Postgres
# In-flight requests are dropped (need client retry)
```

The 4 Kubernetes patterns in the agent's full deployment:

```python
KUBERNETES_PATTERNS = {
    "deployment": {
        "use_case": "The agent (stateless pods)",
        "examples": ["pf-agent", "northwind-agent"],
        "yaml_kind": "Deployment",
        "replicas": "3-10, auto-scaled by HPA",
    },
    "statefulset": {
        "use_case": "Stateful services (databases, queues)",
        "examples": ["postgres", "redis", "kafka"],
        "yaml_kind": "StatefulSet",
        "replicas": "1-3 (depending on quorum)",
    },
    "daemonset": {
        "use_case": "Observability infrastructure",
        "examples": ["fluent-bit (log collector)", "node-exporter (metrics)", "jaeger-agent (traces)"],
        "yaml_kind": "DaemonSet",
        "replicas": "1 per node",
    },
    "job_cronjob": {
        "use_case": "Batch + scheduled tasks",
        "examples": ["weekly-eval-run (CronJob)", "vector-reindex (Job)", "usage-report (CronJob)"],
        "yaml_kind": "Job / CronJob",
        "replicas": "1 (run to completion)",
    },
}
```

The pattern that wins interviews is the "3 platforms × 4 axes + stateless agent" pattern. The candidate who says "I pick Kubernetes for 100+ concurrent + engineering team + on-prem; Lambda for <100 concurrent + spiky + low engineering; VM for stateful + on-prem + budget. The agent is stateless; the state lives in Postgres + Redis + S3; the 3am recovery is `kubectl rollout restart`. The 4 K8s patterns: Deployment (agent), StatefulSet (DBs), DaemonSet (observability), Job/CronJob (batch). The wrong choice is Kubernetes for 10 concurrent runs (over-engineering). The right choice is the platform that matches the dominant axis" is the candidate who demonstrates the deployment-mindset.

## Code or example

The 4-axis deployment rubric (the FDE's tool picker):

```python
def pick_deployment_platform(requirements: dict) -> str:
    """Pick Kubernetes, serverless, or VM based on the 4 axes."""
    scale = requirements.get("concurrent_runs", 50)
    latency_p95_s = requirements.get("latency_p95_s", 2.0)
    team_engineering_depth = requirements.get("team_engineering_depth", "medium")  # low, medium, high
    on_prem = requirements.get("on_prem_required", False)

    if on_prem:
        if team_engineering_depth == "high":
            return "kubernetes (self-hosted)"
        return "vm (on-prem)"

    if team_engineering_depth == "low":
        if scale < 50:
            return "serverless (lambda)"
        return "container (cloud run or ECS Fargate)"

    if team_engineering_depth == "high":
        if scale > 100 or latency_p95_s < 1.0:
            return "kubernetes (EKS/GKE/AKS)"
        if scale < 50:
            return "vm (single EC2) or kubernetes (1 HA cluster)"
        return "kubernetes (EKS/GKE/AKS)"

    # Medium engineering depth
    if scale > 100:
        return "kubernetes (managed: EKS/GKE/AKS)"
    return "container (ECS Fargate or Cloud Run)"
```

The 5 most common deployment errors and fixes:

```python
DEPLOYMENT_ERRORS = {
    "image_pull_error": {
        "symptom": "Pod stuck in 'ImagePullBackOff'",
        "cause": "Image doesn't exist, wrong credentials, or wrong tag",
        "fix": "Verify the image in the registry; check imagePullSecrets; verify the tag matches the deployment",
    },
    "crash_loop_backoff": {
        "symptom": "Pod restarts every 30 seconds",
        "cause": "Application crashes on startup (missing env var, DB connection failed)",
        "fix": "Check pod logs: `kubectl logs <pod> --previous`; verify env vars; verify DB connectivity from the pod",
    },
    "out_of_memory": {
        "symptom": "Pod killed with OOMKilled; restarts",
        "cause": "Memory limit too low; memory leak in the application",
        "fix": "Increase memory limit; check for memory leaks with `kubectl top pod`",
    },
    "readiness_probe_failing": {
        "symptom": "Pod not in service (no traffic); 'Readiness probe failed'",
        "cause": "/readyz endpoint returns non-200; DB connection not established yet",
        "fix": "Increase initialDelaySeconds; verify the /readyz endpoint; check DB connectivity from the pod",
    },
    "hpa_not_scaling": {
        "symptom": "CPU at 90% but HPA didn't add pods",
        "cause": "HPA misconfigured; metrics server not running; maxReplicas too low",
        "fix": "Verify HPA: `kubectl describe hpa`; check metrics server logs; increase maxReplicas",
    },
}
```

The AtlasMart deployment (the case study):

```python
ATLASMART_DEPLOYMENT = {
    "platform": "Kubernetes (EKS on AWS)",
    "region": "us-east-1",
    "cluster": {
        "name": "atlasmart-prod",
        "version": "1.28",
        "node_groups": [
            {"name": "agent-nodes", "instance_type": "t3.medium", "min": 3, "max": 10, "desired": 3},
            {"name": "db-nodes", "instance_type": "t3.large", "min": 2, "max": 4, "desired": 2},
        ],
        "monthly_cost": "$120 (EKS + EC2)",
    },
    "deployments": [
        {"name": "atlasmart-agent", "kind": "Deployment", "replicas": 3, "image": "atlasmart/agent:v1.2.0"},
        {"name": "atlasmart-api", "kind": "Deployment", "replicas": 2, "image": "atlasmart/api:v1.2.0"},
    ],
    "statefulsets": [
        {"name": "postgres", "kind": "StatefulSet", "replicas": 1, "storage": "100GB gp3"},
        {"name": "redis", "kind": "StatefulSet", "replicas": 1, "storage": "10GB gp3"},
    ],
    "daemonsets": [
        {"name": "fluent-bit", "kind": "DaemonSet", "purpose": "log collection → CloudWatch"},
        {"name": "node-exporter", "kind": "DaemonSet", "purpose": "metrics → Prometheus"},
    ],
    "cronjobs": [
        {"name": "weekly-eval-run", "kind": "CronJob", "schedule": "0 9 * * MON", "purpose": "run eval set against production agent"},
        {"name": "daily-cost-report", "kind": "CronJob", "schedule": "0 0 * * *", "purpose": "report daily cost per tenant"},
    ],
    "scaling": {
        "agent_hpa": {"min": 3, "max": 10, "cpu_target": 70, "memory_target": 80},
    },
    "recovery": "kubectl rollout restart deployment/atlasmart-agent (single command)",
}
```

## Production addendum

The deployment question is the answer to "how do you deploy and scale an agent." The 60-second script:

> "3 platforms. Kubernetes (100s-1000s concurrent + engineering team + sub-second p95 + on-prem). Serverless (spiky + <100 concurrent + low engineering + tolerance for cold start). VM (stateful + on-prem + budget). 4 axes: scale, latency, team depth, on-prem. The agent is stateless; the state is in Postgres + Redis + S3; the 3am recovery is a single `kubectl rollout restart`. The 4 K8s patterns: Deployment (agent), StatefulSet (DBs), DaemonSet (observability), Job/CronJob (batch). The wrong choice is Kubernetes for 10 concurrent runs (over-engineering). The right choice is the platform that matches the dominant axis."

This is the difference between a candidate who says "I deployed the agent" and a candidate who says "3 platforms, 4 axes, stateless agent, 3am recovery is a single command, 4 K8s patterns, the wrong choice is over-engineering for scale the customer doesn't have." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/k8s/` — the K8s manifests.
- **Reference implementation**: `course/hardcode/level-6-production-systems/13-autoscaling-llm-service.py` — the canonical deployment patterns.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — deployment as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — multi-agent requires per-agent deployment.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — deployment as a system design topic.

## The 3 questions this lecture preps you for

1. **"How do you deploy and scale an agent?"** Answer: 3 platforms (Kubernetes for high scale + engineering team; serverless for spiky + low scale; VM for stateful + on-prem). 4 K8s patterns (Deployment for the agent, StatefulSet for DBs, DaemonSet for observability, Job/CronJob for batch). The agent is stateless; the state is in Postgres + Redis + S3; the 3am recovery is `kubectl rollout restart`.
2. **"Why is the agent stateless?"** Answer: the agent's state lives in Postgres (messages, tool calls, episodic memory), Redis (cache, idempotency, rate limit), and S3 (logs, backups). The pod can be killed at any time without losing data. The deployment is idempotent; the 3am recovery is a single command. Stateful agents = poor design.
3. **"When do you use Kubernetes vs Lambda?"** Answer: Kubernetes when the customer has 100+ concurrent runs, sub-second p95, or on-prem requirement. Lambda when the customer has spiky workloads, <100 concurrent runs, or limited engineering depth. The wrong choice is Kubernetes for 10 concurrent runs (over-engineering); the right choice is the platform that matches the dominant axis.

## Read next

`L8-3-message-brokers-and-queues.md` — the message broker pillar. SQS, Kafka, Redis Streams, RabbitMQ. Async vs sync, fan-out, exactly-once. How the agent handles 1000s of concurrent runs.