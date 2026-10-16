"""Input/output sanitization and PII redaction.

Three jobs:
  * sanitize_query   - normalise untrusted user text, flag prompt injection.
  * redact_pii       - mask personal data before it reaches logs / audit.
  * sanitize_output  - strip markup/scripts from text we send back to a UI.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Zero-width + bidi override/isolate chars: used to hide instructions or
# spoof text direction. Cc/Cf categories are stripped except \n and \t, and
# ZWNJ/ZWJ (U+200C/D) which are legitimate inside Hindi words.
_STRIP_CATS = {"Cc", "Cf", "Co", "Cs"}
_KEEP = "\n\t\u200c\u200d"

_INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions?|prompts?|rules?)",
    r"disregard (?:(?:all|any|the|your) )*(previous|prior|above|earlier)? ?(instructions?|prompts?|rules?)",
    r"forget (everything|all|your) (above|previous|instructions?|rules?)",
    r"(reveal|show|print|repeat|leak) (me )?(your |the )?(system|hidden|initial) (prompt|instructions?|message)",
    r"you are now (?!able)",
    r"act as (?:a |an )?(?:dan|jailbroken|unrestricted|developer mode)",
    r"\bjailbreak\b",
    r"override (your |the )?(safety|guardrails?|rules?|polic(?:y|ies))",
    r"</?(system|assistant|im_start|im_end)>|<\|im_(start|end)\|>",
    r"\bBEGIN (SYSTEM|PROMPT)\b",
    # Thai
    r"(ไม่ต้องสนใจ|เพิกเฉย|ละเว้น|ลืม)(คำสั่ง|กฎ|ข้อกำหนด)(ก่อนหน้า|ข้างต้น|ทั้งหมด)",
    r"(เปิดเผย|แสดง|บอก).{0,12}(system prompt|พรอมต์ระบบ|คำสั่งระบบ)",
    # Vietnamese
    r"(bỏ qua|phớt lờ|quên)\s+(tất cả\s+|mọi\s+)?(các\s+)?(hướng dẫn|chỉ dẫn|lệnh|quy tắc)\s+(trước|ở trên|phía trên)",
    r"(tiết lộ|hiển thị|in ra).{0,15}(system prompt|lời nhắc hệ thống)",
    # Chinese
    r"(忽略|无视|忘记|忘掉)(之前|以上|先前|上述|所有)(的)?(所有)?(指令|指示|提示|规则|说明)",
    r"(泄露|显示|输出|告诉我).{0,6}(系统提示|系统指令|system prompt)",
    # Hindi
    r"(पिछले|पहले के|ऊपर के|सभी)\s*(निर्देशों|निर्देश|आदेशों|नियमों)\s*(को)?\s*(अनदेखा|नज़रअंदाज़|भूल)",
    r"(सिस्टम प्रॉम्प्ट|system prompt).{0,12}(बताओ|दिखाओ|प्रकट)",
]
# Patterns are NFKC-normalised like the text they match (e.g. Thai sara am "ำ" decomposes).
_INJECTION_RE = re.compile(
    unicodedata.normalize("NFKC", "|".join(f"(?:{p})" for p in _INJECTION_PATTERNS)), re.I)


@dataclass
class SanitizedQuery:
    text: str
    flags: list[str] = field(default_factory=list)

    @property
    def injection(self) -> bool:
        return "prompt_injection" in self.flags


def sanitize_query(raw: str, max_chars: int = 2000) -> SanitizedQuery:
    flags: list[str] = []
    t = unicodedata.normalize("NFKC", raw)
    cleaned = "".join(
        ch for ch in t
        if ch in _KEEP or unicodedata.category(ch) not in _STRIP_CATS
    )
    if cleaned != t:
        flags.append("control_chars_removed")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()[:max_chars]
    if _INJECTION_RE.search(cleaned):
        flags.append("prompt_injection")
    return SanitizedQuery(cleaned, flags)


# ---------- PII ----------

def _luhn(digits: str) -> bool:
    s, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        s += d
        alt = not alt
    return s % 10 == 0


def _thai_id_ok(d: str) -> bool:
    return len(d) == 13 and (11 - sum(int(d[i]) * (13 - i) for i in range(12)) % 11) % 10 == int(d[12])


_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_SECRET = re.compile(r"\b(?:sk|pk|ghp|xox[bap]|AKIA)[-_A-Za-z0-9]{16,}\b")
_LONG_NUM = re.compile(r"(?<![\w])(?:\d[ -]?){12,19}(?![\w])")
_PHONE = re.compile(r"(?<![\w])(?:\+\d{1,3}[ -]?)?(?:\(?\d{2,4}\)?[ -]?)\d{3,4}[ -]?\d{3,4}(?![\w])")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Mask emails, secrets, card numbers (Luhn), Thai national IDs, SSNs, phones."""
    found: list[str] = []

    def sub(kind: str, tag: str):
        def f(m: re.Match) -> str:
            found.append(kind)
            return tag
        return f

    out = _EMAIL.sub(sub("email", "[EMAIL]"), text)
    out = _SECRET.sub(sub("secret", "[SECRET]"), out)

    def num(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn(digits):
            found.append("card")
            return "[CARD]"
        if len(digits) == 13 and _thai_id_ok(digits):
            found.append("national_id")
            return "[NATIONAL_ID]"
        return m.group(0)

    out = _LONG_NUM.sub(num, out)
    out = _SSN.sub(sub("ssn", "[SSN]"), out)

    def phone(m: re.Match) -> str:
        if len(re.sub(r"\D", "", m.group(0))) >= 9:
            found.append("phone")
            return "[PHONE]"
        return m.group(0)

    out = _PHONE.sub(phone, out)
    return out, sorted(set(found))


# ---------- output ----------

_SCRIPT_BLOCK = re.compile(r"<\s*(script|style|iframe|object|embed)\b.*?<\s*/\s*\1\s*>", re.I | re.S)
_TAG = re.compile(r"</?[a-zA-Z!][^>]*>")
_JS_URL = re.compile(r"\b(?:javascript|vbscript|data)\s*:", re.I)


def sanitize_output(text: str) -> str:
    """Strip HTML/script and dangerous URL schemes from text sent to a client.

    React already escapes text nodes; this is defence in depth for any
    consumer (email, markdown renderer, another UI) that doesn't.
    """
    t = _SCRIPT_BLOCK.sub("", text)
    t = _TAG.sub("", t)
    t = _JS_URL.sub("", t)
    return "".join(ch for ch in t if ch in "\n\t" or unicodedata.category(ch) not in _STRIP_CATS)
