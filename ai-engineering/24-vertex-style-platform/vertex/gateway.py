"""Vertex-style unified AI platform: model garden + training + serving.

The shape behind Google's Vertex AI: one registry of model versions,
endpoint deployments with traffic splitting, online prediction, and
batch prediction. The value isn't any one component — it's that
versioned models, deployed endpoints, and split traffic share the same
registry, the same cost line, and the same versioning.

Meaningful workload:
- Registers 5 model versions across 3 base model families on
  different backends (local, bedrock, sagemaker, openai).
- Deploys 3 endpoints, each pinned to a model version.
- Scenario A: register → version → deploy → verify active.
- Scenario B: 500 online prediction requests, p50/p95/p99 latency.
- Scenario C: 80/20 traffic split, verify ratio within ±5%.
- Scenario D: 1000-row batch prediction in one call.
- Asserts: unique IDs, no drops, split ratio, batch count, finite p99.
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ModelEntry:
    model_id: str           # base model family, e.g. "llama-3-8b"
    backend: str            # "local" | "openai" | "bedrock" | "sagemaker"
    handler: Callable       # prompt -> response
    context_window: int = 4096
    cost_per_1k: float = 0.0
    active: bool = True


@dataclass
class ModelVersion:
    """A versioned, deployable artifact in the registry.

    Like Vertex AI model registry: a (model_id, version) pair is
    the canonical identifier. Endpoints pin to a specific version.
    """
    model_id: str           # e.g. "llama-3-8b"
    version: str            # e.g. "v1", "v2"
    artifact_uri: str       # where the weights live
    framework: str          # "pytorch" | "tensorflow" | "vllm" | "onnx"
    created_at: float
    registered: bool = False


@dataclass
class Registry:
    models: dict[str, ModelEntry] = field(default_factory=dict)
    versions: dict[str, ModelVersion] = field(default_factory=dict)  # key = "model_id@version"
    version_seq: dict[str, list[str]] = field(default_factory=dict)  # model_id -> [versions]

    def register(self, m: ModelEntry) -> None:
        self.models[m.model_id] = m

    def resolve(self, model_id: str) -> Optional[ModelEntry]:
        m = self.models.get(model_id)
        return m if m and m.active else None

    def register_version(self, v: ModelVersion) -> None:
        key = f"{v.model_id}@{v.version}"
        if key in self.versions:
            raise ValueError(f"version {key} already registered")
        v.registered = True
        self.versions[key] = v
        self.version_seq.setdefault(v.model_id, []).append(v.version)


@dataclass
class Endpoint:
    """A deployed model endpoint, like a Vertex AI endpoint.

    Has a primary model version, optional secondary for traffic
    splitting, and a traffic_split (e.g. 0.8 → primary, 0.2 → secondary).
    """
    endpoint_id: str
    primary_version: str    # "model_id@version"
    secondary_version: Optional[str] = None
    traffic_split: float = 1.0  # fraction going to primary
    deployed_at: float = 0.0
    deployed: bool = False


@dataclass
class Gateway:
    registry: Registry
    endpoints: dict[str, Endpoint] = field(default_factory=dict)
    fallback_chain: list[str] = field(default_factory=list)
    request_log: list[tuple[str, str, str]] = field(default_factory=list)
    # (endpoint_id, chosen_version, prompt)

    def route(self, model_id: str, prompt: str) -> tuple[str, str]:
        """Returns (chosen_model_id, response). Falls back through chain on miss."""
        tried = [model_id] + [m for m in self.fallback_chain if m != model_id]
        for mid in tried:
            m = self.registry.resolve(mid)
            if m is None:
                continue
            return mid, m.handler(prompt)
        return model_id, "[no model available]"

    def deploy(self, endpoint_id: str, primary_version: str,
               secondary_version: Optional[str] = None,
               traffic_split: float = 1.0) -> Endpoint:
        ep = Endpoint(
            endpoint_id=endpoint_id,
            primary_version=primary_version,
            secondary_version=secondary_version,
            traffic_split=traffic_split,
            deployed_at=time.time(),
            deployed=True,
        )
        self.endpoints[endpoint_id] = ep
        return ep

    def predict(self, endpoint_id: str, prompt: str,
                rng: Optional[random.Random] = None) -> tuple[str, str, float]:
        """Online prediction: pick version per traffic split, run handler.

        Returns (chosen_version, response, latency_seconds).
        """
        ep = self.endpoints[endpoint_id]
        # Choose version by traffic split
        if ep.secondary_version and ep.traffic_split < 1.0:
            r = (rng.random() if rng else random.random())
            chosen = ep.primary_version if r < ep.traffic_split else ep.secondary_version
        else:
            chosen = ep.primary_version

        # Resolve the model entry from the version key "model_id@version"
        model_id = chosen.split("@")[0]
        m = self.registry.resolve(model_id)
        if m is None:
            self.request_log.append((endpoint_id, "[miss]", prompt))
            return "[miss]", "[no model available]", 0.0

        t0 = time.perf_counter()
        resp = m.handler(prompt)
        latency = time.perf_counter() - t0
        self.request_log.append((endpoint_id, chosen, prompt))
        return chosen, resp, latency

    def batch_predict(self, endpoint_id: str, prompts: list[str]) -> list[tuple[str, str]]:
        """Batch prediction: run all prompts through the endpoint's primary version.

        Returns list of (chosen_version, response).
        """
        ep = self.endpoints[endpoint_id]
        model_id = ep.primary_version.split("@")[0]
        m = self.registry.resolve(model_id)
        out = []
        for p in prompts:
            if m is None:
                out.append(("[miss]", "[no model available]"))
                continue
            resp = m.handler(p)
            out.append((ep.primary_version, resp))
        return out


# === helpers ===

def percentile(values: list[float], p: float) -> float:
    """Compute the p-th percentile (0..100) of a list of floats."""
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


# === realistic workload ===

# Model families, each with a stable id and a deterministic handler.
MODEL_FAMILIES = [
    ("llama-3-8b",   "local",     0.0,    8192,    "vllm"),
    ("claude-sonnet","bedrock",   0.003,  200_000, "anthropic"),
    ("finetune-summarizer", "sagemaker", 0.0002, 4096, "pytorch"),
    ("gpt-4o-mini",  "openai",    0.00015,128_000, "openai"),
    ("finetune-classifier", "sagemaker", 0.0001, 4096, "tensorflow"),
]

VERSIONS_PER_FAMILY = ["v1", "v2"]  # → 10 model versions total


def build_model_handlers() -> dict[str, Callable]:
    """Return handler functions keyed by model_id.

    Handlers simulate backend work with a small sleep so latencies
    are realistic (and p99 is finite, but not zero).
    """
    rng = random.Random(7)
    handlers: dict[str, Callable] = {}
    for mid, backend, cost, ctx, fw in MODEL_FAMILIES:
        # Sleep is per-model: stable per model_id so we can attribute latency.
        # Pick a small jitter range (0.05–0.30ms) so p99 is realistic.
        base_ms = rng.uniform(0.05, 0.30)
        def make_handler(mid=mid, base_ms=base_ms):
            def h(prompt: str) -> str:
                # simulate backend work
                jitter = random.uniform(0.8, 1.2)
                time.sleep(base_ms * jitter / 1000.0)
                return f"[{mid}] {prompt[:60]}"
            return h
        handlers[mid] = make_handler()
    return handlers


def build_registry_and_endpoints() -> tuple[Registry, Gateway, list[ModelVersion], list[Endpoint]]:
    """Build the registry, endpoints, and the gateway."""
    reg = Registry()
    handlers = build_model_handlers()
    for mid, backend, cost, ctx, fw in MODEL_FAMILIES:
        reg.register(ModelEntry(
            model_id=mid,
            backend=backend,
            handler=handlers[mid],
            context_window=ctx,
            cost_per_1k=cost,
        ))

    gw = Gateway(
        registry=reg,
        fallback_chain=["claude-sonnet", "gpt-4o-mini", "llama-3-8b"],
    )

    # Register 2 versions per family → 10 model versions total
    versions: list[ModelVersion] = []
    seq = 0
    for mid, backend, cost, ctx, fw in MODEL_FAMILIES:
        for vlabel in VERSIONS_PER_FAMILY:
            seq += 1
            v = ModelVersion(
                model_id=mid,
                version=vlabel,
                artifact_uri=f"s3://models/{mid}/{vlabel}",
                framework=fw,
                created_at=time.time() + seq,
            )
            reg.register_version(v)
            versions.append(v)

    # Deploy 3 endpoints:
    #   ep-chat:  primary llama-3-8b@v1, secondary llama-3-8b@v2, split 0.8
    #   ep-summ:  primary finetune-summarizer@v2
    #   ep-cls:   primary finetune-classifier@v1
    endpoints: list[Endpoint] = []
    endpoints.append(gw.deploy(
        "ep-chat", "llama-3-8b@v1",
        secondary_version="llama-3-8b@v2",
        traffic_split=0.8,
    ))
    endpoints.append(gw.deploy("ep-summ", "finetune-summarizer@v2"))
    endpoints.append(gw.deploy("ep-cls", "finetune-classifier@v1"))

    return reg, gw, versions, endpoints


# === assertion helpers ===

def assert_unique_version_ids(versions: list[ModelVersion], registry: Registry) -> None:
    keys = [f"{v.model_id}@{v.version}" for v in versions]
    assert len(set(keys)) == len(keys), "model version IDs must be unique"
    for k in keys:
        assert k in registry.versions, f"version {k} missing from registry"
        assert registry.versions[k].registered, f"version {k} not marked registered"


def assert_endpoints_deployed(endpoints: list[Endpoint]) -> None:
    for ep in endpoints:
        assert ep.deployed, f"endpoint {ep.endpoint_id} not deployed"
        assert ep.primary_version, f"endpoint {ep.endpoint_id} has no primary version"


def assert_no_dropped_requests(responses: list) -> None:
    """Every predict() call must return a non-empty response."""
    for i, (chosen, resp, _lat) in enumerate(responses):
        assert resp and resp != "[no model available]", (
            f"dropped request at index {i}: chosen={chosen} resp={resp!r}"
        )


def assert_traffic_split(actual: float, target: float, tolerance: float = 0.05) -> None:
    assert abs(actual - target) <= tolerance, (
        f"traffic split off-target: actual={actual:.3f} target={target:.3f} "
        f"tolerance=±{tolerance:.2f}"
    )


def assert_batch_count(batch_out: list, n_inputs: int) -> None:
    assert len(batch_out) == n_inputs, (
        f"batch prediction returned {len(batch_out)} results, expected {n_inputs}"
    )
    for i, (chosen, resp) in enumerate(batch_out):
        assert resp and resp != "[no model available]", (
            f"batch prediction dropped item {i}"
        )


def assert_finite_p99(latencies: list[float]) -> None:
    assert latencies, "no latencies recorded"
    p99 = percentile(latencies, 99)
    assert p99 != float("inf"), "p99 latency is infinite"
    # Sanity: not absurdly high (would suggest a bug, not a real backend)
    assert p99 < 5.0, f"p99 latency too high: {p99:.3f}s"


# === main workload ===

if __name__ == "__main__":
    print("═══ vertex-style-platform: meaningful workload ═══")
    print()

    reg, gw, versions, endpoints = build_registry_and_endpoints()

    print(f"registered {len(versions)} model versions across "
          f"{len({v.model_id for v in versions})} model families")
    for v in versions:
        print(f"  {v.model_id}@{v.version}  ({v.framework:>11})  uri={v.artifact_uri}")
    print()
    print(f"deployed {len(endpoints)} endpoints:")
    for ep in endpoints:
        sec = f"  + split {ep.traffic_split:.0%}→{ep.secondary_version}" if ep.secondary_version else ""
        print(f"  {ep.endpoint_id}: primary={ep.primary_version}{sec}")
    print()

    # --- Invariant: every model version has a unique ID and is registered ---
    assert_unique_version_ids(versions, reg)
    assert_endpoints_deployed(endpoints)
    print("✓ all 10 model versions have unique IDs and are in the registry")
    print("✓ all 3 endpoints are deployed")
    print()

    # === Scenario A: register → version → deploy → verify active ===
    print("═══ Scenario A: model lifecycle (register → version → deploy → active) ═══")
    # Add a new version on-the-fly and deploy it (mimics a real "promote v3" workflow)
    new_v = ModelVersion(
        model_id="llama-3-8b",
        version="v3",
        artifact_uri="s3://models/llama-3-8b/v3",
        framework="vllm",
        created_at=time.time(),
    )
    reg.register_version(new_v)
    assert f"llama-3-8b@v3" in reg.versions, "new version not registered"
    assert new_v.registered, "new version not marked registered"
    # Deploy it to a new endpoint
    ep_chat_v3 = gw.deploy("ep-chat-v3", "llama-3-8b@v3")
    assert ep_chat_v3.deployed, "ep-chat-v3 not deployed"
    # Verify version is active by routing through it
    chosen, resp, _ = gw.predict("ep-chat-v3", "test prompt for v3")
    assert chosen == "llama-3-8b@v3", f"expected llama-3-8b@v3, got {chosen}"
    assert "[llama-3-8b]" in resp, f"v3 handler not invoked: {resp!r}"
    print(f"  registered llama-3-8b@v3, deployed ep-chat-v3, served: {resp}")
    print("✓ scenario A: end-to-end model lifecycle works")
    print()

    # === Scenario B: 500 online prediction requests, p50/p95/p99 ===
    print("═══ Scenario B: 500 online prediction requests on ep-summ ═══")
    rng = random.Random(42)
    prompts = [f"summarize document #{i}: <body of length {rng.randint(100, 5000)}>"
               for i in range(500)]
    latencies: list[float] = []
    responses: list = []
    t0 = time.time()
    for p in prompts:
        chosen, resp, lat = gw.predict("ep-summ", p)
        responses.append((chosen, resp, lat))
        latencies.append(lat)
    total = time.time() - t0

    assert_no_dropped_requests(responses)
    assert_finite_p99(latencies)

    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    rps = len(responses) / total if total > 0 else 0.0
    print(f"  requests:    {len(responses)}")
    print(f"  total time:  {total:.2f}s")
    print(f"  throughput:  {rps:.1f} req/s")
    print(f"  latency ms:  p50={p50*1000:.2f}  p95={p95*1000:.2f}  p99={p99*1000:.2f}")
    print("✓ scenario B: 500 requests, all served, p99 finite and reasonable")
    print()

    # === Scenario C: 80/20 traffic split on ep-chat ===
    print("═══ Scenario C: 80/20 traffic split (ep-chat) ═══")
    split_rng = random.Random(99)
    split_responses: list = []
    N_SPLIT = 2000
    for i in range(N_SPLIT):
        chosen, resp, _ = gw.predict("ep-chat", f"q{i}", rng=split_rng)
        split_responses.append(chosen)

    primary_count = sum(1 for c in split_responses if c == "llama-3-8b@v1")
    secondary_count = sum(1 for c in split_responses if c == "llama-3-8b@v2")
    other = N_SPLIT - primary_count - secondary_count
    actual_primary = primary_count / N_SPLIT
    actual_secondary = secondary_count / N_SPLIT
    target_primary = 0.8
    target_secondary = 0.2

    assert other == 0, f"unexpected version chosen: {other} requests not on v1/v2"
    assert_traffic_split(actual_primary, target_primary, tolerance=0.05)

    print(f"  requests:        {N_SPLIT}")
    print(f"  primary (v1):    {primary_count:>5}  ({actual_primary:.1%})  target={target_primary:.0%}")
    print(f"  secondary (v2):  {secondary_count:>5}  ({actual_secondary:.1%})  target={target_secondary:.0%}")
    print(f"  delta from target: primary={actual_primary - target_primary:+.3f}  "
          f"secondary={actual_secondary - target_secondary:+.3f}")
    print("✓ scenario C: traffic split within ±5% of target")
    print()

    # === Scenario D: batch prediction on 1000 inputs ===
    print("═══ Scenario D: batch prediction, 1000 inputs on ep-cls ═══")
    N_BATCH = 1000
    batch_prompts = [f"classify text #{i}: <{rng.randint(10, 500)} chars>" for i in range(N_BATCH)]
    t0 = time.time()
    batch_out = gw.batch_predict("ep-cls", batch_prompts)
    batch_t = time.time() - t0

    assert_batch_count(batch_out, N_BATCH)
    # Verify all results are for the expected version
    expected_v = "finetune-classifier@v1"
    bad = [i for i, (chosen, _) in enumerate(batch_out) if chosen != expected_v]
    assert not bad, f"batch: {len(bad)} items not on {expected_v}"

    bps = N_BATCH / batch_t if batch_t > 0 else 0.0
    print(f"  inputs:      {N_BATCH}")
    print(f"  results:     {len(batch_out)}")
    print(f"  total time:  {batch_t:.2f}s")
    print(f"  throughput:  {bps:.0f} items/s")
    print(f"  sample:      {batch_out[0][1][:60]}")
    print("✓ scenario D: 1000/1000 results returned, all on finetune-classifier@v1")
    print()

    # === Final state ===
    print("═══ final state ═══")
    print(f"  model versions registered: {len(reg.versions)}")
    print(f"  endpoints deployed:        {len(gw.endpoints)}")
    print(f"  total requests served:     {len(gw.request_log)}")
    print(f"  online (B):                500")
    print(f"  split (C):                 {N_SPLIT}  primary={actual_primary:.1%} secondary={actual_secondary:.1%}")
    print(f"  batch (D):                 {N_BATCH}  results={len(batch_out)}")
    print()
    print("✓ all invariants pass")
