"""
Writer - Outline-first article generation
==========================================
Two-stage: outline (cheap) → write (expensive).

The outline gives the article structure. Each section is then written with
context (research + previous sections), keeping prompts short and quality high.
"""

import time
import json
import logging
from openai import OpenAI

logger = logging.getLogger("content-generator.writer")

OUTLINE_MODEL = "gpt-4o-mini"
WRITE_MODEL = "gpt-4o"
PRICING = {
    "gpt-4o":      {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def _generate_outline(topic: str, keyword: str, research: dict, target_words: int, tone: str, openai_api_key: str) -> tuple[list[str], float]:
    """Generate the article outline. Returns (list of section titles, cost_usd)."""
    client = OpenAI(api_key=openai_api_key)
    related_q = research.get("related_questions", [])
    n_sections = max(6, min(12, target_words // 150))

    sys = (
        f"You are a content strategist. Plan a {target_words}-word blog article. "
        f"Output JSON: {{\"sections\": [{{\"title\": str, \"target_words\": int}}]}}\n"
        f"Rules:\n"
        f"- {n_sections} sections (H2 level), 1 of which is a FAQ section at the end\n"
        f"- Include the keyword '{keyword}' in the first H2 title\n"
        f"- Tone: {tone}\n"
        f"- Total target_words across sections should sum to ~{target_words}"
    )
    user = (
        f"Topic: {topic}\nKeyword: {keyword}\n\n"
        f"Competitor dominant angle: {research.get('dominant_angle','')}\n"
        f"Our unique angle: {research.get('unique_angle','')}\n\n"
        f"Related questions to answer in FAQ:\n" + "\n".join(f"- {q}" for q in related_q) + "\n\n"
        f"Generate outline:"
    )
    resp = client.chat.completions.create(
        model=OUTLINE_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    cost = (resp.usage.prompt_tokens / 1e6) * PRICING[OUTLINE_MODEL]["input"] + \
           (resp.usage.completion_tokens / 1e6) * PRICING[OUTLINE_MODEL]["output"]
    parsed = json.loads(resp.choices[0].message.content)
    sections = parsed.get("sections", [])
    titles = [s.get("title", "") for s in sections if s.get("title")]
    return titles, cost


def _write_section(topic: str, keyword: str, section_title: str, target_words: int, prev_sections: list[str], research: dict, tone: str, openai_api_key: str) -> tuple[str, float]:
    """Write one section. Returns (markdown, cost_usd)."""
    client = OpenAI(api_key=openai_api_key)
    serp_excerpt = "\n".join(
        f"- {r['title']}: {r['snippet']}" for r in research.get("results", [])[:5]
    )
    prev_context = "\n\n".join(prev_sections[-3:])  # last 3 sections for continuity

    sys = (
        f"You are an expert blog writer. Write a {target_words}-word section in markdown.\n"
        f"Rules:\n"
        f"- Don't repeat content from previous sections\n"
        f"- Use the keyword '{keyword}' naturally 1-2 times\n"
        f"- Include at least 1 specific example or number from the research\n"
        f"- End with a 1-sentence transition to the next section\n"
        f"- Tone: {tone}\n"
        f"- Use ## for the section header (already given)"
    )
    user = (
        f"Article topic: {topic}\n"
        f"Section title: ## {section_title}\n"
        f"Target length: {target_words} words\n\n"
        f"Research to draw from:\n{serp_excerpt}\n\n"
        f"Previous sections (last 3):\n{prev_context[:1500]}\n\n"
        f"Write this section:"
    )
    resp = client.chat.completions.create(
        model=WRITE_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.7,
    )
    cost = (resp.usage.prompt_tokens / 1e6) * PRICING[WRITE_MODEL]["input"] + \
           (resp.usage.completion_tokens / 1e6) * PRICING[WRITE_MODEL]["output"]
    text = resp.choices[0].message.content.strip()
    return text, cost


def write_article(topic: str, keyword: str, research: dict, target_words: int, tone: str, openai_api_key: str) -> tuple[list[str], str, float]:
    """Generate the article. Returns (outline, body_markdown, cost_usd)."""
    start = time.time()
    outline, outline_cost = _generate_outline(topic, keyword, research, target_words, tone, openai_api_key)
    total_cost = outline_cost

    if not outline:
        return [], "", total_cost

    # Compute per-section word targets
    n = len(outline)
    per_section = max(150, target_words // n)

    sections_written: list[str] = []
    body_parts = [f"# {topic}\n"]
    for sec in outline:
        sec_text, sec_cost = _write_section(
            topic=topic, keyword=keyword, section_title=sec,
            target_words=per_section, prev_sections=sections_written,
            research=research, tone=tone, openai_api_key=openai_api_key,
        )
        total_cost += sec_cost
        sections_written.append(sec_text)
        body_parts.append(sec_text + "\n")

    # Wrap up with a FAQ section if not in outline
    if not any("FAQ" in s or "frequently asked" in s.lower() for s in outline):
        # use the last section as a quasi-FAQ if room
        pass

    body = "\n".join(body_parts)
    elapsed = time.time() - start
    logger.info(f"wrote {len(body.split())} words in {elapsed:.1f}s cost=${total_cost:.4f}")
    return outline, body, total_cost