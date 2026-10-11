"""OpenAI-style Triton kernel optimization: fused RMSNorm.

When PyTorch is too slow and CUDA is too verbose, Triton hits the
middle. This is a Triton-style sketch of a fused RMSNorm kernel that
reads X once, computes the norm, and writes Y once — no intermediate
tensors, no second kernel launch.

Real Triton source compiles via @triton.jit and runs on the GPU; this
file shows the algorithm in NumPy as a readable stand-in, with the
shape and block-size notes that a real Triton kernel would carry.
"""
from __future__ import annotations
import numpy as np


def rmsnorm_naive(x: np.ndarray, weight: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Vanilla RMSNorm: 2 passes over x (one to compute mean, one to normalize)."""
    rms = np.sqrt((x ** 2).mean(axis=-1, keepdims=True) + eps)
    return (x / rms) * weight


def rmsnorm_fused(x: np.ndarray, weight: np.ndarray, eps: float = 1e-6,
                  block_size: int = 1024) -> np.ndarray:
    """Fused RMSNorm: 1 pass over x in a single kernel.

    Real Triton:
        @triton.jit
        def fused_rmsnorm(X, W, Y, eps, BLOCK_SIZE: tl.constexpr):
            row = tl.program_id(0)
            offs = tl.arange(0, BLOCK_SIZE)
            mask = offs < X.shape[1]
            x = tl.load(X + row * X.shape[1] + offs, mask=mask, other=0.0).to(tl.float32)
            w = tl.load(W + offs, mask=mask, other=0.0)
            mean_sq = tl.sum(x * x, axis=0) / X.shape[1]
            rstd = 1.0 / tl.sqrt(mean_sq + eps)
            y = (x * rstd).to(X.dtype.element_ty) * w
            tl.store(Y + row * X.shape[1] + offs, y, mask=mask)
    """
    # Toy: still 2 passes for correctness, but block_size hints at the kernel
    # config. In real Triton, BLOCK_SIZE is autotuned at compile time.
    n_cols = x.shape[-1]
    if n_cols % block_size != 0:
        # pad to multiple of block_size (real impl: handle mask in kernel)
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
    return out[:, :weight.shape[0]]  # trim padding


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    x = rng.standard_normal((4, 4096)).astype(np.float32)
    w = rng.standard_normal((4096,)).astype(np.float32)

    y_naive = rmsnorm_naive(x, w)
    y_fused = rmsnorm_fused(x, w, block_size=1024)
    print(f"max abs diff (naive vs fused): {np.abs(y_naive - y_fused).max():.6f}")
    print(f"output shape: {y_fused.shape}, dtype: {y_fused.dtype}")
    print(f"per-row mean:  {y_fused.mean(axis=-1)}")
    print(f"per-row std:   {y_fused.std(axis=-1)}")
