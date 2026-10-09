"""
slm/dataset.py — Convert PacificFreight usage.jsonl into a (prompt, response)
training set for the SLM.

What this file does
-------------------
Reads the Phase 3 service's `usage.jsonl` (the audit log of every draft)
and produces a HuggingFace Dataset (or a plain list of dicts if HF
isn't installed) of:

  {
    "prompt":    "<system + retrieved context + email>",
    "response":  "<the final draft that Mei sent (after her edits)>",
    "quality":   "thumbs_up" | "thumbs_down" | "unedited",
  }

The signal we use for training:
  - `outcome=ok` rows (draft returned successfully)
  - `thumbs_up` rows are the HIGH-quality signal (Mei accepted the draft)
  - `thumbs_down` rows are filtered OUT (don't want to teach the SLM bad behavior)
  - Unrated `ok` rows are medium-quality (we keep them as a fallback)

Why a separate file
-------------------
The dataset prep is the bottleneck of any fine-tune. A bad dataset =
a bad model. By isolating the prep step in one file with one function
(`build_dataset()`), the lesson can focus on:
  1. WHERE the training data comes from (usage.jsonl, not a hand-curated set)
  2. WHAT filter we apply (thumbs-up only)
  3. HOW the prompt is constructed (mirrors the production prompt)
  4. WHAT format we save (HuggingFace Dataset → parquet)

If we change the filter or the prompt format, this file changes.
The training script (`train.py`) doesn't.

How to run
----------
    # As a CLI
    python3 dataset.py --usage ../phase-2-applications/service/usage.jsonl \\
                       --out data/train.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Prompt construction — mirrors the Phase 3 drafter's system prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are Mei, a customer-service agent at PacificFreight, a Singapore-based "
    "cross-border logistics company. You draft replies to customer emails about "
    "shipments between Singapore and Vietnam. Be concise, professional, and "
    "empathetic. Always reference the shipment ID and the last known status."
)


def build_prompt(email: str, contexts: list[str] | None = None) -> str:
    """Mirror the Phase 3 drafter's prompt construction.

    The Phase 3 service's `/draft` endpoint does:
      system_prompt + "\n\n" + contexts_joined + "\n\n" + email + "\n\nReply:"
    We mirror that here so the SLM is trained on the same distribution it
    will see in production.
    """
    ctx_block = "\n\n---\n\n".join(contexts or []) or "(no retrieved context)"
    return f"{SYSTEM_PROMPT}\n\nContext:\n{ctx_block}\n\nCustomer email:\n{email}\n\nReply:"


# ---------------------------------------------------------------------------
# The dataset builder
# ---------------------------------------------------------------------------
def build_dataset(
    usage_path: Path,
    *,
    min_quality: str = "ok",
    feedback_path: Optional[Path] = None,
) -> list[dict]:
    """Read usage.jsonl + (optionally) a feedback log, return a list of training rows.

    Each row: { "prompt": str, "response": str, "quality": str, "metadata": dict }

    Args:
        usage_path: Path to the Phase 3 service's usage.jsonl
        min_quality: Minimum quality to keep. One of:
            - "ok"            (default — any successful draft)
            - "unedited"      (drafts that were never rated; equivalent to "ok" here)
            - "thumbs_up"     (only drafts that received a 👍 — the high-quality signal)
        feedback_path: Optional path to a feedback log. The Phase 3 service writes
            one entry per `/feedback` call. If provided, we use it to filter rows
            to `thumbs_up` only.
    """
    if not usage_path.exists():
        raise FileNotFoundError(f"usage.jsonl not found at {usage_path}")

    # Load feedback (if available). Format: {"request_id": ..., "rating": "up"|"down", ...}
    feedback: dict[str, str] = {}
    if feedback_path and feedback_path.exists():
        for line in feedback_path.read_text().splitlines():
            try:
                d = json.loads(line)
                rid = d.get("request_id")
                if rid and "rating" in d:
                    feedback[rid] = d["rating"]
            except Exception:
                continue

    rows: list[dict] = []
    seen: set[str] = set()
    for line in usage_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        # Only successful drafts with an email.
        if entry.get("outcome") != "ok":
            continue
        if not entry.get("email"):
            # The usage log may not include the email body (privacy); we
            # reconstruct a placeholder from the shipment_id.
            sid = entry.get("shipment_id", "PF-XXXX")
            email = f"Hi, can you check the status of {sid}? Thanks."
        else:
            email = entry["email"]
        # Reconstruct the draft from the entry (or fall back to a stub).
        draft = entry.get("draft") or (
            f"Hi,\n\nThanks for reaching out about {entry.get('shipment_id', 'your shipment')}. "
            f"Let me look into it.\n\n— PacificFreight CS"
        )
        # Reconstruct contexts (if logged) — else empty.
        contexts = entry.get("contexts") or []
        rid = entry.get("request_id", "")
        # Dedup by request_id.
        if rid in seen:
            continue
        seen.add(rid)
        # Apply quality filter.
        rating = feedback.get(rid)
        if rating == "down":
            continue  # never train on thumbs-down
        quality = "thumbs_up" if rating == "up" else "unedited"
        if min_quality == "thumbs_up" and quality != "thumbs_up":
            continue
        rows.append({
            "prompt": build_prompt(email, contexts),
            "response": draft,
            "quality": quality,
            "metadata": {
                "request_id": rid,
                "shipment_id": entry.get("shipment_id"),
                "model": entry.get("model", "?"),
                "ts": entry.get("ts"),
            },
        })

    return rows


# ---------------------------------------------------------------------------
# Save in HuggingFace format (or plain JSONL if HF isn't installed)
# ---------------------------------------------------------------------------
def save_dataset(rows: list[dict], out_path: Path) -> None:
    """Save the training set. Tries HuggingFace `datasets` first, falls back
    to plain JSONL."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from datasets import Dataset  # type: ignore
        ds = Dataset.from_list(rows)
        # Parquet is the HF native format.
        ds.to_parquet(str(out_path.with_suffix(".parquet")))
        print(f"  saved {len(rows)} rows → {out_path.with_suffix('.parquet')}")
    except ImportError:
        with out_path.open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"  saved {len(rows)} rows → {out_path} (JSONL fallback — install `datasets` for parquet)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Build SLM training dataset from usage.jsonl")
    p.add_argument("--usage", required=True, help="Path to usage.jsonl")
    p.add_argument("--feedback", default=None, help="Path to feedback log (optional)")
    p.add_argument("--out", default="data/train.jsonl", help="Output path")
    p.add_argument("--min-quality", default="ok", choices=["ok", "thumbs_up"],
                   help="Minimum quality to keep (default: ok)")
    args = p.parse_args(argv)

    print(f"Reading {args.usage} ...")
    rows = build_dataset(
        Path(args.usage),
        min_quality=args.min_quality,
        feedback_path=Path(args.feedback) if args.feedback else None,
    )
    print(f"  built {len(rows)} training rows")
    by_quality: dict[str, int] = {}
    for r in rows:
        by_quality[r["quality"]] = by_quality.get(r["quality"], 0) + 1
    print(f"  by quality: {by_quality}")
    print(f"Saving to {args.out} ...")
    save_dataset(rows, Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
