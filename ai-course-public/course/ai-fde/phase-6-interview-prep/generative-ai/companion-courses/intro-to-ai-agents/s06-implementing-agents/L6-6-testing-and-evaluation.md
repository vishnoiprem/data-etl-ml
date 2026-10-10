# L6.6: Testing and evaluation — the eval set as the spec

> **FDE framing in one line:** the eval set is the spec; the contract tests are the gate; the regression checks are the safety net; the A/B tests are the optimization lever. The FDE ships an eval set with every agent.

## The 3 things you'll learn

1. The 4 testing layers: contract tests (does the prompt produce the expected output), unit tests (does each component work), integration tests (does the agent work end-to-end), regression tests (does the new version preserve the old behavior).
2. The 4 RAGAS metrics: faithfulness, answer relevance, context precision, context recall. The standard eval set for RAG agents.
3. The "eval set as the spec" pattern: the eval set is the source of truth for what good behavior looks like. The agent is tested against the eval set; the FDE tunes the agent until it passes.

## Concept

Testing and evaluation is the 6th layer of the shipping agent. The eval set is the spec — a list of (input, expected output) tuples that defines what good behavior looks like. The contract tests are the gate — automated tests that run in CI and block a deploy if they fail. The regression checks are the safety net — periodic tests that run against the production agent to detect drift. **The FDE ships an eval set with every agent; the eval set is the first-class artifact that survives the FDE's exit.**

The 4 testing layers:

1. **Contract tests.** Does the system prompt + model produce the expected output? For each example in the eval set, the test asserts the model emits the expected action and the expected final answer. The contract test is the prompt-engineering safety net; a prompt change that breaks a test is a breaking change.
2. **Unit tests.** Does each component work? The parser, the schema validator, the cost tracker, the loop detector, the audit log. Each is tested in isolation. The unit tests are the implementation safety net; a refactor that breaks a test is a regression.
3. **Integration tests.** Does the agent work end-to-end? A mock LLM + the full agent + a fixture eval set. The integration test is the system safety net; a change to the loop, the tools, or the memory that breaks the end-to-end behavior is a regression.
4. **Regression tests.** Does the new version preserve the old behavior? The new agent runs against the held-out eval set; the metrics must be ≥ the old metrics. The regression test is the deployment safety net; a model upgrade, a prompt change, or a tool change that drops the metrics is blocked from deploy.

The 4 RAGAS metrics are the standard eval set for RAG agents:

1. **Faithfulness.** Is the answer grounded in the retrieved context? Score: 0.0-1.0; the answer is faithful if every claim is supported by the context. A faithful agent does not hallucinate.
2. **Answer relevance.** Is the answer relevant to the question? Score: 0.0-1.0; the answer is relevant if it addresses the question. A relevant agent does not go off-topic.
3. **Context precision.** Are the retrieved contexts relevant to the question? Score: 0.0-1.0; the retrieval is precise if the top-K contexts are all relevant. A precise retriever does not return noise.
4. **Context recall.** Are the relevant contexts retrieved? Score: 0.0-1.0; the retrieval has high recall if all the contexts needed to answer the question are in the top-K. A high-recall retriever does not miss relevant facts.

The "eval set as the spec" pattern is the recognition that the eval set is the source of truth. The agent is built to pass the eval set; the FDE tunes the system prompt, the model, the retrieval, the tools until the eval set passes. **The eval set is the contract; the agent is the implementation; the contract tests are the gate.**

## The pattern

The eval set as a fixture:

```python
# eval_set.jsonl — one JSON object per line
EVAL_SET = [
    {
        "input": {"email": "Where is my shipment PF-1003?"},
        "expected": {
            "tool": "tracker.lookup",
            "args": {"shipment_id": "PF-1003"},
            "answer_contains": ["PF-1003", "in transit"],
        },
    },
    {
        "input": {"email": "I need a refund for PF-1003, $50."},
        "expected": {
            "tool": "refund.create",
            "args": {"shipment_id": "PF-1003", "amount_usd": 50, "idempotency_key": "<non-empty>"},
            "answer_contains": ["refund", "$50"],
        },
    },
    # ... 98 more
]
```

The RAGAS metric implementation:

```python
def faithfulness(answer: str, context: list[str]) -> float:
    """Is every claim in the answer supported by the context?"""
    claims = extract_claims(answer)
    supported = sum(1 for c in claims if any(supports(c, ctx) for ctx in context))
    return supported / len(claims) if claims else 1.0

def answer_relevance(answer: str, question: str) -> float:
    """Is the answer relevant to the question?"""
    return semantic_similarity(answer, question)  # 0.0-1.0

def context_precision(retrieved: list[str], relevant: list[str]) -> float:
    """Are the retrieved contexts relevant?"""
    relevant_retrieved = sum(1 for r in retrieved if r in relevant)
    return relevant_retrieved / len(retrieved) if retrieved else 1.0

def context_recall(retrieved: list[str], relevant: list[str]) -> float:
    """Are all the relevant contexts retrieved?"""
    retrieved_relevant = sum(1 for r in relevant if r in retrieved)
    return retrieved_relevant / len(relevant) if relevant else 1.0
```

The contract test:

```python
def test_system_prompt_contract():
    """For each eval example, the model emits the expected action and answer."""
    for ex in EVAL_SET:
        output = llm([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ex["input"]["email"]},
        ])
        # Assert: the expected tool was called
        assert ex["expected"]["tool"] in output, f"expected {ex['expected']['tool']}, got: {output}"
        # Assert: the final answer contains the expected substrings
        for substring in ex["expected"]["answer_contains"]:
            assert substring in output, f"expected '{substring}' in: {output}"
```

The regression check:

```python
def regression_check(new_agent: SingleAgent, baseline_metrics: dict) -> dict:
    """Run the new agent against the eval set; assert metrics >= baseline."""
    new_metrics = run_eval(new_agent, EVAL_SET)
    regression = {
        "faithfulness": new_metrics["faithfulness"] >= baseline_metrics["faithfulness"] - 0.02,  # 2% tolerance
        "answer_relevance": new_metrics["answer_relevance"] >= baseline_metrics["answer_relevance"] - 0.02,
        "context_precision": new_metrics["context_precision"] >= baseline_metrics["context_precision"] - 0.02,
        "context_recall": new_metrics["context_recall"] >= baseline_metrics["context_recall"] - 0.02,
    }
    return {"new_metrics": new_metrics, "baseline": baseline_metrics, "passes": all(regression.values()), "regression": regression}
```

The A/B test (the optimization lever):

```python
def ab_test(agent_a: SingleAgent, agent_b: SingleAgent, eval_set: list, traffic_split: float = 0.5) -> dict:
    """Run both agents on the eval set; compare metrics."""
    metrics_a = run_eval(agent_a, eval_set)
    metrics_b = run_eval(agent_b, eval_set)
    return {
        "agent_a": metrics_a,
        "agent_b": metrics_b,
        "winner": "a" if metrics_a["answer_relevance"] > metrics_b["answer_relevance"] else "b",
        "delta": {k: metrics_b[k] - metrics_a[k] for k in metrics_a},
    }

# Example: A/B test gpt-5-mini vs gpt-5 for the planning step
# Result: gpt-5 is 5% more accurate but 15× more expensive
# Verdict: stay with gpt-5-mini (the 5% gain doesn't justify the 15× cost)
```

The pattern that wins interviews is the "4 layers + 4 metrics + eval-as-spec" pattern. The candidate who says "the eval set is the spec; the 4 testing layers are contract (does the prompt work), unit (does each component work), integration (does the agent work end-to-end), regression (does the new version preserve the old). The 4 RAGAS metrics are faithfulness, answer relevance, context precision, context recall. **The eval set is the source of truth; the agent is tuned to pass it**" is the candidate who demonstrates the testing-mindset.

## Code or example

The 4-layer test suite:

```python
# 1. Contract tests (does the prompt produce the expected output?)
def test_prompt_contract():
    for ex in EVAL_SET:
        output = llm([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": ex["input"]["email"]}])
        assert ex["expected"]["tool"] in output

# 2. Unit tests (does each component work?)
def test_parser_handles_final_answer():
    assert parse_step("Final Answer: Hello!") == {"type": "final", "answer": "Hello!"}
def test_schema_validator_catches_missing_field():
    assert "missing field" in validate_args({}, {"shipment_id": {"type": "string"}})
def test_cost_ceiling_breaches_at_threshold():
    cc = CostCeiling(max_run_usd=0.10)
    cc.run_cost = 0.15
    assert cc.breached()[0]

# 3. Integration tests (does the agent work end-to-end?)
def test_agent_handles_status_email():
    agent = SingleAgent(model=MOCK_MODEL, tools=MOCK_TOOLS, memory=Memory(), cost=CostCeiling(), system_prompt=SYSTEM_PROMPT)
    result = agent.run("Where is my shipment PF-1003?")
    assert "in transit" in result.get("answer", "")

# 4. Regression tests (does the new version preserve the old?)
def test_no_regression_on_prompt_change():
    new_agent = SingleAgent(..., system_prompt=NEW_PROMPT)
    result = regression_check(new_agent, BASELINE_METRICS)
    assert result["passes"]
```

The eval-driven iteration loop:

```python
# The FDE's weekly iteration
def weekly_iteration():
    # 1. Run the eval set against the current production agent
    current_metrics = run_eval(PROD_AGENT, EVAL_SET)
    # 2. Identify the failure cases (where metrics < threshold)
    failures = [ex for ex in EVAL_SET if not passes(ex, current_metrics)]
    # 3. Analyze: is it a prompt issue, a tool issue, a model issue, a retrieval issue?
    failure_analysis = analyze_failures(failures)
    # 4. Fix the issue: update the prompt, add a tool, switch the model, improve the retrieval
    fix = make_fix(failure_analysis)
    # 5. Test the fix against the eval set
    new_metrics = run_eval(fix, EVAL_SET)
    # 6. If new_metrics >= current_metrics, ship the fix
    if new_metrics["answer_relevance"] >= current_metrics["answer_relevance"]:
        deploy(fix)
```

## Production addendum

The testing question is the answer to "how do you test a production agent." The 60-second script:

> "4 testing layers. Contract tests (does the prompt produce the expected output). Unit tests (does each component work). Integration tests (does the agent work end-to-end). Regression tests (does the new version preserve the old). 4 RAGAS metrics: faithfulness, answer relevance, context precision, context recall. **The eval set is the spec; the agent is tuned to pass it.** The FDE runs the eval set weekly; identifies failure cases; analyzes; fixes; re-runs. The wrong choice is to ship without an eval set (no way to measure improvement). The right choice is the 4 layers + 4 metrics + weekly iteration."

This is the difference between a candidate who says "we test the agent" and a candidate who says "4 testing layers, 4 RAGAS metrics, eval set is the spec, weekly iteration loop, regression check before deploy." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-6-production/lesson-11-2-eval.py` — the RAGAS metrics implementation.
- **Reference implementation**: `course/ai-fde/phase-2-applications/service/eval.py` — the production eval set + RAGAS metrics.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/11-testing-and-eval.md` — the testing as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/03-distilled-slm/slm/eval.py` — the SLM eval against the PacificFreight eval set.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — testing as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you test a production agent?"** Answer: 4 testing layers. Contract tests (does the prompt produce the expected output). Unit tests (does each component work). Integration tests (does the agent work end-to-end). Regression tests (does the new version preserve the old). 4 RAGAS metrics: faithfulness, answer relevance, context precision, context recall. The eval set is the spec; the agent is tuned to pass it.
2. **"What are the 4 RAGAS metrics?"** Answer: (1) faithfulness — is every claim in the answer supported by the context, (2) answer relevance — is the answer relevant to the question, (3) context precision — are the retrieved contexts relevant, (4) context recall — are all the relevant contexts retrieved. The metrics are scored 0.0-1.0; the FDE tunes the agent to maximize all 4.
3. **"What is the eval set as the spec pattern?"** Answer: the eval set is a list of (input, expected output) tuples that defines what good behavior looks like. The agent is built to pass the eval set; the FDE tunes the system prompt, the model, the retrieval, the tools until the eval set passes. The eval set is the source of truth; the agent is the implementation; the contract tests are the gate. **The eval set is the first-class artifact that survives the FDE's exit.**

## Read next

`L6-7-deployment-and-scaling.md` — the 7th lecture. The deployment patterns: serverless (Lambda, Cloud Functions), container (Docker + ECS / Cloud Run), dedicated VM. The scaling levers: horizontal (more replicas), vertical (bigger model), cost-aware routing.