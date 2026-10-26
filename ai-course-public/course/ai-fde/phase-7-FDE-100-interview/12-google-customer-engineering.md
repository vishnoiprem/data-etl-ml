# Google Cloud — Customer Engineering (FDE-equivalent)

## Company Snapshot
- **HQ**: Mountain View, CA
- **Team Size**: ~600+ Customer Engineers
- **Comp**: Base $180K–$240K; TC $300K–$550K
- **What they deploy**: Vertex AI / Gemini enterprise embedding
- **Travel**: 30–50%

## Interview Process
1. Recruiter
2. Coding (LeetCode medium-hard)
3. System design (Google-flavored)
4. Loop
   - Coding 2
   - GCP architecture
   - Customer scenario
   - Googliness / leadership

---

## ✅ SUCCESS STORIES

### GCP architecture
**Q:** *"Design a multi-region GenAI serving platform on GCP."*
**A (winner):**
- **Edge**: Cloud Armor + Global HTTPS LB.
- **API**: Apigee or Cloud Endpoints in front of services.
- **Compute**: GKE Autopilot with GPU TPU pools; HPA + node auto-provisioning.
- **Inference**: vLLM on GKE with model registry in Artifact Registry.
- **State**: Vertex AI Vector Search for embeddings; Firestore for session state.
- **Eval**: Vertex AI Evaluation + BigQuery for eval sets.
- **Observability**: Cloud Trace + Cloud Logging + Error Reporting.
- **Cost**: committed-use discounts + Spot for batch jobs.
**Why it worked:** GCP-native end-to-end, named real products, addressed cost.

---

### Customer scenario
**Q:** *"An EMEA retailer wants Gemini for product recommendations but data must stay in EU."*
**A (winner):** *"Vertex AI is regional by default. Pin everything to europe-west4, use CMEK with EU-resident keys, disable global routing, and confirm with our Compliance team that Vertex AI doesn't process outside the region. Plus Assured Workloads to enforce. I'd pilot in week 1 on the catalog search use case, measure CTR + latency."*
**Why it worked:** Knew Vertex AI's regional posture, named CMEK + Assured Workloads.

---

## ❌ REJECTION STORIES

### Coding
**Q:** *"Find k-th largest in an array."*
**A (loser):** Sorted the array O(n log n) and returned arr[-k].
**Why it failed:** Right answer, but no discussion of heap (O(n log k)), didn't ask about constraints.
**What they should have said:** *"Heap-based approach: O(n log k), better when k << n. If k = n/2, there's a quickselect O(n) approach."*

---

### Customer scenario
**Q:** *"Customer says Gemini is slow."*
**A (loser):** *"Switch to a faster model."*
**Why it failed:** Same root-cause avoidance.
**What they should have said:** *"Profile. Is it TTFT (time to first token) high? Token throughput? Often it's (a) we're not streaming, (b) we can cache prefix, (c) we can use Gemini Flash for short queries, (d) we can batch async."*

---

## 📚 Reading List
1. Google Cloud docs — Vertex AI, Gemini, BigQuery
2. *"Architecture: GenAI on GCP"* (Google Cloud Architecture Center)
3. Google Cloud Next session recordings
4. r/googlecloud threads
5. levels.fyi Google CE