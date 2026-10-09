"""
Call Analyzer - GPT-4o with function calling
============================================
Extracts structured insights from a sales call transcript:
  - summary
  - talk_ratio (rep % vs prospect %)
  - pace (words/min)
  - objections
  - key_moments
  - sentiment
"""

import time
import json
import logging
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger("sales-coach.analyzer")

ANALYZER_MODEL = "gpt-4o"
PRICING = {"gpt-4o": {"input": 2.50, "output": 10.00}}


# =============================================================================
# Pydantic schemas for the function-call output
# =============================================================================

class Objection(BaseModel):
    type: str = Field(description="price, timing, authority, need, trust, competitor, other")
    timestamp: float = Field(description="When in the call (seconds)")
    prospect_quote: str
    rep_response: Optional[str] = None
    resolved: bool = False


class KeyMoment(BaseModel):
    timestamp: float
    label: str = Field(description="e.g., 'price push-back', 'buying signal', 'demo walkthrough'")
    importance: int = Field(ge=1, le=5, description="1 = minor, 5 = pivotal")
    quote: str


class SentimentSegment(BaseModel):
    start_s: float
    end_s: float
    sentiment: str = Field(description="positive, neutral, negative, mixed")
    score: float = Field(ge=-1.0, le=1.0)


class CallAnalysis(BaseModel):
    summary: str = Field(description="1-3 sentence summary of the call")
    outcome: str = Field(description="demo_booked, follow_up_scheduled, not_interested, no_clear_next_step, closed_won, closed_lost")
    talk_ratio_rep_pct: float = Field(ge=0, le=100)
    pace_wpm: float = Field(description="words per minute across the full call")
    objections: list[Objection]
    key_moments: list[KeyMoment]
    sentiment_segments: list[SentimentSegment]
    discovery_questions_asked: int
    next_steps_defined: bool


def _compute_basic_metrics(transcript: dict) -> dict:
    """Compute talk ratio and pace from the transcript segments (no LLM)."""
    segments = transcript.get("segments", [])
    if not segments:
        return {"talk_ratio_rep_pct": 50.0, "pace_wpm": 0.0}

    # Heuristic: assume speaker labels would come from diarization
    # Without diarization, we just measure pace and use 50/50 as talk ratio
    total_words = sum(len(s.get("text", "").split()) for s in segments)
    duration = transcript.get("duration_s") or sum(s.get("end", 0) - s.get("start", 0) for s in segments)
    pace = (total_words / duration * 60) if duration > 0 else 0.0
    return {"talk_ratio_rep_pct": 50.0, "pace_wpm": round(pace, 1)}


def analyze_call(transcript: dict, openai_api_key: str) -> tuple[dict, float]:
    """Run GPT-4o with function calling to extract structured analysis."""
    client = OpenAI(api_key=openai_api_key)

    # Prepare the transcript for the prompt (cap to fit context)
    segments = transcript.get("segments", [])
    seg_text = "\n".join(
        f"[{s.get('start', 0):.1f}s] {s.get('text', '')}" for s in segments[:400]
    )
    full_text = transcript.get("text", "")

    basic = _compute_basic_metrics(transcript)

    sys = (
        "You are a sales call analyst. Given a transcript with timestamps, extract a structured analysis. "
        "Be specific: quote the actual words the prospect used. "
        "For objections, list every distinct one. "
        "For key_moments, identify the 3-5 most important moments (e.g., price push-back, "
        "buying signal, demo agreement, clear next step). "
        "For sentiment_segments, break the call into 3-5 segments and label sentiment per segment."
    )
    user = (
        f"Measured pace: {basic['pace_wpm']} wpm\n\n"
        f"Transcript:\n{seg_text}\n\n"
        f"Full text (for context):\n{full_text[:4000]}\n\n"
        f"Extract the analysis as JSON matching the schema:"
    )

    tools = [{
        "type": "function",
        "function": {
            "name": "submit_analysis",
            "description": "Submit the structured call analysis.",
            "parameters": CallAnalysis.model_json_schema(),
        }
    }]

    start = time.time()
    resp = client.chat.completions.create(
        model=ANALYZER_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "submit_analysis"}},
        temperature=0.0,
    )
    elapsed = time.time() - start
    usage = resp.usage
    cost = (usage.prompt_tokens / 1e6) * PRICING[ANALYZER_MODEL]["input"] + \
           (usage.completion_tokens / 1e6) * PRICING[ANALYZER_MODEL]["output"]

    # Extract the function call args
    tool_call = resp.choices[0].message.tool_calls[0]
    parsed = json.loads(tool_call.function.arguments)
    parsed["pace_wpm"] = parsed.get("pace_wpm") or basic["pace_wpm"]
    parsed["talk_ratio_rep_pct"] = parsed.get("talk_ratio_rep_pct") or basic["talk_ratio_rep_pct"]

    # Validate via Pydantic (raises if schema drift)
    validated = CallAnalysis.model_validate(parsed).model_dump()

    logger.info(
        f"analyzer done in {elapsed:.1f}s "
        f"in_tok={usage.prompt_tokens} out_tok={usage.completion_tokens} "
        f"cost=${cost:.4f}"
    )
    return validated, cost
