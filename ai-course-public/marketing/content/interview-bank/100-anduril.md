# 100. Anduril (ML / Lattice)

- **Role:** ML Engineer / Computer Vision Engineer (Lattice, Sentry, Ghost Helicopter, Roadrunner, Bolt)
- **Tech stack:** Rust, C++, Python, TypeScript, PyTorch, TensorRT, CUDA, ROS, gRPC, Kubernetes, embedded Linux
- **Comp band:** $180K-$400K (L3-L4 Senior); L5 (Staff) $350K-$700K; L6 Principal $500K-$1.2M (Levels.fyi 2026; lower than Big Tech, but mission + equity)
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, clearance status | 30 min | ~50% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML/CV or system design | 60 min | ~30% advance |
| 3. **Onsite (4-5 rounds)** | 1-2 coding, 1 system design, 1 ML/CV deep-dive, 1 behavioral | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Cross-functional review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp + level + team | 1 week | — |

Anduril is a defense-tech company building autonomous systems (Sentry towers, Ghost helicopters, Roadrunner interceptors, Bolt drones) and the Lattice software platform that connects them. ML is the core — perception, sensor fusion, autonomy, target tracking. The bar is high on technical depth and low on bureaucracy. Most roles require US citizenship; some need clearance.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your ML background"
**Answer:** "I built [X] for [Y], working on [perception / autonomy / sensor fusion / tracking]. Most recently I shipped [Z]."
**Tip:** Be specific. Anduril is defense-tech — they value mission clarity.

### Q1.2: "Why Anduril?"
**Answer:** "Three reasons. First, the mission is concrete — autonomous systems for national security is a meaningful application of ML. Second, Anduril ships hardware-software integrated systems at scale, not just models. Third, the engineering culture is fast and meritocratic — small teams, real ownership. I want my ML to actually move a drone, not just sit in a notebook."
**Tip:** Reference Lattice, specific products (Sentry, Ghost, Roadrunner, Bolt), and the 2026 launches.

### Q1.3: "Citizenship, clearance, willingness to deploy"
**Answer:** US citizenship is required for most roles. Active TS/SCI is a strong plus. Be honest about clearance status.

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Two Sum" or "LRU cache"
**Answer:** Standard.
**Tip:** Medium LeetCode. Anduril is moderate-hard but values clean, fast code.

### Q2.2: ML/CV — "How would you detect and track a drone in video?"
**Answer:** "Detection: YOLO-based or transformer-based object detector (RT-DETR, DINO) fine-tuned on drone imagery. Tracking: SORT or DeepSORT for short-term association, re-identification network for long-term across cameras. Sensor fusion: combine with radar and acoustic for redundancy. Latency: 30+ fps on embedded GPU (Jetson Orin). Eval: mAP for detection, MOTA for tracking, false-positive cost (false alarm → real missile is bad)."
**Tip:** Defense is asymmetric — false positives are very expensive. Mention this.

### Q2.3: System design — "Design Lattice's sensor fusion pipeline"
**Answer:** "Multiple sensors (camera, radar, lidar, acoustic) at different rates and latencies. Time sync via PTP. Per-sensor detections → tracker (Kalman + association) → fused track state → Lattice platform. Real-time constraints (<100ms latency). Edge inference (Jetson, embedded GPU). Backhaul: low-bandwidth metadata to command center. Eval: track continuity, ID swap rate, latency under load."
**Tip:** Sensor fusion is the Lattice core. Show you understand real-time constraints.

## Stage 3: Onsite (4-5 rounds, 1-2 days)

### Round 3.1: Coding (1-2 rounds)
**Q3.1.1:** "LRU cache" or "Merge intervals."
**Q3.1.2:** "Parse a config file" — recursive descent, error handling.
**Q3.1.3:** "Design a thread pool" — task queue, worker threads, graceful shutdown.

### Round 3.2: System design
**Q3.2.1:** "Design an autonomous drone's perception stack." Sensor pipeline, detection, tracking, SLAM, planning, control loop. Discuss embedded constraints (compute, power, latency).
**Q3.2.2:** "Design Lattice's command and control." Real-time video + telemetry, multi-user, low latency, RBAC, audit logging.

### Round 3.3: ML / CV deep-dive
**Q3.3.1:** "Walk me through a perception system you've shipped." End-to-end: data collection, labeling, training, optimization, deployment, monitoring.
**Q3.3.2:** "How do you handle adversarial conditions (low light, fog, rain, camouflage)?"
**Answer:** "Data augmentation: synthetic + real (collect in adverse conditions). Multi-modal sensor fusion (camera + radar + lidar + IR) — different sensors have different failure modes. Domain randomization. Test in conditions the model was trained for. Online adaptation. Reference Anduril's published work on adverse-weather perception."

### Round 3.4: Behavioral
**Q3.4.1:** "Time you shipped a feature to a hard deadline." STAR.
**Q3.4.2:** "Time you had to defend a technical decision to a non-technical stakeholder." STAR — military customers are not engineers.
**Q3.4.3:** "What's your view on autonomous weapons?" — be thoughtful. Anduril is controversial.

## Stage 4: Hiring committee
Anduril's committee is a structured loop debrief. L4 (Senior) requires independent ownership of a perception / autonomy module. L5 (Staff) requires cross-team influence on the platform. L6 (Principal) is rare and requires org-level technical leadership. Clearance is a real filter — many candidates can't progress without one.

## Stage 5: Offer
Anduril comp is below Big Tech for base, but equity is meaningful and the mission is unique. RSU is 4-year vest. They negotiate on equity. Relocation to Costa Mesa, Boston, or other sites is funded. Team match is usually pre-onsite for some roles.

## Tips for the Anduril loop
1. **Mission clarity matters** — be ready to defend why defense-tech.
2. **Real-time / embedded ML is the differentiator** — show you understand latency, power, edge inference.
3. **Sensor fusion is Lattice's core** — know the basics (Kalman, association, multi-modal).
4. **Asymmetric costs** — defense ML has very different false-positive vs false-negative tradeoffs.
5. **Coding is medium-hard LeetCode** — clean, fast code, often with system programming flavor.
6. **US citizenship and clearance are real filters** — be honest about your status.
7. **Reference Anduril's products** — Sentry, Ghost, Roadrunner, Bolt, Lattice.

## Real candidate report
> "I interviewed for ML on the perception team. The deep-dive was on detecting and tracking drones in cluttered environments — they pushed on sensor fusion (camera + radar) and the false-positive cost (a false alarm sends a $1M interceptor at a bird). Got L4 offer at $280K base + $500K RSU/4yr, Costa Mesa. They moved equity by $80K on negotiation. The loop was rigorous but the interviewers were mission-driven and friendly." — Blind, 2025

## Sources
- [Anduril Engineering Blog](https://www.anduril.com/newsroom/category/engineering/)
- [Anduril Lattice Platform](https://www.anduril.com/lattice/)
- [Levels.fyi Anduril](https://www.levels.fyi/companies/anduril-industries)
- [Glassdoor Anduril interviews](https://www.glassdoor.com/Interview/Anduril-Industries-Interview-Questions-E5131445.htm)
- [LeetCode Anduril tagged](https://leetcode.com/company/anduril/)