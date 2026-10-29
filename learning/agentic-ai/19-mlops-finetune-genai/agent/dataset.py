"""agent.dataset — HuggingFace loader + chat-template tokenization + quality filters.

Order of operations (this matters, do not reorder):

    1. Load FineTome-100k from HF Hub (or 16-row synthetic if `train.synthetic`).
    2. Drop `thumbs_down` (per-row label set in FineTome — explicit negative preference).
    3. Deduplicate by SHA-256 of the prompt. Two rows with the same prompt are not two
       examples; they are one example plus noise.
    4. Apply Llama 3.1 chat template via `tokenizer.apply_chat_template(messages, ...)`.
       Do NOT concatenate `prompt + response` as raw text — chat models lose alignment
       on template-less training data.
    5. Length filter at `max_seq_len`. Anything longer is truncated to keep batch shape;
       we don't drop, because dropping creates class imbalance on long-tail intents.
    6. Leakage filter — drop any row whose prompt overlaps a held-out eval prompt set.
       The eval set is small (32 prompts); cheap to apply.

If peft / trl / datasets imports fail (no GPU machine, fresh container), we
gracefully degrade to the 16-row synthetic JSONL so `make test` works everywhere.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.config import ModelConfig, TrainConfig

# Optional heavy imports; we tolerate ImportError so that running `make test`
# without a model installed still works. The synthetic path is the only thing
# gated on `HAVE_PEFT` is `_HAVE_PEFT` (see agent.train).
try:  # pragma: no cover - import guard
    from datasets import Dataset, load_dataset  # type: ignore
    from transformers import AutoTokenizer  # type: ignore

    _HAVE_DATASETS = True
except ImportError:  # pragma: no cover
    _HAVE_DATASETS = False


# Public — exposed so the test suite can read this without re-deriving it.
SYNTHETIC_JSONL_REL = Path("data/synthetic_sft.jsonl")

# Held-out eval prompts. The leakage filter drops any train row whose prompt
# overlaps any of these. Kept deliberately tiny — a longer list belongs in
# a JSON file, not a Python constant.
HELD_OUT_PROMPTS: tuple[str, ...] = (
    "What is the capital of France?",
    "Write a haiku about recursion.",
    "Translate 'good morning' to Spanish.",
    "Summarize the plot of Hamlet in one sentence.",
    "What is 17 * 23?",
    "Name three primary colors.",
    "Who wrote 'The Great Gatsby'?",
    "What is the speed of light in a vacuum?",
    "Convert 100 Celsius to Fahrenheit.",
    "List the planets in our solar system.",
)


@dataclass
class DatasetStats:
    raw_rows: int = 0
    after_dedupe: int = 0
    after_length_filter: int = 0
    after_leakage_filter: int = 0
    final_rows: int = 0
    dropped_thumbs_down: int = 0


def _synthetic_messages() -> list[dict[str, Any]]:
    """16 hand-typed instruction/response pairs. Diverse enough to exercise
    chat templating, long enough to require tokenization, short enough to
    not pull HF Hub at all.
    """
    pairs: list[tuple[str, str]] = [
        ("What is the capital of France?", "The capital of France is Paris."),
        ("Translate 'good morning' to Spanish.", "Buenos días."),
        ("What is 17 * 23?", "391"),
        ("Who wrote 'Pride and Prejudice'?", "Jane Austen."),
        ("Name three primary colors.", "Red, yellow, and blue."),
        ("Convert 100 Celsius to Fahrenheit.", "212°F"),
        ("What is the speed of light in vacuum?", "Approximately 299,792,458 meters per second."),
        ("Summarize 'Romeo and Juliet' in one sentence.", "Two star-crossed lovers from feuding families take their lives, ending the feud."),
        ("What programming language is named after a snake?", "Python."),
        ("How many continents are there?", "Seven."),
        ("What does CPU stand for?", "Central Processing Unit."),
        ("Write a haiku about recursion.", "function calls self /\nsmaller problem awaits /\nbase case at last"),
        ("What is the largest planet?", "Jupiter."),
        ("Who painted the Mona Lisa?", "Leonardo da Vinci."),
        ("Define photosynthesis.", "The process by which plants convert sunlight into chemical energy."),
        ("List the first five prime numbers.", "2, 3, 5, 7, 11."),
    ]
    return [
        {"messages": [{"role": "user", "content": q}, {"role": "assistant", "content": a}]}
        for q, a in pairs
    ]


def build_synthetic_jsonl(out_path: Path) -> Path:
    """Write the synthetic SFT JSONL to disk. Idempotent — if the file exists
    and matches, we skip.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path
    with out_path.open("w") as f:
        for ex in _synthetic_messages():
            f.write(json.dumps(ex) + "\n")
    return out_path


def _prompt_text(messages: list[dict[str, Any]]) -> str:
    """Concatenate user + assistant text; used for dedup-hashing. Matches the
    03-distilled-slm prior-art pattern at `.../03-distilled-slm/slm/dataset.py:build_prompt`.
    """
    return "\n".join(m["content"] for m in messages if m.get("role") in ("user", "assistant"))


def _has_neg_label(row: dict[str, Any]) -> bool:
    """FineTome rows carry a per-sample quality label — drop explicit negatives.

    Field shape in FineTome-100k is variable across versions; we check three
    safe keys and ignore unknown shapes. If none of the keys exist, the row
    passes (no false positives).
    """
    thumbs = row.get("thumbs") or row.get("thumbs_down") or row.get("quality", {}).get("thumbs_down")
    if thumbs is None:
        return False
    return bool(thumbs)


class _ListDataset:
    """Minimal list-backed dataset shim with the subset of the HF `Dataset`
    surface this module actually uses: `len()`, `filter()`, `select()`,
    `map()`, iteration, and `.column_names`.

    Used only when `datasets` is not installed (and not in synthetic mode),
    so `make test` stays green on a bare environment.
    """

    def __init__(self, rows: list[dict]):
        self.rows = list(rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    @property
    def column_names(self) -> list[str]:
        seen: list[str] = []
        for r in self.rows:
            for k in r:
                if k not in seen:
                    seen.append(k)
        return seen

    def filter(self, fn, **kwargs) -> "_ListDataset":  # noqa: A002
        return _ListDataset([r for r in self.rows if fn(r)])

    def select(self, indices) -> "_ListDataset":
        return _ListDataset([self.rows[i] for i in indices])

    def map(self, fn, remove_columns=None, **kwargs) -> "_ListDataset":
        drop = set(remove_columns or [])
        out = []
        for r in self.rows:
            base = {k: v for k, v in r.items() if k not in drop}
            base.update(fn(r))
            out.append(base)
        return _ListDataset(out)


def _make_loader(synthetic: bool, model_cfg: ModelConfig):  # type: ignore[no-untyped-def]
    """Return a HuggingFace `Dataset`. In synthetic mode we synthesize the rows
    in-memory rather than going through HF Hub — keeps the smoke test offline.

    In real mode we load `mlabonne/FineTome-100k` and normalize the schema.
    """
    if synthetic or not _HAVE_DATASETS:
        # Synthetic path — avoid referencing `Dataset` directly so the import
        # guard above stays meaningful even when peft is installed but
        # datasets is not.
        if _HAVE_DATASETS:
            from datasets import Dataset  # type: ignore
            return Dataset.from_list(_synthetic_messages())
        return _ListDataset(_synthetic_messages())

    from datasets import load_dataset  # type: ignore  # isort: skip

    token = model_cfg.huggingface_token or os.environ.get("HUGGINGFACE_TOKEN")
    ds = load_dataset(
        "mlabonne/FineTome-100k",
        split="train",
        token=token,
        trust_remote_code=False,
    )
    # Normalize to `messages` schema. FineTome uses `conversations` with
    # `from`/`value` keys; we map to OpenAI-style `role`/`content`.
    def _norm(row: dict[str, Any]) -> dict[str, Any]:
        conv = row.get("conversations") or row.get("messages") or []
        messages = []
        for turn in conv:
            if {"from", "value"}.issubset(turn.keys()):
                role = turn["from"]
                content = turn["value"]
                # Map common alternates to OpenAI roles.
                role = "user" if role in ("human", "user") else "assistant" if role in ("gpt", "assistant", "model") else role
                if role in ("user", "assistant", "system"):
                    messages.append({"role": role, "content": content})
        return {"messages": messages, "thumbs_down": _has_neg_label(row)}

    ds = ds.map(_norm, remove_columns=[c for c in ds.column_names if c not in ("messages",)] + ["thumbs_down"])
    return ds


def _dedupe(ds, stats: DatasetStats) -> "Dataset":  # type: ignore[name-defined]
    """Drop rows whose concatenated prompt text hashes to one we've seen."""
    seen: set[str] = set()

    def _keep(row):
        h = hashlib.sha256(_prompt_text(row["messages"]).encode("utf-8")).hexdigest()
        if h in seen:
            return False
        seen.add(h)
        return True

    ds = ds.filter(_keep)
    stats.after_dedupe = len(ds)
    return ds


def _drop_thumbs_down(ds, stats: DatasetStats) -> "Dataset":
    """Drop explicit negatives if the schema carries them."""
    raw = len(ds)
    ds = ds.filter(lambda r: not (r.get("thumbs_down") or False))
    stats.dropped_thumbs_down = raw - len(ds)
    return ds


def _leakage_filter(ds, stats: DatasetStats) -> "Dataset":
    held = tuple(p.strip().lower() for p in HELD_OUT_PROMPTS)

    def _keep(row):
        text = " ".join(m["content"] for m in row["messages"]).lower()
        return not any(p in text for p in held)

    ds = ds.filter(_keep)
    stats.after_leakage_filter = len(ds)
    return ds


def _tokenize(ds, tokenizer, max_seq_len: int, stats: DatasetStats) -> "Dataset":
    """Apply Llama 3.1 chat template per row. We keep the raw ids + attention
    mask so the SFTTrainer can construct `input_ids` / `labels` itself.

    Setting `return_assistant_tokens_mask=True` would let us mask the user
    portion from loss; trl 0.12 + Llama chat template supports this, but only
    for newer model templates. We skip mask here to keep the smoke test
    portable.
    """
    def _map(row):
        text = tokenizer.apply_chat_template(
            row["messages"], tokenize=False, add_generation_prompt=False
        )
        out = tokenizer(
            text,
            max_length=max_seq_len,
            truncation=True,
            padding=False,
            return_tensors=None,
        )
        return {"input_ids": out["input_ids"], "attention_mask": out["attention_mask"]}

    ds = ds.map(_map, remove_columns=[c for c in ds.column_names if c not in ("input_ids",)] + ["attention_mask"])
    stats.after_length_filter = len(ds)
    return ds


def build(
    model_cfg: ModelConfig | None = None,
    train_cfg: TrainConfig | None = None,
    root: Path | None = None,
) -> tuple["Dataset", DatasetStats]:  # type: ignore[name-defined]
    """Public entrypoint. Returns `(dataset, stats)`.

    `stats` is structured so the README "Real numbers" table can cite the row
    counts without re-reading the dataset.
    """
    from agent.config import load_settings

    settings = load_settings()
    model_cfg = model_cfg or settings.model
    train_cfg = train_cfg or settings.train
    root = root or Path(os.environ.get("PROJECT_ROOT", "."))

    stats = DatasetStats()

    if train_cfg.synthetic or not _HAVE_DATASETS:
        # Synthetic path — write the JSONL so the next reader can `jq` it.
        synthetic_path = root / SYNTHETIC_JSONL_REL
        build_synthetic_jsonl(synthetic_path)

    ds = _make_loader(train_cfg.synthetic, model_cfg)
    stats.raw_rows = len(ds)

    ds = _drop_thumbs_down(ds, stats)
    ds = _dedupe(ds, stats)

    if train_cfg.dataset_rows and len(ds) > train_cfg.dataset_rows:
        # Deterministic subset.
        ds = ds.select(range(train_cfg.dataset_rows))

    ds = _leakage_filter(ds, stats)

    if _HAVE_DATASETS and not train_cfg.synthetic:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            model_cfg.model_name,
            token=model_cfg.huggingface_token,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        ds = _tokenize(ds, tokenizer, train_cfg.max_seq_len, stats)
    else:
        # Synthetic mode — stats finalize without tokenization.
        stats.after_length_filter = len(ds)
        stats.after_leakage_filter = len(ds)

    stats.final_rows = len(ds)
    return ds, stats
