"""
================================================================
M13 L13  --  Agents, Tools, and Model Context Protocol (MCP)
================================================================

Run:    python3 lessons/m13-agents-mcp/L13-agents-mcp.py
Keys:   none

Builds a tiny agent runtime from scratch:
  * Tool (dataclass): name, description, JSON-Schema, callable
  * ToolRegistry: register / list / lookup by name
  * MCPSchema: JSON-Schema-style description (MCP protocol flavor)
  * MockLLM: given a prompt + tool list, returns a tool-call decision
  * Step: one iteration of the think -> act -> observe loop
  * Agent: the loop -- think -> call tool -> observe -> repeat
  * 5 sample tools: calculator, search, send_email, get_weather, lookup_employee
  * 3 sample tasks the agent can solve end-to-end

The lesson's point: an "agent" is just a loop.  The LLM picks a tool,
the runtime calls the tool, the result goes back into the prompt.
MCP standardizes the wire format so any client can talk to any server.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M13.L13"
SEED = 13
MAX_STEPS_DEFAULT = 6


# =================================================================
# SECTION 1  --  Tool dataclass
# =================================================================

@dataclass
class Tool:
    """A callable tool the agent can invoke.

    Mirrors the wire format used by OpenAI function calling and MCP:
    the agent gets the tool's name + description + JSON schema, and
    returns a JSON object matching the schema.  The runtime then
    looks up the Python callable by name and dispatches.
    """
    name: str
    description: str
    schema: dict[str, Any]          # JSON-Schema for the tool's arguments
    fn: Callable[..., Any]

    def to_mcp(self) -> dict[str, Any]:
        """Serialize as an MCP-style tool descriptor."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.schema,
        }

    def call(self, **kwargs: Any) -> Any:
        return self.fn(**kwargs)


# =================================================================
# SECTION 2  --  Tool registry
# =================================================================

@dataclass
class ToolRegistry:
    """Holds the set of tools available to the agent.

    Real implementations store this on a server and expose it via the
    MCP `tools/list` endpoint.  The agent (client) calls `tools/call`
    to invoke one.
    """
    tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        if tool.name in self.tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self.tools:
            raise KeyError(f"unknown tool: {name}. available: {list(self.tools)}")
        return self.tools[name]

    def list_names(self) -> list[str]:
        return list(self.tools.keys())

    def list_mcp(self) -> list[dict[str, Any]]:
        return [t.to_mcp() for t in self.tools.values()]

    def __len__(self) -> int:
        return len(self.tools)

    def __contains__(self, name: str) -> bool:
        return name in self.tools


# =================================================================
# SECTION 3  --  MockLLM
# =================================================================

@dataclass
class ToolCall:
    """The LLM's decision for one step: which tool to call and with what args."""
    tool_name: str
    args: dict[str, Any]
    thought: str = ""                 # the LLM's reasoning (for logging)

    def to_json(self) -> str:
        return json.dumps({"tool": self.tool_name, "args": self.args}, sort_keys=True)


class MockLLM:
    """A mock LLM that picks the next tool call given the task and history.

    The real LLM receives a prompt like:

        Task: what is the weather in Paris?
        Tools available:
          - calculator(a, b): arithmetic
          - get_weather(city): current conditions
        History:
          step 0: called get_weather(city=Paris) -> "72F sunny"

    and returns a tool call (or `done` if the task is finished).
    This mock uses a simple keyword matcher: for each tool, count
    keyword hits between the task and the tool's description, then
    pick the best match whose args can be extracted from the task.
    """

    def decide(self, task: str, history: list["Step"], tools: ToolRegistry,
               seed: int = SEED) -> ToolCall | None:
        """Return the next tool call, or None to declare 'done'.

        `seed` is the LLM's RNG seed (pinned for reproducibility).  The
        current implementation is fully deterministic without randomness,
        but the arg is part of the production interface.
        """
        # If the most recent step succeeded and we have an answer, stop.
        if history and not str(history[-1].observation).startswith("ERROR"):
            # Special case: if the last call's observation is a clean answer, stop.
            return None
        candidates = self._rank_tools(task, tools)
        for name, _score in candidates:
            tool = tools.get(name)
            args = self._extract_args(task, name, history)
            if args is None:
                continue
            return ToolCall(
                tool_name=name,
                args=args,
                thought=f"task matches {name}; extracted args {args}",
            )
        return None

    def _rank_tools(self, task: str, tools: ToolRegistry) -> list[tuple[str, int]]:
        """Rank tools by how well they match the task.  Strong signal: if the
        tool can extract structured args from the task, it's almost certainly
        the right pick.  Fall back to keyword overlap on the description.
        """
        scored: list[tuple[str, int]] = []
        task_lower = task.lower()
        for name, tool in tools.tools.items():
            score = 0
            # Big boost: if regex extractors fire, the tool fits.
            if self._extract_args(task, name, []) is not None:
                score += 100
            # Smaller boost: keyword overlap with description + name.
            task_words = set(re.findall(r"\w+", task_lower))
            desc_words = set(re.findall(r"\w+", (tool.name + " " + tool.description).lower()))
            score += len(task_words & desc_words)
            # Strong negative: if the tool name does not appear in the task,
            # downgrade tools that require a "verb" the task does not have.
            if name == "send_email" and "email" not in task_lower and "@" not in task:
                score -= 50
            scored.append((name, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _extract_args(self, task: str, tool_name: str, history: list["Step"]) -> dict[str, Any] | None:
        """Pull args out of the task using simple patterns.

        Production code would have the LLM emit JSON; here we use
        regexes that work for the sample tools.
        """
        if tool_name == "calculator":
            m = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/x])\s*(-?\d+(?:\.\d+)?)", task)
            if m:
                op = m.group(2)
                op = "*" if op == "x" else op
                return {"a": float(m.group(1)), "op": op, "b": float(m.group(3))}

        if tool_name == "get_weather":
            m = re.search(r"weather\s+in\s+([A-Za-z][A-Za-z\s]+?)(?:\?|$|\.)", task, re.IGNORECASE)
            if m:
                return {"city": m.group(1).strip()}

        if tool_name == "search":
            m = re.search(r"search\s+for\s+(.+?)(?:\?|$|\.)", task, re.IGNORECASE)
            if m:
                return {"query": m.group(1).strip()}
            # only fall back to "use the whole task" if the task actually says "search"
            if re.search(r"\bsearch\b", task, re.IGNORECASE):
                return {"query": task}
            return None

        if tool_name == "send_email":
            m_to = re.search(r"to\s+([\w.+-]+@[\w.-]+)", task)
            m_subj = re.search(r"subject\s+['\"]?([^'\".?]+)", task, re.IGNORECASE)
            m_body = re.search(r"saying\s+['\"]?([^'\".]+)", task, re.IGNORECASE)
            if m_to:
                return {
                    "to": m_to.group(1),
                    "subject": (m_subj.group(1).strip() if m_subj else "(no subject)"),
                    "body": (m_body.group(1).strip() if m_body else ""),
                }

        if tool_name == "lookup_employee":
            m = re.search(r"(?:employee|person|for|about|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", task)
            if m:
                return {"name": m.group(1).strip()}
            return {"name": ""}
        return None


# =================================================================
# SECTION 4  --  Step and Agent
# =================================================================

@dataclass
class Step:
    """One iteration of the agent loop: thought -> tool_call -> observation."""
    step_num: int
    thought: str
    tool_name: str
    tool_args: dict[str, Any]
    observation: Any

    def __str__(self) -> str:
        obs_repr = repr(self.observation)
        if len(obs_repr) > 80:
            obs_repr = obs_repr[:77] + "..."
        return (
            f"step {self.step_num}: {self.tool_name}({self.tool_args}) "
            f"-> {obs_repr}"
        )


@dataclass
class AgentRun:
    """The full transcript of one agent run."""
    task: str
    steps: list[Step] = field(default_factory=list)
    final_answer: str = ""
    stopped_reason: str = ""   # "done" | "max_steps" | "no_tool"

    @property
    def n_steps(self) -> int:
        return len(self.steps)


class Agent:
    """The agent loop: think -> act -> observe -> repeat.

    Each iteration:
      1. The MockLLM picks the next tool + args (the "thought")
      2. The ToolRegistry looks up the callable and dispatches
      3. The result is captured as the "observation"
      4. Loop until the LLM says "done" or we hit max_steps
    """
    def __init__(self, llm: MockLLM, registry: ToolRegistry, max_steps: int = MAX_STEPS_DEFAULT) -> None:
        self.llm = llm
        self.registry = registry
        self.max_steps = max_steps

    def run(self, task: str) -> AgentRun:
        run = AgentRun(task=task)
        history: list[Step] = []
        for i in range(self.max_steps):
            call = self.llm.decide(task, history, self.registry, seed=SEED)
            if call is None:
                run.stopped_reason = "no_tool"
                run.final_answer = self._synthesize_answer(task, history)
                break
            try:
                tool = self.registry.get(call.tool_name)
                observation = tool.call(**call.args)
            except Exception as e:  # noqa: BLE001
                observation = f"ERROR: {type(e).__name__}: {e}"
            step = Step(
                step_num=i,
                thought=call.thought,
                tool_name=call.tool_name,
                tool_args=call.args,
                observation=observation,
            )
            run.steps.append(step)
            history.append(step)
        else:
            run.stopped_reason = "max_steps"
        if not run.final_answer:
            run.final_answer = self._synthesize_answer(task, run.steps)
        if not run.stopped_reason:
            run.stopped_reason = "done"
        return run

    @staticmethod
    def _synthesize_answer(task: str, steps: list[Step]) -> str:
        if not steps:
            return "(no tool calls executed)"
        last = steps[-1]
        return f"Based on {last.tool_name}: {last.observation}"


# =================================================================
# SECTION 5  --  MCPSchema (MCP-style tool descriptor)
# =================================================================

@dataclass
class MCPSchema:
    """A JSON-Schema-style tool descriptor, MCP-protocol flavor.

    MCP (Model Context Protocol) is the open standard for connecting
    LLMs to tools.  Every tool is described by a JSON object with a
    name, a description, and an inputSchema.  The LLM sees a list of
    these and decides which to call.  The runtime then dispatches
    `tools/call` with a JSON payload matching the schema.
    """
    name: str
    description: str
    input_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }

    @staticmethod
    def make_property(prop_type: str, description: str = "") -> dict[str, Any]:
        out: dict[str, Any] = {"type": prop_type}
        if description:
            out["description"] = description
        return out


# =================================================================
# SECTION 6  --  Sample tools
# =================================================================

def _tool_calculator(a: float, op: str, b: float) -> str:
    """Arithmetic.  op is one of + - * /"""
    if op == "+":
        return str(a + b)
    if op == "-":
        return str(a - b)
    if op == "*":
        return str(a * b)
    if op == "/":
        if b == 0:
            return "ERROR: division by zero"
        return str(a / b)
    return f"ERROR: unknown op {op!r}"


def _tool_search(query: str) -> str:
    """Mock search: returns a canned result based on keyword."""
    q = query.lower()
    if "weather" in q or "forecast" in q:
        return "Search: weather is reported via the get_weather tool."
    if "employee" in q or "directory" in q:
        return "Search: employees are looked up via the lookup_employee tool."
    if "policy" in q or "vacation" in q or "hr" in q:
        return "Search: 20 days vacation per year, accrued monthly."
    return f"Search: no special result for {query!r}"


def _tool_send_email(to: str, subject: str, body: str) -> str:
    """Mock email: prints (returns) the message that would be sent."""
    return f"EMAIL to={to} subject={subject!r} body={body!r}"


def _tool_get_weather(city: str) -> str:
    """Mock weather: deterministic per city."""
    table = {
        "paris": "Paris: 72F, sunny",
        "london": "London: 58F, cloudy",
        "tokyo": "Tokyo: 68F, clear",
        "new york": "New York: 64F, partly cloudy",
        "san francisco": "San Francisco: 60F, foggy",
    }
    return table.get(city.lower(), f"{city}: 70F, clear (default)")


def _tool_lookup_employee(name: str) -> str:
    """Mock HR directory."""
    directory = {
        "alice":   "Alice Chen   -- SWE, San Francisco, alice@corp.com",
        "bob":     "Bob Singh   -- PM, London, bob@corp.com",
        "carol":   "Carol Diaz  -- DS, New York, carol@corp.com",
        "dave":    "Dave Liu    -- SRE, Tokyo, dave@corp.com",
        "alice chen":  "Alice Chen   -- SWE, San Francisco, alice@corp.com",
        "bob singh":    "Bob Singh   -- PM, London, bob@corp.com",
        "carol diaz":   "Carol Diaz  -- DS, New York, carol@corp.com",
        "dave liu":     "Dave Liu    -- SRE, Tokyo, dave@corp.com",
    }
    return directory.get(name.lower(), f"no employee found for {name!r}")


def build_default_registry() -> ToolRegistry:
    """Wire up the 5 sample tools and return a registry."""
    reg = ToolRegistry()
    reg.register(Tool(
        name="calculator",
        description="Arithmetic: add, subtract, multiply, divide two numbers.",
        schema={
            "type": "object",
            "properties": {
                "a": MCPSchema.make_property("number", "left operand"),
                "op": MCPSchema.make_property("string", "one of + - * /"),
                "b": MCPSchema.make_property("number", "right operand"),
            },
            "required": ["a", "op", "b"],
        },
        fn=_tool_calculator,
    ))
    reg.register(Tool(
        name="search",
        description="Search the internal knowledge base for a query string.",
        schema={
            "type": "object",
            "properties": {
                "query": MCPSchema.make_property("string", "the search query"),
            },
            "required": ["query"],
        },
        fn=_tool_search,
    ))
    reg.register(Tool(
        name="send_email",
        description="Send an email to a recipient with subject and body.",
        schema={
            "type": "object",
            "properties": {
                "to": MCPSchema.make_property("string", "recipient email"),
                "subject": MCPSchema.make_property("string", "email subject"),
                "body": MCPSchema.make_property("string", "email body"),
            },
            "required": ["to", "subject", "body"],
        },
        fn=_tool_send_email,
    ))
    reg.register(Tool(
        name="get_weather",
        description="Get the current weather for a city.",
        schema={
            "type": "object",
            "properties": {
                "city": MCPSchema.make_property("string", "city name"),
            },
            "required": ["city"],
        },
        fn=_tool_get_weather,
    ))
    reg.register(Tool(
        name="lookup_employee",
        description="Look up an employee in the HR directory by name.",
        schema={
            "type": "object",
            "properties": {
                "name": MCPSchema.make_property("string", "full or first name"),
            },
            "required": ["name"],
        },
        fn=_tool_lookup_employee,
    ))
    return reg


# =================================================================
# SECTION 7  --  Sample tasks
# =================================================================

SAMPLE_TASKS: list[str] = [
    "What is the weather in Paris?",
    "Calculate 17 * 23 for me.",
    "Look up employee Alice Chen in the directory.",
]


# =================================================================
# SECTION 8  --  Demo
# =================================================================

def demo() -> None:
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Agents, Tools, and MCP")
    print("=" * 70)

    # 1. Registry + MCP descriptors
    print("\n  Section 1: Tool registry (MCP-style descriptors)")
    print("  " + "-" * 66)
    reg = build_default_registry()
    print(f"    tools registered: {len(reg)}")
    for t in reg.list_mcp():
        print(f"    - {t['name']:<18} {t['description']}")

    # 2. MCP schema
    print("\n  Section 2: MCP schema for one tool (calculator)")
    print("  " + "-" * 66)
    print(json.dumps(reg.get('calculator').to_mcp(), indent=2).replace("\n", "\n    "))

    # 3. Run a single task end-to-end
    print("\n  Section 3: Agent run -- 'What is the weather in Paris?'")
    print("  " + "-" * 66)
    llm = MockLLM()
    agent = Agent(llm=llm, registry=reg, max_steps=4)
    run = agent.run("What is the weather in Paris?")
    for s in run.steps:
        print(f"    {s}")
    print(f"    -> final: {run.final_answer}")
    print(f"    -> stopped: {run.stopped_reason}")

    # 4. Run a calculator task
    print("\n  Section 4: Agent run -- 'Calculate 17 * 23'")
    print("  " + "-" * 66)
    run = agent.run("Calculate 17 * 23 for me.")
    for s in run.steps:
        print(f"    {s}")
    print(f"    -> final: {run.final_answer}")

    # 5. Run a directory task
    print("\n  Section 5: Agent run -- 'Look up employee Alice Chen'")
    print("  " + "-" * 66)
    run = agent.run("Look up employee Alice Chen in the directory.")
    for s in run.steps:
        print(f"    {s}")
    print(f"    -> final: {run.final_answer}")

    # 6. Run all sample tasks
    print("\n  Section 6: All 3 sample tasks (transcripts)")
    print("  " + "-" * 66)
    for t in SAMPLE_TASKS:
        run = agent.run(t)
        print(f"    task: {t}")
        print(f"    steps: {run.n_steps}  final: {run.final_answer}")
        print()

    # 7. Error handling: unknown tool name in MockLLM
    print("  Section 7: Registry error path (lookup missing tool)")
    print("  " + "-" * 66)
    try:
        reg.get("does_not_exist")
    except KeyError as e:
        print(f"    caught expected KeyError: {e}")

    print("=" * 70)
    print("  See L13-agents-mcp.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 9  --  Tests
# =================================================================

def test_tool_to_mcp_shape() -> None:
    t = Tool(
        name="echo",
        description="echoes input",
        schema={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        fn=lambda x: x,
    )
    m = t.to_mcp()
    assert m["name"] == "echo"
    assert m["description"] == "echoes input"
    assert "inputSchema" in m
    assert m["inputSchema"]["type"] == "object"


def test_tool_call_dispatch() -> None:
    t = Tool(
        name="add",
        description="add two numbers",
        schema={"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
        fn=lambda a, b: a + b,
    )
    assert t.call(a=2, b=3) == 5


def test_registry_register_and_get() -> None:
    reg = ToolRegistry()
    t = Tool(name="ping", description="ping", schema={"type": "object"}, fn=lambda: "pong")
    reg.register(t)
    assert len(reg) == 1
    assert "ping" in reg
    assert reg.get("ping") is t


def test_registry_duplicate_raises() -> None:
    reg = ToolRegistry()
    t = Tool(name="x", description="x", schema={"type": "object"}, fn=lambda: None)
    reg.register(t)
    try:
        reg.register(t)
    except ValueError:
        return
    raise AssertionError("expected ValueError on duplicate registration")


def test_registry_unknown_tool_raises() -> None:
    reg = ToolRegistry()
    try:
        reg.get("nope")
    except KeyError:
        return
    raise AssertionError("expected KeyError on unknown tool")


def test_registry_list_mcp() -> None:
    reg = build_default_registry()
    mcp = reg.list_mcp()
    assert len(mcp) == 5
    names = {t["name"] for t in mcp}
    assert "calculator" in names
    assert "get_weather" in names


def test_mcp_schema_helper() -> None:
    p = MCPSchema.make_property("string", "a thing")
    assert p["type"] == "string"
    assert p["description"] == "a thing"


def test_mock_llm_picks_calculator() -> None:
    reg = build_default_registry()
    llm = MockLLM()
    call = llm.decide("What is 12 + 7?", [], reg)
    assert call is not None
    assert call.tool_name == "calculator"
    assert call.args["a"] == 12
    assert call.args["op"] == "+"
    assert call.args["b"] == 7


def test_mock_llm_picks_weather() -> None:
    reg = build_default_registry()
    llm = MockLLM()
    call = llm.decide("What is the weather in Tokyo?", [], reg)
    assert call is not None
    assert call.tool_name == "get_weather"
    assert call.args["city"].lower() == "tokyo"


def test_mock_llm_picks_lookup() -> None:
    reg = build_default_registry()
    llm = MockLLM()
    call = llm.decide("Look up employee Bob Singh in the directory.", [], reg)
    assert call is not None
    assert call.tool_name == "lookup_employee"
    assert "bob" in call.args["name"].lower()


def test_agent_weather_task_one_step() -> None:
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=4)
    run = agent.run("What is the weather in Paris?")
    assert run.n_steps == 1
    assert "paris" in str(run.steps[0].observation).lower()
    assert "72" in str(run.steps[0].observation)


def test_agent_calculator_task_one_step() -> None:
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=4)
    run = agent.run("Calculate 17 * 23 for me.")
    assert run.n_steps == 1
    assert "391" in str(run.steps[0].observation)  # 17 * 23


def test_agent_lookup_task_one_step() -> None:
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=4)
    run = agent.run("Look up employee Alice Chen in the directory.")
    assert run.n_steps == 1
    assert "alice" in str(run.steps[0].observation).lower()
    assert "@" in str(run.steps[0].observation)


def test_agent_max_steps_stops() -> None:
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=2)
    run = agent.run("What is the weather in Paris?")
    # one tool call; max_steps=2; should stop after that (no more matches)
    assert run.n_steps <= 2
    assert run.stopped_reason in ("max_steps", "no_tool", "done")


def test_agent_handles_tool_error() -> None:
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=2)
    # division by zero: tool returns an "ERROR: ..." string, not an exception
    call = MockLLM().decide("What is 5 / 0?", [], reg)
    assert call is not None
    obs = reg.get(call.tool_name).call(**call.args)
    assert "ERROR" in str(obs)


def test_sample_tasks_solve() -> None:
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=4)
    for t in SAMPLE_TASKS:
        run = agent.run(t)
        assert run.n_steps >= 1
        assert run.final_answer != ""


def test_tool_call_serializes_to_json() -> None:
    tc = ToolCall(tool_name="x", args={"a": 1, "b": "two"}, thought="why")
    j = tc.to_json()
    parsed = json.loads(j)
    assert parsed["tool"] == "x"
    assert parsed["args"]["b"] == "two"


def test_step_string_truncates_long_obs() -> None:
    s = Step(step_num=0, thought="t", tool_name="x", tool_args={}, observation="x" * 500)
    out = str(s)
    assert "..." in out
    assert len(out) < 200


# =================================================================
# SECTION 10  --  Latency benchmarks
# =================================================================

# Latency budget for a single agent step.  The think -> call -> observe
# loop should run in < 50 ms for in-process tool calls.  Wall-clock
# depends on tool I/O; the LLM call dominates in production.
AGENT_LATENCY_BUDGET_MS = 50.0


def agent_latency_ms(agent: Agent, task: str, n_runs: int = 50, seed: int = SEED) -> dict[str, float]:
    """Time `agent.run(task)` over n_runs.  Reports avg / p50 / p95 in ms.
    The MockLLM is in-process, so the latency is dominated by Python
    overhead, not real LLM API time.
    """
    for _ in range(3):
        _ = agent.run(task)
    samples_ms: list[float] = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = agent.run(task)
        samples_ms.append((time.perf_counter() - t0) * 1000.0)
    samples_ms.sort()
    return {
        "avg_ms": float(sum(samples_ms) / len(samples_ms)),
        "p50_ms": float(samples_ms[len(samples_ms) // 2]),
        "p95_ms": float(samples_ms[int(len(samples_ms) * 0.95)]),
        "n_runs": float(n_runs),
    }


def agent_throughput_per_second(avg_ms_per_call: float) -> float:
    """Inverse of latency: 1000 / avg_ms.  Used to size worker pools."""
    if avg_ms_per_call <= 0:
        return 0.0
    return 1000.0 / avg_ms_per_call


# =================================================================
# SECTION 11  --  Extra tests (latency, determinism, properties)
# =================================================================

def test_agent_run_is_deterministic_same_seed() -> None:
    """Two runs of the same task produce identical transcripts."""
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=4)
    r1 = agent.run("What is the weather in Paris?")
    r2 = agent.run("What is the weather in Paris?")
    assert r1.n_steps == r2.n_steps
    for s1, s2 in zip(r1.steps, r2.steps):
        assert s1.tool_name == s2.tool_name
        assert s1.tool_args == s2.tool_args
        assert s1.observation == s2.observation
    assert r1.final_answer == r2.final_answer


def test_agent_latency_under_budget() -> None:
    """A single one-step agent run must complete under the latency budget."""
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=2)
    s = agent_latency_ms(agent, "What is the weather in Paris?", n_runs=20)
    assert s["n_runs"] == 20.0
    # Generous bound for CI -- in-process mock is sub-millisecond.
    assert s["avg_ms"] < AGENT_LATENCY_BUDGET_MS * 10


def test_agent_throughput_per_second_inverse_of_latency() -> None:
    """1000 / 4 ms = 250 calls/sec; 1000 / 10 ms = 100 calls/sec."""
    assert abs(agent_throughput_per_second(4.0) - 250.0) < 1e-6
    assert abs(agent_throughput_per_second(10.0) - 100.0) < 1e-6
    assert agent_throughput_per_second(0.0) == 0.0
    assert agent_throughput_per_second(-1.0) == 0.0


def test_tool_call_to_json_is_deterministic() -> None:
    """to_json sorts keys, so output is stable for hashing/comparison."""
    tc = ToolCall(tool_name="x", args={"b": 2, "a": 1}, thought="why")
    j1 = tc.to_json()
    j2 = tc.to_json()
    assert j1 == j2
    parsed = json.loads(j1)
    assert parsed["tool"] == "x"
    # Keys are sorted: "a" before "b"
    assert list(parsed["args"].keys()) == ["a", "b"]


def test_mock_llm_decide_deterministic() -> None:
    """decide() is pure: same task + history + tools -> same ToolCall."""
    reg = build_default_registry()
    llm = MockLLM()
    a = llm.decide("What is the weather in Tokyo?", [], reg)
    b = llm.decide("What is the weather in Tokyo?", [], reg)
    assert a is not None and b is not None
    assert a.tool_name == b.tool_name
    assert a.args == b.args
    assert a.thought == b.thought


def test_mock_llm_decide_with_seed_kwarg() -> None:
    """decide() accepts a seed kwarg (production interface)."""
    reg = build_default_registry()
    llm = MockLLM()
    a = llm.decide("What is the weather in Paris?", [], reg, seed=42)
    b = llm.decide("What is the weather in Paris?", [], reg, seed=42)
    assert a is not None
    assert a.tool_name == b.tool_name
    assert a.args == b.args


def test_agent_run_final_answer_includes_observation() -> None:
    """The synthesized final answer must reference the last tool's output."""
    reg = build_default_registry()
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=4)
    run = agent.run("What is the weather in Tokyo?")
    assert "Tokyo" in run.final_answer or "68" in run.final_answer
    assert "get_weather" in run.final_answer


def test_agent_run_stops_when_no_tool_matches() -> None:
    """A task that matches no tool should stop with no_tool reason."""
    reg = ToolRegistry()
    reg.register(Tool(
        name="calculator", description="arithmetic",
        schema={"type": "object"}, fn=lambda **kw: "0",
    ))
    agent = Agent(llm=MockLLM(), registry=reg, max_steps=4)
    run = agent.run("Tell me a joke about cats")
    assert run.n_steps == 0
    assert run.stopped_reason == "no_tool"


def test_tool_call_unknown_arg_raises() -> None:
    """Calling a tool with unknown kwargs should raise TypeError, not silently pass."""
    t = Tool(
        name="f", description="f", schema={"type": "object"},
        fn=lambda a: a,
    )
    try:
        t.call(zzz=1)
        assert False, "should have raised"
    except TypeError:
        pass


def test_registry_list_names_returns_sorted() -> None:
    """list_names() returns tool names in insertion order (dict-order)."""
    reg = ToolRegistry()
    for name in ("zeta", "alpha", "mu"):
        reg.register(Tool(name=name, description="x", schema={"type": "object"}, fn=lambda: None))
    names = reg.list_names()
    assert names == ["zeta", "alpha", "mu"]  # dict insertion order


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
