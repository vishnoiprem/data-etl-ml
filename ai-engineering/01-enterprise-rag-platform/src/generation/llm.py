"""LLM adapter — Local extractive stub + Bedrock Claude.

The LOCAL backend is intentionally an extractive summarizer rather than a
real generator. It picks the best-matching sentences from the retrieved
chunks. This lets the demo run without a GPU or API keys and still
demonstrates the *plumbing* of grounded answers. Swap in Ollama or a real
small-LLM if you want generation.

The AWS backend uses Bedrock Claude with a strict citation prompt.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from loguru import logger

from src.config import settings


@dataclass
class LLMResponse:
    text: str
    in_tokens: int = 0
    out_tokens: int = 0
    model: str = "unknown"


SYSTEM_PROMPT = """You are AskAcme, a careful enterprise knowledge assistant.

Rules:
1. Answer ONLY based on the provided context chunks. If the context does not contain
   the answer, say "I don't know based on available documents."
2. After every factual claim, cite the chunk(s) that support it using square brackets:
   [chunk_id]. You may cite more than one.
3. Be concise. Prefer a short, direct answer over a long one.
4. Never invent chunk_ids. Only cite the ones in the context block.
5. Never fabricate URLs, names, dates, or numbers."""


def build_user_prompt(question: str, contexts: list[dict]) -> str:
    blocks = []
    for c in contexts:
        blocks.append(
            f"[chunk_id: {c['chunk_id']}]  (source: {c['source']} / {c['title']})\n"
            f"{c['text']}"
        )
    ctx = "\n\n---\n\n".join(blocks)
    return f"""<context>
{ctx}
</context>

<question>{question}</question>

Provide your answer below, with inline [chunk_id] citations."""


class LLM(ABC):
    @abstractmethod
    def generate(self, system: str, user: str, max_tokens: int = 1024, temperature: float = 0.1) -> LLMResponse: ...


class LocalExtractiveLLM(LLM):
    """No-API "LLM" that does extractive summarization with citations.

    Strategy: extract the top-N sentences from the context that best
    overlap with the question's terms, attaching the chunk_id as citation.
    """

    def __init__(self, max_sentences: int = 3):
        self.max_sentences = max_sentences

    @staticmethod
    def _tokens(t: str) -> set[str]:
        return {w.lower() for w in re.findall(r"\b\w+\b", t) if len(w) > 2}

    def generate(self, system: str, user: str, max_tokens: int = 1024, temperature: float = 0.1) -> LLMResponse:
        # Parse user prompt back into question + contexts (simple parser)
        q_match = re.search(r"<question>(.+?)</question>", user, re.DOTALL)
        question = q_match.group(1).strip() if q_match else ""
        ctx_match = re.search(r"<context>(.+?)</context>", user, re.DOTALL)
        ctx_text = ctx_match.group(1) if ctx_match else ""

        # Each context block starts with "[chunk_id: ...]"
        block_re = re.compile(r"\[chunk_id:\s*([^\]]+)\][^\n]*\n(.+?)(?=\n\[chunk_id:|\Z)", re.DOTALL)
        blocks = block_re.findall(ctx_text)
        if not blocks:
            return LLMResponse(
                text="I don't know based on available documents.",
                model="local-extractive",
            )

        q_terms = self._tokens(question)
        if not q_terms:
            return LLMResponse(
                text="I don't know based on available documents.",
                model="local-extractive",
            )

        # Score each sentence in each chunk by term overlap with the question
        candidates = []
        for chunk_id, text in blocks:
            for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
                if len(sent) < 15:
                    continue
                overlap = len(self._tokens(sent) & q_terms)
                if overlap == 0:
                    continue
                candidates.append((overlap / max(len(q_terms), 1), sent.strip(), chunk_id.strip()))

        if not candidates:
            return LLMResponse(
                text="I don't know based on available documents.",
                model="local-extractive",
            )

        candidates.sort(reverse=True)
        top = candidates[: self.max_sentences]
        # Build a readable answer with inline citations
        parts = []
        for _, sent, cid in top:
            sent = sent.rstrip(".") + f" [{cid}]."
            parts.append(sent)
        answer = " ".join(parts)
        return LLMResponse(
            text=answer,
            in_tokens=len(user.split()),
            out_tokens=len(answer.split()),
            model="local-extractive",
        )


class BedrockClaude(LLM):
    """Bedrock Anthropic Claude 3.x via the Messages API."""

    def __init__(self, model_id: str | None = None):
        import boto3
        self.model_id = model_id or settings.BEDROCK_GENERATION_MODEL
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)

    def generate(self, system: str, user: str, max_tokens: int = 1024, temperature: float = 0.1) -> LLMResponse:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        })
        resp = self.client.invoke_model(modelId=self.model_id, body=body)
        payload = json.loads(resp["body"].read())
        text = "".join(b["text"] for b in payload["content"] if b["type"] == "text")
        usage = payload.get("usage", {})
        return LLMResponse(
            text=text,
            in_tokens=usage.get("input_tokens", 0),
            out_tokens=usage.get("output_tokens", 0),
            model=self.model_id,
        )


def get_llm() -> LLM:
    if settings.is_aws:
        return BedrockClaude()
    return LocalExtractiveLLM()
