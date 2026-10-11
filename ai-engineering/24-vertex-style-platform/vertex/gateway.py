"""Vertex-style unified AI platform: model garden + training + serving.

The shape: one registry, one gateway, many backends. The toy captures
the routing layer — the same client code talks to a local model, a
remote API, or a fine-tuned variant, and the gateway picks the right one
based on the request's model_id.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ModelEntry:
    model_id: str
    backend: str          # "local" | "openai" | "bedrock" | "sagemaker"
    handler: Callable     # prompt -> response
    context_window: int = 4096
    cost_per_1k: float = 0.0  # USD
    active: bool = True


@dataclass
class Registry:
    models: dict[str, ModelEntry] = field(default_factory=dict)

    def register(self, m: ModelEntry) -> None:
        self.models[m.model_id] = m

    def resolve(self, model_id: str) -> Optional[ModelEntry]:
        m = self.models.get(model_id)
        return m if m and m.active else None


@dataclass
class Gateway:
    registry: Registry
    fallback_chain: list[str] = field(default_factory=list)

    def route(self, model_id: str, prompt: str) -> tuple[str, str]:
        """Returns (chosen_model_id, response). Falls back through chain on miss."""
        tried = [model_id] + [m for m in self.fallback_chain if m != model_id]
        for mid in tried:
            m = self.registry.resolve(mid)
            if m is None:
                continue
            return mid, m.handler(prompt)
        return model_id, "[no model available]"


if __name__ == "__main__":
    reg = Registry()
    reg.register(ModelEntry(
        model_id="llama-3-8b",
        backend="local",
        handler=lambda p: f"[local:llama-3-8b] {p[:40]}",
        context_window=8192,
        cost_per_1k=0.0,
    ))
    reg.register(ModelEntry(
        model_id="claude-sonnet",
        backend="bedrock",
        handler=lambda p: f"[bedrock:claude-sonnet] {p[:40]}",
        context_window=200_000,
        cost_per_1k=0.003,
    ))
    reg.register(ModelEntry(
        model_id="my-finetune-v1",
        backend="sagemaker",
        handler=lambda p: f"[sagemaker:my-finetune-v1] {p[:40]}",
        context_window=4096,
        cost_per_1k=0.0002,
    ))

    gw = Gateway(registry=reg, fallback_chain=["claude-sonnet", "llama-3-8b"])

    # hit a registered model
    mid, resp = gw.route("my-finetune-v1", "Summarize the Q3 risk report.")
    print(f"chosen: {mid}\nresponse: {resp}")

    # miss a model, gateway falls back
    mid, resp = gw.route("gpt-99-not-here", "Plan the migration.")
    print(f"\nchosen: {mid}\nresponse: {resp}")
