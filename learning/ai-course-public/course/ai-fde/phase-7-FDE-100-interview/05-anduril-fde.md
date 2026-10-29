# Anduril Industries — Forward Deployed / Mission Engineer

## Company Snapshot
- **HQ**: Costa Mesa, CA
- **Team Size**: ~300–500 FDEs (Forward Deployed + Mission Engineers)
- **Comp**: Mid $170K–$210K base; TC $300K–$500K+
- **What they deploy**: Lattice / OS for DoD / DHS / foreign gov; on-site tactical integration
- **Travel**: heavy; many roles require TS/SCI

## Interview Process
1. Recruiter (often ex-military on recruiting team)
2. Coding screen (mid LeetCode + systems-flavored)
3. Technical phone — system design for defense systems
4. On-site loop
   - Coding 2
   - Systems design for real-time defense
   - Mission scenario (often scenario-based)
   - Bar-raiser (cross-functional: PM + engineer)
5. Final with hiring manager (often senior director)

---

## ✅ SUCCESS STORIES

### Mission scenario
**Q:** *"A US ally wants Lattice integrated with their existing C2 system in 90 days. The integration spec is incomplete. How do you proceed?"*
**A (winner):** *"Treat the spec as a hypothesis. Week 1: send 1 senior FDE + 1 FSE (field SE) on-site for 5 days. Build the smallest possible integration: Lattice tracks one entity class (say, surface vessels), exchanges with their C2's MOST simplest message. Don't try to do all of C2. Validate the data model. Week 2-8: iterate on the data contract + add 1 sensor feed at a time. Week 9-12: hardening, training, ops handoff. The work expands after confidence, not before."*
**Why it worked:** Started with a small, mission-shaped demo. Reduced risk iteratively. Showed awareness of customer relationships (5-day trip, not email). Anduril specific.

---

### Real-time systems design
**Q:** *"Design the system that fuses drone video + radar tracks into a single Common Operating Picture."*
**A (winner):**
- **Ingest**: WebRTC for video, ASTERIX or proprietary for radar, both at 30Hz.
- **Time sync**: PTP on the network; every track tagged with millisecond UTC + sensor id.
- **Fusion**: a probabilistic tracker (UKF) running on a Jetson Orin at the edge; publishes fused tracks at 10Hz to Lattice over gRPC.
- **Display**: Lattice operator console rendering targets as glyphs on a Cesium map.
- **Failure modes**: drop video if bandwidth low, increase track cadence, alert operator if latency > 500ms.
**Why it worked:** Right primitives (PTP, UKF, gRPC), right failure modes, latency-budget aware. Exactly what an Anduril FDE would design.

---

## ❌ REJECTION STORIES

### Coding
**Q:** *"Parse a binary packet format with header + payload + footer."*
**A (loser):** Assumed ASCII input, didn't handle malformed packets, no CRC check.
**Why it failed:** Defense systems care about correctness on malformed input more than happy-path.
**What they should have said:** Define packet format in hex bytes first, validate header magic, check CRC, raise on bad input with clear error, log it.

---

### Behavioral
**Q:** *"Tell me about a time you operated under fire."*
**A (loser):** Generic startup war story ("we had a deadline, I shipped, etc.")
**Why it failed:** No actual ops-under-pressure; no mention of trade-offs made in time-critical conditions; no mention of consequences.
**What they should have said:** A real time-pressure story: a production outage, a ship-or-miss-the-quarter launch, a hostile contract negotiation, etc. Show stakes, decisions, outcome.

---

## 📚 Reading List
1. Anduril blog — *"How Lattice works"* (Palmer Luckey + team posts)
2. Anduril YouTube demos
3. *"Mission Engineering at Anduril"* (LinkedIn by Anduril engineers)
4. DoD Open Mission Systems (OMS) standards
5. STANAG 4609 (GMTI), Cursor on Target (CoT)
6. r/DefenseIndustry threads
7. levels.fyi Anduril FDE
