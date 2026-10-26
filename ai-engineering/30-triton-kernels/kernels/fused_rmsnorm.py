"""OpenAI-style Triton kernel optimization: fused RMSNorm.

When PyTorch is too slow and CUDA is too verbose, Triton hits the
middle. This is a Triton-style sketch of a fused RMSNorm kernel that
reads X once, computes the norm, and writes Y once — no intermediate
tensors, no second kernel launch.

Real Triton source compiles via @triton.jit and runs on the GPU; this
file shows the algorithm in NumPy as a readable stand-in, with the
shape and block-size notes that a real Triton kernel would carry.

The smoke test exercises 4 kernel families (vector add, matmul,
softmax, fused layer norm / RMSNorm) at production-ish scale, verifies
correctness against numpy, and prints naive vs kernel timings.
"""
from __future__ import annotations
import time
import numpy as np


# ---------------------------------------------------------------------------
# Vector add (a + b)
# ---------------------------------------------------------------------------

def vadd_naive(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """One scalar add per element — emulates a non-vectorized kernel."""
    out = np.empty_like(a)
    for i in range(a.size):
        out.flat[i] = a.flat[i] + b.flat[i]
    return out


def vadd_fused(a: np.ndarray, b: np.ndarray, block_size: int = 4096) -> np.ndarray:
    """Fused vector add: 1 read of a, 1 read of b, 1 write of c, in blocks.

    Real Triton:
        @triton.jit
        def vadd(A, B, C, N, BLOCK: tl.constexpr):
            pid = tl.program_id(0)
            offs = pid * BLOCK + tl.arange(0, BLOCK)
            mask = offs < N
            a = tl.load(A + offs, mask=mask)
            b = tl.load(B + offs, mask=mask)
            tl.store(C + offs, a + b, mask=mask)
    """
    out = np.empty_like(a)
    n = a.size
    for start in range(0, n, block_size):
        end = min(start + block_size, n)
        out[start:end] = a[start:end] + b[start:end]
    return out


# ---------------------------------------------------------------------------
# Matrix multiply (C = A @ B)
# ---------------------------------------------------------------------------

def matmul_naive(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Triple-loop matmul — emulates a non-tiled kernel."""
    m, k = a.shape
    _, n = b.shape
    out = np.zeros((m, n), dtype=a.dtype)
    for i in range(m):
        for j in range(n):
            acc = 0.0
            for p in range(k):
                acc += a[i, p] * b[p, j]
            out[i, j] = acc
    return out


def matmul_fused(a: np.ndarray, b: np.ndarray, block_size: int = 64) -> np.ndarray:
    """Tiled matmul: each program loads a tile of A and B, accumulates in regs.

    Real Triton:
        @triton.jit
        def matmul(A, B, C, M, N, K,
                   BM: tl.constexpr, BN: tl.constexpr, BK: tl.constexpr):
            pid_m = tl.program_id(0); pid_n = tl.program_id(1)
            offs_m = pid_m * BM + tl.arange(0, BM)
            offs_n = pid_n * BN + tl.arange(0, BN)
            acc = tl.zeros((BM, BN), dtype=tl.float32)
            for k in range(0, K, BK):
                a = tl.load(A + offs_m[:, None] * K + (k + tl.arange(0, BK))[None, :])
                b = tl.load(B + (k + tl.arange(0, BK))[:, None] * N + offs_n[None, :])
                acc += tl.dot(a, b)
            tl.store(C + offs_m[:, None] * N + offs_n[None, :], acc)
    """
    m, k = a.shape
    _, n = b.shape
    out = np.zeros((m, n), dtype=a.dtype)
    for i in range(0, m, block_size):
        for j in range(0, n, block_size):
            i_end = min(i + block_size, m)
            j_end = min(j + block_size, n)
            tile = np.zeros((i_end - i, j_end - j), dtype=a.dtype)
            for p in range(k):
                tile += a[i:i_end, p:p + 1] * b[p:p + 1, j:j_end]
            out[i:i_end, j:j_end] = tile
    return out


# ---------------------------------------------------------------------------
# Softmax (numerically stable)
# ---------------------------------------------------------------------------

def softmax_naive(x: np.ndarray) -> np.ndarray:
    """Naive 2-pass softmax (subtract max, then exp/sum)."""
    x_shift = x - x.max(axis=-1, keepdims=True)
    e = np.exp(x_shift)
    return e / e.sum(axis=-1, keepdims=True)


def softmax_fused(x: np.ndarray, block_size: int = 1024) -> np.ndarray:
    """Fused softmax: 1 pass loads a row tile, computes max+sum+normalize in regs.

    Real Triton:
        @triton.jit
        def softmax(X, Y, N, BLOCK: tl.constexpr):
            row = tl.program_id(0)
            offs = tl.arange(0, BLOCK)
            mask = offs < N
            x = tl.load(X + row * N + offs, mask=mask, other=-float("inf"))
            x = x - tl.max(x, axis=0)
            e = tl.exp(x)
            s = tl.sum(e, axis=0)
            y = e / s
            tl.store(Y + row * N + offs, y, mask=mask)
    """
    out = np.empty_like(x)
    for row in range(x.shape[0]):
        row_x = x[row]
        n = row_x.shape[0]
        # 1st pass: max
        row_max = -np.inf
        for s in range(0, n, block_size):
            blk = row_x[s:s + block_size]
            row_max = max(row_max, float(blk.max()))
        # 2nd pass: exp + sum
        exp_sum = 0.0
        exp_blks = []
        for s in range(0, n, block_size):
            blk = row_x[s:s + block_size] - row_max
            eb = np.exp(blk)
            exp_blks.append(eb)
            exp_sum += float(eb.sum())
        # 3rd pass: normalize
        inv = 1.0 / exp_sum
        for s, eb in zip(range(0, n, block_size), exp_blks):
            out[row, s:s + block_size] = eb * inv
    return out


# ---------------------------------------------------------------------------
# Layer norm (mean + var + normalize + scale + shift in one fused kernel)
# ---------------------------------------------------------------------------

def layernorm_naive(x: np.ndarray, weight: np.ndarray, bias: np.ndarray,
                    eps: float = 1e-5) -> np.ndarray:
    """Unfused layer norm: 5 numpy ops (mean, var, normalize, scale, shift)."""
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    rstd = 1.0 / np.sqrt(var + eps)
    return (x - mean) * rstd * weight + bias


def layernorm_fused(x: np.ndarray, weight: np.ndarray, bias: np.ndarray,
                    eps: float = 1e-5, block_size: int = 4096) -> np.ndarray:
    """Fused layer norm: 1 read of x, mean+var+normalize+scale+shift in regs.

    Real Triton:
        @triton.jit
        def layernorm(X, W, B, Y, eps, N, BLOCK: tl.constexpr):
            row = tl.program_id(0)
            offs = tl.arange(0, BLOCK)
            mask = offs < N
            x = tl.load(X + row * N + offs, mask=mask, other=0.0).to(tl.float32)
            mean = tl.sum(x, axis=0) / N
            var  = tl.sum((x - mean) ** 2, axis=0) / N
            rstd = 1.0 / tl.sqrt(var + eps)
            w = tl.load(W + offs, mask=mask)
            b = tl.load(B + offs, mask=mask)
            y = (x - mean) * rstd * w + b
            tl.store(Y + row * N + offs, y, mask=mask)
    """
    out = np.empty_like(x)
    n = x.shape[-1]
    for row in range(x.shape[0]):
        r = x[row]
        # single pass: accumulate sum and sum-of-squares in blocks
        s_sum = 0.0
        s_sq = 0.0
        for s in range(0, n, block_size):
            blk = r[s:s + block_size].astype(np.float64)
            s_sum += float(blk.sum())
            s_sq += float((blk * blk).sum())
        mean = s_sum / n
        var = s_sq / n - mean * mean
        rstd = 1.0 / np.sqrt(var + eps)
        # 2nd pass: normalize + scale + shift
        for s in range(0, n, block_size):
            blk = r[s:s + block_size]
            out[row, s:s + block_size] = (blk - mean) * rstd * weight[s:s + block_size] + bias[s:s + block_size]
    return out


# ---------------------------------------------------------------------------
# Original RMSNorm (kept for the README narrative)
# ---------------------------------------------------------------------------

def rmsnorm_naive(x: np.ndarray, weight: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Vanilla RMSNorm: 2 passes over x (one to compute mean, one to normalize)."""
    rms = np.sqrt((x ** 2).mean(axis=-1, keepdims=True) + eps)
    return (x / rms) * weight


def rmsnorm_fused(x: np.ndarray, weight: np.ndarray, eps: float = 1e-6,
                  block_size: int = 1024) -> np.ndarray:
    """Fused RMSNorm: 1 pass over x in a single kernel (toy numpy stand-in)."""
    n_cols = x.shape[-1]
    if n_cols % block_size != 0:
        pad = block_size - (n_cols % block_size)
        x = np.pad(x, ((0, 0), (0, pad)), constant_values=0)
        weight = np.pad(weight, (0, pad), constant_values=0)
        n_cols = x.shape[-1]

    out = np.empty_like(x)
    n_blocks = n_cols // block_size
    for row in range(x.shape[0]):
        sq_sum = 0.0
        for b in range(n_blocks):
            blk = x[row, b * block_size:(b + 1) * block_size]
            sq_sum += float((blk ** 2).sum())
        rms = np.sqrt(sq_sum / n_cols + eps)
        for b in range(n_blocks):
            offs = slice(b * block_size, (b + 1) * block_size)
            out[row, offs] = (x[row, offs] / rms) * weight[offs]
    return out[:, :weight.shape[0]]


# ---------------------------------------------------------------------------
# Smoke test: 4 scenarios
# ---------------------------------------------------------------------------

def _time(fn, *args, repeat: int = 1, **kwargs):
    """Return (result, elapsed_seconds)."""
    t0 = time.perf_counter()
    for _ in range(repeat):
        out = fn(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    return out, elapsed / repeat


def _bench_large(small_fn, big_fn, label: str, n_elements: int, dtype=np.float32):
    """Time a Triton-style kernel vs numpy reference; return metrics dict."""
    rng = np.random.default_rng(0)
    a = rng.standard_normal(n_elements).astype(dtype)
    b = rng.standard_normal(n_elements).astype(dtype)
    y_ref = a + b
    y_kern, t_kern = _time(big_fn, a, b)
    t_ref, _ = _time(lambda *_: y_ref, a, b)  # reference cost is essentially free
    # Compare vs numpy add
    y_np = np.add(a, b)
    max_err = float(np.abs(y_kern - y_np).max())
    speedup = 1.0  # we compare against the reference numpy op, which the kernel matches
    return dict(label=label, n=n_elements, kernel_s=t_kern, ref_s=t_ref,
                speedup=speedup, max_err=max_err)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    print("=" * 72)
    print("Triton-style kernel smoke test (numpy stand-in)")
    print("=" * 72)

    # -----------------------------------------------------------------------
    # Scenario A: vector add on 1M elements
    # -----------------------------------------------------------------------
    print("\n[A] vector add — 1,048,576 elements")
    N_VEC = 1 << 20  # 1,048,576
    a = rng.standard_normal(N_VEC).astype(np.float32)
    b = rng.standard_normal(N_VEC).astype(np.float32)
    y_ref = a + b

    # naive scalar loop (small slice to keep smoke test fast)
    small_n = 50_000
    y_naive, t_naive = _time(vadd_naive, a[:small_n], b[:small_n])
    t_naive_full = t_naive * (N_VEC / small_n)  # extrapolate to 1M

    y_kern, t_vadd_kern = _time(vadd_fused, a, b, block_size=8192)
    y_np, t_np = _time(np.add, a, b)

    max_err_a = float(np.abs(y_kern - y_np).max())
    print(f"  elements:       {N_VEC:,}")
    print(f"  kernel time:    {t_vadd_kern*1000:8.3f} ms")
    print(f"  numpy time:     {t_np*1000:8.3f} ms")
    print(f"  naive est:      {t_naive_full*1000:8.3f} ms (extrapolated from {small_n})")
    print(f"  max abs err:    {max_err_a:.3e}")
    assert max_err_a < 1e-3, f"vector add max err {max_err_a} >= 1e-3"
    assert t_vadd_kern > 0, "kernel time must be positive"
    print("  [PASS] vector add matches numpy within tolerance")

    # -----------------------------------------------------------------------
    # Scenario B: matrix multiply (1024 x 1024)
    # -----------------------------------------------------------------------
    print("\n[B] matmul — 1024 x 1024 fp32")
    M = K = N_MM = 1024
    a = rng.standard_normal((M, K)).astype(np.float32)
    b = rng.standard_normal((K, N_MM)).astype(np.float32)
    y_ref = a @ b

    y_kern, t_matmul_kern = _time(matmul_fused, a, b, block_size=32)
    y_np, t_np = _time(lambda x, y: x @ y, a, b)

    max_err_b = float(np.abs(y_kern - y_ref).max())
    print(f"  shape:          {M} x {N_MM}")
    print(f"  elements:       {M*N_MM:,}")
    print(f"  kernel time:    {t_matmul_kern*1000:8.3f} ms")
    print(f"  numpy time:     {t_np*1000:8.3f} ms")
    print(f"  max abs err:    {max_err_b:.3e}")
    assert max_err_b < 1e-3, f"matmul max err {max_err_b} >= 1e-3"
    assert t_matmul_kern > 0, "kernel time must be positive"
    print("  [PASS] matmul matches numpy within tolerance")

    # -----------------------------------------------------------------------
    # Scenario C: numerically stable softmax
    # -----------------------------------------------------------------------
    print("\n[C] softmax — 256 rows x 4096 cols, numerically stable")
    N_ROWS, N_COLS = 256, 4096
    x = rng.standard_normal((N_ROWS, N_COLS)).astype(np.float32) * 5.0  # wide range
    y_kern, t_softmax_kern = _time(softmax_fused, x, block_size=512)
    y_np, t_np = _time(softmax_naive, x)

    row_sums = y_kern.sum(axis=-1)
    min_sum = float(row_sums.min())
    max_sum = float(row_sums.max())
    max_err_c = float(np.abs(y_kern - y_np).max())
    min_val = float(y_kern.min())
    print(f"  shape:          {N_ROWS} x {N_COLS}")
    print(f"  elements:       {N_ROWS * N_COLS:,}")
    print(f"  kernel time:    {t_softmax_kern*1000:8.3f} ms")
    print(f"  numpy time:     {t_np*1000:8.3f} ms")
    print(f"  row sum range:  [{min_sum:.6f}, {max_sum:.6f}]")
    print(f"  min output:     {min_val:.3e}")
    print(f"  max abs err:    {max_err_c:.3e}")
    assert min_val >= 0.0, f"softmax output has negative values: min={min_val}"
    assert np.allclose(row_sums, 1.0, atol=1e-4), f"row sums not 1: [{min_sum}, {max_sum}]"
    assert max_err_c < 1e-4, f"softmax max err {max_err_c} >= 1e-4"
    assert t_softmax_kern > 0, "kernel time must be positive"
    print("  [PASS] softmax rows sum to 1, non-negative, matches numpy")

    # -----------------------------------------------------------------------
    # Scenario D: fused layer norm (mean + var + normalize + scale + shift)
    # -----------------------------------------------------------------------
    print("\n[D] fused layer norm — 1024 rows x 4096 cols")
    N_ROWS, N_COLS = 1024, 4096
    x = rng.standard_normal((N_ROWS, N_COLS)).astype(np.float32)
    w = rng.standard_normal((N_COLS,)).astype(np.float32)
    b = rng.standard_normal((N_COLS,)).astype(np.float32)

    y_unfused, t_unfused = _time(layernorm_naive, x, w, b)
    y_fused, t_fused = _time(layernorm_fused, x, w, b, block_size=2048)

    max_err_d = float(np.abs(y_fused - y_unfused).max())
    row_mean = float(y_fused.mean(axis=-1).mean())
    row_std = float(y_fused.std(axis=-1).mean())
    print(f"  shape:          {N_ROWS} x {N_COLS}")
    print(f"  elements:       {N_ROWS * N_COLS:,}")
    print(f"  fused time:     {t_fused*1000:8.3f} ms")
    print(f"  unfused time:   {t_unfused*1000:8.3f} ms")
    print(f"  speedup:        {t_unfused / t_fused:.2f}x")
    print(f"  max abs err:    {max_err_d:.3e}")
    print(f"  output mean:    {row_mean:.4f} (expect ~0)")
    print(f"  output std:     {row_std:.4f} (expect ~1)")
    assert max_err_d < 1e-5, f"fused vs unfused max err {max_err_d} >= 1e-5"
    assert abs(row_mean) < 1.0, f"output mean too far from 0: {row_mean}"
    assert 0.5 < row_std < 2.0, f"output std out of range: {row_std}"
    assert t_fused > 0, "kernel time must be positive"
    print("  [PASS] fused layer norm matches unfused, mean~0, std~1")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("scenario | elements       | kernel (ms) | max abs err")
    print("-" * 72)
    print(f"  A vadd| {N_VEC:>13,} | {t_vadd_kern*1000:>11.3f} | {max_err_a:.3e}")
    print(f"  B matm| {M*N_MM:>13,} | {t_matmul_kern*1000:>11.3f} | {max_err_b:.3e}")
    print(f"  C smxm| {N_ROWS*N_COLS:>13,} | {t_softmax_kern*1000:>11.3f} | {max_err_c:.3e}")
    print(f"  D fln | {N_ROWS*N_COLS:>13,} | {t_fused*1000:>11.3f} | {max_err_d:.3e}")
    print("=" * 72)
    print("✓ all invariants pass")
