from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import wikipedia
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WikipediaResearchAssistant")
BASE_DIR = Path(__file__).resolve().parent


def _resolve_page(topic: str) -> wikipedia.WikipediaPage:
    """Return the best matching page or raise a Wikipedia exception."""
    query = topic.strip()
    if not query:
        raise ValueError("topic must not be empty")

    matches = wikipedia.search(query, results=5)
    if not matches:
        raise wikipedia.PageError(query)
    return wikipedia.page(matches[0], auto_suggest=False)


def _error_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, wikipedia.DisambiguationError):
        return {
            "ok": False,
            "error": "ambiguous_topic",
            "message": f"'{exc.title}' is ambiguous.",
            "suggestions": exc.options[:8],
        }
    if isinstance(exc, wikipedia.PageError):
        return {
            "ok": False,
            "error": "page_not_found",
            "message": "No matching Wikipedia page was found.",
        }
    return {"ok": False, "error": type(exc).__name__, "message": str(exc)}


@mcp.tool()
def fetch_wikipedia_info(query: str, sentences: int = 5) -> dict[str, Any]:
    """Find the best Wikipedia article and return title, summary, and URL.

    Args:
        query: Topic or article name to search for.
        sentences: Approximate number of summary sentences, from 1 to 10.
    """
    try:
        sentence_count = max(1, min(sentences, 10))
        page = _resolve_page(query)
        summary = wikipedia.summary(
            page.title, sentences=sentence_count, auto_suggest=False
        )
        return {
            "ok": True,
            "title": page.title,
            "summary": summary,
            "url": page.url,
        }
    except Exception as exc:
        return _error_payload(exc)


@mcp.tool()
def list_wikipedia_sections(topic: str) -> dict[str, Any]:
    """Return the section titles available in the best matching article.

    Args:
        topic: Topic or article name.
    """
    try:
        page = _resolve_page(topic)
        return {
            "ok": True,
            "title": page.title,
            "url": page.url,
            "sections": page.sections,
        }
    except Exception as exc:
        return _error_payload(exc)


@mcp.tool()
def get_section_content(
    topic: str, section_title: str, max_characters: int = 12000
) -> dict[str, Any]:
    """Return text from one named section of a Wikipedia article.

    Args:
        topic: Topic or article name.
        section_title: Section heading to retrieve.
        max_characters: Safety limit for returned text, from 500 to 20000.
    """
    try:
        page = _resolve_page(topic)
        content = page.section(section_title)
        if not content:
            return {
                "ok": False,
                "error": "section_not_found",
                "message": f"Section '{section_title}' was not found.",
                "available_sections": page.sections,
            }

        limit = max(500, min(max_characters, 20000))
        truncated = len(content) > limit
        return {
            "ok": True,
            "title": page.title,
            "section": section_title,
            "content": content[:limit],
            "truncated": truncated,
            "url": page.url,
        }
    except Exception as exc:
        return _error_payload(exc)


@mcp.prompt()
def highlight_sections_prompt(topic: str) -> str:
    """Create instructions for selecting the most useful article sections."""
    return f"""You are a careful Wikipedia research assistant.
For the topic '{topic}':
1. Call list_wikipedia_sections.
2. Select 3 to 5 sections most useful for a general reader.
3. Explain each choice in one concise sentence.
4. Do not invent section names. Use only values returned by the tool.
5. If the topic is ambiguous, show the suggestions and ask the user to choose.
"""


@mcp.resource("file://suggested_titles")
def suggested_titles() -> str:
    """Return a newline-separated list of suggested research topics."""
    path = BASE_DIR / "suggested_titles.txt"
    if not path.exists():
        return "No suggested titles file was found."
    return path.read_text(encoding="utf-8").strip()


if __name__ == "__main__":
    print("Starting MCP Wikipedia server over stdio...", file=sys.stderr)
    mcp.run(transport="stdio")
