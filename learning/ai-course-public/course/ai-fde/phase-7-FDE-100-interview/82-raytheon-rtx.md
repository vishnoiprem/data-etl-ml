# Raytheon / RTX — Defense AI FDE

## Company Snapshot
- **HQ**: Arlington, VA
- **Team Size**: ~50–100
- **Comp**: $130K–$190K; TC $180K–$320K
- **What they deploy**: Defense AI FDE (RTX)
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Defense / sensor AI design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Sensor-AI scenario
**Q:** *"Customer wants radar ML for missile-defense."*
**A (winner):** *"Radar DSP + ML classifier on FPGA / GPU. Track-before-detect pipeline, multi-sensor fusion. Latency budget: 100ms detection + 50ms classification. Test in HWIL, then field test. ITAR + NIST compliance."*
**Why it worked:** Right radar/sensor + latency-aware.

---

## ❌ REJECTION STORIES
### Sensor scenario
**Q:** *"False alarms in clutter."*
**A (loser):** "Better ML."
**What they should have said:** *"CFAR + clutter-map + adaptive thresholds. Add classification per track-association. Reduce system noise. Most false alarms come from CCF clutter."*

---

## 📚 Reading List
1. Skolnik — *Radar Handbook*
2. RTX engineering blog
3. r/DefenseIndustry radar ML
4. levels.fyi Raytheon