# Lambda Labs — FDE

## Company Snapshot
- **HQ**: San Jose, CA
- **Team Size**: ~30–60
- **Comp**: $150K–$210K; TC $220K–$380K
- **What they deploy**: GPU cluster + model serving deployments (Lambda Cloud, Lambda Inference API)
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium)
3. ML infra design
4. Loop — coding, GPU deployment case, customer scenario

---

## ✅ SUCCESS STORIES

### GPU deployment
**Q:** *"Stand up a multi-node training cluster for a 70B fine-tune."*
**A (winner):** *"Lambda Sky cluster with 8×8 H100 nodes, InfiniBand fabric for NCCL. Use Lambda's cluster API + Slurm for scheduling. Pre-built NGC containers with PyTorch + FSDP. Checkpoint to shared Lustre. Monitor with Lambda Cloud dashboard + custom Grafana. Cost: $X/hr per node."*
**Why it worked:** Lambda-native primitives.

---

## ❌ REJECTION STORIES
### GPU scenario
**Q:** *"Customer needs more GPUs."*
**A (loser):** "Wait for supply."
**What they should have said:** Lambda has reserved capacity contracts + spot pricing. Plan ahead with reservation. Use mixed precision + gradient checkpointing to fit on fewer GPUs.

---

## 📚 Reading List
1. Lambda Cloud + Inference docs
2. NVIDIA NCCL docs
3. FSDP paper
4. r/LocalLLaMA
5. levels.fyi Lambda
