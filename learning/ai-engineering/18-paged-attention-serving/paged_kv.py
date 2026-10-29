"""
Toy PagedAttention-style KV cache.

Treats GPU memory as a pool of fixed-size blocks. Each request owns a
list of block IDs (not a contiguous buffer). This is the core idea
behind vLLM's PagedAttention.

The real vLLM does this with CUDA kernels, fused attention, and a
continuous-batching scheduler. This toy captures the indirection.
"""
from __future__ import annotations
import torch
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Block:
    """A fixed-size block of K/V cache."""
    block_id: int
    k: Optional[torch.Tensor] = None      # shape: (block_size, n_heads, head_dim)
    v: Optional[torch.Tensor] = None
    fill: int = 0                         # how many tokens in this block


class PagedKVCache:
    def __init__(self, n_blocks: int, n_heads: int, head_dim: int, block_size: int = 16):
        self.block_size = block_size
        self.n_heads = n_heads
        self.head_dim = head_dim
        self.blocks: list[Block] = [Block(block_id=i) for i in range(n_blocks)]
        self.free: deque[int] = deque(range(n_blocks - 1, -1, -1))
        self.tables: dict[int, list[int]] = {}   # request_id -> [block_id, ...]

    def alloc(self, request_id: int, n_tokens: int) -> list[int]:
        needed = (n_tokens + self.block_size - 1) // self.block_size
        if len(self.free) < needed:
            raise MemoryError(f"need {needed} blocks, have {len(self.free)}")
        ids = [self.free.pop() for _ in range(needed)]
        # Lazy-init the K/V tensors on first alloc
        for bid in ids:
            b = self.blocks[bid]
            b.k = torch.empty(self.block_size, self.n_heads, self.head_dim, device="cuda")
            b.v = torch.empty(self.block_size, self.n_heads, self.head_dim, device="cuda")
        self.tables[request_id] = ids
        return ids

    def append(self, request_id: int, k: torch.Tensor, v: torch.Tensor) -> None:
        """Append one token's K/V. Allocs a new block if the current one is full."""
        ids = self.tables[request_id]
        if not ids or self.blocks[ids[-1]].fill >= self.block_size:
            new_id = self.alloc(request_id, self.block_size)
            ids.append(new_id[0])
        bid = ids[-1]
        b = self.blocks[bid]
        b.k[b.fill] = k
        b.v[b.fill] = v
        b.fill += 1

    def free(self, request_id: int) -> None:
        for bid in self.tables.pop(request_id, []):
            self.blocks[bid].k = None
            self.blocks[bid].v = None
            self.blocks[bid].fill = 0
            self.free.append(bid)

    def gather(self, request_id: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Reassemble the K/V for a request from its scattered blocks."""
        ids = self.tables[request_id]
        ks = [self.blocks[i].k[: self.blocks[i].fill] for i in ids if self.blocks[i].k is not None]
        vs = [self.blocks[i].v[: self.blocks[i].fill] for i in ids if self.blocks[i].v is not None]
        return torch.cat(ks, dim=0), torch.cat(vs, dim=0)

    def stats(self) -> dict:
        used = sum(1 for b in self.blocks if b.fill > 0)
        return {
            "total_blocks": len(self.blocks),
            "used_blocks": used,
            "free_blocks": len(self.free),
            "active_requests": len(self.tables),
        }


# --- Toy comparison: contiguous vs paged ------------------------------------

def contiguous_budget(n_layers: int, n_heads: int, head_dim: int, max_seq: int, dtype_bytes: int = 2) -> int:
    """Memory cost of a contiguous KV cache: max_seq * 2 (K+V) * n_layers * n_heads * head_dim * dtype_bytes."""
    return max_seq * 2 * n_layers * n_heads * head_dim * dtype_bytes


def paged_budget(n_blocks: int, block_size: int, n_layers: int, n_heads: int, head_dim: int, dtype_bytes: int = 2) -> int:
    """Memory cost of paged: same total, but allocated on demand in block_size chunks."""
    return n_blocks * block_size * 2 * n_layers * n_heads * head_dim * dtype_bytes


if __name__ == "__main__":
    # Realistic LLM-serving numbers
    n_layers, n_heads, head_dim, max_seq = 32, 32, 128, 4096
    dtype_bytes = 2  # fp16

    contig = contiguous_budget(n_layers, n_heads, head_dim, max_seq, dtype_bytes)
    paged = paged_budget(n_blocks=2048, block_size=16, n_layers=n_layers, n_heads=n_heads, head_dim=head_dim, dtype_bytes=dtype_bytes)
    print(f"contiguous per-request KV: {contig / 1e6:.1f} MB")
    print(f"paged total KV budget:    {paged / 1e6:.1f} MB  (serves {(paged/contig):.0f}x more concurrent requests at same memory)")
