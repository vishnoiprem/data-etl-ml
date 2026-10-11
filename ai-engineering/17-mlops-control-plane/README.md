# 17. MLOps Control Plane (SageMaker-style)

A SageMaker-style lifecycle: data labeling → training → registry → deployment → monitoring → retrain trigger. The control plane is a small set of services behind one workflow spec.

## The shape

```
              ┌─────────────────────────────────────────────────────┐
              │            MLOps Control Plane (one API)           │
              └─────────────────────────────────────────────────────┘
                                       │
   ┌──────────────┬──────────────┬──────┴──────┬──────────────┬──────────────┐
   ▼              ▼              ▼             ▼              ▼              ▼
Labeling       Training        Registry     Deployment     Monitoring    Retrain
(workers +     (K8s jobs,     (model       (canary /     (drift,        (trigger on
 active        GPU pools,     weights +    blue-green /   latency,      drift OR
 learning)     FSDP)          metrics)     shadow)        cost)         schedule)
```

## What I actually built

- `control_plane/api.py` — FastAPI service that takes a `WorkflowSpec` and orchestrates the lifecycle.
- `control_plane/registry.py` — model + dataset registry (Postgres + S3, with content-addressed storage).
- `control_plane/deployer.py` — canary deployer that ships 1% → 10% → 50% → 100% on metric gates.
- `control_plane/monitor.py` — drift + latency + cost watcher; closes the loop by writing a `RetrainRequest`.
- `examples/train_xgboost.py` — minimal training script that registers itself.

## The world-top pattern

SageMaker / Vertex / Azure ML all converge on the same shape: **a single workflow spec, an immutable registry, a promotion gate, and a retrain trigger**. The value isn't any one component — it's the loop.

## Run

```bash
pip install -r requirements.txt
make up        # docker-compose brings up postgres + minio
make api       # uvicorn on :8080
```

## What I learned the hard way

The first version had a `PUT /model/{id}/production` endpoint. That was a footgun — a one-line bug and every model was prod. Replaced with an explicit `PromoteRequest` that takes a model id, a previous-prod id, and a gate result. Now the audit log has a reason for every promotion.
