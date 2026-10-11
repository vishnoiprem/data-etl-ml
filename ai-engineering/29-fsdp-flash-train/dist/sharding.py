"""Nvidia-style distributed training: FSDP sharding math + FlashAttention.

FSDP (Fully Sharded Data Parallel) splits model parameters, gradients,
and optimizer states across N GPUs. Each GPU holds 1/N of the state.
This toy computes the memory and compute budget for a given model +
GPU count, so you can answer "will 7B params fit on 8x A10G?" before
you start the run.

Meaningful workload:
- Scenario A: shard a 7B-style model across N simulated workers and
  verify each worker holds exactly 1/N of the parameters.
- Scenario B: gather parameters onto each worker, run a forward pass,
  scatter gradients back, and verify per-worker memory is reduced
  proportional to N.
- Scenario C: training loop with gradient accumulation
  (accumulation_steps=4) on a synthetic dataset of 10,000 samples,
  verifying effective batch size = batch * accum_steps.
- Scenario D: FlashAttention-style tiled attention — compute Q @ K^T
  in tiles of 64 along seq_len=512, softmax, and verify output
  matches naive full-sequence attention within tolerance.

Assertion-based correctness:
- sharded parameters sum to total parameters (lossless split)
- gather/scatter round-trip preserves values within float32 epsilon
- effective batch size = batch_size * accumulation_steps
- tiled attention output matches naive output (max abs diff < 1e-4)
- loss decreases over training
"""
from __future__ import annotations
import time
from dataclasses import dataclass

import numpy as np


# ============================================================================
# Original bytes-per-param accounting (kept intact — public API unchanged)
# ============================================================================
@dataclass
class ModelConfig:
    n_params_b: float       # in billions
    dtype_bytes: int = 2    # bf16/fp16
    optimizer: str = "adamw"  # adamw | sgd | adafactor
    grad_accum_steps: int = 1
    activation_gb: float = 8.0   # activations, bs=1 estimate

    def bytes_per_param(self) -> dict:
        # params: 2 bytes (bf16)
        # grads:  2 bytes (bf16)
        # optimizer (AdamW): 4 (fp32 master) + 4 (m) + 4 (v) = 12 bytes in fp32
        # optimizer (SGD): 4 bytes
        # optimizer (Adafactor): 4 bytes
        opt_bytes = {"adamw": 12, "sgd": 4, "adafactor": 4}.get(self.optimizer, 12)
        return {
            "params": self.dtype_bytes,
            "grads": self.dtype_bytes,
            "optimizer": opt_bytes,
            "total_per_param": self.dtype_bytes + self.dtype_bytes + opt_bytes,
        }


@dataclass
class ShardingPlan:
    n_gpus: int
    cfg: ModelConfig
    fsdp: bool = True

    def per_gpu_memory_gb(self) -> dict:
        bpp = self.cfg.bytes_per_param()
        n_params = self.cfg.n_params_b * 1e9
        if self.fsdp:
            params_per_gpu = n_params * bpp["params"] / self.n_gpus
            grads_per_gpu = n_params * bpp["grads"] / self.n_gpus
            opt_per_gpu = n_params * bpp["optimizer"] / self.n_gpus
        else:
            # DDP: every GPU holds full params + grads, optimizer sharded
            params_per_gpu = n_params * bpp["params"]
            grads_per_gpu = n_params * bpp["grads"]
            opt_per_gpu = n_params * bpp["optimizer"] / self.n_gpus
        bytes_to_gb = 1 / (1024 ** 3)
        return {
            "params_gb": params_per_gpu * bytes_to_gb,
            "grads_gb": grads_per_gpu * bytes_to_gb,
            "optimizer_gb": opt_per_gpu * bytes_to_gb,
            "static_total_gb": (params_per_gpu + grads_per_gpu + opt_per_gpu) * bytes_to_gb,
            "activations_gb": self.cfg.activation_gb * self.cfg.grad_accum_steps,
        }


# ============================================================================
# New: simulated FSDP workers with explicit parameter sharding
# ============================================================================
@dataclass
class ShardedWorker:
    worker_id: int
    shard: np.ndarray          # local slice of the flattened parameter array
    grad_shard: np.ndarray     # local slice of the flattened gradient
    n_params_total: int
    shard_size: int


def shard_parameters(params: np.ndarray, n_workers: int) -> list[ShardedWorker]:
    """Split a 1-D parameter vector across n_workers. Returns a worker per shard.

    Each worker holds floor(total / n_workers) or ceil(total / n_workers)
    parameters — the last worker absorbs the remainder.
    """
    total = params.size
    base = total // n_workers
    rem = total % n_workers
    workers = []
    offset = 0
    for wid in range(n_workers):
        size = base + (1 if wid < rem else 0)
        shard = params[offset:offset + size].copy()
        grad_shard = np.zeros_like(shard)
        workers.append(ShardedWorker(
            worker_id=wid,
            shard=shard,
            grad_shard=grad_shard,
            n_params_total=total,
            shard_size=size,
        ))
        offset += size
    return workers


def gather_workers(workers: list[ShardedWorker], total: int) -> np.ndarray:
    """All-gather all worker parameter shards back into one contiguous vector."""
    out = np.empty(total, dtype=workers[0].shard.dtype)
    offset = 0
    for w in workers:
        sz = w.shard.size
        out[offset:offset + sz] = w.shard
        offset += sz
    return out


def gather_gradients(workers: list[ShardedWorker], total: int) -> np.ndarray:
    """All-gather all worker gradient shards back into one contiguous vector."""
    out = np.empty(total, dtype=workers[0].grad_shard.dtype)
    offset = 0
    for w in workers:
        sz = w.grad_shard.size
        out[offset:offset + sz] = w.grad_shard
        offset += sz
    return out


def scatter_gradients(workers: list[ShardedWorker], grads_full: np.ndarray) -> None:
    """Reduce a full-size gradient back onto each worker (scatter the chunks)."""
    offset = 0
    for w in workers:
        sz = w.shard.size
        w.grad_shard = grads_full[offset:offset + sz].copy()
        offset += sz


# ============================================================================
# New: tiny dense model for the training loop (no torch)
# ============================================================================
@dataclass
class TinyModel:
    W1: np.ndarray   # (hidden, in)
    b1: np.ndarray   # (hidden,)
    W2: np.ndarray   # (out, hidden)
    b2: np.ndarray   # (out,)

    def flat_params(self) -> np.ndarray:
        return np.concatenate([
            self.W1.ravel(), self.b1.ravel(),
            self.W2.ravel(), self.b2.ravel(),
        ])

    def set_flat_params(self, p: np.ndarray) -> None:
        # sizes: in=H_in, hidden=H, out=H_out
        h_in = self.W1.shape[0]
        h = self.W1.shape[1]
        h_out = self.W2.shape[0]
        # layout: W1 (hidden, in), b1 (hidden,), W2 (out, hidden), b2 (out,)
        # but our W1 stored as (hidden, in), so sizes match the constructor's
        # convention. Use known sizes to split.
        n_w1 = self.W1.size
        n_b1 = self.b1.size
        n_w2 = self.W2.size
        n_b2 = self.b2.size
        self.W1 = p[0:n_w1].reshape(self.W1.shape).astype(self.W1.dtype)
        self.b1 = p[n_w1:n_w1 + n_b1].reshape(self.b1.shape).astype(self.b1.dtype)
        self.W2 = p[n_w1 + n_b1:n_w1 + n_b1 + n_w2].reshape(self.W2.shape).astype(self.W2.dtype)
        self.b2 = p[n_w1 + n_b1 + n_w2:n_w1 + n_b1 + n_w2 + n_b2].reshape(self.b2.shape).astype(self.b2.dtype)


def init_tiny_model(rng: np.random.Generator, h_in: int = 32, h: int = 64, h_out: int = 10) -> TinyModel:
    # Note: W1 stored as (h, h_in) so that W1 @ x operates via (h, h_in) @ (h_in,)
    return TinyModel(
        W1=(rng.standard_normal((h, h_in)) * 0.1).astype(np.float32),
        b1=np.zeros(h, dtype=np.float32),
        W2=(rng.standard_normal((h_out, h)) * 0.1).astype(np.float32),
        b2=np.zeros(h_out, dtype=np.float32),
    )


def model_forward(m: TinyModel, x: np.ndarray) -> np.ndarray:
    """x: (batch, h_in) -> (batch, h_out). Two-layer MLP with ReLU."""
    h_pre = m.W1 @ x.T + m.b1[:, None]   # (h, batch)
    h_act = np.maximum(0.0, h_pre)
    out = (m.W2 @ h_act + m.b2[:, None]).T   # (batch, h_out)
    return out


def cross_entropy_loss_and_grad(logits: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray]:
    """Mean cross-entropy + dL/dlogits. y: int array of shape (batch,)."""
    # Numerically stable softmax
    z = logits - logits.max(axis=1, keepdims=True)
    exp_z = np.exp(z)
    p = exp_z / exp_z.sum(axis=1, keepdims=True)
    n = logits.shape[0]
    loss = float(-np.log(np.clip(p[np.arange(n), y], 1e-12, 1.0)).mean())
    p[np.arange(n), y] -= 1.0
    p /= n
    return loss, p


def gradient_accumulation_steps_for(batch_size: int, total: int) -> int:
    """How many optimizer steps for `total` samples at batch_size.

    Returns accumulation_steps such that batch_size * accum_steps is the
    effective batch size used per optimizer step.
    """
    accum = max(1, total // batch_size)
    return accum


# ============================================================================
# New: FlashAttention-style tiled attention (no torch, no flash kernels)
# ============================================================================
def naive_attention(Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
    """Reference attention: O(seq^2) memory, full softmax over all keys.

    Q: (seq, d_k), K: (seq, d_k), V: (seq, d_v). Returns (seq, d_v).
    """
    d_k = Q.shape[1]
    scores = Q @ K.T / np.sqrt(d_k)              # (seq, seq)
    # Stable row-wise softmax
    scores = scores - scores.max(axis=1, keepdims=True)
    exp_s = np.exp(scores)
    p = exp_s / exp_s.sum(axis=1, keepdims=True)
    return p @ V


def tiled_attention(Q: np.ndarray, K: np.ndarray, V: np.ndarray, tile: int = 64) -> np.ndarray:
    """FlashAttention-style tiled attention: streams over keys in chunks of `tile`.

    Q: (seq, d_k), K: (seq, d_k), V: (seq, d_v). Returns (seq, d_v).

    Implements the standard online-softmax tiling: scales + max-tracking so
    each row is computed correctly even though not all (score, value) pairs
    fit in memory at once.
    """
    seq, d_k = Q.shape
    d_v = V.shape[1]
    scale = 1.0 / np.sqrt(d_k)
    # Outputs
    O = np.zeros((seq, d_v), dtype=np.float32)
    # Running max and denominator for online softmax
    m_run = np.full(seq, -np.inf, dtype=np.float32)
    l_run = np.zeros(seq, dtype=np.float32)
    for ks in range(0, seq, tile):
        ke = min(ks + tile, seq)
        Kb = K[ks:ke]                                  # (tile_k, d_k)
        Vb = V[ks:ke]                                  # (tile_k, d_v)
        Sb = (Q @ Kb.T) * scale                        # (seq, tile_k)
        m_new = np.maximum(m_run, Sb.max(axis=1))      # (seq,)
        # Rescale previous O and l by exp(m_run - m_new)
        alpha = np.exp(m_run - m_new)
        Sb = np.exp(Sb - m_new[:, None])               # (seq, tile_k) shifted exp
        l_new = alpha * l_run + Sb.sum(axis=1)         # (seq,)
        # Rescale previous O
        O = O * alpha[:, None]
        # Accumulate weighted V contribution
        O = O + Sb @ Vb
        m_run = m_new
        l_run = l_new
    O = O / l_run[:, None]
    return O


# ============================================================================
# Meaningful workload driver
# ============================================================================
def _rng(seed: int = 42) -> np.random.Generator:
    return np.random.default_rng(seed)


def scenario_a_shard_across_workers(rng: np.random.Generator) -> dict:
    """Shard a 7B-param-equivalent vector across N workers, verify 1/N split."""
    # Use a much smaller stand-in: we don't actually allocate 7B floats;
    # use the same SHAPE-PROPORTIONAL test with a downscaled parameter array
    # of a known size.
    n_workers = 8
    total_params = 1_024   # stand-in vector (we can reason about proportions)
    params = rng.standard_normal(total_params).astype(np.float32) * 0.1
    workers = shard_parameters(params, n_workers)
    sizes = [w.shard.size for w in workers]
    total_shard = sum(sizes)
    # Each worker should have ~1/N of params
    expected = total_params / n_workers
    assert total_shard == total_params, "shards must sum to total"
    for w in workers:
        # Allow off-by-one for the remainder
        assert abs(w.shard.size - expected) <= 1, (
            f"worker {w.worker_id} shard size {w.shard.size} far from 1/N={expected}"
        )
    return {
        "n_workers": n_workers,
        "total_params": total_params,
        "per_worker": sizes,
        "expected_per_worker": expected,
    }


def scenario_b_gather_scatter_memory(rng: np.random.Generator, n_workers: int = 8) -> dict:
    """Gather params on each worker, run forward, scatter grads back. Compare memory."""
    cfg = ModelConfig(n_params_b=7.0, dtype_bytes=2, optimizer="adamw",
                      grad_accum_steps=4, activation_gb=6.0)
    plan_fsdp = ShardingPlan(n_gpus=n_workers, cfg=cfg, fsdp=True)
    plan_ddp = ShardingPlan(n_gpus=n_workers, cfg=cfg, fsdp=False)
    m_fsdp = plan_fsdp.per_gpu_memory_gb()
    m_ddp = plan_ddp.per_gpu_memory_gb()

    # Simulate: gather params on worker 0, run forward on a single shard
    # worth of data, scatter gradients back.
    model = init_tiny_model(_rng(0))
    full_params = model.flat_params()
    # Initialize sharded workers
    workers = shard_parameters(full_params, n_workers)
    # Each worker's shard size
    per_worker_params_bytes = workers[0].shard.nbytes
    # Gather: pretend we all-gather onto worker 0 for the forward pass
    t0 = time.time()
    gathered = gather_workers(workers, full_params.size)
    gather_ms = (time.time() - t0) * 1000
    # Run a forward on worker 0 with synthetic input
    model.set_flat_params(gathered)
    x = rng.standard_normal((4, model.W1.shape[1])).astype(np.float32)
    logits = model_forward(model, x)
    # Compute the grad w.r.t. flat params (numerical-perturbation style:
    # we don't need a real backward here — we just need a grad vector of
    # the same length to verify scatter round-trip is lossless).
    # Synthetic gradient: noise with the same shape as the params.
    grads_full = (rng.standard_normal(full_params.shape).astype(np.float32)) * 0.001
    # Scatter grads back to the workers
    t0 = time.time()
    scatter_gradients(workers, grads_full)
    scatter_ms = (time.time() - t0) * 1000
    # Verify round-trip
    gathered_back = gather_gradients(workers, grads_full.size)
    assert np.allclose(gathered_back, grads_full, atol=1e-6), (
        "scatter round-trip is not lossless within float32 epsilon"
    )
    # FSDP shards params+grads+opt; DDP shards only opt. The savings factor
    # therefore depends on the optimizer's bytes. For AdamW (12B/param),
    # savings = (params+grads+opt/N) / (params+grads+opt)/N.
    n = n_workers
    bpp = cfg.bytes_per_param()
    fsdp_per_param = (bpp["params"] + bpp["grads"] + bpp["optimizer"]) / n
    ddp_per_param = (bpp["params"] + bpp["grads"]) + bpp["optimizer"] / n
    expected_savings = ddp_per_param / fsdp_per_param
    return {
        "n_workers": n_workers,
        "static_per_worker_fsdp_gb": m_fsdp["static_total_gb"],
        "static_per_worker_ddp_gb": m_ddp["static_total_gb"],
        "fsdp_savings_factor": m_ddp["static_total_gb"] / m_fsdp["static_total_gb"],
        "expected_savings_factor": expected_savings,
        "per_worker_shard_bytes": per_worker_params_bytes,
        "gather_ms": gather_ms,
        "scatter_ms": scatter_ms,
        "forward_output_shape": tuple(logits.shape),
    }


def scenario_c_training_with_accumulation(rng: np.random.Generator) -> dict:
    """Training loop with gradient accumulation. Verify effective batch size
    and that loss decreases."""
    # Synthetic dataset
    n_samples = 10_000
    n_features = 32
    n_classes = 10
    X = rng.standard_normal((n_samples, n_features)).astype(np.float32)
    # Synthetic labels — class = argmax over a linear projection + noise
    proj = rng.standard_normal((n_features, n_classes)).astype(np.float32)
    logits_true = X @ proj
    # Add class-dependent bias so the projection is roughly discriminative
    y = np.argmax(logits_true + rng.standard_normal(logits_true.shape) * 0.3, axis=1).astype(np.int64)

    model = init_tiny_model(_rng(1), h_in=n_features, h=64, h_out=n_classes)
    batch_size = 32
    n_steps = 60          # >50 training steps
    accumulation_steps = 4
    effective_batch = batch_size * accumulation_steps
    lr = 0.05

    losses = []
    sample_idx = 0
    for step in range(n_steps):
        # Accumulation loop: gather `accumulation_steps` micro-batches
        accum_grad = None
        accum_loss_sum = 0.0
        for micro in range(accumulation_steps):
            # Slice with wrap-around so we keep moving through the dataset
            start = (sample_idx) % n_samples
            end = start + batch_size
            if end <= n_samples:
                Xb = X[start:end]
                yb = y[start:end]
            else:
                # tail: wrap + concat
                first = X[start:n_samples]
                second = X[0:end - n_samples]
                Xb = np.concatenate([first, second], axis=0)
                first_y = y[start:n_samples]
                second_y = y[0:end - n_samples]
                yb = np.concatenate([first_y, second_y], axis=0)
            sample_idx = (sample_idx + batch_size) % n_samples

            # Forward
            logits = model_forward(model, Xb)
            loss, dlogits = cross_entropy_loss_and_grad(logits, yb)
            accum_loss_sum += loss

            # Compute gradient w.r.t. each parameter via finite differences
            # is too slow. Instead, do a real analytic gradient for this
            # tiny model: chain rule through ReLU + linear.
            # dL/dz (z is pre-activation of layer 2)
            # z = W2 @ h + b2, h = ReLU(z1), z1 = W1 @ x + b1
            # dlogits is dL/dout, where out = z + b2 (i.e., we treat z as the
            # pre-b2 logit). Since logits = z + b2 (broadcast), dL/dz = dlogits.
            # Implementation note: model_forward computes z = W2 @ h + b2,
            # so dL/dz = dlogits.
            z2 = (model.W2 @ np.maximum(0.0, model.W1 @ Xb.T + model.b1[:, None]) + model.b2[:, None])
            # We recompute h1, h to keep code explicit
            h1_pre = model.W1 @ Xb.T + model.b1[:, None]              # (h, batch)
            h1_act = np.maximum(0.0, h1_pre)                            # (h, batch)
            h2_pre = model.W2 @ h1_act + model.b2[:, None]              # (out, batch)

            # dL/dz2 = dlogits.T  (since dlogits is (batch, out))
            dz2 = dlogits.T                                            # (out, batch)
            dW2 = dz2 @ h1_act.T                                       # (out, h)
            db2 = dz2.sum(axis=1)                                      # (out,)
            dh1 = model.W2.T @ dz2                                     # (h, batch)
            dh1 = dh1 * (h1_pre > 0).astype(np.float32)                # ReLU'
            dW1 = dh1 @ Xb                                             # (h, in)
            db1 = dh1.sum(axis=1)                                      # (h,)

            # Flatten and scale by 1/accum_steps (proper effective-batch gradient)
            micro_grad = np.concatenate([
                dW1.ravel() / accumulation_steps,
                db1.ravel() / accumulation_steps,
                dW2.ravel() / accumulation_steps,
                db2.ravel() / accumulation_steps,
            ]).astype(np.float32)
            if accum_grad is None:
                accum_grad = micro_grad
            else:
                accum_grad = accum_grad + micro_grad

        # SGD step
        params = model.flat_params() - lr * accum_grad
        model.set_flat_params(params)
        losses.append(accum_loss_sum / accumulation_steps)

    # Assertions
    assert effective_batch == batch_size * accumulation_steps, (
        "effective_batch must equal batch * accum_steps"
    )
    assert len(losses) == n_steps
    # Loss must decrease (allow some noise: use first-decile vs last-decile)
    head = np.mean(losses[: n_steps // 10])
    tail = np.mean(losses[-n_steps // 10:])
    loss_decreased = tail < head
    assert loss_decreased, (
        f"loss did not decrease: head={head:.4f}, tail={tail:.4f}"
    )

    return {
        "n_samples": n_samples,
        "batch_size": batch_size,
        "accumulation_steps": accumulation_steps,
        "effective_batch": effective_batch,
        "n_steps": n_steps,
        "loss_first": float(losses[0]),
        "loss_last": float(losses[-1]),
        "loss_head_mean": float(head),
        "loss_tail_mean": float(tail),
        "loss_reduction": float(head - tail),
    }


def scenario_d_tiled_attention(rng: np.random.Generator) -> dict:
    """FlashAttention-style tiled attention vs naive attention. Verify output matches."""
    seq_len = 512
    d_k = 64
    d_v = 64
    Q = (rng.standard_normal((seq_len, d_k))).astype(np.float32)
    K = (rng.standard_normal((seq_len, d_k))).astype(np.float32)
    V = (rng.standard_normal((seq_len, d_v))).astype(np.float32)

    tile = 64

    t0 = time.time()
    naive_out = naive_attention(Q, K, V)
    naive_ms = (time.time() - t0) * 1000

    t0 = time.time()
    tiled_out = tiled_attention(Q, K, V, tile=tile)
    tiled_ms = (time.time() - t0) * 1000

    max_abs_diff = float(np.max(np.abs(tiled_out - naive_out)))
    mean_abs_diff = float(np.mean(np.abs(tiled_out - naive_out)))
    # Output shape sanity
    assert naive_out.shape == tiled_out.shape == (seq_len, d_v)
    # Row-sum of softmax: each row of p @ V should be weighted by ~1
    # (sanity check the attention weights indirectly: row-norm should be > 0)
    assert max_abs_diff < 1e-4, (
        f"tiled attention output diverges from naive: max_abs_diff={max_abs_diff}"
    )

    return {
        "seq_len": seq_len,
        "d_k": d_k,
        "d_v": d_v,
        "tile": tile,
        "naive_ms": naive_ms,
        "tiled_ms": tiled_ms,
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff": mean_abs_diff,
    }


# ============================================================================
# Main: meaningful workload
# ============================================================================
if __name__ == "__main__":
    print("═══ FSDP + FlashAttention training: meaningful workload ═══")
    rng = _rng(42)
    print()

    # ------------------------------------------------------------------
    # Baseline memory plan (original public API)
    # ------------------------------------------------------------------
    cfg = ModelConfig(n_params_b=7.0, dtype_bytes=2, optimizer="adamw",
                      grad_accum_steps=4, activation_gb=6.0)
    plan = ShardingPlan(n_gpus=8, cfg=cfg, fsdp=True)
    m = plan.per_gpu_memory_gb()
    print("baseline FSDP memory plan (7B / AdamW / 8 GPUs):")
    for k, v in m.items():
        print(f"  {k}: {v:.2f} GB")
    print(f"  fits in 24 GB A10G: {m['static_total_gb'] + m['activations_gb'] < 24}")

    plan_ddp = ShardingPlan(n_gpus=8, cfg=cfg, fsdp=False)
    m2 = plan_ddp.per_gpu_memory_gb()
    print(f"baseline DDP memory plan:")
    print(f"  static_total_gb: {m2['static_total_gb']:.2f} GB (vs FSDP {m['static_total_gb']:.2f})")
    print(f"  fits in 24 GB A10G: {m2['static_total_gb'] + m2['activations_gb'] < 24}")
    print()

    # ------------------------------------------------------------------
    # Scenario A: shard across workers, verify 1/N split
    # ------------------------------------------------------------------
    print("═══ Scenario A: shard a model across N simulated workers ═══")
    a = scenario_a_shard_across_workers(rng)
    print(f"  n_workers:       {a['n_workers']}")
    print(f"  total_params:     {a['total_params']:,}")
    print(f"  shard sizes:      {a['per_worker']}")
    print(f"  expected each:    {a['expected_per_worker']:.2f}")
    total_shards = sum(a['per_worker'])
    assert total_shards == a['total_params'], "shards must sum to total params"
    for sz in a['per_worker']:
        assert abs(sz - a['expected_per_worker']) <= 1, (
            f"shard {sz} far from 1/N={a['expected_per_worker']}"
        )
    print(f"  ✓ sharded parameters sum to total parameters")
    print(f"  ✓ each worker holds 1/N of parameters (±1 for remainder)")
    print()

    # ------------------------------------------------------------------
    # Scenario B: gather/forward/scatter + per-worker memory reduction
    # ------------------------------------------------------------------
    print("═══ Scenario B: gather → forward → scatter, verify memory reduced ═══")
    b = scenario_b_gather_scatter_memory(rng, n_workers=8)
    print(f"  n_workers:                    {b['n_workers']}")
    print(f"  FSDP static per worker:       {b['static_per_worker_fsdp_gb']:.2f} GB")
    print(f"  DDP  static per worker:       {b['static_per_worker_ddp_gb']:.2f} GB")
    print(f"  DDP→FSDP memory savings:      {b['fsdp_savings_factor']:.1f}x")
    print(f"  expected (AdamW math):        {b['expected_savings_factor']:.2f}x")
    print(f"  per-worker shard bytes:       {b['per_worker_shard_bytes']:,}")
    print(f"  gather time:                  {b['gather_ms']:.3f} ms")
    print(f"  scatter time:                 {b['scatter_ms']:.3f} ms")
    print(f"  forward output shape:         {b['forward_output_shape']}")
    # The savings factor depends on the optimizer: DDP shards only optimizer,
    # so the savings is asymptotic to (N × (params+grads)) / (params+grads+optimizer).
    # For AdamW with N=8, this is ~2.75x. The key invariant: FSDP per-worker
    # memory < DDP per-worker memory.
    assert b['fsdp_savings_factor'] > 1.0, (
        f"FSDP should reduce per-worker memory vs DDP; got {b['fsdp_savings_factor']}"
    )
    assert b['static_per_worker_fsdp_gb'] < b['static_per_worker_ddp_gb'], (
        "FSDP per-worker memory must be strictly less than DDP"
    )
    # Ratio must match the analytical formula within rounding
    assert abs(b['fsdp_savings_factor'] - b['expected_savings_factor']) < 0.01, (
        f"savings factor {b['fsdp_savings_factor']} should match expected "
        f"{b['expected_savings_factor']}"
    )
    print(f"  ✓ gather/scatter round-trip lossless within float32 epsilon")
    print(f"  ✓ FSDP reduces per-worker memory by {b['fsdp_savings_factor']:.1f}x vs DDP")
    print()

    # ------------------------------------------------------------------
    # Scenario C: training loop with gradient accumulation
    # ------------------------------------------------------------------
    print("═══ Scenario C: training with gradient accumulation ═══")
    c = scenario_c_training_with_accumulation(rng)
    print(f"  n_samples:                {c['n_samples']:,}")
    print(f"  batch_size × accum_steps: {c['batch_size']} × {c['accumulation_steps']} = {c['effective_batch']}")
    print(f"  n_steps:                  {c['n_steps']}")
    print(f"  loss (first step):        {c['loss_first']:.4f}")
    print(f"  loss (last step):         {c['loss_last']:.4f}")
    print(f"  head mean (first 10%):    {c['loss_head_mean']:.4f}")
    print(f"  tail mean (last 10%):     {c['loss_tail_mean']:.4f}")
    print(f"  loss reduction:           {c['loss_reduction']:.4f}")
    assert c['effective_batch'] == c['batch_size'] * c['accumulation_steps']
    assert c['loss_reduction'] > 0.0, "loss must decrease"
    print(f"  ✓ effective batch = batch × accum_steps = {c['effective_batch']}")
    print(f"  ✓ loss decreases by {c['loss_reduction']:.4f} over {c['n_steps']} steps")
    print()

    # ------------------------------------------------------------------
    # Scenario D: FlashAttention-style tiled attention
    # ------------------------------------------------------------------
    print("═══ Scenario D: FlashAttention-style tiled attention ═══")
    d = scenario_d_tiled_attention(rng)
    print(f"  seq_len:        {d['seq_len']}")
    print(f"  d_k = d_v:      {d['d_k']}")
    print(f"  tile size:      {d['tile']}")
    print(f"  naive attention:    {d['naive_ms']:.3f} ms")
    print(f"  tiled attention:    {d['tiled_ms']:.3f} ms")
    print(f"  max abs diff:       {d['max_abs_diff']:.6e}")
    print(f"  mean abs diff:      {d['mean_abs_diff']:.6e}")
    assert d['max_abs_diff'] < 1e-4, (
        f"tiled vs naive mismatch: {d['max_abs_diff']}"
    )
    print(f"  ✓ tiled attention output matches naive within 1e-4 tolerance")
    print()

    print("✓ all invariants pass")
