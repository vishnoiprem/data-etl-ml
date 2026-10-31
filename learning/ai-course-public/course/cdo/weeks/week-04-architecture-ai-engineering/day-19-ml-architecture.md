# Lesson 19: ML architecture

> **Week 4 · Day 19 · 90 min**
> **Deliverable:** The ML lifecycle architecture — feature → train → serve → monitor.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The ML architecture is the same shape as the data architecture, with one extra layer: the **model lifecycle**.

| Stage | What happens | Key choices | Build vs. buy |
|---|---|---|---|
| **Feature store** | Curated features for training and serving | Feast, Tecton, Databricks Feature Store, in-house | Buy (start); build (scale) |
| **Training** | Fit models on historical data | SageMaker, Vertex, Databricks ML, in-house | Buy (compute); build (code) |
| **Registry** | Version and govern models | MLflow, SageMaker Registry, Vertex Registry | Buy |
| **Serving** | Real-time or batch inference | SageMaker Endpoints, Vertex Prediction, in-house | Buy (start); build (latency) |
| **Monitoring** | Detect drift, bias, performance decay | Evidently, Arize, WhyLabs, in-house | Buy |
| **Orchestration** | Retrain, redeploy, A/B | Airflow, Kubeflow, Argo, Metaflow | Buy / build |

The single biggest mistake is to **skip the feature store**. A team without a feature store is a team where every model has its own data pipeline. The data quality is unreviewable; the lineage is untraceable. The feature store is the platform team's job.

The second biggest mistake is to **not monitor in production**. "We trained the model" is not "we shipped the model." A model that decays silently is a liability, not an asset. Monitor for data drift, prediction drift, and outcome drift.

The third biggest mistake is to **not version the model and the data**. "Which model is in production?" and "which data did it train on?" must be answerable in 60 seconds. If not, you have a governance problem, not just a tech problem.

The right portfolio shape: **80% of models are "traditional ML" (forecasting, classification, recommendation), 20% are deep learning.** The deep learning gets the attention; the traditional ML gets the ROI.

## 🛠️ Build It

**Spec:** For the retailer, design the ML architecture for 5 use cases (demand forecasting, customer 360, dynamic pricing, churn, document intelligence).

**Acceptance:**
- 6 stages named
- 1-2 technologies per stage
- Build-vs-buy per stage
- Governance (registry, monitoring) named
- 1 paragraph on the feature store rationale

**Starter:** Use the 5 use cases from Day 14's commercial menu.

**Solution (ML architecture, abridged):**

| Stage | Choice | Why | Build vs. buy |
|---|---|---|---|
| Feature store | Feast (open source) | Open, multi-cloud, no vendor lock | Build (in-house) |
| Training | Databricks ML + Spark | Same platform as data | Buy (compute) + build (code) |
| Registry | MLflow | Open, integrates with Databricks | Buy |
| Serving | SageMaker Endpoints (real-time); Spark (batch) | Latency needs vary by use case | Buy (managed) |
| Monitoring | Evidently AI | Open, drift + bias detection | Buy |
| Orchestration | Airflow | Same as data orchestration | Buy |

**Governance:** Every model in MLflow registry. Every feature in Feast. Every prediction logged. Every outcome (where measurable) joined back. Quarterly model review with the business.

## 🏛️ Architect Notes

- **Trade-off:** Build vs. buy. Default: buy the managed services (Databricks, SageMaker, Vertex), build the feature store and the orchestrator. The model code is always in-house.
- **Capacity / cost:** A 5-model portfolio needs 8-10 ML engineers + 2-3 MLOps. Below that, models don't reach production.
- **When NOT to use:** Don't ship models you can't monitor. A model with no monitoring is a model that will fail silently.
- **Production checklist:**
  - [ ] 6 stages named
  - [ ] 1-2 technologies per stage
  - [ ] Build-vs-buy per stage
  - [ ] Feature store rationale
  - [ ] Monitoring stack named
  - [ ] Governance process named

## 🌙 Reflect

- Which of your shipped models is your strongest example of "we monitored it and caught drift"? Pre-write the answer.
- Which ML architecture choice would the CTO challenge first?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 20 — GenAI architecture.