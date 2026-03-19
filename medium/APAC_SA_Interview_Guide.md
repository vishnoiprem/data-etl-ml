# How I would Prepare for an APAC Senior Solution Architect Interview  AI Infrastructure & Strategy

*A no-BS guide with real questions, real answers, flow diagrams, and code prototypes. Read this cover to cover and you'll walk in ready.*

---

## The Role in 60 Seconds

You're interviewing for a **Senior Solution Architect** at a global tech company building AI infrastructure across APAC — think pre-sales, CTO-level conversations, designing GPU clusters, and navigating compliance in Singapore, Japan, India, and Australia simultaneously. The bonus is 5–8 months. They're serious. You should be too.

This guide covers **12 real interview questions** spanning four rounds:

| Round       | Focus                          | Questions   |
|-------------|--------------------------------|-------------|
| **Round 1** | Technical Deep Dive            | Q1 – Q4     |
| **Round 2** | Solution Design & Architecture | Q5 – Q8     |
| **Round 3** | Strategy & Go-to-Market        | Q9 – Q10    |
| **Round 4** | Leadership & Ecosystem         | Q11 – Q12   |

---

## ROUND 1: Technical Deep Dive

---

### Q1: "Walk me through how you'd design an AI training infrastructure for a large APAC media company processing 50TB of video data daily."

**Why they ask this:** They want to see if you can translate a vague business requirement into a concrete, scalable architecture. This is your bread and butter.

**The Answer:**

Start by framing the problem before jumping into architecture. Say something like:

> "Before I sketch anything, I'd ask three questions: What's the training objective — generative models, recommendation, or content moderation? What's the latency tolerance for pipeline ingestion? And what's the compliance posture — is data staying in-region?"

Then walk through this architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                     │
│                                                             │
│   Video Sources ──► Kafka/Pulsar ──► Spark Streaming        │
│   (50TB/day)        (buffering)      (frame extraction,     │
│                                       transcoding)          │
│                          │                                  │
│                          ▼                                  │
├─────────────────────────────────────────────────────────────┤
│                    STORAGE LAYER                            │
│                                                             │
│   Raw: Object Storage (S3/OBS)  ──► Processed: Parallel FS  │
│   (cold tier, compliance)           (Lustre/GPFS for        │
│                                      training I/O)          │
│                          │                                  │
│                          ▼                                  │
├─────────────────────────────────────────────────────────────┤
│                    COMPUTE LAYER                            │
│                                                             │
│   GPU Cluster: 8x nodes, each 8x A100/H100 (80GB)           │
│   Interconnect: NVLink intra-node, RoCE v2 inter-node       │
│   Framework: PyTorch DDP / DeepSpeed ZeRO Stage 3           │
│                          │                                  │
│                          ▼                                  │
├─────────────────────────────────────────────────────────────┤
│                    ORCHESTRATION                            │
│                                                             │
│   Kubernetes + Volcano scheduler (gang scheduling)          │
│   MLflow (experiment tracking) + Airflow (pipeline DAGs)    │
│                          │                                  │
│                          ▼                                  │
├─────────────────────────────────────────────────────────────┤
│                    SERVING / OUTPUT                         │
│                                                             │
│   Model Registry ──► Triton Inference Server ──► CDN Edge   │
│                      (batched inference,                    │
│                       dynamic batching)                     │
└─────────────────────────────────────────────────────────────┘
```

**Code Prototype — GPU Health Check Script:**

This is the kind of thing you'd hand to an ops team on day one:

```python
import subprocess
import json
from datetime import datetime

def gpu_cluster_health_check(nodes: list[str]) -> dict:
    """
    Quick GPU cluster health assessment.
    Run this before any large training job kicks off.
    """
    report = {"timestamp": datetime.utcnow().isoformat(), "nodes": []}
    
    for node in nodes:
        node_status = {"hostname": node, "gpus": [], "healthy": True}
        
        # Query GPU stats via nvidia-smi
        cmd = f"ssh {node} nvidia-smi --query-gpu=index,name,temperature.gpu,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        
        for line in result.stdout.strip().split("\n"):
            idx, name, temp, mem_used, mem_total, util = line.split(", ")
            gpu = {
                "index": int(idx),
                "model": name,
                "temp_c": int(temp),
                "memory_used_mb": int(mem_used),
                "memory_total_mb": int(mem_total),
                "utilization_pct": int(util),
            }
            
            # Flag unhealthy conditions
            if gpu["temp_c"] > 85:
                gpu["warning"] = "THERMAL_THROTTLE_RISK"
                node_status["healthy"] = False
            if gpu["memory_used_mb"] > gpu["memory_total_mb"] * 0.95:
                gpu["warning"] = "MEMORY_NEAR_FULL"
                node_status["healthy"] = False
            
            node_status["gpus"].append(gpu)
        
        report["nodes"].append(node_status)
    
    healthy_count = sum(1 for n in report["nodes"] if n["healthy"])
    report["summary"] = f"{healthy_count}/{len(nodes)} nodes healthy"
    return report

# Usage
nodes = ["gpu-node-01", "gpu-node-02", "gpu-node-03", "gpu-node-04"]
health = gpu_cluster_health_check(nodes)
print(json.dumps(health, indent=2))
```

**Key talking points to emphasize:**
- You chose **parallel filesystem** over NFS because 50TB/day will destroy NFS throughput
- **RoCE v2** over InfiniBand if the client is cost-sensitive (common in APAC media)
- **Gang scheduling** via Volcano ensures all GPUs for a job are available before any start — prevents resource deadlock
- Mention compliance: "In APAC, I'd confirm if PDPA (Singapore), APPI (Japan), or DPDP (India) apply to the video data"

---

### Q2: "Explain the difference between AI training and inference infrastructure. How does this affect your architecture recommendations?"

**Why they ask this:** This is a filter question. If you can't articulate this cleanly, the interview is over.

**The Answer:**

```
TRAINING vs INFERENCE — Side by Side

┌──────────────────────┬───────────────────────┐
│      TRAINING        │      INFERENCE        │
├──────────────────────┼───────────────────────┤
│ GPU: H100/A100 80GB  │ GPU: L4/T4 or custom  │
│ (max memory & FLOPS) │ (cost per query)      │
├──────────────────────┼───────────────────────┤
│ Batch-oriented       │ Real-time / streaming │
│ Hours to weeks       │ Milliseconds          │
├──────────────────────┼───────────────────────┤
│ Network: 400Gbps+    │ Network: 10-25Gbps    │
│ (all-reduce comms)   │ (load balancing)      │
├──────────────────────┼───────────────────────┤
│ Storage: High IOPS   │ Storage: Model cache  │
│ parallel FS          │ fast SSD              │
├──────────────────────┼───────────────────────┤
│ Scale: Fewer, bigger │ Scale: Many, smaller  │
│ clusters             │ distributed nodes     │
├──────────────────────┼───────────────────────┤
│ Cost driver: GPU hrs │ Cost driver: Queries  │
│ (CapEx heavy)        │ (OpEx heavy)          │
├──────────────────────┼───────────────────────┤
│ Failure mode:        │ Failure mode:         │
│ Checkpoint & resume  │ Failover & replicate  │
└──────────────────────┴───────────────────────┘
```

Then say:

> "This distinction fundamentally shapes my recommendations. For a client building an AIGC product, I'd propose a **shared data lake** feeding both pipelines, but with **separate compute pools**. Training runs on a scheduled, burst-capable cluster. Inference runs on an auto-scaling fleet behind a load balancer. They share nothing at the compute layer — different failure domains, different SLAs."

**Code Prototype — Simple Cost Estimator:**

```python
def estimate_infra_cost(
    mode: str,           # "training" or "inference"
    gpu_type: str,       # "H100", "A100", "L4"
    gpu_count: int,
    hours_per_day: float,
    days: int,
    queries_per_day: int = 0  # for inference
) -> dict:
    """
    Back-of-envelope cost estimator for client proposals.
    Prices approximate — adjust per region and vendor.
    """
    GPU_HOURLY_RATES = {
        "H100": 3.50, "A100": 2.20, "L4": 0.70, "T4": 0.40
    }
    
    rate = GPU_HOURLY_RATES.get(gpu_type, 2.00)
    total_gpu_hours = gpu_count * hours_per_day * days
    compute_cost = total_gpu_hours * rate
    
    # Networking: ~15% of compute for training, ~5% for inference
    network_multiplier = 0.15 if mode == "training" else 0.05
    
    # Storage: ~10% of compute for training, ~3% for inference
    storage_multiplier = 0.10 if mode == "training" else 0.03
    
    total = compute_cost * (1 + network_multiplier + storage_multiplier)
    
    result = {
        "mode": mode,
        "gpu": f"{gpu_count}x {gpu_type}",
        "duration": f"{days} days @ {hours_per_day}h/day",
        "compute_cost": f"${compute_cost:,.0f}",
        "total_estimated": f"${total:,.0f}",
    }
    
    if mode == "inference" and queries_per_day > 0:
        cost_per_1k_queries = (total / days) / (queries_per_day / 1000)
        result["cost_per_1k_queries"] = f"${cost_per_1k_queries:.2f}"
    
    return result

# Training scenario
print(estimate_infra_cost("training", "H100", 64, 24, 30))
# Inference scenario  
print(estimate_infra_cost("inference", "L4", 16, 24, 30, queries_per_day=1_000_000))
```

---

### Q3: "A client in Singapore wants to deploy a real-time recommendation engine. They're seeing 200ms p99 latency. How do you diagnose and fix this?"

**Why they ask this:** Performance debugging is a daily reality. They want to see your diagnostic methodology, not just "add more GPUs."

**The Answer:**

Walk through a systematic debugging flow:

```
LATENCY DIAGNOSIS FLOW
══════════════════════

Client reports: p99 = 200ms (target: <50ms)
                     │
                     ▼
          ┌─────────────────────┐
          │  1. WHERE is the    │
          │     latency?        │
          └─────────┬───────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Network │ │  Model  │ │  Data   │
   │ Transit │ │ Compute │ │  Fetch  │
   │  ~20ms  │ │ ~100ms  │ │  ~80ms  │
   └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Fix:    │ │ Fix:    │ │ Fix:    │
   │ Edge    │ │ Quantize│ │ Feature │
   │ deploy, │ │ INT8,   │ │ store,  │
   │ keep-   │ │ distill,│ │ cache   │
   │ alive   │ │ batch   │ │ hot     │
   │ conns   │ │ optimize│ │ items   │
   └─────────┘ └─────────┘ └─────────┘
                    │
                    ▼
          ┌─────────────────────┐
          │  2. VALIDATE fix    │
          │  A/B test with      │
          │  canary deployment  │
          └─────────────────────┘
```

> "My first move is always **distributed tracing** — I'd instrument the pipeline with OpenTelemetry to see exactly where the 200ms is going. In my experience, it's rarely the model itself. Most APAC recommendation latency issues come from **feature store lookups** hitting a database that's in a different availability zone, or **cold model loading** after scale-up events."

**Code Prototype — Latency Profiler:**

```python
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

@dataclass
class LatencyProfile:
    """Profile each stage of the inference pipeline."""
    stages: dict = field(default_factory=dict)
    
    @contextmanager
    def measure(self, stage_name: str):
        start = time.perf_counter_ns()
        yield
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        self.stages[stage_name] = elapsed_ms
    
    def report(self) -> str:
        total = sum(self.stages.values())
        lines = [f"{'Stage':<25} {'Time (ms)':>10} {'%':>6}"]
        lines.append("-" * 43)
        for stage, ms in sorted(self.stages.items(), key=lambda x: -x[1]):
            lines.append(f"{stage:<25} {ms:>10.2f} {ms/total*100:>5.1f}%")
        lines.append("-" * 43)
        lines.append(f"{'TOTAL':<25} {total:>10.2f}")
        return "\n".join(lines)

# Usage in a recommendation pipeline
profile = LatencyProfile()

with profile.measure("feature_store_lookup"):
    time.sleep(0.08)  # Simulating 80ms feature fetch

with profile.measure("model_inference"):
    time.sleep(0.10)  # Simulating 100ms inference

with profile.measure("post_processing"):
    time.sleep(0.015) # Simulating 15ms ranking/filtering

with profile.measure("network_serialization"):
    time.sleep(0.005) # Simulating 5ms response encoding

print(profile.report())
```

Output:
```
Stage                      Time (ms)      %
-------------------------------------------
model_inference               100.00  50.0%
feature_store_lookup           80.00  40.0%
post_processing                15.00   7.5%
network_serialization           5.00   2.5%
-------------------------------------------
TOTAL                         200.00
```

> "Once I see that breakdown, my playbook is: quantize the model to INT8 (cuts inference by ~40%), move the feature store to a co-located Redis cluster, and pre-compute the top-1000 items per user segment. That should get us under 50ms."

---

### Q4: "How do you handle data sovereignty and compliance when designing AI infrastructure across multiple APAC countries?"

**Why they ask this:** APAC is a compliance minefield. This question separates architects who've actually deployed in-region from those who just draw boxes.

**The Answer:**

```
APAC DATA SOVEREIGNTY MAP
═══════════════════════════

┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  SINGAPORE  │   │    JAPAN    │   │    INDIA    │
│             │   │             │   │             │
│ PDPA 2012   │   │ APPI 2003   │   │ DPDP 2023   │
│ + Amendments│   │ + 2022 Rev  │   │ (New!)      │
│             │   │             │   │             │
│ Cross-border│   │ Adequacy    │   │ Data local- │
│ transfers   │   │ countries   │   │ ization for │
│ OK with     │   │ whitelisted │   │ "critical"  │
│ safeguards  │   │             │   │ personal    │
│             │   │             │   │ data        │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────┬────────┘                 │
                │                          │
                ▼                          ▼
   ┌────────────────────┐    ┌────────────────────┐
   │  ARCHITECTURE:     │    │  ARCHITECTURE:     │
   │  Regional Hub      │    │  Sovereign Zone    │
   │                    │    │                    │
   │  • SG + JP can     │    │  • India compute   │
   │    share compute   │    │    stays in India  │
   │    pool            │    │  • Separate K8s    │
   │  • Unified model   │    │    cluster         │
   │    registry        │    │  • Local model     │
   │  • Cross-border    │    │    registry mirror │
   │    training OK     │    │  • Federated       │
   │                    │    │    learning for    │
   │                    │    │    training        │
   └────────────────────┘    └────────────────────┘

       ┌─────────────────┐   ┌─────────────────┐
       │   AUSTRALIA     │   │ SOUTH KOREA     │
       │                 │   │                 │
       │ Privacy Act     │   │ PIPA 2011       │
       │ 1988 + APPs     │   │ + 2023 Amend    │
       │                 │   │                 │
       │ Flexible but    │   │ Strict consent  │
       │ "reasonable     │   │ requirements,   │
       │ steps" for      │   │ cross-border    │
       │ overseas        │   │ transfer rules  │
       │ disclosure      │   │ relaxing        │
       └─────────────────┘   └─────────────────┘
```

> "My approach is what I call **'Compliance by Architecture.'** Instead of bolting compliance on after the design, I build the infrastructure topology around the regulatory map. For APAC, this usually means a **hub-and-spoke model**: Singapore as the hub for training (it has the most flexible data transfer rules), with sovereign inference zones in India and any other countries requiring data localization."

> "Practically, that means: Kubernetes federation across regions, each cluster self-contained for inference. Training data is anonymized and aggregated before it leaves a sovereign zone. Model weights (not data) are synced centrally. I'd also implement **data classification at ingestion** — every record gets tagged with its jurisdiction, and the orchestration layer enforces placement rules."

---

## ROUND 2: Solution Design & Architecture

---

### Q5: "Walk me through how you'd approach a pre-sales engagement with a major OTT platform looking to build AIGC capabilities."

**Why they ask this:** This is the job. Pre-sales is where deals are won or lost. They want to see your process.

**The Answer:**

```
PRE-SALES ENGAGEMENT FLOW
══════════════════════════

WEEK 1-2: DISCOVERY
────────────────────
     ┌──────────────────────────────┐
     │     STAKEHOLDER MAPPING      │
     │                              │
     │  CTO ─── "What's possible?"  │
     │  VP Eng ─ "Can we build it?" │
     │  CFO ─── "What's the ROI?"   │
     │  Legal ── "Are we covered?"  │
     └──────────────┬───────────────┘
                    │
                    ▼
     ┌──────────────────────────────┐
     │     NEEDS ASSESSMENT         │
     │                              │
     │  • Current infra audit       │
     │  • AI maturity score (1-5)   │
     │  • Use case prioritization   │
     │  • Data readiness check      │
     └──────────────┬───────────────┘
                    │
WEEK 3-4: SOLUTION DESIGN             
──────────────────────────
                    │
                    ▼
     ┌──────────────────────────────┐
     │     REFERENCE ARCHITECTURE   │
     │                              │
     │  Tailored to their stack     │
     │  3 options: Good/Better/Best │
     │  TCO comparison vs. cloud    │
     │  Migration roadmap           │
     └──────────────┬───────────────┘
                    │
WEEK 5-6: VALIDATION
────────────────────
                    │
                    ▼
     ┌──────────────────────────────┐
     │     POC / BENCHMARK          │
     │                              │
     │  Run their actual workload   │
     │  on proposed infra           │
     │  Measure: throughput, cost,  │
     │  time-to-train               │
     └──────────────┬───────────────┘
                    │
                    ▼
     ┌──────────────────────────────┐
     │     PROPOSAL & CLOSE         │
     │                              │
     │  POC results as evidence     │
     │  Phased deployment plan      │
     │  Support & SLA framework     │
     └──────────────────────────────┘
```

> "I always start with stakeholder mapping. In APAC OTT companies, the buying committee is usually fragmented — the CTO cares about capabilities, the VP of Engineering about integration, and the CFO about payback period. I tailor different narratives for each."

> "For the solution itself, I present three tiers. The 'Good' tier is cloud-based with managed services — fast to deploy, higher unit cost. 'Better' is a hybrid with on-prem GPU clusters for training and cloud burst for peak inference. 'Best' is a fully optimized on-prem AI factory with our hardware, custom-tuned networking, and long-term support. Most APAC OTT clients land on 'Better' because they want control over training data but don't want to manage inference scaling."

---

### Q6: "Design an AI architecture for a media company that needs real-time content recommendation AND offline content generation (AIGC). How do you handle the shared infrastructure?"

**Why they ask this:** Dual-workload architecture is the real world. They want to see if you can optimize shared resources without creating conflicts.

**The Answer:**

```
DUAL-WORKLOAD ARCHITECTURE
═══════════════════════════

                    ┌─────────────────────┐
                    │    SHARED DATA LAKE │
                    │   (Object Storage)  │
                    │                     │
                    │  User behavior logs │
                    │  Content metadata   │
                    │  Generated assets   │
                    └─────────┬───────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
    ┌────────────────────┐   ┌────────────────────┐
    │  RECOMMENDATION    │   │     AIGC           │
    │  PIPELINE          │   │     PIPELINE       │
    │  (Real-time)       │   │     (Batch/Stream) │
    ├────────────────────┤   ├────────────────────┤
    │                    │   │                    │
    │ Feature Store      │   │ Prompt Queue       │
    │ (Redis Cluster)    │   │ (Kafka)            │
    │       │            │   │       │            │
    │       ▼            │   │       ▼            │
    │ Ranking Model      │   │ Diffusion/LLM      │
    │ (Lightweight,      │   │ (Heavy GPU,        │
    │  INT8 quantized)   │   │  FP16/BF16)        │
    │       │            │   │       │            │
    │       ▼            │   │       ▼            │
    │ Serving: Triton    │   │ Output: Asset      │
    │ SLA: <50ms p99     │   │ Store + CDN        │
    │                    │   │ SLA: <30min/asset  │
    │ GPU: L4 fleet      │   │                    │
    │ (auto-scaling)     │   │ GPU: H100 cluster  │
    │                    │   │ (scheduled jobs)   │
    └────────────────────┘   └────────────────────┘
                 │                         │
                 └────────────┬────────────┘
                              │
                 ┌────────────┴────────────-┐
                 │    SHARED SERVICES       │
                 │                          │
                 │  • Kubernetes Platform   │
                 │  • Monitoring (Grafana)  │
                 │  • Model Registry (MLflow│
                 │  • CI/CD Pipeline        │
                 │  • Identity & Access     │
                 └─────────────────────────-┘
```

> "The key insight is: **share the platform, separate the compute.** Both workloads run on the same Kubernetes cluster, but in different node pools with different GPU types. The recommendation pipeline gets L4 GPUs with autoscaling — it needs to handle traffic spikes. The AIGC pipeline gets H100s on a fixed schedule — it runs batch jobs overnight when recommendation traffic is low."

> "The real trick is the **GPU time-sharing policy.** During peak hours (6 PM – midnight in each timezone), 100% of GPU resources go to recommendation. During off-peak, AIGC jobs can burst onto recommendation nodes. Kubernetes priority classes make this automatic."

**Code Prototype — Resource Scheduler:**

```python
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

@dataclass
class GPUPool:
    name: str
    total_gpus: int
    gpu_type: str
    
@dataclass  
class WorkloadPolicy:
    """Dynamic GPU allocation based on time of day per APAC timezone."""
    
    recommendation_pool: GPUPool
    aigc_pool: GPUPool
    
    APAC_PEAK_HOURS = range(18, 24)  # 6 PM to midnight local
    
    def get_allocation(self, local_hour: int) -> dict:
        is_peak = local_hour in self.APAC_PEAK_HOURS
        
        if is_peak:
            return {
                "recommendation": {
                    "pool": self.recommendation_pool.name,
                    "gpus": self.recommendation_pool.total_gpus,
                    "priority": "CRITICAL",
                    "can_preempt_aigc": True,
                },
                "aigc": {
                    "pool": self.aigc_pool.name,
                    "gpus": self.aigc_pool.total_gpus,
                    "priority": "BEST_EFFORT",
                    "can_burst": False,
                }
            }
        else:
            # Off-peak: AIGC can burst onto recommendation GPUs
            return {
                "recommendation": {
                    "pool": self.recommendation_pool.name,
                    "gpus": self.recommendation_pool.total_gpus // 2,
                    "priority": "HIGH",
                    "can_preempt_aigc": True,
                },
                "aigc": {
                    "pool": self.aigc_pool.name,
                    "gpus": self.aigc_pool.total_gpus + self.recommendation_pool.total_gpus // 2,
                    "priority": "HIGH",
                    "can_burst": True,
                }
            }

# Example
policy = WorkloadPolicy(
    recommendation_pool=GPUPool("rec-pool", 32, "L4"),
    aigc_pool=GPUPool("aigc-pool", 16, "H100")
)

# Peak hour allocation (8 PM Singapore)
print("Peak:", policy.get_allocation(20))
# Off-peak allocation (3 AM Singapore)  
print("Off-peak:", policy.get_allocation(3))
```

---

### Q7: "You're presenting to a CTO who is skeptical about on-premises AI infrastructure vs. going all-cloud. How do you make the case?"

**Why they ask this:** This is a sales conversation disguised as a technical question. They want to see you balance technical truth with business persuasion.

**The Answer:**

> "I never argue against cloud. Instead, I reframe the conversation around total cost of ownership and control."

```
THE TCO CONVERSATION
════════════════════

CLOUD-ONLY (Year 1-3)
──────────────────────
Year 1:  $████████████  ($1.2M)  ← Fast start
Year 2:  $████████████████  ($1.6M)  ← Usage grows  
Year 3:  $████████████████████  ($2.1M)  ← Lock-in premium
TOTAL:   $4.9M
Control: Low | Data exit cost: High | Customization: Limited

HYBRID (Our Proposal)
─────────────────────
Year 1:  $████████████████  ($1.8M)  ← Higher upfront
Year 2:  $████████████  ($0.9M)  ← Amortization kicks in
Year 3:  $████████  ($0.6M)  ← Running cost only
TOTAL:   $3.3M (33% savings)
Control: High | Data sovereignty: Full | Customization: Full

ON-PREM AI FACTORY
──────────────────
Year 1:  $████████████████████████  ($3.0M)  ← Big CapEx
Year 2:  $████  ($0.4M)  ← Ops only
Year 3:  $████  ($0.4M)  ← Ops only
TOTAL:   $3.8M
Control: Maximum | But: Scaling flexibility limited
```

> "I show three scenarios. Cloud is cheapest in year one but the most expensive by year three because of egress fees and GPU-hour accumulation. Hybrid is the sweet spot for most APAC enterprises — train on-prem where data is sensitive, burst to cloud for experimentation and inference scaling. I also bring up a point that resonates strongly with APAC CTOs: **data gravity.** Once 50TB of training data lives in a cloud provider, you're paying to move it forever."

---

### Q8: "Tell me about a time you identified an infrastructure bottleneck that the client didn't even know existed."

**Why they ask this:** Behavioral question testing real-world experience. Use STAR format but keep it technical.

**The Answer (use your own experience, but here's a strong template):**

> "At a streaming platform in Southeast Asia, the client complained that their recommendation model training was taking 3x longer than expected. They assumed they needed more GPUs."

> "I profiled the training pipeline and found the bottleneck wasn't compute — GPU utilization was only 40%. The issue was their **data loading pipeline.** They were reading training samples from a standard NFS share, and the I/O throughput was 2 GB/s on a system that needed 12 GB/s to keep 64 GPUs fed."

```
BOTTLENECK ANALYSIS
═══════════════════

BEFORE (Client's assumption)
─────────────────────────────
Data (NFS) ──[2 GB/s]──► CPU ──► GPU (40% util)
                              ↑
                         Bottleneck was HERE
                         (not GPU count)

AFTER (Our fix)
───────────────
Data (Lustre) ──[15 GB/s]──► CPU ──► GPU (92% util)
  + prefetch                    + DALI pipeline
  + local NVMe cache            (GPU-accelerated
                                 preprocessing)
```

> "We replaced NFS with Lustre, added NVIDIA DALI for GPU-accelerated data preprocessing, and implemented a prefetch buffer on local NVMe. GPU utilization went from 40% to 92%. Training time dropped by 60% — without adding a single GPU. The client saved $400K in hardware they were about to order."

---

## ROUND 3: Strategy & Go-to-Market

---

### Q9: "How would you build a go-to-market strategy for AI infrastructure solutions targeting APAC internet companies?"

**Why they ask this:** You're not just a technician. This role requires strategic thinking about markets, segments, and competitive positioning.

**The Answer:**

```
GTM STRATEGY — APAC AI INFRASTRUCTURE
══════════════════════════════════════

SEGMENT ──────────► TIER 1: Hyperscale OTT
(Who)                (3-5 accounts: deep engagement)
                    │
                    ├─► TIER 2: Regional Tech
                    │   (10-15 accounts: solution selling)
                    │
                    └─► TIER 3: AI-Native Startups
                        (50+ accounts: product-led, self-serve)

POSITION ─────────► "Not selling hardware.
(What)               Selling time-to-production."
                    │
                    Key differentiator:
                    End-to-end AI factory, not components

CHANNEL ──────────► Direct (Tier 1)
(How)               + SI Partners (Tier 2)
                    + Cloud Marketplace (Tier 3)

PROVE ────────────► Reference architectures per vertical:
(Evidence)          │
                    ├─► Media: AIGC + Recommendation
                    ├─► Gaming: Real-time inference at edge
                    ├─► E-commerce: Search + Personalization
                    └─► FinTech: Fraud detection + Risk scoring

TIMELINE ─────────► Q1: Lighthouse wins (2-3 logos)
                    Q2: Case studies + ecosystem events
                    Q3: Scale via partners
                    Q4: Refresh cycle for next gen hardware
```

> "My GTM philosophy for APAC is: **win the lighthouse, publish the playbook, enable the channel.** I'd identify 2-3 marquee OTT or internet companies per market — the ones that everyone else benchmarks against. Win those accounts with deep, white-glove solution architecture. Then package those wins into reusable playbooks that our partner SI firms can execute at scale."

---

### Q10: "What are the biggest competitive threats in the APAC AI infrastructure market and how would you position against them?"

**Why they ask this:** Market awareness. You need to know the landscape cold.

**The Answer:**

```
COMPETITIVE LANDSCAPE — APAC AI INFRA
══════════════════════════════════════

┌─────────────────────────────────────────────────────┐
│                POSITIONING MAP                       │
│                                                     │
│  Full-Stack │  [OUR CLIENT]     [NVIDIA DGX]       │
│  Solution   │       ●                ●             │
│             │                                       │
│             │                                       │
│             │  [Cloud              [CoreWeave/      │
│  Platform   │   Providers]          Lambda]         │
│             │    ● AWS/Azure/GCP       ●            │
│             │                                       │
│             │                                       │
│  Components │  [ODM/White-box]   [Supermicro]      │
│  Only       │       ●                ●             │
│             │                                       │
│             └───────────────────────────────────────│
│               Low Cost/        Premium/             │
│               Commodity        Differentiated       │
└─────────────────────────────────────────────────────┘
```

> "In APAC, the competitive dynamic is three-layered. At the top, NVIDIA sells DGX directly — premium, proven, but expensive and supply-constrained. In the middle, cloud providers offer GPU instances — flexible but with data sovereignty concerns that matter a lot in Japan, India, and Indonesia. At the bottom, ODMs offer cheap hardware but zero solution capability."

> "Our position is the **integrated sweet spot**: competitive hardware with full solution architecture, local support, and compliance-aware design. Against NVIDIA, we compete on price and local presence. Against cloud, we compete on TCO and data control. Against ODMs, we compete on everything above the hardware."

---

## ROUND 4: Leadership & Ecosystem

---

### Q11: "How would you enable a team of 20 solution architects across APAC who have networking backgrounds but limited AI experience?"

**Why they ask this:** Knowledge transfer and team building. This role is a force multiplier.

**The Answer:**

```
ENABLEMENT PROGRAM
══════════════════

MONTH 1: FOUNDATIONS
────────────────────
┌──────────────────────────────────────────┐
│  Week 1-2: "AI Infra 101" bootcamp      │
│  • GPU architecture (why GPUs, not CPUs) │
│  • Training vs inference fundamentals    │
│  • Hands-on: deploy a model on Triton   │
│                                          │
│  Week 3-4: "The Conversation"            │
│  • How to talk to a CTO about AI        │
│  • Discovery question frameworks         │
│  • Objection handling playbook           │
└──────────────────────────────────────────┘

MONTH 2-3: SPECIALIZATION
─────────────────────────
┌──────────────────────────────────────────┐
│  Track A: Training Architecture          │
│  Track B: Inference & Edge               │
│  Track C: Data Platform & Compliance     │
│                                          │
│  Each SA picks a primary + secondary     │
│  Certification exam at end               │
└──────────────────────────────────────────┘

ONGOING: COMMUNITY OF PRACTICE
──────────────────────────────
┌──────────────────────────────────────────┐
│  • Weekly "Win/Loss Review" calls        │
│  • Monthly "Architecture Clinic"         │
│  • Shared playbook repo (living docs)    │
│  • Buddy system: pair new SA with        │
│    experienced SA for first 3 deals      │
└──────────────────────────────────────────┘
```

> "The biggest mistake I've seen is dumping a 200-slide AI training on network engineers. My approach is **learn by doing.** In the first week, every SA deploys a real model on a real GPU server. They see the nvidia-smi output, they watch GPU utilization spike during inference, they experience what happens when you run out of GPU memory. That visceral understanding is worth more than a month of theory."

> "I'd also create a **playbook repository** — living documents for every engagement type. When an SA walks into a meeting with a media company CTO, they open the 'Media & AIGC Playbook' and it has discovery questions, reference architectures, competitive positioning, and objection handlers all in one place."

---

### Q12: "Where do you see AI infrastructure evolving in APAC over the next 3 years, and how would you position us for that future?"

**Why they ask this:** Vision and strategic thinking. They want to see if you're a forward-looking leader, not just a reactive architect.

**The Answer:**

```
APAC AI INFRA EVOLUTION — 2025-2028
════════════════════════════════════

2025 (NOW)                    2026                       2027-2028
──────────                    ────                       ─────────

Centralized                   Distributed                Sovereign
GPU clusters                  AI Factories               AI Mesh
     │                             │                          │
     │  • Training in              │  • Multi-site            │  • Country-level
     │    data centers             │    training              │    AI sovereignty
     │  • Cloud inference          │  • Edge inference        │  • Federated
     │  • Batch AIGC               │    networks              │    learning at
     │                             │  • Real-time AIGC        │    scale
     │                             │                          │  • AI-as-
     ▼                             ▼                          │    infrastructure
                                                              ▼
MARKET SIZE (APAC AI Infra):                                   
$15B ──► $28B ──► $45B+                                       

KEY SHIFTS:
───────────
1. GPU scarcity ──► GPU commoditization (custom silicon enters)
2. Training-centric ──► Inference-centric (80% of spend)
3. English-first AI ──► Multilingual-native (JP, KR, TH, ID)
4. Cloud-default ──► Hybrid-default (sovereignty drives this)
5. Single-model ──► Compound AI systems (RAG, agents, pipelines)
```

> "Three big shifts will define APAC AI infrastructure. First, **inference will dominate spend** — by 2027, I expect 80% of AI compute in production will be inference, not training. That means our product roadmap should prioritize inference-optimized hardware and edge deployment capabilities."

> "Second, **sovereign AI** is coming. India's DPDP Act, Indonesia's forthcoming PDP law, and Vietnam's data localization requirements will force every major enterprise to have in-country AI compute. That's a massive opportunity for a hardware vendor with local presence."

> "Third, **compound AI systems** — not single models, but orchestrated pipelines of models, retrievers, and agents — will be the dominant architecture pattern. Our infrastructure needs to support not just raw GPU compute but the orchestration layer: fast inter-service communication, shared memory pools, and intelligent scheduling across heterogeneous hardware."

---

## Final Tips for the Day

**Before the interview:**
- Know the company's recent AI product launches (search their newsroom the morning of)
- Have 3 customer stories ready: one success, one failure you recovered from, one where you walked away
- Prepare a 1-page "90-day plan" for the role — interviewers love proactive candidates

**During the interview:**
- Draw. Always draw. Ask for a whiteboard or share your screen. Architects who only talk lose to architects who sketch
- Name specific technologies, not categories ("Triton Inference Server" not "a serving platform")
- When you don't know something, say "I'd need to research that, but my instinct is..." — then give your instinct

**APAC-specific signals to hit:**
- Mention at least 2 specific regulations by name (PDPA, APPI, DPDP)
- Reference timezone-aware operations (APAC spans UTC+5 to UTC+12)
- Show awareness of language diversity in AI models (Japanese, Korean, Thai, Bahasa)
- Acknowledge the SI/partner ecosystem — APAC enterprise sales run through partners

---

*Good luck. You've got this.*
