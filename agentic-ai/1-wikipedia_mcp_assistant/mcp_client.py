from __future__ import annotations

import asyncio
import os
import shlex
import sys
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing_extensions import TypedDict

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def text_from_prompt_message(message: object) -> str:
    content = getattr(message, "content", "")
    if hasattr(content, "text"):
        return str(content.text)
    return str(content)


def text_from_resource_content(content: object) -> str:
    if hasattr(content, "text"):
        return str(content.text)
    if hasattr(content, "blob"):
        return "[Binary resource returned]"
    return str(content)


async def create_graph(session: ClientSession):
    tools = await load_mcp_tools(session)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    llm = ChatOpenAI(model=model_name, temperature=0)
    tool_enabled_llm = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a Wikipedia research assistant. Use MCP tools for "
                "Wikipedia facts. Never invent article titles or sections. "
                "State clearly when a tool returns an error, ambiguity, or "
                "truncated content. Include the article URL when available.",
            ),
            MessagesPlaceholder("messages"),
        ]
    )
    chain = prompt | tool_enabled_llm

    async def chat_node(state: State):
        response = await chain.ainvoke({"messages": state["messages"]})
        return {"messages": [response]}

    builder = StateGraph(State)
    builder.add_node("chat", chat_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "chat")
    builder.add_conditional_edges("chat", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "chat")
    return builder.compile(checkpointer=MemorySaver())


async def list_prompts(session: ClientSession) -> None:
    response = await session.list_prompts()
    if not response.prompts:
        print("No prompts are registered.")
        return
    print("\nAvailable prompts:")
    for prompt in response.prompts:
        args = [arg.name for arg in (prompt.arguments or [])]
        print(f"  - {prompt.name}({', '.join(args)})")
    print('Usage: /prompt highlight_sections_prompt "Alan Turing"')


async def handle_prompt(
    session: ClientSession, agent: object, command: str, config: dict
) -> None:
    parts = shlex.split(command)
    if len(parts) < 3:
        print('Usage: /prompt <name> "argument values"')
        return

    prompt_name, values = parts[1], parts[2:]
    available = await session.list_prompts()
    definition = next((p for p in available.prompts if p.name == prompt_name), None)
    if definition is None:
        print(f"Unknown prompt: {prompt_name}")
        return

    argument_names = [arg.name for arg in (definition.arguments or [])]
    if len(values) != len(argument_names):
        print(f"Expected arguments: {argument_names}; received {len(values)} value(s).")
        return

    rendered = await session.get_prompt(
        prompt_name, arguments=dict(zip(argument_names, values))
    )
    rendered_text = "\n".join(text_from_prompt_message(m) for m in rendered.messages)
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=rendered_text)]}, config=config
    )
    print("\nAssistant:", result["messages"][-1].content)


async def list_resources(session: ClientSession) -> None:
    response = await session.list_resources()
    if not response.resources:
        print("No resources are registered.")
        return
    print("\nAvailable resources:")
    for index, resource in enumerate(response.resources, start=1):
        print(f"  {index}. {resource.name} -> {resource.uri}")
    print("Usage: /resource suggested_titles")


async def handle_resource(session: ClientSession, command: str) -> None:
    parts = shlex.split(command)
    if len(parts) != 2:
        print("Usage: /resource <name or number>")
        return

    response = await session.list_resources()
    resources = list(response.resources)
    token = parts[1]
    selected = None

    if token.isdigit() and 1 <= int(token) <= len(resources):
        selected = resources[int(token) - 1]
    else:
        selected = next((r for r in resources if r.name == token), None)

    if selected is None:
        print(f"Unknown resource: {token}")
        return

    result = await session.read_resource(selected.uri)
    print(f"\nResource: {selected.name}")
    for content in result.contents:
        print(text_from_resource_content(content))


async def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing. Copy .env.example to .env and add it.")

    server_path = BASE_DIR / "mcp_server.py"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        cwd=str(BASE_DIR),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            agent = await create_graph(session)
            config = {"configurable": {"thread_id": "wiki-session"}}

            print("\nWikipedia MCP assistant is ready.")
            print("Commands: /prompts, /prompt ..., /resources, /resource ..., /quit")

            while True:
                user_input = (await asyncio.to_thread(input, "\nYou: ")).strip()
                if not user_input:
                    continue
                if user_input.lower() in {"/quit", "quit", "exit", "q"}:
                    break

                try:
                    if user_input == "/prompts":
                        await list_prompts(session)
                    elif user_input.startswith("/prompt "):
                        await handle_prompt(session, agent, user_input, config)
                    elif user_input == "/resources":
                        await list_resources(session)
                    elif user_input.startswith("/resource "):
                        await handle_resource(session, user_input)
                    else:
                        result = await agent.ainvoke(
                            {"messages": [HumanMessage(content=user_input)]},
                            config=config,
                        )
                        print("\nAssistant:", result["messages"][-1].content)
                except Exception as exc:
                    print(f"Error: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
