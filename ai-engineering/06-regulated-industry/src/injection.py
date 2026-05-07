"""Prompt-injection detection.

Categories of injection we try to catch:
  1. Instruction override  ("ignore previous instructions")
  2. Role manipulation     ("pretend you are an admin")
  3. Data exfiltration     ("print the system prompt", "list customers")
  4. Encoded payloads      (base64 instruction blocks, unicode tags)
  5. Tool abuse            ("use the email tool to send to attacker@…")

Production stack: Bedrock Guardrails + a fine-tuned classifier (e.g., Lakera
PromptGuard, Meta PromptGuard 86M). This module is the deterministic last
line of defense; never rely on it alone.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


SUSPICIOUS_PATTERNS: list[tuple[str, str]] = [
    ("instruction_override", r"\b(ignore|disregard|override|forget)\s+(all|the|previous|above|earlier)\s+(instructions?|prompts?|rules?|constraints?)\b"),
    ("role_manipulation",    r"\b(pretend|act as|roleplay|you are now|behave as)\b"),
    ("system_prompt_leak",   r"\b(system\s+prompt|reveal\s+your\s+(rules|instructions)|print\s+your\s+prompt)\b"),
    ("jailbreak_keyword",    r"\b(DAN|jailbreak|developer\s+mode|do\s+anything\s+now)\b"),
    ("data_exfil",           r"\b(list|export|email|send|print)\s+(all\s+)?(customers?|users?|emails?|passwords?|secrets?)\b"),
    ("tool_abuse",           r"\b(call|invoke|use)\s+(the\s+)?(email|http|exec|shell|file)\s+tool\b"),
    ("encoded_payload",      r"(base64|b64|rot13)[\s:=]"),
    ("unicode_tag_block",    r"[\U000E0020-\U000E007F]"),  # tag-block characters
]

_COMPILED = [(name, re.compile(p, re.IGNORECASE)) for name, p in SUSPICIOUS_PATTERNS]


@dataclass
class InjectionVerdict:
    blocked: bool
    risk_score: float       # 0..1
    reasons: list[str]


def detect(text: str) -> InjectionVerdict:
    reasons: list[str] = []
    for name, rx in _COMPILED:
        if rx.search(text):
            reasons.append(name)
    # Risk score: 0.4 per category up to 1.0; block above 0.5
    risk = min(1.0, 0.4 * len(reasons))
    return InjectionVerdict(blocked=risk >= 0.4, risk_score=risk, reasons=reasons)
