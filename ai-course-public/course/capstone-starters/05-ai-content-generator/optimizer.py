"""
Optimizer - SEO scoring + meta generation
==========================================
- score_seo: 0-100 score with breakdown (keyword, structure, length, readability)
- generate_meta: GPT-4o-mini generates title + description

Scoring rubric (out of 100):
  Keyword in title/H1/first 100 words: 25 pts
  Keyword density (1-2% target): 15 pts
  Word count meets target: 15 pts
  H2/H3 hierarchy (>= 4 H2s, no skipped): 25 pts
  Readability (Flesch 60-70): 10 pts
  Paragraph length (< 100 words avg): 10 pts
"""

import re
import json
import time
import logging
from openai import OpenAI

logger = logging.getLogger("content-generator.optimizer")

META_MODEL = "gpt-4o-mini"
PRICING = {"gpt-4o-mini": {"input": 0.15, "output": 0.60}}


def _count_syllables(word: str) -> int:
    """Approximate syllable count for Flesch reading ease."""
    word = word.lower().strip(".,!?;:")
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for c in word:
        is_vowel = c in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _flesch_reading_ease(text: str) -> float:
    """Compute Flesch reading ease score. Higher = easier. 60-70 = plain English."""
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    words = re.findall(r"\b\w+\b", text)
    n_words = max(1, len(words))
    n_syllables = sum(_count_syllables(w) for w in words)
    score = 206.835 - 1.015 * (n_words / sentences) - 84.6 * (n_syllables / n_words)
    return round(score, 1)


def _parse_headings(md: str) -> tuple[list[str], list[str]]:
    """Return (h1_list, h2_list)."""
    h1 = re.findall(r"^# (.+)$", md, re.MULTILINE)
    h2 = re.findall(r"^## (.+)$", md, re.MULTILINE)
    return h1, h2


def _paragraph_lengths(md: str) -> list[int]:
    """Word count per paragraph (paragraphs separated by blank lines)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", md) if p.strip()]
    return [len(p.split()) for p in paras]


def score_seo(body: str, keyword: str, target_words: int = 1500) -> dict:
    """Compute an SEO score. Returns a dict with overall score and breakdown."""
    breakdown = {}
    text_lower = body.lower()
    kw_lower = keyword.lower()

    # 1. Keyword placement (25 pts)
    has_h1 = bool(re.search(r"^# .*$", body, re.MULTILINE))
    h1_list, h2_list = _parse_headings(body)
    first_h1 = h1_list[0] if h1_list else ""
    first_100_words = " ".join(body.split()[:100])

    kw_in_title = kw_lower in first_h1.lower()
    kw_in_first_100 = kw_lower in first_100_words.lower()
    kw_in_h2 = any(kw_lower in h.lower() for h in h2_list)

    placement_score = 0
    placement_score += 10 if kw_in_title else 0
    placement_score += 10 if kw_in_first_100 else 0
    placement_score += 5 if kw_in_h2 else 0
    breakdown["keyword_placement"] = {"score": placement_score, "max": 25, "in_title": kw_in_title, "in_first_100": kw_in_first_100, "in_h2": kw_in_h2}

    # 2. Keyword density (15 pts)
    words = re.findall(r"\b\w+\b", body.lower())
    n_words = max(1, len(words))
    kw_count = sum(1 for w in words if kw_lower in w)
    density = kw_count / n_words * 100
    if 0.5 <= density <= 2.5:
        density_score = 15
    elif 0.1 <= density < 0.5 or 2.5 < density <= 4.0:
        density_score = 8
    else:
        density_score = 0
    breakdown["keyword_density"] = {"score": density_score, "max": 15, "density_pct": round(density, 2)}

    # 3. Word count (15 pts)
    actual_words = len(body.split())
    if actual_words >= target_words * 0.9:
        length_score = 15
    elif actual_words >= target_words * 0.75:
        length_score = 10
    elif actual_words >= target_words * 0.5:
        length_score = 5
    else:
        length_score = 0
    breakdown["word_count"] = {"score": length_score, "max": 15, "actual": actual_words, "target": target_words}

    # 4. Heading structure (25 pts)
    n_h2 = len(h2_list)
    structure_score = 0
    structure_score += 15 if n_h2 >= 4 else (10 if n_h2 >= 2 else 0)
    structure_score += 10 if h1_list else 0
    breakdown["heading_structure"] = {"score": structure_score, "max": 25, "n_h1": len(h1_list), "n_h2": n_h2}

    # 5. Readability (10 pts)
    flesch = _flesch_reading_ease(body)
    if 60 <= flesch <= 80:
        readability_score = 10
    elif 50 <= flesch < 60 or 80 < flesch <= 90:
        readability_score = 6
    else:
        readability_score = 3
    breakdown["readability"] = {"score": readability_score, "max": 10, "flesch": flesch}

    # 6. Paragraph length (10 pts)
    paras = _paragraph_lengths(body)
    avg_para = sum(paras) / max(1, len(paras))
    if avg_para <= 80:
        para_score = 10
    elif avg_para <= 120:
        para_score = 6
    else:
        para_score = 3
    breakdown["paragraph_length"] = {"score": para_score, "max": 10, "avg_words": round(avg_para, 1)}

    overall = sum(b["score"] for b in breakdown.values())
    return {"overall_score": overall, "max_score": 100, "breakdown": breakdown}


def generate_meta(topic: str, keyword: str, body: str, openai_api_key: str) -> tuple[str, str, float]:
    """Generate SEO meta title + description. Returns (title, description, cost_usd)."""
    client = OpenAI(api_key=openai_api_key)

    body_excerpt = body[:2500]

    sys = (
        "You are an SEO copywriter. Given an article topic, target keyword, and excerpt, "
        "write:\n"
        "- meta_title: 50-60 characters, includes the keyword, compelling\n"
        "- meta_description: 150-160 characters, includes the keyword, summarizes value\n"
        "Return JSON: {\"meta_title\": str, \"meta_description\": str}"
    )
    user = (
        f"Topic: {topic}\nKeyword: {keyword}\n\n"
        f"Article excerpt:\n{body_excerpt}\n\n"
        f"Generate meta:"
    )
    resp = client.chat.completions.create(
        model=META_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0.6,
    )
    cost = (resp.usage.prompt_tokens / 1e6) * PRICING[META_MODEL]["input"] + \
           (resp.usage.completion_tokens / 1e6) * PRICING[META_MODEL]["output"]
    parsed = json.loads(resp.choices[0].message.content)
    return parsed["meta_title"], parsed["meta_description"], cost