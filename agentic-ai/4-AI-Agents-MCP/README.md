# AI Agents + MCP — study notes & reference links

> **A reading list and small working example for the
> Anthropic Model Context Protocol (MCP) and the agent
> patterns that ride on top of it.** Two references, one
> book, one repo. The protocol is small; the design
> space on top of it is large.

This directory is a **pointer**, not a project. It exists
to anchor two things in the portfolio:

1. The O'Reilly book *AI Agents with MCP* (the
   protocol-first framing of agents).
2. The
   [`kylestratis/ai_agents_mcp_examples`](https://github.com/kylestratis/ai_agents_mcp_examples)
   repo (the canonical small examples: host, client,
   tools, sampling).

The actual reference builds in this repo that use MCP
live elsewhere:

- [`../ai-agent/`](../ai-agent/) — Synapse, a working
  multi-agent system with four MCP servers.
- [`../8-swe-agent-devin-style/`](../8-swe-agent-devin-style/) —
  a Bedrock-Agents-style SWE agent with tool use.
- [`../../ai-engineering/03-multi-agent-platform/`](../../ai-engineering/03-multi-agent-platform/) —
  the production-shaped multi-agent platform with
  LangGraph, Bedrock, and shared memory.

---

## The two references

### 1. *AI Agents with MCP* (O'Reilly)

The book that names the pattern: an agent is a host
process that calls one or more MCP servers, each of which
exposes typed tools. The host holds the model; the
servers hold the tools. The protocol between them is
JSON-RPC.

- [Read online (O'Reilly Learning)](https://learning.oreilly.com/library/view/ai-agents-with/9798341639546/preface01.html#id58)
- The book's thesis: *MCP is to agents what LSP is to
  editors* — one protocol, many language servers, many
  editors. The same shape (one protocol, many tool
  servers, many hosts) maps directly to the agent world.

### 2. `kylestratis/ai_agents_mcp_examples`

A small, well-structured reference repo. The chapter 3
example ([`02_host_w_client_interface/agent.py`](https://github.com/kylestratis/ai_agents_mcp_examples/blob/main/ch3/02_host_w_client_interface/agent.py))
is the canonical "minimum viable MCP host" — a Python
agent that connects to one MCP server and calls one tool.

The shape:

```
   Host (the agent process)
     │
     │  JSON-RPC over stdio (or HTTP/SSE for remote)
     ▼
   MCP server (exposes typed tools)
     │
     ▼
   Tool implementation (Python function)
```

Three components, one protocol, one round-trip per call.
The rest of the design space is "what tools do you
expose, what does the host do with the response."

---

## What MCP actually gives you

Three primitives, all over the same JSON-RPC transport:

| Primitive | Direction | What it does |
|-----------|-----------|--------------|
| `tools/list` | Host → Server | Discover the tools a server exposes |
| `tools/call` | Host → Server | Invoke a tool with typed arguments |
| `resources/read` | Host → Server | Read a named resource (file, URL, DB row) |

The transport is **stdio** for local servers (the host
spawns the server as a subprocess) and **HTTP + SSE** for
remote servers (the server is a long-lived process the
host connects to).

The same `Tool` type is the same shape regardless of
transport. That's the whole point of the protocol — you
can swap a local stdio server for a remote HTTP one
without changing the host.

---

## What an MCP server looks like in practice

A minimal Python MCP server (using the official SDK):

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("weather")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(
        name="get_forecast",
        description="Get the weather forecast for a city",
        inputSchema={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "days": {"type": "integer", "default": 3},
            },
            "required": ["city"],
        },
    )]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_forecast":
        return [TextContent(type="text", text=f"Sunny, 72°F in {arguments['city']}")]
    raise ValueError(f"Unknown tool: {name}")
```

The host binds to this server at startup, sees one tool
(`get_forecast`), and can call it. The protocol is
already done; the work is the tool's business logic.

---

## How this maps to the portfolio

| Project | MCP role |
|---------|----------|
| [`../ai-agent/`](../ai-agent/) | 4 MCP servers (finance, media, weather, world_data) consumed by a Scout agent |
| [`../8-swe-agent-devin-style/`](../8-swe-agent-devin-style/) | Tools-as-MCP-servers: file system, shell, git, web fetch |
| [`../../ai-engineering/03-multi-agent-platform/`](../../ai-engineering/03-multi-agent-platform/) | MCP as the agent↔tool boundary in a production-shaped multi-agent build |

The pattern repeats. The protocol is stable; the tools
change per domain.

---

## What this is NOT

- **Not a tutorial.** This directory is the *reference
  pointer*. For a step-by-step build, follow the
  `kylestratis/ai_agents_mcp_examples` repo chapter by
  chapter, or read Synapse in [`../ai-agent/`](../ai-agent/).
- **Not a critique of MCP.** The protocol is the right
  shape; the design space on top of it (when to spawn
  many servers, when to compose them, when to inline the
  tool) is the actual interesting question.
- **Not a comprehensive agent framework comparison.**
  LangChain / LangGraph / CrewAI / AutoGen all support
  MCP to varying degrees. The book and the
  `kylestratis` repo are the MCP-first references; the
  framework-specific patterns live in their own docs.

---

## Related directories

- [`../ai-agent/`](../ai-agent/) — Synapse: 3 agents
  (Scout → Contextualist → Publisher) + 4 MCP servers.
  The most complete working example in this repo.
- [`../8-swe-agent-devin-style/`](../8-swe-agent-devin-style/) —
  a SWE agent where the tools (file system, shell, git,
  web fetch) are exposed as MCP servers.
- [`../../ai-engineering/03-multi-agent-platform/`](../../ai-engineering/03-multi-agent-platform/) —
  the production-shaped multi-agent platform: LangGraph
  orchestrator, Bedrock model, shared memory store.
- [`../../ai-engineering/`](../../ai-engineering/) —
  the parent AI-engineering directory (40 projects).
