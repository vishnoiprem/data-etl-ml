# Shield AI — FDE / Deployment Engineer (Hivemind)

## Company Snapshot
- **HQ**: San Diego, CA
- **Team Size**: ~100–200 FDEs
- **Comp**: $160K–$220K base; TC $250K–$400K
- **What they deploy**: Hivemind autonomy stack for DoD + allies
- **Travel**: heavy; on-site with military units

## Interview Process
1. Recruiter (often ex-military)
2. Coding (medium-hard)
3. Robotics / autonomy phone screen
4. Loop
   - Coding
   - Autonomy system design
   - Customer scenario (military)
   - Bar-raiser (often engineering leadership)

---

## ✅ SUCCESS STORIES

### Autonomy system design
**Q:** *"Design the autonomy stack for a tactical drone operating in GPS-denied environments."*
**A (winner):**
- **Perception**: stereo + IMU + event camera for low-light; visual-inertial odometry with MSCKF.
- **Localization**: VIO + terrain-relative navigation when GPS denied.
- **Planning**: 2-layer — reactive (obstacle avoidance at 100Hz) + deliberative (goal-reaching at 10Hz).
- **State estimation**: EKF fusing VIO + barometer + magnetometer; outlier rejection on each.
- **Sim**: test against hardware-in-loop simulation before every flight.
- **Comms**: dual-band (C-band for command, L-band for telemetry) with frequency hopping.
**Why it worked:** Right primitive choices (VIO, EKF, dual-layer planning), named real algorithms, addressed GPS-denied.

---

### Customer scenario
**Q:** *"Marine unit wants to integrate Hivemind with their existing tactical comms. Your first 30 days?"*
**A (winner):** *"Discovery: 2 weeks on-base with their comms team — TBIT, RF spectrum allocation, LINK 16 compatibility. Build: 4 weeks shipping a Hivemind-comms adapter. Pilot: 2 weeks of joint exercises. Rollout: train 4 operators, hand off to their program office. Plus a CI/CD loop so future updates deploy via over-the-air."*
**Why it worked:** On-site discovery first, named real military comms (LINK 16, TBIT), proposed a handoff plan.

---

## ❌ REJECTION STORIES

### Autonomy design
**Q:** *"Build a drone collision-avoidance system."*
**A (loser):** Generic "use ML" answer, no sensor specifics, no latency budget, no test plan.
**Why it failed:** Didn't show domain depth.
**What they should have said:** Sensor choice (radar vs vision vs lidar for the environment), control loop at 100Hz, ML only for classification (not the control loop), sim testbed, certified MAVLink integration.

---

### Customer scenario
**Q:** *"Customer says the drone crashed on landing."*
**A (loser):** *"We'll debug the logs."*
**Why it failed:** No root-cause methodology, no customer empathy.
**What they should have said:** *"Two tracks. (1) Pull the black-box, look at last 5 sec of state estimation + control, classify the failure (sensor dropout, wind gust, geofence violation?). (2) Sit with the operator, hear what they saw. Often there's a UI gap or a comms dropout that didn't surface in logs. We patch + add a regression test + an alert."*

---

## 📚 Reading List
1. Shield AI engineering blog
2. VIO / SLAM papers (Forster et al. MSCKF)
3. MAVLink protocol docs
4. PX4 / ArduPilot autonomy frameworks
5. r/robotics + r/DefenseIndustry
6. levels.fyi Shield AI