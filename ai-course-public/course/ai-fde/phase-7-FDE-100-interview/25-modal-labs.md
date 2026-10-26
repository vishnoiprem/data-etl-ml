# Modal Labs — FDE

## Company Snapshot
- **HQ**: NYC / SF
- **Team Size**: ~20–40
- **Comp**: $170K–$230K; TC $270K–$450K
- **What they deploy**: Serverless GPU/AI infra for enterprise
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. ML infra design
4. Loop — coding, Modal case, customer scenario

---

## ✅ SUCCESS STORIES

### Modal case
**Q:** *"Run a batch inference of 10M images."*
**A (winner):** *"Modal function with `@modal.enter(snapshots=True)` for warm container. Parallelize with `.map()` over a 10K-element batch size. Use Modal's GPU pool with H100s. Persist results to S3. Cost at ~$0.001 / image with A10Gs."*
**Why it worked:** Modal-native idioms (map, snapshots, GPU pool).

---

## ❌ REJECTION STORIES
### Modal case
**Q:** *"Run a job in the cloud."*
**A (loser):** "Spin up an EC2."
**What they should have said:** Use Modal's primitives — `@app.function`, `.map()`, autoscaler, snapshot caching, GPU. No infra to manage.

---

## 📚 Reading List
1. Modal docs + blog
2. modal.com/examples (github)
3. r/MachineLearning
4. levels.fyi Modal
