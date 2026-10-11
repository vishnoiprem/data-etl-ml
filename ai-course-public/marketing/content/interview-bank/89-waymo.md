# 89. Waymo

- **Role:** ML Engineer (Perception / Planning)
- **Tech stack:** C++, Python, PyTorch/JAX, CUDA, TensorFlow, ROS
- **Comp band:** $250K-$700K total comp (L3-L6) | RSUs 4-year, 1-year cliff (Alphabet GOOG)
- **Cumulative pass rate:** ~2-3%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (a self-driving sensor stack — a roof-mounted lidar with camera + radar pods fanning into a fused BEV map). Color: Waymo green-blue (#0F9D58) on charcoal. Headline: "Waymo / AI ML Engineer / 2026".

> **TL;DR:** Waymo's loop is safety-first autonomy — every round asks "what could go wrong?" and the design question is almost always a perception or planning pipeline, not a generic web system. The winning candidate treats safety as a meta-rubric, has read the Disengagement Reports, and can derive BEV attention on a whiteboard.

```
┌──────────────────────────────────────────────────────────────────┐
│                     WAYMO AUTONOMY STACK                          │
├──────────────────────────────────────────────────────────────────┤
│  Cameras + Lidar + Radar                                          │
│          │                                                        │
│          ▼                                                        │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐  │
│  │   Perception   │───▶│   Prediction   │───▶│   Planning     │  │
│  │  (BEV / Det)   │    │ (motion model) │    │ (lattice / RL) │  │
│  └────────────────┘    └────────────────┘    └────────────────┘  │
│          │                       │                     │          │
│          ▼                       ▼                     ▼          │
│      Tracking              Scene graph           Trajectory →     │
│   (Kalman + Hungarian)   (agents + map)         Controller       │
│                                                                  │
│  Closed loop ──▶ Simulation (10M mi/day) ──▶ Safety review       │
└──────────────────────────────────────────────────────────────────┘
```

## Hiring rounds (5 stages)

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, team fit (Perception, Planning, Simulation, ML Infra). | 1 week | ~50% advance |
| 2. **Technical phone screen (60 min)** | 1 coding (C++/Python medium) + 1 ML fundamentals. | 1-2 weeks | ~40% advance |
| 3. **Onsite (4-5 rounds in 1-2 days)** | 2 coding → 1 system design (autonomy) → 1 ML deep-dive → 1 behavioral (safety). | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Packet + safety review. | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp negotiation. | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about a recent ML system you shipped to production."
**Answer:** Use STAR: situation (the product), task (your role), action (the technical decisions: model architecture, data pipeline, eval framework, deployment), result (latency, accuracy, business impact with specific numbers). Example: "I shipped a real-time object detection model to a 10K-DPU fleet, reducing false negatives by 23% while keeping p99 latency under 80ms."
**Tip:** Waymo values safety-critical systems thinking. Mention monitoring, rollback, and failure modes.

### Q1.2: "Why Waymo, specifically?"
**Answer:** Specific bet + test + disagreement. "I want to work on the Perception team because the safety bar is 10× higher than consumer AV. The bet: the camera + lidar + radar fusion is the key moat vs. Tesla's vision-only approach. The 1 thing I'd test: whether the bird's-eye-view transformer can replace the per-object detection pipeline for highway driving. The 1 thing I disagree with: I think Waymo is too conservative on the consumer-ride-share pricing — the cost per mile needs to drop 5× to hit mainstream adoption."
**Tip:** Show you've read the Waymo safety reports + Disengagement Reports (CA DMV).

Waymo's recruiter screen is the easy filter — they're checking comp, location, and team fit (Perception vs Planning vs Simulation). The phone screen is where autonomy starts showing up: expect a BFS or graph problem and a sensor-fusion question that tests whether you actually know the difference between camera, lidar, and radar.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Given a 2D grid, find the shortest path from top-left to bottom-right, but you can only move right or down. Walls block movement. Use BFS."
**Answer:**
```python
from collections import deque
def shortest_path(grid):
    if not grid or not grid[0]: return -1
    rows, cols = len(grid), len(grid[0])
    if grid[0][0] == 1 or grid[rows-1][cols-1] == 1: return -1
    q = deque([(0, 0, 1)])
    visited = {(0, 0)}
    while q:
        r, c, d = q.popleft()
        if r == rows-1 and c == cols-1: return d
        for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited and grid[nr][nc] == 0:
                visited.add((nr, nc))
                q.append((nr, nc, d+1))
    return -1
```
**Tip:** For Waymo, mention A* heuristic search, motion planning algorithms (RRT*, lattice planners), and the trade-off between optimality and real-time performance.

### Q2.2: "Explain the difference between camera, lidar, and radar. When would you use each for autonomous driving?"
**Answer:** Camera: 2D RGB, high resolution, semantic info, but fails in low light/weather. Lidar: 3D point cloud, accurate depth, robust to lighting, but expensive and sparse. Radar: 3D, robust to weather, measures velocity, but low resolution. Waymo uses all 3 + sensor fusion. Trade-off: cost vs. reliability.
**Tip:** Mention the camera-lidar-radar fusion architecture, the Kalman filter or transformer-based fusion, and the failure modes (lidar in fog, camera in glare, radar in clutter).

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min, 2 problems)

### Q3.1.1: "Implement a Kalman filter for tracking an object's position with noisy sensor readings."
**Answer:**
```python
import numpy as np
class KalmanFilter:
    def __init__(self, x0, P0, Q, R):
        self.x = x0  # state [pos, vel]
        self.P = P0  # covariance
        self.Q = Q   # process noise
        self.R = R   # measurement noise
    def predict(self, dt):
        F = np.array([[1, dt], [0, 1]])
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
    def update(self, z):
        H = np.array([[1, 0]])
        y = z - H @ self.x
        S = (H @ self.P @ H.T + self.R)[0, 0]
        K = self.P @ H.T / S
        self.x = (self.x + K.flatten() * float(y)).reshape(-1)
        self.P = (np.eye(2) - K @ H) @ self.P
```
**Tip:** Explain the 2-step predict-update cycle, the trade-off between trusting the model (Q) vs. sensor (R), and the extension to EKF/UKF for nonlinear motion.

### Q3.1.2: "Given a list of 3D bounding boxes (cars, pedestrians, cyclists), check for collisions in O(n log n)."
**Answer:** Use a spatial index (KD-tree or R-tree). For each box, query neighbors within the max bounding box size. Check pairwise collisions for neighbors. Discuss the trade-off: O(n²) brute force vs. O(n log n) with spatial index.
**Tip:** For Waymo, mention motion prediction (where each object will be in 1-3 seconds) and the planning collision check.

### Round 3.2: System design (60 min, autonomy-themed)

### Q3.2.1: "Design a real-time obstacle detection pipeline for a self-driving car. 10 cameras + 5 lidars, must run at 30 Hz on a 500W compute budget."
**Answer:** Multi-stage: (1) sensor fusion: project lidar to camera frame, time-sync, ego-motion compensation. (2) perception: BEV (bird's eye view) transformer that takes all sensors and produces 3D bounding boxes. (3) tracking: Kalman + Hungarian for association. (4) planning: lattice planner with the tracked objects as dynamic obstacles. Trade-off: latency vs. accuracy. Mention TensorRT, INT8 quantization, model pruning.
**Tip:** Name the 4 stages, name the BEV architecture (BEVFormer, Waymo's BlockFormer), name the latency budget (33ms per stage at 30 Hz).

### Q3.2.2: "Design a simulation platform for testing autonomous driving policies at 10M miles per day."
**Answer:** Log replay + neural rendering + adversarial scenarios. Use real-world driving logs, simulate the sensors, inject perturbations (other agents, weather), evaluate the policy. Mention Waymo's SimulationCity, CARLA, the importance of distribution shift. Trade-off: fidelity vs. scale.
**Tip:** Show you understand sim-to-real transfer, the importance of long-tail scenarios, and how Waymo uses simulation to catch edge cases.

### Round 3.3: ML deep-dive (60 min)

### Q3.3.1: "Walk through how a transformer-based perception model works for 3D object detection. Compare to a CNN-based model."
**Answer:** Transformer: multi-head self-attention over BEV features, captures long-range dependencies, better for occluded objects. CNN: convolutional, local receptive field, faster but misses long-range context. Trade-off: accuracy vs. latency. For Waymo, the trend is BEVFormer-style architectures.
**Tip:** Derive the attention on a whiteboard. Mention positional encoding, the BEV grid, the loss function (focal loss for class imbalance).

### Q3.3.2: "How do you evaluate an autonomous driving policy? What metrics matter?"
**Answer:** Disengagement rate (interventions per 1K miles), safety-critical events (collisions, near-misses), comfort (jerk, lateral acceleration), efficiency (time to destination, energy use). Trade-off: offline metrics (replay logs) vs. online (real-world fleet). Mention importance sampling for rare events.
**Tip:** Waymo's safety reports are public. Reference the CA DMV Disengagement Reports.

### Round 3.4: Behavioral (45 min, safety-focused)

### Q3.4.1: "Tell me about a time you caught a safety issue before it shipped."
**Answer:** Use STAR. Situation (the product), Task (your role), Action (the specific check you added, e.g., a unit test for an edge case, a manual review of a config change), Result (the issue caught, the metric avoided, the team adoption). Example: "I caught a data race in the inference server that could have caused silent corruption under load. I added a stress test, the bug was caught in CI, and the team adopted the test as the standard pattern."
**Tip:** Waymo values the safety mindset. Show you think about edge cases, failure modes, and rollback plans.

The onsite is 4-5 rounds across 1-2 days, and the system-design round is the autonomy litmus test: a real-time obstacle pipeline at 30 Hz on 500W, or a 10M-mile simulation platform. The ML deep-dive wants BEV attention derived, not summarized. The behavioral round is a separate safety review — bring STAR stories about catching bugs before they shipped.

## Stage 4: Hiring committee
The committee reviews the packet and votes. The safety review is separate: a panel evaluates whether the candidate demonstrates the safety mindset required for autonomy work. ~60% advance.

## Stage 5: Offer
Cash-heavy comp (Waymo is Alphabet, not a startup). Comp band L3-L6: $250K-$700K. Equity is Alphabet stock (GOOG). Comp negotiation is real at L5+.

## Tips for the Waymo loop

1. **Read the Waymo safety reports + Disengagement Reports** before the loop. Show you've done the homework.
2. **The safety mindset is the meta-rubric.** Every answer should mention edge cases, failure modes, rollback plans.
3. **C++ is non-negotiable for systems roles.** For ML roles, Python + PyTorch is the bar, but C++ helps for the perception stack.
4. **The perception vs. planning vs. simulation split matters.** Read the team's recent publications and tailor your answers.
5. **The autonomy domain is hard to fake.** If you don't have AV experience, be honest about it and emphasize the transferability of your skills (e.g., real-time systems, sensor fusion, safety-critical code).

## Real candidate report

> "Waymo's loop is the most safety-focused of the AV companies. Every interviewer asked 'what could go wrong?' and 'how would you test it?' The coding round was a standard LeetCode medium (LRU cache), but the system design was autonomy-specific. The behavioral round is the safety review. If you've never worked in safety-critical systems, prep 3 STAR stories about catching bugs before they shipped."
> — r/SelfDrivingCars, on the Waymo loop

## Sources

- [Levels.fyi — Waymo compensation](https://www.levels.fyi/companies/waymo/salaries/software-engineer)
- [Waymo Safety Report](https://waymo.com/safety/) — the source for the safety mindset
- [CA DMV Disengagement Reports](https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicle-disengagement-reports/) — the public autonomy benchmarks
- [Waymo Engineering Blog](https://waymo.com/blog/) — the perception, planning, and simulation posts
- [r/SelfDrivingCars — Waymo interview threads](https://www.reddit.com/r/SelfDrivingCars/)

---

## The 1 thing to remember

At Waymo, the safety mindset is the meta-rubric — the L5+ candidate is the one who names failure modes, rollback plans, and edge cases before the interviewer asks, and treats every metric as a safety metric, not just a product one.
