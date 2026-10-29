# Two Sigma — AI Engineering FDE

## Company Snapshot
- **HQ**: NYC
- **Team Size**: ~30–60
- **Comp**: $200K–$280K; TC $400K–$700K
- **What they deploy**: Quant + AI deployment teams
- **Travel**: ~0%

## Interview Process
1. Recruiter (often quant-flavored)
2. Coding (medium-hard + probability)
3. ML system / market microstructure
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Quant scenario
**Q:** *"Design a low-latency ML inference for signals."*
**A (winner):** *"C++ core + Python orchestration. Model compiled to ONNX + TensorRT on H100. Batched inference with sliding window. Latency budget: 200µs model + 50µs network = 250µs p99. Risk checks upstream. Validation via shadow vs incumbent for 1 month. Compliance: SOC2."*
**Why it worked:** Latency-budget aware, named quant primitives.

---

## ❌ REJECTION STORIES
### Quant scenario
**Q:** *"Model underperforms in prod."*
**A (loser):** "Retrain."
**What they should have said:** *"Diagnose: regime change? feature drift? labeling issue? Quant walk-forward analysis + factor attribution. Often it's feature drift (market microstructure changed)."*

---

## 📚 Reading List
1. *"Advances in Financial ML"* — Marcos López de Prado
2. ONNX / TensorRT
3. r/quant
4. levels.fyi Two Sigma