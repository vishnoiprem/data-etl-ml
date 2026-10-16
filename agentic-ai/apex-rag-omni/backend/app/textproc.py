"""Language-aware text processing for English, Thai, Vietnamese, Chinese, Hindi.

One tokenizer / sentence splitter / language detector shared by indexing,
retrieval, the grounded answerer, the hallucination check and the explainer,
so a word is the same "term" everywhere.

  * Latin (en, vi): lowercase words; Vietnamese diacritics are folded so
    "tiền"/"tien" match; light English stemming.
  * Han (zh): no spaces, so overlapping character bigrams (a standard,
    dictionary-free IR approach).
  * Thai: no spaces, so overlapping character trigrams (dictionary-free).
  * Devanagari (hi): space-separated words; combining vowel signs are kept
    inside the word (Python's \\w would split on them).
  * Digits from any script (๑๒๓ १२३ ٣) become ASCII so numbers can be compared.
"""
from __future__ import annotations

import re
import unicodedata

# ---------- normalisation ----------


def normalize(text: str) -> str:
    """NFKC, lowercase, any-script decimal digits -> ASCII."""
    t = unicodedata.normalize("NFKC", text).lower()
    if t.isascii():
        return t
    return "".join(
        str(unicodedata.decimal(c)) if (not c.isascii() and unicodedata.category(c) == "Nd") else c
        for c in t
    )


def normalize_digits(text: str) -> str:
    return "".join(
        str(unicodedata.decimal(c)) if (not c.isascii() and unicodedata.category(c) == "Nd") else c
        for c in text
    )


def _script(ch: str) -> str:
    o = ord(ch)
    if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0xF900 <= o <= 0xFAFF:
        return "han"
    if 0x0E00 <= o <= 0x0E7F:
        return "thai"
    return "word"


_VI_CHARS = set("ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ")


def detect_lang(text: str) -> str:
    """'th' | 'zh' | 'hi' | 'vi' | 'en' (en = anything else Latin)."""
    t = unicodedata.normalize("NFC", text.lower())
    n = {"th": 0, "zh": 0, "hi": 0, "vi": 0, "latin": 0}
    for c in t:
        o = ord(c)
        if 0x0E00 <= o <= 0x0E7F:
            n["th"] += 1
        elif _script(c) == "han":
            n["zh"] += 1
        elif 0x0900 <= o <= 0x097F:
            n["hi"] += 1
        elif c in _VI_CHARS:
            n["vi"] += 1
        elif c.isalpha():
            n["latin"] += 1
    for k in ("th", "zh", "hi"):
        if n[k] and n[k] >= max(2, 0.25 * sum(n.values())):
            return k
    if n["vi"] >= 2:
        return "vi"
    return "en"


LANG_NAMES = {"en": "English", "th": "Thai", "vi": "Vietnamese", "zh": "Chinese", "hi": "Hindi"}

# ---------- tokenisation ----------

STOP = frozenset(
    # English
    "a an the of to in on for and or is are was were be do does did how what when where which who i my me we our "
    "you your it its this that with at by from as can should will about get s t much many "
    # Vietnamese (after diacritic folding)
    "la va cua cac co cho mot duoc trong khi nhu the nao gi toi ban "
    # Hindi
    "का के की है हैं में से को और या पर एक यह वह कि क्या कैसे मैं मुझे हम आप कितना कितनी "
    # Chinese single chars (bigrams made only of these are dropped)
    "的 了 是 在 和 我 你 吗 么 呢 吧 啊 与 或 及 有 个 这 那".split()
)
_ZH_STOP = frozenset("的了是在和我你吗么呢吧啊与或及有个这那什怎如何")
_TH_STOP_GRAMS = frozenset()  # Thai particles are handled by IDF (n-grams are not dictionary words)


def _fold_latin(w: str) -> str:
    w = w.replace("đ", "d")
    d = unicodedata.normalize("NFD", w)
    if all(unicodedata.category(c) != "Mn" or c in "̛̣̀́̃̉̂̆" for c in d):
        return "".join(c for c in d if unicodedata.category(c) != "Mn")
    return w


def stem(w: str) -> str:
    for suf in ("ations", "ation", "ings", "ing", "ies", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _is_latin_word(w: str) -> bool:
    return all(c.isascii() or unicodedata.name(c, "").startswith("LATIN") or unicodedata.category(c) == "Mn" for c in w)


def tokens(text: str) -> list[str]:
    t = normalize(text)
    out: list[str] = []
    run: list[str] = []
    run_kind = ""

    def flush() -> None:
        nonlocal run, run_kind
        if not run:
            return
        s = "".join(run)
        if run_kind == "han":
            if len(s) == 1:
                if s not in _ZH_STOP:
                    out.append(s)
            else:
                for i in range(len(s) - 1):
                    g = s[i:i + 2]
                    if not (g[0] in _ZH_STOP and g[1] in _ZH_STOP):
                        out.append(g)
        elif run_kind == "thai":
            if len(s) <= 3:
                out.append(s)
            else:
                out.extend(s[i:i + 3] for i in range(len(s) - 2))
        else:
            if _is_latin_word(s):
                s = _fold_latin(s)
                if s not in STOP:
                    out.append(stem(s))
            elif s not in STOP:
                out.append(s)
        run, run_kind = [], ""

    for c in t:
        cat = unicodedata.category(c)
        if cat[0] in "LN" or (cat[0] == "M"):
            k = _script(c) if cat[0] != "M" else (run_kind or "word")
            if run and k != run_kind:
                flush()
            run.append(c)
            run_kind = k
        elif c in "‌‍" and run:  # ZWNJ/ZWJ are part of Indic words
            run.append(c)
        else:
            flush()
    flush()
    return out


# ---------- sentences ----------

_PIECES = re.compile(r"(?<=[.!?])[ \t]+|(?<=[।。！？])|\n+")
_HAS_THAI = re.compile(r"[฀-๿]")


def split_sentences(text: str) -> list[str]:
    """Sentence/passage-sized units for citing.

    Latin: split after . ! ? + space, but not before a lowercase word
    (e.g. 'approx. 5'). Chinese/Hindi: split after 。！？ and the danda ।.
    Thai has no end punctuation, so long runs are split at spaces into clauses.
    """
    raw = [p for p in _PIECES.split(text) if p and p.strip()]
    merged: list[str] = []
    for p in raw:
        p = p.strip()
        if merged and p[0].islower() and merged[-1][-1:] in ".!?":
            merged[-1] = f"{merged[-1]} {p}"
        else:
            merged.append(p)
    out: list[str] = []
    for s in merged:
        if _HAS_THAI.search(s) and len(s) > 80 and " " in s:
            # Thai separates clauses/sentences with spaces. Only split where BOTH
            # neighbours are Thai (never around Latin words or numbers), and keep
            # clauses >= 40 chars so citations are meaningful phrases.
            parts = re.split(r"(?<=[\u0E00-\u0E7F]) (?=[\u0E00-\u0E7F])", s)
            cur = ""
            for part in parts:
                if cur and len(cur) >= 40:
                    out.append(cur)
                    cur = part
                else:
                    cur = f"{cur} {part}".strip()
            if cur:
                out.append(cur)
        else:
            out.append(s)
    return out


SENT_END = ".!?。！？।"
