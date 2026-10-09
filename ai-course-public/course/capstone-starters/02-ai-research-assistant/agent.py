"""
Research Agent - ReAct / plan-and-execute via LangGraph
========================================================
A 5-node state machine that takes a research question and returns a cited report:
  1. plan       - decompose into 5-10 sub-questions (GPT-4o)
  2. search     - for each sub-question, call Tavily (Tavily)
  3. scrape     - for each unique URL, fetch + extract text (httpx + trafilatura)
  4. synthesize - write a section per sub-question (GPT-4o-mini)
  5. critique   - check for gaps, add 1-2 more searches if needed
  6. finalize   - assemble the report (GPT-4o)

Each node writes to a shared dict. The graph is deterministic and easy to debug.
"""

import time
import json
import logging
from typing import TypedDict, Annotated
from openai import OpenAI
from langgraph.graph import StateGraph, END

from tools import tavily_search, scrape_url

logger = logging.getLogger("research-assistant.agent")

PLANNER_MODEL = "gpt-4o"
SYNTH_MODEL = "gpt-4o-mini"
FINALIZER_MODEL = "gpt-4o"

# Pricing per 1M tokens (2026)
PRICING = {
    "gpt-4o":       {"input": 2.50, "output": 10.00},
    "gpt-4o-mini":  {"input": 0.15, "output": 0.60},
}

# Tool budgets to keep costs predictable
MAX_SUBQUESTIONS = 8
MAX_SEARCH_RESULTS_PER_Q = 3
MAX_SOURCES = 30
MAX_TOTAL_SEARCHES = 30


class ResearchState(TypedDict):
    question: str
    plan: list[str]
    searches: list[dict]        # [{sub_q, results: [{url, title, snippet}]}]
    sources: list[dict]         # unique URLs we've scraped
    sections: list[dict]        # [{sub_q, text, source_ids}]
    critique_notes: str
    cost_usd: float
    elapsed_s: float


def _add_cost(state: ResearchState, model: str, in_tok: int, out_tok: int) -> None:
    p = PRICING.get(model, {"input": 0, "output": 0})
    state["cost_usd"] = state.get("cost_usd", 0.0) + (in_tok / 1e6) * p["input"] + (out_tok / 1e6) * p["output"]


# =============================================================================
# NODES
# =============================================================================

def plan_node(state: ResearchState) -> ResearchState:
    """Decompose the question into 5-8 sub-questions."""
    client = OpenAI()
    sys = (
        "You are a research planner. Given a complex research question, "
        "decompose it into 5-8 specific sub-questions that, when answered together, "
        "fully address the original question. Output a JSON array of strings, nothing else."
    )
    user = f"Research question: {state['question']}\n\nSub-questions (JSON array):"
    resp = client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    _add_cost(state, PLANNER_MODEL, resp.usage.prompt_tokens, resp.usage.completion_tokens)
    parsed = json.loads(resp.choices[0].message.content)
    # accept either {"sub_questions": [...]} or a bare list
    if isinstance(parsed, dict):
        sub_qs = parsed.get("sub_questions") or parsed.get("questions") or list(parsed.values())[0]
    else:
        sub_qs = parsed
    sub_qs = [str(s).strip() for s in sub_qs][:MAX_SUBQUESTIONS]
    state["plan"] = sub_qs
    logger.info(f"plan: {len(sub_qs)} sub-questions")
    return state


def search_node(state: ResearchState) -> ResearchState:
    """For each sub-question, call Tavily."""
    searches = []
    budget = MAX_TOTAL_SEARCHES
    for sub_q in state["plan"]:
        if budget <= 0:
            break
        results = tavily_search(sub_q, max_results=MAX_SEARCH_RESULTS_PER_Q)
        searches.append({"sub_q": sub_q, "results": results})
        budget -= 1
    state["searches"] = searches
    logger.info(f"search: {sum(len(s['results']) for s in searches)} results across {len(searches)} sub-questions")
    return state


def scrape_node(state: ResearchState) -> ResearchState:
    """For each unique URL in searches, fetch + extract text."""
    seen = set()
    sources = []
    for s in state["searches"]:
        for r in s["results"]:
            url = r.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            if len(sources) >= MAX_SOURCES:
                break
            text = scrape_url(url)
            if text:
                sources.append({
                    "url": url,
                    "title": r.get("title", url),
                    "text": text[:8000],  # cap per source
                })
        if len(sources) >= MAX_SOURCES:
            break
    state["sources"] = sources
    logger.info(f"scrape: {len(sources)} sources extracted")
    return state


def synthesize_node(state: ResearchState) -> ResearchState:
    """Write a section per sub-question using the scraped sources."""
    client = OpenAI()
    sources = state["sources"]
    if not sources:
        state["sections"] = []
        return state

    # Build a numbered source list to reference
    src_list = "\n".join(f"[{i+1}] {s['title']} — {s['url']}" for i, s in enumerate(sources))

    sections = []
    for sub_q in state["plan"]:
        # find the most relevant sources via simple keyword overlap (cheap)
        kw = set(sub_q.lower().split())
        ranked = sorted(
            sources,
            key=lambda s: sum(1 for w in s["text"].lower().split() if w in kw),
            reverse=True,
        )
        top = ranked[:5]
        ctx = "\n\n".join(f"[{sources.index(s)+1}] {s['text'][:1500]}" for s in top)

        sys = (
            "You are a research writer. Using ONLY the numbered sources below, "
            "write 2-4 paragraphs answering the sub-question. Cite sources as [1], [2], etc. "
            "If the sources don't cover the question, say so. Be specific and factual."
        )
        user = f"Sub-question: {sub_q}\n\nSources:\n{ctx}\n\nWrite the answer:"
        resp = client.chat.completions.create(
            model=SYNTH_MODEL,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        _add_cost(state, SYNTH_MODEL, resp.usage.prompt_tokens, resp.usage.completion_tokens)
        # map cited numbers back to source indices
        cited = []
        for s in top:
            cited.append(sources.index(s) + 1)
        sections.append({"sub_q": sub_q, "text": resp.choices[0].message.content, "source_ids": cited})

    state["sections"] = sections
    logger.info(f"synthesize: {len(sections)} sections written")
    return state


def critique_node(state: ResearchState) -> ResearchState:
    """Check if the report is missing critical info; if so, queue one more search."""
    client = OpenAI()
    body = "\n\n".join(f"Q: {s['sub_q']}\nA: {s['text'][:400]}" for s in state["sections"])
    sys = (
        "You are a research editor. Given the original question and the drafted sections, "
        "identify any major gaps that would make the report incomplete. "
        "Output JSON: {\"needs_more\": bool, \"gaps\": [str], \"suggested_queries\": [str]}"
    )
    user = f"Original question: {state['question']}\n\nDrafted sections:\n{body}\n\nCritique:"
    resp = client.chat.completions.create(
        model=SYNTH_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    _add_cost(state, SYNTH_MODEL, resp.usage.prompt_tokens, resp.usage.completion_tokens)
    parsed = json.loads(resp.choices[0].message.content)
    state["critique_notes"] = json.dumps(parsed)

    # If critique suggests more queries and we have budget, do one more search round
    if parsed.get("needs_more") and parsed.get("suggested_queries"):
        new_qs = parsed["suggested_queries"][:2]
        for sub_q in new_qs:
            results = tavily_search(sub_q, max_results=2)
            for r in results:
                url = r.get("url")
                if url and not any(s["url"] == url for s in state["sources"]):
                    text = scrape_url(url)
                    if text:
                        state["sources"].append({"url": url, "title": r.get("title", url), "text": text[:8000]})
    return state


def finalize_node(state: ResearchState) -> ResearchState:
    """Assemble the report."""
    client = OpenAI()
    sources = state["sources"]
    src_list = "\n".join(f"[{i+1}] {s['title']} — {s['url']}" for i, s in enumerate(sources))
    body = "\n\n---\n\n".join(
        f"## {s['sub_q']}\n\n{s['text']}" for s in state["sections"]
    )
    sys = (
        "You are a research editor. Given the original question, the section drafts, and the source list, "
        "produce a polished ~1500 word markdown report. Use the section drafts as-is unless they're factually wrong. "
        "End with a '## Sources' section listing each [n] reference with its URL."
    )
    user = (
        f"Original question: {state['question']}\n\n"
        f"Sources:\n{src_list}\n\n"
        f"Section drafts:\n{body}\n\n"
        f"Final report:"
    )
    resp = client.chat.completions.create(
        model=FINALIZER_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    _add_cost(state, FINALIZER_MODEL, resp.usage.prompt_tokens, resp.usage.completion_tokens)
    state["final_report"] = resp.choices[0].message.content
    return state


# =============================================================================
# GRAPH
# =============================================================================

def build_graph() -> StateGraph:
    g = StateGraph(ResearchState)
    g.add_node("plan", plan_node)
    g.add_node("search", search_node)
    g.add_node("scrape", scrape_node)
    g.add_node("synthesize", synthesize_node)
    g.add_node("critique", critique_node)
    g.add_node("finalize", finalize_node)
    g.set_entry_point("plan")
    g.add_edge("plan", "search")
    g.add_edge("search", "scrape")
    g.add_edge("scrape", "synthesize")
    g.add_edge("synthesize", "critique")
    g.add_edge("critique", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


class ResearchAgent:
    def __init__(self, openai_api_key: str, tavily_api_key: str):
        self.openai = OpenAI(api_key=openai_api_key)
        self.tavily_key = tavily_api_key
        self.graph = build_graph()

    def run(self, question: str, max_sources: int = 30) -> dict:
        global MAX_SOURCES
        MAX_SOURCES = max_sources
        start = time.time()
        state: ResearchState = {
            "question": question,
            "plan": [],
            "searches": [],
            "sources": [],
            "sections": [],
            "critique_notes": "",
            "cost_usd": 0.0,
            "elapsed_s": 0.0,
        }
        out = self.graph.invoke(state)
        out["elapsed_s"] = time.time() - start
        logger.info(f"research done cost=${out['cost_usd']:.3f} elapsed={out['elapsed_s']:.1f}s")
        return {
            "plan": out["plan"],
            "sources": [{"url": s["url"], "title": s["title"]} for s in out["sources"]],
            "report": out.get("final_report", ""),
            "cost_usd": out["cost_usd"],
            "latency_s": out["elapsed_s"],
        }
