"""
Feedback Engine - Coaching report generation
============================================
Given a CallAnalysis, generates:
  - 5 rubric scores (0-10)
  - top wins
  - top improvements (with specific timestamps)
  - a "drill" practice exercise
"""

import time
import json
import logging
from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger("sales-coach.feedback")

FEEDBACK_MODEL = "gpt-4o-mini"
PRICING = {"gpt-4o-mini": {"input": 0.15, "output": 0.60}}


class RubricScore(BaseModel):
    rapport: int = Field(ge=0, le=10, description="Personal connection, warmth, active listening")
    discovery: int = Field(ge=0, le=10, description="Quality of questions to uncover pain")
    objection_handling: int = Field(ge=0, le=10, description="Acknowledge, reframe, advance")
    value_communication: int = Field(ge=0, le=10, description="Tied benefits to prospect's stated needs")
    close: int = Field(ge=0, le=10, description="Clear next step, urgency, ask for the sale")


class CoachingFeedback(BaseModel):
    scores: RubricScore
    overall: int = Field(ge=0, le=10)
    top_wins: list[str] = Field(description="3 specific things the rep did well, with timestamps")
    top_improvements: list[dict] = Field(
        description='[{"issue": str, "timestamp": float, "suggestion": str}, ...]'
    )
    drill: str = Field(description="A 5-minute practice exercise to address the weakest area")


def generate_feedback(analysis: dict, transcript: dict, openai_api_key: str) -> tuple[dict, float]:
    """Generate the coaching feedback for a call."""
    client = OpenAI(api_key=openai_api_key)

    # Build a compact transcript excerpt
    segments = transcript.get("segments", [])
    seg_text = "\n".join(f"[{s.get('start', 0):.1f}s] {s.get('text', '')}" for s in segments[:200])

    sys = (
        "You are a veteran sales coach (20+ years experience). "
        "You give specific, actionable feedback. You cite timestamps for every claim. "
        "You never give generic advice — every point is grounded in something the rep actually said or did."
    )
    user = (
        f"Analysis:\n{json.dumps(analysis, indent=2)}\n\n"
        f"Transcript (with timestamps):\n{seg_text}\n\n"
        f"Generate coaching feedback as JSON matching the schema:"
    )

    tools = [{
        "type": "function",
        "function": {
            "name": "submit_feedback",
            "description": "Submit the coaching feedback.",
            "parameters": CoachingFeedback.model_json_schema(),
        }
    }]

    start = time.time()
    resp = client.chat.completions.create(
        model=FEEDBACK_MODEL,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "submit_feedback"}},
        temperature=0.3,
    )
    elapsed = time.time() - start
    usage = resp.usage
    cost = (usage.prompt_tokens / 1e6) * PRICING[FEEDBACK_MODEL]["input"] + \
           (usage.completion_tokens / 1e6) * PRICING[FEEDBACK_MODEL]["output"]

    tool_call = resp.choices[0].message.tool_calls[0]
    parsed = json.loads(tool_call.function.arguments)
    validated = CoachingFeedback.model_validate(parsed).model_dump()

    logger.info(
        f"feedback done in {elapsed:.1f}s "
        f"in_tok={usage.prompt_tokens} out_tok={usage.completion_tokens} "
        f"cost=${cost:.4f}"
    )
    return validated, cost
