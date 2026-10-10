# L6.1: The agent framework ecosystem — when to pick which

> **FDE framing in one line:** the framework choice is a config decision, not an architecture decision. LangChain for prototyping, LangGraph for stateful workflows, LlamaIndex for RAG-heavy agents, AutoGen for multi-agent conversations, CrewAI for role-based teams. The FDE picks the framework that matches the production pattern.

## The 3 things you'll learn

1. The 5 major agent frameworks in 2026: LangChain, LangGraph, LlamaIndex, AutoGen, CrewAI — and what each is best at.
2. The 4-axis framework-selection rubric: agent complexity, state management, RAG vs tool-use, team vs single-agent.
3. The "stdlib-only for prototypes, framework for production" pattern: ship the 200-line stdlib agent first, graduate to a framework when the requirements demand it.

## Concept

The agent framework ecosystem in 2026 has 5 major players, each with a different design philosophy. The FDE's framework choice is a config decision: the architecture (the 7 ingredients, the 5 guardrails, the topology) is invariant; the framework is the implementation. **The wrong choice is to pick the framework before the architecture; the right choice is to ship the stdlib-only 200-line agent first, then graduate to a framework when the requirements demand it.**

The 5 major frameworks:

1. **LangChain.** The first framework; the broadest ecosystem; the default for prototyping. LangChain provides the `AgentExecutor`, the tool registry, the memory backends, and 200+ integrations. Best for: prototypes, simple tool-using agents, RAG pipelines. Weak for: complex stateful workflows (use LangGraph instead), multi-agent conversations (use AutoGen instead).
2. **LangGraph.** A stateful agent framework built on top of LangChain. LangGraph provides the `StateGraph` primitive, conditional edges, interrupt points (for HITL), and human-in-the-loop. Best for: complex stateful workflows, multi-step agents with replanning, HITL approval flows. Weak for: simple tool-using agents (overkill), multi-agent conversations (use AutoGen).
3. **LlamaIndex.** A RAG-first framework. LlamaIndex provides the `QueryEngine`, the index abstractions, the data connectors, and the retrieval pipelines. Best for: RAG-heavy agents (the action space is dominated by retrieval). Weak for: tool-using agents without retrieval, multi-agent systems.
4. **AutoGen.** A multi-agent conversation framework from Microsoft. AutoGen provides the `GroupChat` primitive, the `UserProxyAgent`, and the conversation protocols. Best for: multi-agent conversations, debate-style agents, simulations. Weak for: production tool-using agents (debugging is hard), single-agent workflows.
5. **CrewAI.** A role-based team framework. CrewAI provides the `Crew`, the `Agent` with a `Role`, and the `Task` primitive. Best for: role-based multi-agent teams, hierarchical workflows. Weak for: complex stateful workflows (use LangGraph), RAG-heavy agents (use LlamaIndex).

The 4-axis framework-selection rubric:

1. **Agent complexity.** How complex is the agent? Simple (1-3 tools, 1-5 steps) → LangChain. Medium (4-7 tools, 5-10 steps with replanning) → LangGraph. Complex (10+ tools, hierarchical plans) → LangGraph + custom logic.
2. **State management.** How much state does the agent hold? Minimal (just the messages) → LangChain. Moderate (shared state across sub-agents) → LangGraph. Heavy (episodic memory + long-term vector) → LangChain + custom memory backend.
3. **RAG vs tool-use.** Is the agent RAG-heavy or tool-heavy? RAG-heavy → LlamaIndex. Tool-heavy → LangChain or LangGraph. Mixed → LangGraph.
4. **Team vs single-agent.** Is it a multi-agent system? Single-agent → LangChain. Multi-agent with conversation → AutoGen. Multi-agent with hierarchy → LangGraph or CrewAI.

The "stdlib-only for prototypes, framework for production" pattern is the FDE's primary design heuristic. The 200-line stdlib agent (from L6.2) is the prototype. The framework is the production implementation. The graduate triggers: (a) the agent has > 7 tools (the framework's tool registry is more robust), (b) the agent has complex state (the framework's memory backend is more robust), (c) the team needs to maintain the code (the framework's abstractions are more familiar).

## The pattern

The framework-selection decision rubric:

```python
def pick_framework(requirements: dict) -> str:
    """Pick the agent framework based on the production requirements."""
    complexity = requirements.get("complexity", "simple")  # simple | medium | complex
    state_mgmt = requirements.get("state_management", "minimal")  # minimal | moderate | heavy
    rag_vs_tools = requirements.get("rag_vs_tools", "tools")  # rag | tools | mixed
    team_vs_single = requirements.get("team_vs_single", "single")  # single | team

    if team_vs_single == "team" and requirements.get("conversation_heavy", False):
        return "autogen"  # Multi-agent conversations
    if team_vs_single == "team" and requirements.get("role_based", False):
        return "crewai"  # Role-based teams
    if rag_vs_tools == "rag":
        return "llamaindex"  # RAG-heavy
    if state_mgmt in ("moderate", "heavy") or complexity in ("medium", "complex"):
        return "langgraph"  # Stateful workflows
    return "langchain"  # Default for simple tool-using agents
```

The stdlib-only prototype that precedes the framework choice:

```python
# 200-line stdlib agent (from L6.2)
# The FDE writes this first, tests it, then graduates to a framework
# if the requirements demand it.
PROTOTYPE_AGENT = SingleAgent(
    model=Model("gpt-5-mini", openai_chat, PRICING["gpt-5-mini"]),
    tools=ToolRegistry([...]),
    memory=Memory(),
    cost=CostCeiling(max_run_usd=0.10),
    system_prompt=CS_DRAFTER_SYSTEM_PROMPT,
)

# After 4 weeks of production usage, evaluate:
# - Tool count > 7? -> Graduate to LangGraph
# - Complex state (episodic memory)? -> Graduate to LangChain + custom memory
# - RAG-heavy (the action space is dominated by retrieval)? -> Graduate to LlamaIndex
# - Multi-agent with conversation? -> Graduate to AutoGen
# - Multi-agent with role-based hierarchy? -> Graduate to CrewAI
# - All of the above are "no"? -> Stay with the stdlib agent (it's simpler)
```

The pattern that wins interviews is the "stdlib first, graduate when needed" pattern. The candidate who says "I ship the 200-line stdlib agent first. I measure the production requirements: tool count, state complexity, RAG-vs-tool ratio, team-vs-single. I graduate to a framework only when the requirements demand it. The framework choice is a config decision, not an architecture decision. The wrong choice is to pick LangChain before writing the 200-line agent (over-engineering, 5× complexity). The right choice is stdlib first, then graduate" is the candidate who demonstrates the framework-mindset.

## Code or example

The 5 frameworks compared on a canonical CS-drafter use case:

```python
# LangChain (simple tool-using agent)
from langchain.agents import AgentExecutor, create_react_agent
lc_agent = AgentExecutor(agent=create_react_agent(llm, tools, prompt), tools=tools)
result = lc_agent.invoke({"input": email})  # 1 line

# LangGraph (stateful workflow with replanning)
from langgraph.graph import StateGraph, END
graph = StateGraph(SupportState)
graph.add_node("lookup", lookup_node)
graph.add_node("classify", classify_node)
graph.add_node("draft", draft_node)
graph.add_conditional_edges("lookup", lambda s: "classify" if s.shipment else "clarify", {...})
app = graph.compile()
result = app.invoke({"email": email})  # 10 lines for the graph

# LlamaIndex (RAG-heavy)
from llama_index.core import VectorStoreIndex
index = VectorStoreIndex.from_documents(documents)
rag_engine = index.as_query_engine()
result = rag_engine.query("What is the refund policy for damaged packages?")  # 1 line

# AutoGen (multi-agent conversation)
from autogen import GroupChat, ConversableAgent
cs_agent = ConversableAgent("cs", system_message=CS_PROMPT, llm_config=llm_config)
ops_agent = ConversableAgent("ops", system_message=OPS_PROMPT, llm_config=llm_config)
group = GroupChat([cs_agent, ops_agent], messages=[])
result = cs_agent.initiate_chat(ops_agent, message=email)  # 5 lines for the group

# CrewAI (role-based team)
from crewai import Crew, Agent, Task
cs_agent = Agent(role="CS Drafter", goal="Draft replies", backstory=CS_BACKSTORY)
ops_agent = Agent(role="Ops Summarizer", goal="Summarize shipments", backstory=OPS_BACKSTORY)
task = Task(description=f"Draft reply to: {email}", agent=cs_agent)
crew = Crew(agents=[cs_agent, ops_agent], tasks=[task])
result = crew.kickoff()  # 5 lines for the crew
```

The framework graduation triggers (the FDE's decision tree):

```python
GRADUATION_TRIGGERS = {
    "tool_count": "> 7",                    # LangGraph for context isolation
    "complex_state": "shared across sub-agents",  # LangGraph for state management
    "rag_heavy": "action space dominated by retrieval",  # LlamaIndex
    "multi_agent_conversation": "agents debate / chat",  # AutoGen
    "multi_agent_role_based": "agents have distinct roles",  # CrewAI or LangGraph
    "hitl_required": "interrupts for human approval",  # LangGraph
    "replanning_required": "observations contradict plan",  # LangGraph
}
```

## Production addendum

The framework question is the answer to "which agent framework do you use." The 60-second script:

> "Stdlib first, framework when needed. Ship the 200-line stdlib agent. Measure the production requirements: tool count, state complexity, RAG-vs-tool ratio, team-vs-single. Graduate to a framework when the requirements demand it. **The framework choice is a config decision, not an architecture decision.** LangChain for simple tool-using agents. LangGraph for stateful workflows with replanning and HITL. LlamaIndex for RAG-heavy. AutoGen for multi-agent conversations. CrewAI for role-based teams. The wrong choice is to pick LangChain before writing the stdlib agent (over-engineering, 5× complexity). The right choice is stdlib first, then graduate based on requirements."

This is the difference between a candidate who says "I used LangChain" and a candidate who says "stdlib first, graduated to LangGraph when tool count exceeded 7 and HITL was required." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-4-langgraph.py` — the LangGraph StateGraph with 6 nodes.
- **Reference implementation**: `course/hardcode/level-5-agentic-workflows/09-react-agent-tools.py` — the stdlib production agent.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/10-framework-choice.md` — the framework as a config decision.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/02-multi-agent-dispatcher/` — the production orchestrator uses LangGraph patterns.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — framework choice as a system design decision.

## The 3 questions this lecture preps you for

1. **"Which agent framework do you use?"** Answer: depends on the production requirements. LangChain for simple tool-using agents (default for prototypes). LangGraph for stateful workflows with replanning and HITL. LlamaIndex for RAG-heavy. AutoGen for multi-agent conversations. CrewAI for role-based teams. The FDE ships the 200-line stdlib agent first and graduates to a framework when the requirements demand it.
2. **"When do you graduate from stdlib to a framework?"** Answer: when one of 6 triggers fires — tool count > 7, complex state across sub-agents, RAG-heavy, multi-agent conversation, multi-agent role-based, or HITL required. The framework's abstractions are more familiar to the team; the stdlib agent is more transparent. The graduation is a one-way door; once on a framework, the team rarely goes back.
3. **"What is the difference between LangChain and LangGraph?"** Answer: LangChain is the broader ecosystem (tools, memory, integrations) with a simple `AgentExecutor`; LangGraph is the stateful workflow framework built on top of LangChain, with `StateGraph`, conditional edges, interrupt points, and HITL. Use LangChain for simple tool-using agents; use LangGraph when the agent has complex state, replanning, or HITL.

## Read next

`L6-2-building-the-minimum-viable-agent.md` — the 200-line shipping agent. The 7 ingredients + 5 guardrails in 200 lines of stdlib Python. The prototype that precedes the framework choice.