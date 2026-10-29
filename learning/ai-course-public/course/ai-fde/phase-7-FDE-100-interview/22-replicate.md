# Replicate — FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~20–40
- **Comp**: $170K–$220K; TC $260K–$400K
- **What they deploy**: Open-model cloud (Cog) + on-prem for enterprise
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. ML system design
4. Loop — coding, Cog deployment case, customer scenario

---

## ✅ SUCCESS STORIES

### Cog case
**Q:** *"Package a custom model for production."*
**A (winner):** *"Write a Cog predict.py with a typed Predictor, pin Python + CUDA versions in cog.yaml, add a Pusher to ship to Replicate. Front with a thin FastAPI for auth/quotas. Add a basic eval harness (50 prompts, BLEU + human eval) before going live."*
**Why it worked:** Cog-native.

---

## ❌ REJECTION STORIES
### ML ops
**Q:** *"Deploy a model to prod."*
**A (loser):** Custom Docker without naming Replicate/Cog.
**What they should have said:** Use Cog to standardize the Docker packaging, push to Replicate for serving.

---

## 📚 Reading List
1. Cog docs (github.com/replicate/cog)
2. Replicate API docs
3. r/LocalLLaMA
4. levels.fyi Replicate
