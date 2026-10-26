"""
bedrock_lambda.py
=================

AWS Lambda handler that calls AWS Bedrock (Cohere Command) to summarize
and classify a manufacturing defect description.

The function accepts:

    {"defect_description": "free text from the operator"}

and returns:

    {
        "summary":  "one-sentence summary",
        "category": "mechanical" | "electrical" | "pneumatic" | "other",
        "severity": "low" | "medium" | "high" | "critical"
    }

The implementation is a single-file Lambda (handler at the bottom of the
file) plus a `__main__` block so you can test the prompt logic locally
without AWS credentials by passing a `--fake-bedrock` flag.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import ClientError

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

# These defaults match the production env-var layout from L43.
DEFAULT_MODEL_ID = "cohere.command-text-v14"
DEFAULT_REGION = "us-east-1"
DEFAULT_MAX_INPUT_CHARS = 4_000

ALLOWED_CATEGORIES = ("mechanical", "electrical", "pneumatic", "other")
ALLOWED_SEVERITIES = ("low", "medium", "high", "critical")

# The system prompt and the user-prompt template are kept in a
# sibling .txt file (code/prompt_template.txt) so non-coders can edit
# them without touching Python. We read it lazily on the first call.
_PROMPT_TEMPLATE: str | None = None


def _load_prompt_template() -> str:
    """Load the prompt template from the sibling ``prompt_template.txt``.

    The Lambda deployment package always contains both files in the same
    directory, so we resolve the path relative to *this* file's location.
    """
    global _PROMPT_TEMPLATE
    if _PROMPT_TEMPLATE is not None:
        return _PROMPT_TEMPLATE

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(here, "..", "prompt_template.txt"))
    with open(path, "r", encoding="utf-8") as fh:
        _PROMPT_TEMPLATE = fh.read()
    return _PROMPT_TEMPLATE


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

class ValidationError(ValueError):
    """Raised when the incoming event is malformed."""


def _extract_defect_text(event: dict[str, Any]) -> str:
    """Pull the operator's defect description out of the API Gateway event.

    Accepts both:
      {"defect_description": "..."}
      {"body": "{\"defect_description\":\"...\"}"}      (REST API proxy)
    """
    if "defect_description" in event and isinstance(event["defect_description"], str):
        return event["defect_description"]

    if "body" in event and event["body"] is not None:
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        except json.JSONDecodeError as exc:
            raise ValidationError(f"body is not valid JSON: {exc}") from exc
        if not isinstance(body, dict) or "defect_description" not in body:
            raise ValidationError("body JSON must contain 'defect_description'")
        if not isinstance(body["defect_description"], str):
            raise ValidationError("'defect_description' must be a string")
        return body["defect_description"]

    raise ValidationError(
        "event must include either 'defect_description' or a 'body' field"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Bedrock client
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BedrockConfig:
    model_id: str
    region: str
    max_input_chars: int

    @classmethod
    def from_env(cls) -> "BedrockConfig":
        return cls(
            model_id=os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID),
            region=os.environ.get("BEDROCK_REGION", DEFAULT_REGION),
            max_input_chars=int(
                os.environ.get("MAX_INPUT_CHARS", str(DEFAULT_MAX_INPUT_CHARS))
            ),
        )


def _get_bedrock_client(region: str):
    """Return a cached Bedrock Runtime client.

    The Lambda execution environment is reused across invocations, so we
    keep the client on a module-level dict to avoid the per-call handshake.
    """
    global _bedrock_client_cache
    try:
        return _bedrock_client_cache[region]
    except KeyError:
        pass
    client = boto3.client("bedrock-runtime", region_name=region)
    _bedrock_client_cache[region] = client
    return client


_bedrock_client_cache: dict[str, Any] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Prompt construction
# ─────────────────────────────────────────────────────────────────────────────

def _build_prompt(defect_text: str) -> str:
    """Render the prompt from the template and the operator's text.

    The template (code/prompt_template.txt) contains two ``{slot}``
    placeholders: ``{system}`` is filled with the system instructions
    already inline in the template, and ``{user}`` is filled with the
    operator's defect description.
    """
    template = _load_prompt_template()
    if "{user}" not in template:
        # Defensive: prevents silent prompt-rendering bugs.
        raise RuntimeError("prompt_template.txt must contain a '{user}' placeholder")
    return template.replace("{user}", defect_text.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Bedrock invocation
# ─────────────────────────────────────────────────────────────────────────────

def _call_bedrock(
    prompt: str,
    cfg: BedrockConfig,
    client=None,
) -> dict[str, Any]:
    """Call Bedrock and return the parsed JSON dict from the model.

    The body shape below is specific to **Cohere Command text models**.
    Other families (Anthropic Claude, Meta Llama) use different body
    schemas. If you switch ``BEDROCK_MODEL_ID`` to a non-Cohere model,
    you must also rewrite this body and the response parser.
    """
    client = client or _get_bedrock_client(cfg.region)

    body = {
        "prompt": prompt,
        "max_tokens": 256,
        "temperature": 0.2,
        "p": 0.9,
        "k": 0,
        "stop_sequences": [],
        "return_likelihoods": "NONE",
    }

    try:
        t0 = time.perf_counter()
        response = client.invoke_model(
            modelId=cfg.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body).encode("utf-8"),
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
    except ClientError as exc:
        LOG.exception("bedrock invoke_model failed")
        raise

    raw = response["body"].read()
    payload = json.loads(raw)

    # Cohere Command text models return {"generations": [{"text": "..."}]}
    # Some Cohere chat models return a different shape; this handler is
    # written for the text model variant.
    try:
        text = payload["generations"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"unexpected Bedrock payload shape: {payload!r}") from exc

    LOG.info(
        "bedrock.invoke_model: model=%s latency_ms=%s input_chars=%s output_chars=%s",
        cfg.model_id,
        latency_ms,
        len(prompt),
        len(text),
    )

    return _parse_model_json(text)


# ─────────────────────────────────────────────────────────────────────────────
# Response parsing & normalization
# ─────────────────────────────────────────────────────────────────────────────

# Cohere sometimes wraps the JSON in ```json ... ``` fences; strip them.
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _parse_model_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from the model's free-text response.

    We try three strategies, in order:
      1. The whole response is JSON.
      2. The response contains a JSON object (regex search).
      3. A very tolerant trailing-brace scan.
    """
    text = _FENCE_RE.sub("", text).strip()

    # Strategy 1: parse whole text.
    try:
        return _coerce_dict(json.loads(text))
    except json.JSONDecodeError:
        pass

    # Strategy 2: find first {...} block.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return _coerce_dict(json.loads(match.group(0)))
        except json.JSONDecodeError:
            pass

    # Strategy 3: tolerant trailing-brace scan.
    end = text.rfind("}")
    start = text.find("{")
    if 0 <= start < end:
        try:
            return _coerce_dict(json.loads(text[start : end + 1]))
        except json.JSONDecodeError:
            pass

    raise RuntimeError(f"could not parse model output as JSON: {text!r}")


def _coerce_dict(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise RuntimeError(f"model output is not a JSON object: {obj!r}")
    return obj


def _normalize_category(raw: Any) -> str:
    """Map whatever the model produced onto the allowed enum."""
    if not isinstance(raw, str):
        return "other"
    candidate = raw.strip().lower()
    if candidate in ALLOWED_CATEGORIES:
        return candidate
    # Be tolerant of synonyms Cohere sometimes uses.
    synonyms = {
        "mech": "mechanical",
        "mechanical_failure": "mechanical",
        "elec": "electrical",
        "electrical_failure": "electrical",
        "wiring": "electrical",
        "pneu": "pneumatic",
        "air": "pneumatic",
        "hydraulic": "pneumatic",
    }
    return synonyms.get(candidate, "other")


def _normalize_severity(raw: Any) -> str:
    if not isinstance(raw, str):
        return "medium"
    candidate = raw.strip().lower()
    if candidate in ALLOWED_SEVERITIES:
        return candidate
    synonyms = {
        "1": "low",
        "2": "low",
        "3": "medium",
        "4": "high",
        "5": "critical",
        "minor": "low",
        "major": "high",
        "urgent": "high",
        "blocker": "critical",
    }
    return synonyms.get(candidate, "medium")


def _normalize_output(parsed: dict[str, Any]) -> dict[str, str]:
    """Return the final 3-field dict the API contract requires."""
    summary = parsed.get("summary") or parsed.get("Summary") or ""
    if not isinstance(summary, str) or not summary.strip():
        summary = "Defect reported but no summary generated."

    return {
        "summary": summary.strip(),
        "category": _normalize_category(parsed.get("category")),
        "severity": _normalize_severity(parsed.get("severity")),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Lambda entry point
# ─────────────────────────────────────────────────────────────────────────────

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """API Gateway proxy integration entry point.

    Returns a dict that API Gateway serializes to a 200 OK response.
    Validation errors are translated to 400; Bedrock failures to 502.
    """
    cfg = BedrockConfig.from_env()
    try:
        defect_text = _extract_defect_text(event)
    except ValidationError as exc:
        LOG.warning("validation error: %s", exc)
        return _response(400, {"error": str(exc)})

    # Truncate to bound token costs and prevent accidental megabyte inputs.
    if len(defect_text) > cfg.max_input_chars:
        defect_text = defect_text[: cfg.max_input_chars]

    if not defect_text.strip():
        return _response(400, {"error": "defect_description is empty"})

    try:
        prompt = _build_prompt(defect_text)
        parsed = _call_bedrock(prompt, cfg)
    except (ClientError, RuntimeError) as exc:
        LOG.exception("bedrock call failed")
        return _response(502, {"error": "model invocation failed", "detail": str(exc)})

    return _response(200, _normalize_output(parsed))


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Build an API Gateway proxy response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Local entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Run the handler end-to-end against a fake Bedrock client.

    Usage:
        python bedrock_lambda.py
        python bedrock_lambda.py path/to/event.json
        python bedrock_lambda.py --real       # attempt a real Bedrock call
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "event_path",
        nargs="?",
        default=None,
        help="Path to a JSON file containing the event payload.",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use the real boto3 Bedrock client (requires AWS credentials).",
    )
    parser.add_argument(
        "--defect",
        default=(
            "Line 3 stamping press #2 is producing parts with a 2 mm burr "
            "on the trailing edge; coolant pressure dropped to 12 psi at 14:08."
        ),
        help="Inline defect description to use if no event file is given.",
    )
    args = parser.parse_args()

    if args.event_path:
        with open(args.event_path, "r", encoding="utf-8") as fh:
            event = json.load(fh)
    else:
        event = {"defect_description": args.defect}

    if not args.real:
        # Inject a stub Bedrock client so the rest of the pipeline runs.
        class _StubBody:
            def __init__(self):
                self._buf = __import__("io").BytesIO(
                    json.dumps(
                        {
                            "generations": [
                                {
                                    "text": json.dumps(
                                        {
                                            "summary": (
                                                "Stamping press #2 producing 2 mm burr on flange; "
                                                "coolant pressure dropped to 12 psi."
                                            ),
                                            "category": "mechanical",
                                            "severity": "high",
                                        }
                                    )
                                }
                            ]
                        }
                    ).encode("utf-8")
                )

            def read(self):
                return self._buf.read()

        class _StubClient:
            def invoke_model(self, **_kwargs):
                return {"body": _StubBody()}

        # Monkey-patch the factory so the handler uses our stub.
        globals()["_get_bedrock_client"] = lambda region: _StubClient()

    result = lambda_handler(event, context=None)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["statusCode"] == 200 else 1)
