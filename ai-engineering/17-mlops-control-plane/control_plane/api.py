"""
Minimal SageMaker-style MLOps control plane.

One FastAPI app, one workflow spec, one registry, one promotion gate, one
retrain trigger. The same shape AWS SageMaker / Vertex / Azure ML converge on.

Run:  uvicorn control_plane.api:app --reload --port 8080
"""
from __future__ import annotations
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="MLOps Control Plane")


# --- Workflow spec ----------------------------------------------------------

class Stage(str, Enum):
    LABEL = "label"
    TRAIN = "train"
    REGISTER = "register"
    DEPLOY = "deploy"
    MONITOR = "monitor"
    RETRAIN = "retrain"


@dataclass
class WorkflowSpec:
    """A linear pipeline of stages. Each stage has a handler + a gate."""
    name: str
    stages: list[Stage]
    handlers: dict[Stage, Callable] = field(default_factory=dict)
    gates: dict[Stage, Callable] = field(default_factory=dict)
    # State is a content-addressed dict so every transition is auditable.
    state: dict[str, Any] = field(default_factory=dict)

    def run_id(self) -> str:
        blob = json.dumps({"name": self.name, "stages": [s.value for s in self.stages]}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]


class RunRecord(BaseModel):
    run_id: str
    workflow: str
    started_at: float
    finished_at: float | None
    status: str
    transitions: list[dict]


RUNS: dict[str, RunRecord] = {}


# --- Reference handlers -----------------------------------------------------

def label_handler(spec: WorkflowSpec) -> dict:
    """Stand-in for an active-learning labeling job. Returns labeled count."""
    return {"labeled_count": 1000, "labeler": "human-in-the-loop"}


def train_handler(spec: WorkflowSpec) -> dict:
    """Stand-in for a training job. Returns a model artifact reference."""
    artifact = f"s3://models/{spec.run_id()}/model.bin"
    return {"artifact": artifact, "metrics": {"auc": 0.91, "loss": 0.21}}


def register_handler(spec: WorkflowSpec) -> dict:
    """Register the model. Real impl: write to a model registry table."""
    model_id = f"mdl-{uuid.uuid4().hex[:8]}"
    return {"model_id": model_id, "version": 1}


def deploy_handler(spec: WorkflowSpec) -> dict:
    """Canary deploy: 1% -> 10% -> 50% -> 100% on gate pass."""
    return {"endpoint": f"https://api.example.com/{spec.run_id()}", "canary_pct": 1}


def monitor_handler(spec: WorkflowSpec) -> dict:
    """Real impl: pull from Prometheus, compute drift, write to retrain queue."""
    return {"drift_score": 0.03, "p95_latency_ms": 180, "cost_per_1k": 0.42}


def retrain_handler(spec: WorkflowSpec) -> dict:
    """Triggered by monitor when drift crosses threshold."""
    return {"triggered": True, "reason": "drift > 0.05"}


HANDLERS = {
    Stage.LABEL: label_handler,
    Stage.TRAIN: train_handler,
    Stage.REGISTER: register_handler,
    Stage.DEPLOY: deploy_handler,
    Stage.MONITOR: monitor_handler,
    Stage.RETRAIN: retrain_handler,
}


# --- Promotion gate (the part that prevents footguns) -----------------------

class PromotionRequest(BaseModel):
    """Explicit promotion. NOT a generic PUT. Every promotion is logged with a reason."""
    model_id: str
    previous_prod_id: str | None
    gate_result: dict  # must include {"passed": true, "metric": ..., "threshold": ...}
    reason: str


REGISTRY: dict[str, dict] = {}  # model_id -> {version, metrics, promoted_at, reason}
PROD: str | None = None


@app.post("/promote")
def promote(req: PromotionRequest):
    if not req.gate_result.get("passed"):
        raise HTTPException(status_code=400, detail="gate did not pass")
    if not req.reason.strip():
        raise HTTPException(status_code=400, detail="reason required for promotion")
    REGISTRY[req.model_id] = {
        "previous": req.previous_prod_id,
        "gate": req.gate_result,
        "reason": req.reason,
        "promoted_at": time.time(),
    }
    global PROD
    PROD = req.model_id
    return {"status": "promoted", "prod": PROD, "registry_size": len(REGISTRY)}


# --- The control plane itself -----------------------------------------------

class RunRequest(BaseModel):
    workflow: str  # "linear" or "monitoring_loop"


@app.post("/run")
def start_run(req: RunRequest):
    stages = [Stage.LABEL, Stage.TRAIN, Stage.REGISTER, Stage.DEPLOY, Stage.MONITOR]
    if req.workflow == "monitoring_loop":
        stages.append(Stage.RETRAIN)

    spec = WorkflowSpec(name=req.workflow, stages=stages, handlers=HANDLERS)
    rid = spec.run_id()

    rec = RunRecord(
        run_id=rid, workflow=req.workflow, started_at=time.time(),
        finished_at=None, status="running", transitions=[],
    )
    RUNS[rid] = rec

    for s in stages:
        handler = HANDLERS[s]
        out = handler(spec)
        spec.state[s.value] = out
        rec.transitions.append({"stage": s.value, "output": out, "ts": time.time()})

    rec.finished_at = time.time()
    rec.status = "succeeded"
    return {"run_id": rid, "transitions": rec.transitions, "final_state": spec.state}


@app.get("/runs/{rid}")
def get_run(rid: str):
    if rid not in RUNS:
        raise HTTPException(status_code=404, detail="run not found")
    return RUNS[rid]


@app.get("/registry")
def list_registry():
    return {"prod": PROD, "models": REGISTRY}


@app.get("/healthz")
def healthz():
    return {"ok": True, "runs": len(RUNS), "registry": len(REGISTRY)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("control_plane.api:app", host="0.0.0.0", port=8080, reload=True)
