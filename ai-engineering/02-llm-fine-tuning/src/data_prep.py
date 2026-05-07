"""Data preparation: convert raw labeled data into instruction-tuning JSONL.

The output is the standard messages-format used by HuggingFace TRL,
SageMaker JumpStart fine-tuning recipes, and Bedrock customization jobs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from loguru import logger


SYSTEM_PROMPT = (
    "You are AcmeUW, an insurance underwriting assistant. "
    "Given a declaration page, extract the structured fields as a JSON object. "
    "Never include the full SSN — only the last four digits."
)


def to_instruction_record(raw: dict) -> dict:
    """Convert one raw-label record into a multi-turn messages record."""
    user = (
        "Extract the structured underwriting fields as JSON from this declaration:\n\n"
        f"{raw['raw_text']}"
    )
    # Real label as the assistant turn
    assistant = json.dumps(raw["extraction"], separators=(",", ":"))
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "policy_type": raw["label"],
    }


def to_classification_record(raw: dict) -> dict:
    """Convert into an `(text, label)` pair for the LoRA-on-classifier demo."""
    return {"text": raw["raw_text"], "label": raw["label"]}


def load_jsonl(path: Path) -> list[dict]:
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_jsonl(records: Iterable[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
            n += 1
    logger.info(f"Wrote {n} records to {path}")
    return n
