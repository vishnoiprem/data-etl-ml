"""Nvidia-style distributed training: FSDP sharding math.

FSDP (Fully Sharded Data Parallel) splits model parameters, gradients,
and optimizer states across N GPUs. Each GPU holds 1/N of the state.
This toy computes the memory and compute budget for a given model +
GPU count, so you can answer "will 7B params fit on 8x A10G?"
before you start the run.
"""
from __future__ import annotations
from dataclasses import dataclass


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


if __name__ == "__main__":
    # 7B model, bf16, AdamW, on 8x A10G (24 GB each)
    cfg = ModelConfig(n_params_b=7.0, dtype_bytes=2, optimizer="adamw", grad_accum_steps=4, activation_gb=6.0)
    plan = ShardingPlan(n_gpus=8, cfg=cfg, fsdp=True)
    m = plan.per_gpu_memory_gb()
    print(f"FSDP, 7B model, 8 GPUs, AdamW:")
    for k, v in m.items():
        print(f"  {k}: {v:.2f} GB")
    print(f"  fits in 24 GB A10G: {m['static_total_gb'] + m['activations_gb'] < 24}")

    # Same model, DDP (no sharding)
    plan_ddp = ShardingPlan(n_gpus=8, cfg=cfg, fsdp=False)
    m2 = plan_ddp.per_gpu_memory_gb()
    print(f"\nDDP, 7B model, 8 GPUs, AdamW:")
    print(f"  static_total_gb: {m2['static_total_gb']:.2f} GB (vs FSDP {m['static_total_gb']:.2f})")
    print(f"  fits in 24 GB A10G: {m2['static_total_gb'] + m2['activations_gb'] < 24}")
