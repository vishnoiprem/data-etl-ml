"""PII / PHI detection and redaction.

Production note: this is a regex-based implementation that catches common
patterns. In a real regulated deployment you'd layer:
  1. AWS Comprehend Detect PII Entities (managed, multilingual)
  2. Bedrock Guardrails sensitive-information filter
  3. This regex layer as a belt-and-braces backstop

Layered defenses are non-negotiable: a single classifier WILL miss things.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass(frozen=True)
class PIIRule:
    name: str
    pattern: Pattern[str]
    replacement: str
    category: str   # "pii" | "phi" | "credential"


def _compile(s: str) -> Pattern[str]:
    return re.compile(s, re.IGNORECASE)


PII_RULES: list[PIIRule] = [
    # --- credentials / financial -------------------------------------------
    PIIRule("ssn_full", _compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "[REDACTED:SSN]", "pii"),
    PIIRule("credit_card", _compile(r"\b(?:\d[ -]?){13,16}\b"), "[REDACTED:CC]", "credential"),
    PIIRule("aws_access_key", _compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED:AWS_KEY]", "credential"),
    PIIRule("aws_secret", _compile(r"\b[A-Za-z0-9/+=]{40}\b"), "[REDACTED:AWS_SECRET]", "credential"),
    PIIRule("api_key_generic", _compile(r"\b(sk|pk)-[A-Za-z0-9]{20,}\b"), "[REDACTED:API_KEY]", "credential"),

    # --- personal -----------------------------------------------------------
    PIIRule("email", _compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED:EMAIL]", "pii"),
    PIIRule("phone_us", _compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED:PHONE]", "pii"),
    PIIRule("dob_iso", _compile(r"\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b"), "[REDACTED:DOB]", "pii"),

    # --- protected health (PHI) --------------------------------------------
    PIIRule("mrn", _compile(r"\bMRN[:\s]*\d{6,10}\b"), "[REDACTED:MRN]", "phi"),
    PIIRule("icd10", _compile(r"\b[A-TV-Z]\d{2}(?:\.\d{1,4})?\b"), "[REDACTED:ICD10]", "phi"),
]


@dataclass
class RedactionReport:
    text: str                          # post-redaction text
    findings: list[dict]               # detected entities

    @property
    def has_pii(self) -> bool:
        return bool(self.findings)


def redact(text: str, rules: list[PIIRule] | None = None) -> RedactionReport:
    """Apply all rules in order and return the redacted text + findings."""
    rules = rules or PII_RULES
    findings: list[dict] = []
    out = text
    for rule in rules:
        for m in rule.pattern.finditer(out):
            findings.append({
                "rule": rule.name,
                "category": rule.category,
                "span": [m.start(), m.end()],
                "match_preview": m.group()[:4] + "…",   # keep audit value but not full PII
            })
        out = rule.pattern.sub(rule.replacement, out)
    return RedactionReport(text=out, findings=findings)
