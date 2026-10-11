"""Hugging Face-style model registry: versioning + license gate.

The shape behind HF Hub: a registry of models, each with a version
line, a license, an eval table, and download stats. The license gate
is the part that matters in production — a non-commercial-licensed
model cannot be served commercially.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


COMMERCIAL_LICENSES = {"apache-2.0", "mit", "bsd-3-clause", "llama3-community"}
NON_COMMERCIAL_LICENSES = {"cc-by-nc-4.0", "research-only", "cc-by-nc-sa-4.0"}


@dataclass
class ModelVersion:
    sha: str
    eval_table: dict = field(default_factory=dict)  # {"mmlu": 0.62, "gsm8k": 0.41}
    downloads: int = 0
    artifact_uri: str = ""


@dataclass
class Model:
    name: str                     # "my-org/llama-3-8b-finetune"
    license: str
    versions: list[ModelVersion] = field(default_factory=list)
    gated: bool = False

    def latest(self) -> Optional[ModelVersion]:
        return self.versions[-1] if self.versions else None

    def can_serve_commercially(self) -> bool:
        return self.license.lower() in COMMERCIAL_LICENSES


@dataclass
class Hub:
    models: dict[str, Model] = field(default_factory=dict)
    blocked_licenses: set[str] = field(default_factory=lambda: NON_COMMERCIAL_LICENSES.copy())

    def publish(self, model: Model, version: ModelVersion) -> None:
        if model.name not in self.models:
            self.models[model.name] = model
        self.models[model.name].versions.append(version)

    def serve_url(self, name: str, commercial: bool) -> Optional[str]:
        m = self.models.get(name)
        if m is None:
            return None
        if commercial and not m.can_serve_commercially():
            return None
        v = m.latest()
        if v is None:
            return None
        return f"hub://{name}@{v.sha}"

    def list_licenses(self) -> dict:
        out: dict[str, int] = {}
        for m in self.models.values():
            out[m.license] = out.get(m.license, 0) + 1
        return out


if __name__ == "__main__":
    hub = Hub()
    hub.publish(
        Model(name="acme/llama-finetune", license="apache-2.0"),
        ModelVersion(sha="abc123", eval_table={"mmlu": 0.64, "gsm8k": 0.48}, downloads=12_400),
    )
    hub.publish(
        Model(name="acme/research-only-7b", license="cc-by-nc-4.0"),
        ModelVersion(sha="def456", eval_table={"mmlu": 0.59}, downloads=300),
    )
    hub.publish(
        Model(name="acme/llama-finetune", license="apache-2.0"),
        ModelVersion(sha="abc124", eval_table={"mmlu": 0.66, "gsm8k": 0.51}, downloads=2_100),
    )

    print("commercial serve URL (acme/llama-finetune):", hub.serve_url("acme/llama-finetune", commercial=True))
    print("commercial serve URL (acme/research-only-7b):", hub.serve_url("acme/research-only-7b", commercial=True))
    print("research  serve URL (acme/research-only-7b):", hub.serve_url("acme/research-only-7b", commercial=False))
    print(f"latest version of acme/llama-finetune: {hub.models['acme/llama-finetune'].latest().sha}")
    print(f"license distribution: {hub.list_licenses()}")
