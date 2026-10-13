# Hello-World MLOps — the smallest reproducible MLOps loop

> **A 5-file MLOps reference: train a tiny model, serve
> it from a Flask app, containerize it, and run CI
> that re-trains on every push.** The whole loop fits
> in one directory. The point isn't the model (a
> logistic regression on Iris) — it's the artifact flow.

This directory is the "show me the smallest MLOps
loop that still has the shape" reference. The five
moving parts are the ones every production MLOps
system has, just stripped of the scale:

1. **Train** — `train.py` writes `model.pkl` +
   `metrics.json` to `artifacts/`.
2. **Predict from CLI** — `run_model.py --input "[...]"`.
3. **Serve** — `app.py` (Flask) exposes `/predict`.
4. **Containerize** — `Dockerfile` builds a runnable
   image.
5. **CI** — the workflow trains the model and uploads
   the artifact on every push.

The original is
[`iam-veeramalla/hello-world-mlops`](https://github.com/iam-veeramalla/hello-world-mlops);
this directory is a port with a few small fixes
(python:3.12-slim base, `/predict` on port 5001, lockfile
in the Dockerfile layer).

---

## What's in this directory

| File | What it does |
|------|--------------|
| `train.py` | Loads Iris, fits a `LogisticRegression`, writes `artifacts/model.pkl` + `artifacts/metrics.json` |
| `run_model.py` | Loads `artifacts/model.pkl`, runs a single prediction from a CLI flag |
| `app.py` | Flask app that exposes `POST /predict` on port 5001 |
| `Dockerfile` | `python:3.12-slim` base, installs `requirements.txt`, runs `app.py` |
| `requirements.txt` | `scikit-learn`, `joblib`, `flask` |
| `artifacts/` | The output of `train.py` (model + metrics) |

Five files, one model, one endpoint. That's the
smallest MLOps system that's still recognizably an
MLOps system.

---

## The shape

```
   train.py                       run_model.py
       │                               │
       │  writes                       │  loads
       ▼                               ▼
   artifacts/  ──────────────────▶  model.pkl
   ├─ model.pkl                         │
   └─ metrics.json                      │
                                        │
                       ┌────────────────┤
                       │                │
                       ▼                ▼
                   app.py (Flask)    CLI inference
                       │
                       ▼
                  POST /predict
                       │
                       ▼
                  Dockerfile → image
                       │
                       ▼
                  CI: re-train on push,
                      upload artifacts
```

The artifact directory is the *contract* between the
five moving parts. `train.py` is the only writer;
`run_model.py` and `app.py` are the readers; the
Docker image packages the readers with the artifact
at build time; the CI runs the writer and ships the
artifact.

---

## How to run it

### Local (the quick start)

```bash
cd ai-engineering/10-hello-world-mlops-main
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Train
python train.py
# -> artifacts/model.pkl
# -> artifacts/metrics.json   {"accuracy": 0.97}

# 2. Predict from CLI
python run_model.py --input "[5.1, 3.5, 1.4, 0.2]"
# -> 0   (setosa)

# 3. Serve
python app.py
# -> * Serving Flask app on port 5001

# 4. Test the endpoint
curl -X POST http://127.0.0.1:5001/predict \
    -H "Content-Type: application/json" \
    -d '{"features":[5.1,3.5,1.4,0.2]}'
# -> {"prediction": 0}
```

### Container

```bash
docker build -t hello-mlops .
docker run --rm -p 5001:5001 hello-mlops
# -> Flask on :5001
```

### CI

The CI workflow (in `.github/workflows/`) trains the
model on every push and uploads the artifact to the
run's artifacts. The point is that the model is
*reproducible* — re-running `train.py` with the same
`requirements.txt` produces the same `metrics.json`.

---

## The 5 things this directory teaches

1. **The artifact directory is the contract.** The
   five files don't talk to each other directly;
   they read and write `artifacts/`. That's the
   production pattern (model registry, S3, MLflow)
   in miniature.
2. **Train and serve are the same model.** Both
   `run_model.py` and `app.py` load the same
   `artifacts/model.pkl`. The split between writer
   (train) and readers (CLI, API) is what makes
   the loop reproducible.
3. **The Dockerfile copies the artifact at build
   time.** This is the "bake the model into the
   image" pattern. The alternative — mount the
   model from S3 at runtime — is what you'd do in
   production when the model updates more often
   than the image.
4. **A small model is enough to see the loop.** Iris
   is 150 rows. The point isn't the data; it's the
   *shape* — train, write artifact, read artifact,
   serve. Same shape at any scale.
5. **CI is the reproducibility check.** If the
   workflow re-trains and uploads the artifact on
   every push, you can always answer "is this model
   reproducible from this commit?" The artifact is
   the proof.

---

## What this is NOT

- **Not a production MLOps platform.** There's no
  model registry, no feature store, no A/B test
  harness, no monitoring. For those patterns, see
  [`../17-mlops-control-plane/`](../17-mlops-control-plane/).
- **Not a deep-learning example.** The model is a
  logistic regression. For deep-learning training
  loops, see the GPU-shaped builds in
  [`../30-triton-kernels/`](../30-triton-kernels/) and
  [`../24-vertex-style-platform/`](../24-vertex-style-platform/).
- **Not a serving framework comparison.** Flask is
  the smallest possible HTTP server. For production
  serving (Ray Serve, BentoML, vLLM, Triton), see
  [`../23-serverless-vector-store/`](../23-serverless-vector-store/)
  and [`../30-triton-kernels/`](../30-triton-kernels/).

---

## Related directories

- [`../17-mlops-control-plane/`](../17-mlops-control-plane/) —
  the production-shaped MLOps control plane
  (registry, feature store, deployment, monitoring).
- [`../30-triton-kernels/`](../30-triton-kernels/) —
  the GPU-shaped serving pattern (Triton, vLLM,
  custom kernels).
- [`../24-vertex-style-platform/`](../24-vertex-style-platform/) —
  the GCP-Vertex-style end-to-end ML platform.
- [`../19-rerank-service/`](../19-rerank-service/) —
  the small RAG-rerank service, a "Hello World"
  of retrieval + ranking.
