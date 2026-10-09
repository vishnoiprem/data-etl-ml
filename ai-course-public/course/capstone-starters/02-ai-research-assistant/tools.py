"""
Tools for the Research Agent
============================
- tavily_search: web search via Tavily API
- scrape_url: fetch + extract main text from a URL
- (PDF, file loaders can be added in week 4)
"""

import os
import time
import logging
import httpx
import trafilatura

logger = logging.getLogger("research-assistant.tools")

TAVILY_ENDPOINT = "https://api.tavily.com/search"
SCRAPE_TIMEOUT = 15.0
SCRAPE_MAX_BYTES = 5 * 1024 * 1024  # 5MB
SCRAPE_USER_AGENT = "AIResearchAssistant/1.0 (+https://example.com)"


def tavily_search(query: str, max_results: int = 3) -> list[dict]:
    """Call Tavily search. Returns [{url, title, content, score}]."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not set")
        return []
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",     # use "advanced" for deeper (more credits)
        "include_answer": False,
        "include_raw_content": False,
    }
    try:
        r = httpx.post(TAVILY_ENDPOINT, json=payload, timeout=15.0)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        return [
            {
                "url": x.get("url", ""),
                "title": x.get("title", ""),
                "content": x.get("content", ""),
                "score": x.get("score", 0.0),
            }
            for x in results
        ]
    except httpx.HTTPError as e:
        logger.warning(f"tavily error for '{query}': {e}")
        return []


def scrape_url(url: str) -> str:
    """Fetch a URL and return extracted main text. Empty string on failure."""
    try:
        with httpx.Client(
            timeout=SCRAPE_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": SCRAPE_USER_AGENT},
        ) as client:
            r = client.get(url)
            if r.status_code >= 400:
                logger.info(f"scrape {url} -> {r.status_code}")
                return ""
            if len(r.content) > SCRAPE_MAX_BYTES:
                logger.info(f"scrape {url} -> too large ({len(r.content)} bytes)")
                return ""
            html = r.text
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        return (text or "").strip()
    except Exception as e:
        logger.warning(f"scrape {url} failed: {e}")
        return ""
