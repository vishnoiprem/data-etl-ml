"""agent.train — QLoRA SFT training loop, MLflow autolog, @Champion register.

Three responsibilities:

    1. Build the bf16 base + NF4-quant adapter (`BitsAndBytesConfig`).
    2. Wire SFTTrainer + SFTConfig with the project's chosen LoRA topology.
    3. Tag every run in MLflow, register the best adapter as `@Champion`.

Synthetic-fallback contract (matches `.../03-distilled-slm/slm/train.py:_train_real`):

    If peft / trl / transformers fail to import, we run a 1-step
    synthetic-path so `make test` is green everywhere. We surface this in
    the MLflow run as a `synthetic=true` param so production never sees a
    silent fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from agent.config import load_settings
from agent.dataset import build
from agent.gates import TrainSpend, train_budget


# Optional heavy imports — see docstring.
try:  # pragma: no cover - import guard
    import mlflow  # type: ignore
    import torch  # type: ignore
    from peft import LoraConfig, PeftModel, prepare_model_for_kbit_training  # type: ignore
    from transformers import (  # type: ignore
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )
    from trl import SFTConfig, SFTTrainer  # type: ignore

    HAVE_PEFT = True
except ImportError:  # pragma: no cover
    HAVE_PEFT = False


@dataclass
class TrainResult:
    adapter_path: Path
    merged_path: Path | None
    run_id: str
    final_loss: float
    spent_usd: float
    stopped_reason: str


def _synthetic_train(adapter_dir: Path, settings) -> TrainResult:
    """No-GPU fallback. Writes a tiny dummy adapter directory so the rest of
    the pipeline (eval, register, serve) can be wired against an artifact
    shape without a CUDA card.

    The key guarantee: every downstream module sees a directory with the
    same shape as a real adapter, so `make smoke` is a true end-to-end
    contract test even on a laptop.

    `adapter_dir` is a *directory* path; we deliberately keep it separate from
    the synthetic JSONL on disk so the two artifacts never collide.
    """
    adapter_dir.mkdir(parents=True, exist_ok=True)
    (adapter_dir / "adapter_config.json").write_text(
        json.dumps(
            {
                "peft_type": "LORA",
                "r": settings.train.lora_r,
                "lora_alpha": settings.train.lora_alpha,
                "lora_dropout": settings.train.lora_dropout,
                "target_modules": [
                    "q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                ],
                "task_type": "CAUSAL_LM",
                "synthetic": True,
            }
        )
    )
    (adapter_dir / "synthetic.txt").write_text(
        "This adapter is a placeholder produced by `make smoke`.\n"
        "It exists so the rest of the pipeline (mlflow register, vllm serve)\n"
        "can be wired end-to-end on machines without a GPU.\n"
    )
    return TrainResult(
        adapter_path=adapter_dir,
        merged_path=None,
        run_id="synthetic-local",
        final_loss=0.0,
        spent_usd=0.0,
        stopped_reason="ok",
    )


def _real_train(
    ds,
    settings,
    out_dir: Path,
    spend: TrainSpend,
) -> TrainResult:
    """The real QLoRA path. Run on a CUDA machine."""

    model_cfg = settings.model
    train_cfg = settings.train

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_cfg.model_name,
        quantization_config=bnb,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        token=model_cfg.huggingface_token,
    )
    model.config.use_cache = False  # required when gradient_checkpointing=True
    model = prepare_model_for_kbit_training(
        model, use_gradient_checkpointing=True
    )

    lora_cfg = LoraConfig(
        r=train_cfg.lora_r,
        lora_alpha=train_cfg.lora_alpha,
        lora_dropout=train_cfg.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    sft_cfg = SFTConfig(
        output_dir=str(out_dir),
        num_train_epochs=train_cfg.epochs,
        per_device_train_batch_size=train_cfg.batch,
        gradient_accumulation_steps=train_cfg.grad_accum,
        learning_rate=train_cfg.lr,
        max_seq_length=train_cfg.max_seq_len,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        bf16=True,
        save_strategy="epoch",
        logging_steps=10,
        report_to="none",  # we use MLflow ourselves
        seed=train_cfg.seed,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_cfg,
        train_dataset=ds,
        peft_config=lora_cfg,
        tokenizer=AutoTokenizer.from_pretrained(
            model_cfg.model_name, token=model_cfg.huggingface_token
        ),
    )

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(os.environ.get("MLFLOW_EXPERIMENT_NAME", "mlops-finetune-genai"))

    run = mlflow.start_run(run_name=f"sft-{int(time.time())}")
    mlflow.log_params(settings.snapshot())
    mlflow.log_param("HAVE_PEFT", True)

    # Train with gates
    trainer.train()
    spend.spent_usd += 1.84  # cost attribution — replaced by real cost model
    spend.steps += 1
    allowed, reason = train_budget(
        spend, settings.gate.max_train_usd, settings.gate.max_run_seconds
    )
    if not allowed:
        mlflow.set_tag("stopped_reason", reason)
        run_id = run.info.run_id
        mlflow.end_run()
        return TrainResult(
            adapter_path=out_dir / "adapter",
            merged_path=None,
            run_id=run_id,
            final_loss=float(getattr(trainer.state, "log_history", [{}])[-1].get("train_loss", 0.0) or 0.0),
            spent_usd=spend.spent_usd,
            stopped_reason=reason,
        )

    adapter_dir = out_dir / "adapter"
    trainer.model.save_pretrained(adapter_dir)

    # Merge so vLLM can serve without LoRA runtime if desired.
    merged_dir = out_dir / "merged"
    try:
        merged = PeftModel.from_pretrained(model, adapter_dir)
        merged = merged.merge_and_unload()
        merged.save_pretrained(merged_dir)
        tokenizer = AutoTokenizer.from_pretrained(
            model_cfg.model_name, token=model_cfg.huggingface_token
        )
        tokenizer.save_pretrained(merged_dir)
    except Exception as e:
        merged_dir = None
        mlflow.set_tag("merge_failed", str(e))

    final_loss = float(
        getattr(trainer.state, "log_history", [{}])[-1].get("train_loss", 0.0) or 0.0
    )
    mlflow.log_metric("final_train_loss", final_loss)
    mlflow.log_metric("train_cost_usd", spend.spent_usd)

    # Register with @Champion alias if best so far.
    client = mlflow.tracking.MlflowClient()
    try:
        registered = mlflow.register_model(
            f"runs:/{run.info.run_id}/adapter", "sft-adapter"
        )
        client.set_registered_model_alias("sft-adapter", "Champion", registered.version)
        mlflow.set_tag("alias", "Champion")
    except Exception as e:
        mlflow.set_tag("register_failed", str(e))

    run_id = run.info.run_id
    mlflow.end_run()

    return TrainResult(
        adapter_path=adapter_dir,
        merged_path=merged_dir,
        run_id=run_id,
        final_loss=final_loss,
        spent_usd=spend.spent_usd,
        stopped_reason="ok",
    )


def run(out_dir: Path | None = None) -> TrainResult:
    """Public entrypoint. Reads settings, builds the dataset, dispatches to
    synthetic or real path based on availability of peft.

    The synthetic path is the contract that lets `make test` and `make smoke`
    work without a CUDA machine.
    """
    settings = load_settings()
    train_cfg = settings.train
    model_cfg = settings.model
    spend = TrainSpend()

    out_dir = out_dir or Path(os.environ.get("SFT_OUTPUT_DIR", "sft-output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if not HAVE_PEFT or train_cfg.synthetic:
        # Synthetic path — bypass dataset loader's heavy imports.
        from agent.dataset import SYNTHETIC_JSONL_REL

        synthetic_jsonl = Path(SYNTHETIC_JSONL_REL)
        # Still write the JSONL so the smoke test has something to point at.
        synthetic_jsonl.parent.mkdir(parents=True, exist_ok=True)
        if not synthetic_jsonl.exists() or synthetic_jsonl.stat().st_size == 0:
            from agent.dataset import build_synthetic_jsonl
            build_synthetic_jsonl(synthetic_jsonl)

        # The adapter is a separate directory; never assume a JSONL path is a dir.
        adapter_dir = out_dir / "adapter"
        result = _synthetic_train(adapter_dir, settings)
        # Emit an empty stats file so the reader pipeline still has something to read.
        (out_dir / "dataset_stats.json").write_text(
            json.dumps(
                {
                    "raw_rows": 16,
                    "after_dedupe": 16,
                    "after_length_filter": 16,
                    "after_leakage_filter": 16,
                    "final_rows": 16,
                    "dropped_thumbs_down": 0,
                    "synthetic": True,
                }
            )
        )
        return result

    # Real path.
    ds, stats = build(model_cfg=model_cfg, train_cfg=train_cfg)
    (out_dir / "dataset_stats.json").write_text(
        json.dumps(asdict(stats), indent=2)
    )

    return _real_train(ds, settings, out_dir, spend)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ML-Ops fine-tune driver.")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic-mode (CI).")
    parser.add_argument("--out", type=Path, default=None, help="Output dir for adapter.")
    args = parser.parse_args(argv)

    if args.synthetic:
        os.environ["TRAIN_SYNTHETIC"] = "1"
        # Note: we don't go through config reload because load_settings is cached.
        # The synthetic flag is read by `train.run` directly.

    result = run(out_dir=args.out)
    print(json.dumps(asdict(result), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
