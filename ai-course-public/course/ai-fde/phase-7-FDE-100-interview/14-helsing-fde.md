# Helsing — FDE (Defense AI, EU)

## Company Snapshot
- **HQ**: Munich, Germany / London
- **Team Size**: ~150–250 FDEs
- **Comp**: €90K–€160K base; TC €140K–€280K
- **What they deploy**: AI for European defense (UK/DE/FR/EE); on-site with militaries
- **Travel**: heavy (often on-base weeks at a time)

## Interview Process
1. Recruiter
2. Coding (medium LeetCode + Python data engineering)
3. System design (defense / edge AI)
4. Loop
   - Coding 2
   - Edge AI / defense scenario
   - Customer scenario (military / gov stakeholder)
   - Values (Helsing's civic mission)

---

## ✅ SUCCESS STORIES

### Edge AI scenario
**Q:** *"Design a real-time acoustic-detection AI running on a portable edge box. Detecting drones within 5km, 1 sec latency budget, battery for 24 hrs."*
**A (winner):**
- **Hardware**: NVIDIA Jetson Orin (40–60W), 4× MEMS mic array.
- **Model**: small CNN (1M params), quantized, INT8. Outputs probabilities over 50ms windows.
- **Pipeline**: sliding-window FFT → log-mel → model → threshold → alert.
- **Latency budget**: capture 200ms + inference 50ms + alert 50ms + buffer = 300ms; 700ms slack.
- **Power**: duty-cycle CPU; only run inference when noise > threshold.
- **Comms**: 4G LTE backhaul with LoRa fallback.
- **Failure modes**: high winds, urban noise; ship a noise-classifier and degrade gracefully.
**Why it worked:** Right power budget, real-time discipline, named hardware, addressed noise.

---

### Military stakeholder scenario
**Q:** *"A general says: 'I don't trust AI to make targeting decisions.' How do you respond?"*
**A (winner):** *"You're right to be skeptical — and the right architecture puts a human in the decision. Helsing's products are decision-support, with the human commander always in the loop. We provide ranked options + evidence + confidence, not autonomous decisions. I'd love to demo on a non-lethal use case (e.g., logistics, ISR), build trust, and then expand."*
**Why it worked:** Acknowledged the concern as valid, named the right product pattern (decision-support), proposed trust-building.

---

## ❌ REJECTION STORIES

### Coding
**Q:** *"Process a stream of acoustic samples in real time."*
**A (loser):** Loaded all samples into memory, processed batch-wise.
**Why it failed:** Didn't think about real-time constraints.
**What they should have said:** Streaming via generator, sliding window with collections.deque, fixed memory footprint.

---

### Stakeholder scenario
**Q:** *"Military customer asks for autonomous targeting."*
**A (loser):** "Sure, we'll build it."
**Why it failed:** Helsing explicitly does *not* do autonomous targeting. Wrong cultural fit, would not pass values screen.
**What they should have said:** "That's a use case we don't build. Helsing's products are decision-support, with human commanders in the loop. We can build the best target-prioritization tool in the world, but the kill decision is always the human's."

---

## 📚 Reading List
1. Helsing blog + reports (publicly available)
2. *"AI in defense"* — Helsing's published position papers
3. NATO STANAG 4586 (UAV data-link), STANAG 4609 (GMTI)
4. NVIDIA Jetson / edge AI papers
5. r/DefenseIndustry threads
6. levels.fyi Helsing