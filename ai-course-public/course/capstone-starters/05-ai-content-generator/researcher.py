"""
Researcher - SERP research + competitive angle
===============================================
Uses Tavily to fetch top results for a keyword, then GPT-4o-mini to identify
the unique angle the new article should take.
"""

import os
import time
import json
import logging
import httpx
from openai import OpenAI

logger = logging.getLogger("content-generator.researcher")

TAVILY_ENDPOINT = "https://api.tavily.com/search"
RESEARCH_MODEL = "gpt-4o-mini"
PRICING = {"gpt-4o-mini": {"input": 0.15, "output": 0.60}}

MAX_SERP_RESULTS = 10
MAX_CONTENT_CHARS = 3000


def tavily_search(query: str, api_key: str, max_results: int = MAX_SERP_RESULTS) -> list[dict]:
    """Call Tavily search. Returns [{url, title, content, score}]."""
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": False,
        "include_raw_content": False,
    }
    try:
        r = httpx.post(TAVILY_ENDPOINT, json=payload, timeout=20.0)
        r.raise_for_status()
        data = r.json()
        return data.get("results", [])
    except httpx.HTTPError as e:
        logger.warning(f"tavily error for '{query}': {e}")
        return []


def research_serp(keyword: str, tavily_api_key: str, openai_api_key: str) -> tuple[dict, float]:
    """Run SERP research. Returns ({results, angle, related_questions}, cost_usd)."""
    start = time.time()

    # Step 1: Tavily search
    results = tavily_search(keyword, tavily_api_key)
    if not results:
        logger.warning(f"no SERP results for '{keyword}', falling back to general knowledge")

    # Step 2: GPT-4o-mini identifies the unique angle
    client = OpenAI(api_key=openai_api_key)
    serp_excerpt = "\n\n".join(
        f"[{i+1}] {r.get('title','')} — {r.get('url','')}\n{(r.get('content','') or '')[:600]}"
        for i, r in enumerate(results[:8])
    )

    sys = (
        "You are a content strategist. Given a target keyword and the top SERP results, "
        "identify:\n"
        "1. The dominant angle competitors take (what everyone says)\n"
        "2. The unique angle the new article should take (what's missing or wrong)\n"
        "3. 5 related questions people ask about this topic (for an FAQ section)\n"
        "Return JSON: {\"dominant_angle\": str, \"unique_angle\": str, \"related_questions\": [str]}"
    )
    user = (
        f"Target keyword: {keyword}\n\n"
        f"Top SERP results:\n{serp_excerpt}\n\n"
        f"Strategy:"
    )
    resp = client.chat.completions.create(
        model=RESEARCH_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    usage = resp.usage
    cost = (usage.prompt_tokens / 1e6) * PRICING[RESEARCH_MODEL]["input"] + \
           (usage.completion_tokens / 1e6) * PRICING[RESEARCH_MODEL]["output"]
    strategy = json.loads(resp.choices[0].message.content)

    elapsed = time.time() - start
    logger.info(f"research done in {elapsed:.1f}s cost=${cost:.4f}")
    return {
        "keyword": keyword,
        "results": [{"title": r.get("title",""), "url": r.get("url",""), "snippet": (r.get("content","") or "")[:300]} for r in results],
        "dominant_angle": strategy.get("dominant_angle", ""),
        "unique_angle": strategy.get("unique_angle", ""),
        "related_questions": strategy.get("related_questions", []),
    }, cost