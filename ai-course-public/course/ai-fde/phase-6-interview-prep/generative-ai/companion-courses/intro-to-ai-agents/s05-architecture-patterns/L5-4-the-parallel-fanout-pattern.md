# L5.4: The parallel fan-out / fan-in pattern

> **FDE framing in one line:** the parallel fan-out / fan-in pattern runs N agents concurrently and merges the results. The right pattern when sub-tasks are independent and the latency budget is tight. The total latency is `max(sub_task_latency)`, not `sum(sub_task_latency)`.

## The 3 things you'll learn

1. The 3 components of the parallel pattern: fan-out (dispatch N agents), fan-in (merge results), merge strategy (concatenate, vote, synthesize).
2. The 4-axis parallelism rubric: independence, latency budget, merge strategy, error tolerance.
3. The race condition and the timeout: parallel agents have non-deterministic completion order; the merge must handle missing or partial results.

## Concept

The parallel fan-out / fan-in pattern is the right shape when the work decomposes into independent sub-tasks that can run concurrently. The orchestrator fans out: it dispatches N sub-agents in parallel, each with its own sub-goal. The fan-in: the orchestrator waits for all sub-agents to complete (or timeout) and merges the results. **The total latency is `max(sub_task_latency)`, not `sum(sub_task_latency)`.** For 3 sub-tasks of 5s each, sequential is 15s; parallel is 5s. The 3× latency reduction is the value proposition.

The 3 components:

1. **Fan-out (dispatch N agents).** The orchestrator dispatches N sub-agents concurrently. Each sub-agent receives its own sub-goal; the sub-agents do not share state during execution. The fan-out can be implemented with `concurrent.futures.ThreadPoolExecutor` (for I/O-bound agents) or `ProcessPoolExecutor` (for CPU-bound agents).
2. **Fan-in (merge results).** The orchestrator waits for all sub-agents to complete (or timeout) and collects the results. The fan-in handles the case where some sub-agents succeed and others fail; the merge strategy decides how to handle partial results.
3. **Merge strategy (concatenate, vote, synthesize).** The orchestrator merges the sub-results into a single output. Three common strategies: (a) concatenate (append all results, useful for parallel research), (b) vote (each sub-agent votes, take the majority, useful for MoE-style classification), (c) synthesize (use an LLM to combine the results, useful for parallel analysis).

The 4-axis parallelism rubric:

1. **Independence.** Are the sub-tasks independent? Yes → parallel. No (sub-task B depends on sub-task A's output) → sequential.
2. **Latency budget.** Is the latency budget tight? Yes (< 30s) → parallel. No (latency budget allows sequential) → either works.
3. **Merge strategy.** Can the results be merged deterministically? Yes (concatenate, vote) → parallel. No (requires synthesis) → parallel + synthesis step.
4. **Error tolerance.** Can the workflow tolerate partial failures? Yes → parallel with per-sub-agent error handling. No (all sub-tasks must succeed) → parallel with retry/timeout.

The race condition and the timeout are the operational consequences of parallelism. Sub-agents complete in non-deterministic order; the fan-in must wait for the slowest sub-agent. The timeout (e.g., 30s) is critical: a hung sub-agent blocks the fan-in indefinitely. The per-sub-agent circuit breaker + timeout is the FDE's safety net.

## The pattern

The parallel fan-out / fan-in, as a class:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class ParallelFanOut:
    """Parallel fan-out / fan-in. N sub-agents run concurrently."""

    def __init__(self, sub_agents: dict[str, SingleAgent], merge_strategy: str = "synthesize",
                 timeout_s: float = 30.0):
        self.sub_agents = sub_agents
        self.merge_strategy = merge_strategy
        self.timeout_s = timeout_s

    def run(self, sub_goals: dict[str, str]) -> dict:
        """Fan out: dispatch N sub-agents concurrently. Fan in: merge results."""
        # Fan-out: dispatch all sub-agents in parallel
        with ThreadPoolExecutor(max_workers=len(sub_goals)) as executor:
            future_to_agent = {
                executor.submit(self._safe_run, name, goal): name
                for name, goal in sub_goals.items()
            }
            results = {}
            for future in as_completed(future_to_agent, timeout=self.timeout_s):
                agent_name = future_to_agent[future]
                try:
                    results[agent_name] = future.result()
                except Exception as e:
                    results[agent_name] = {"error": str(e)}
                # Per-sub-agent timeout
                if time.time() - start_time > self.timeout_s:
                    results[agent_name] = {"error": "timeout"}

        # Fan-in: merge results
        return self._merge(results)

    def _safe_run(self, agent_name: str, goal: str) -> dict:
        """Run a sub-agent with circuit breaker + timeout."""
        sub_agent = self.sub_agents[agent_name]
        if not sub_agent.breaker.allow():
            return {"error": "breaker_open"}
        try:
            result = sub_agent.run(goal)
            sub_agent.breaker.record_success()
            return result
        except Exception as e:
            sub_agent.breaker.record_failure()
            return {"error": str(e)}

    def _merge(self, results: dict) -> dict:
        """Merge results by strategy."""
        if self.merge_strategy == "concatenate":
            return {"results": list(results.values())}
        if self.merge_strategy == "vote":
            return {"votes": results, "winner": majority_vote(results)}
        if self.merge_strategy == "synthesize":
            synthesis_llm = self.sub_agents[list(self.sub_agents.keys())[0]].model
            return {"synthesis": synthesis_llm.run(f"Synthesize: {results}")}
        return results
```

The PacificFreight parallel research use case:

```python
PARALLEL_RESEARCH = ParallelFanOut(
    sub_agents={
        "web_search": WEB_SEARCH_AGENT,    # 1 tool, 5s latency
        "db_query": DB_QUERY_AGENT,         # 1 tool, 3s latency
        "rag_lookup": RAG_LOOKUP_AGENT,    # 1 tool, 4s latency
    },
    merge_strategy="synthesize",
    timeout_s=10.0,  # Total budget: 10s
)
# Sequential: 5 + 3 + 4 = 12s. Parallel: max(5, 3, 4) = 5s. 2.4× faster.
```

The pattern that wins interviews is the "parallel fan-out + per-sub-agent timeout + merge strategy" pattern. The candidate who says "I fan out N sub-agents concurrently, fan in by waiting for all (or timeout), merge by concatenate/vote/synthesize. The latency is max(sub_task_latency), not sum. Per-sub-agent timeout + circuit breaker is the safety net. The wrong choice is sequential when sub-tasks are independent (3-5× latency waste). The wrong choice is parallel when sub-tasks are dependent (race conditions). The right choice is parallel when independence + latency budget + error tolerance are present" is the candidate who demonstrates the parallelism-mindset.

## Code or example

The 4-axis parallelism rubric in action:

```python
def should_parallelize(sub_tasks: list[dict], latency_budget_s: float) -> bool:
    """Decide whether to run sub-tasks in parallel or sequentially."""
    # Axis 1: Independence
    independent = all(not st.get("depends_on") for st in sub_tasks)
    if not independent:
        return False  # Sequential dependency; cannot parallelize

    # Axis 2: Latency budget
    sequential_latency = sum(estimate_latency(st) for st in sub_tasks)
    parallel_latency = max(estimate_latency(st) for st in sub_tasks)
    if sequential_latency <= latency_budget_s:
        return False  # Sequential fits; parallel not needed

    # Axis 3: Merge strategy
    mergeable = has_deterministic_merge(sub_tasks) or has_synthesis_merge(sub_tasks)
    if not mergeable:
        return False  # Cannot merge results; parallel not useful

    # Axis 4: Error tolerance
    error_tolerant = all(st.get("optional", False) for st in sub_tasks) or len(sub_tasks) > 1
    if not error_tolerant:
        return False  # All must succeed; parallel risk is too high

    return True  # All 4 axes positive; parallelize
```

The merge strategies compared:

```python
# Strategy 1: Concatenate (for parallel research)
def merge_concatenate(results: dict) -> dict:
    return {"combined": "\n".join(r.get("content", "") for r in results.values())}
# Use case: research agent queries 3 sources, results are concatenated into a single report.

# Strategy 2: Vote (for MoE-style classification)
def merge_vote(results: dict) -> dict:
    votes = [r.get("vote") for r in results.values()]
    return {"winner": majority(votes), "vote_count": Counter(votes)}
# Use case: 3 classifier agents vote on whether an email is spam; majority wins.

# Strategy 3: Synthesize (for parallel analysis)
def merge_synthesize(results: dict, llm) -> dict:
    return {"synthesis": llm(f"Combine these analyses: {results}")}
# Use case: 3 analyst agents each analyze a different aspect; the synthesizer combines them.
```

The race condition handling (the FDE's safety net):

```python
def safe_parallel_dispatch(sub_goals: dict, sub_agents: dict, timeout_s: float = 30.0) -> dict:
    """Parallel dispatch with per-sub-agent timeout + circuit breaker."""
    results = {}
    start = time.time()
    with ThreadPoolExecutor(max_workers=len(sub_goals)) as executor:
        futures = {executor.submit(sub_agents[name].run, goal): name
                   for name, goal in sub_goals.items()}
        for future in as_completed(futures, timeout=timeout_s):
            name = futures[future]
            elapsed = time.time() - start
            if elapsed > timeout_s:
                results[name] = {"error": "global_timeout", "elapsed_s": elapsed}
                continue
            try:
                results[name] = future.result(timeout=max(0, timeout_s - elapsed))
            except Exception as e:
                results[name] = {"error": str(e)}
    # Fill in any missing sub-agents
    for name in sub_goals:
        if name not in results:
            results[name] = {"error": "did_not_complete"}
    return results
```

## Production addendum

The parallel pattern question is the answer to "when do you parallelize agent work." The 60-second script:

> "Parallel fan-out / fan-in for independent sub-tasks with a tight latency budget. Fan out: N sub-agents dispatched concurrently. Fan in: wait for all (or timeout), merge results. **Total latency is max(sub_task_latency), not sum.** For 3 sub-tasks of 5s each, sequential is 15s; parallel is 5s. The 3× latency reduction is the value. The 4 axes: independence, latency budget, merge strategy, error tolerance. The merge strategies: concatenate, vote, synthesize. The safety net: per-sub-agent timeout + circuit breaker. The wrong choice is parallel when sub-tasks are dependent (race conditions). The wrong choice is sequential when sub-tasks are independent (3-5× latency waste). The right choice is parallel when all 4 axes are positive."

This is the difference between a candidate who says "I made it faster" and a candidate who says "parallel fan-out / fan-in, 4 axes (independence, latency, merge, error tolerance), per-sub-agent timeout + circuit breaker, max latency instead of sum." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-3-parallel.py` — the parallel fan-out / fan-in pattern.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/15-parallel-agent.py` — the production parallel pattern with timeout + circuit breaker.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/07-orchestrator-pattern.md` — parallelism as a sub-pattern of the orchestrator.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — the orchestrator uses parallel for independent sub-tasks.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — parallel as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you parallelize agent work?"** Answer: when 4 axes are positive — sub-tasks are independent, latency budget is tight (< 30s), results can be merged (concatenate / vote / synthesize), workflow tolerates partial failures. Parallel reduces latency from `sum(sub_task_latency)` to `max(sub_task_latency)`.
2. **"What are the 3 merge strategies?"** Answer: (1) concatenate (append all results, for parallel research), (2) vote (each sub-agent votes, majority wins, for MoE-style classification), (3) synthesize (LLM combines results, for parallel analysis). The merge strategy is the FDE's primary design decision for the fan-in step.
3. **"What is the safety net for parallel agents?"** Answer: per-sub-agent timeout + circuit breaker. Sub-agents complete in non-deterministic order; the fan-in must handle missing or partial results. The timeout (e.g., 30s) is critical — a hung sub-agent blocks the fan-in indefinitely. The per-sub-agent circuit breaker catches repeated failures.

## Read next

`L5-5-the-hierarchical-task-network.md` — the fifth pattern. The HTN pattern is for hierarchical tasks where the plan is a tree, not a list. Recursive sub-plans for tasks like "research a topic" (which decomposes into "search, read, summarize" each of which is a sub-plan).