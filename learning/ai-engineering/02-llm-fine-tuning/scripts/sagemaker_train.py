"""Illustrative production training launcher for SageMaker.

This script is NOT runnable in the demo (no SageMaker access in sandbox).
It shows the shape of a real LoRA fine-tuning job submission using the
SageMaker Python SDK + HuggingFace DLC.

Reference: https://docs.aws.amazon.com/sagemaker/latest/dg/hugging-face.html
"""
from __future__ import annotations

import os
from datetime import datetime


def launch():
    import sagemaker
    from sagemaker.huggingface import HuggingFace

    role = os.environ["SAGEMAKER_ROLE_ARN"]
    bucket = os.environ["TRAINING_BUCKET"]
    train_s3 = f"s3://{bucket}/instruction.jsonl"

    job_name = f"lora-uw-{datetime.utcnow():%Y%m%d-%H%M%S}"

    estimator = HuggingFace(
        entry_point="train.py",                         # your training script
        source_dir="training/",
        role=role,
        instance_type="ml.g5.12xlarge",                 # 4× A10G, 96 GB
        instance_count=1,
        transformers_version="4.41",
        pytorch_version="2.3",
        py_version="py311",
        hyperparameters={
            "model_id": "meta-llama/Meta-Llama-3-8B-Instruct",
            "lora_r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "epochs": 3,
            "lr": 2e-4,
            "batch_size": 4,
            "gradient_accumulation_steps": 4,
            "use_qlora": True,                          # 4-bit base
            "max_seq_length": 2048,
        },
        use_spot_instances=True,
        max_wait=8 * 3600,
        max_run=6 * 3600,
        checkpoint_s3_uri=f"s3://{bucket}/checkpoints/{job_name}/",
        job_name=job_name,
    )
    estimator.fit({"train": train_s3})

    # Register in Model Registry
    model_pkg = estimator.register(
        model_package_group_name="acme-uw-lora",
        approval_status="PendingManualApproval",
        content_types=["application/json"],
        response_types=["application/json"],
        framework="HuggingFace",
        framework_version="4.41",
        description=f"LoRA adapter for UW extraction, job={job_name}",
    )
    print(f"Registered: {model_pkg.model_package_arn}")


if __name__ == "__main__":
    launch()
