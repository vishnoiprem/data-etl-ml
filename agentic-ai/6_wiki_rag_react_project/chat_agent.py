import os
import chainlit as cl
from chainlit.input_widget import Select, TextInput

from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.llms.openai import OpenAI

from index_wikipages import create_index
from utils import get_apikey

os.environ["OPENAI_API_KEY"] = get_apikey()


def wikisearch_engine(index):
    return index.as_query_engine(
        response_mode="compact",
        verbose=True,
        similarity_top_k=10,
    )


def create_react_agent(index, model_name: str):
    wikipedia_tool = QueryEngineTool(
        query_engine=wikisearch_engine(index),
        metadata=ToolMetadata(
            name="Wikipedia",
            description="Useful for performing searches on the indexed Wikipedia knowledge base.",
        ),
    )
    llm = OpenAI(model=model_name, temperature=0)
    return ReActAgent.from_tools(
        tools=[wikipedia_tool],
        llm=llm,
        verbose=True,
        max_iterations=10,
    )


async def configure_agent(settings: dict):
    request_query = settings.get("WIKIPAGES", "").strip()
    model_name = settings.get("MODEL", "gpt-5-nano")
    if not request_query:
        raise ValueError("Enter a request such as: Please index: 2023 United States banking crisis")

    status = cl.Message(content="Indexing the requested Wikipedia pages...")
    await status.send()
    index = await cl.make_async(create_index)(request_query)
    agent = create_react_agent(index, model_name)
    cl.user_session.set("agent", agent)
    await status.update(content="Wikipedia pages indexed. You can now ask grounded questions.")


@cl.on_chat_start
async def on_chat_start():
    settings = await cl.ChatSettings(
        [
            Select(
                id="MODEL",
                label="OpenAI model",
                values=["gpt-5-nano"],
                initial_index=0,
            ),
            TextInput(
                id="WIKIPAGES",
                label="Wikipedia pages",
                initial="Please index: 2023 United States banking crisis",
                placeholder="Please index: London, Birmingham, New York",
            ),
        ]
    ).send()
    try:
        await configure_agent(settings)
    except Exception as exc:
        await cl.Message(content=f"Setup failed: {exc}").send()


@cl.on_settings_update
async def setup_agent(settings):
    try:
        await configure_agent(settings)
    except Exception as exc:
        await cl.Message(content=f"Setup failed: {exc}").send()


@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    if agent is None:
        await cl.Message(content="Configure the Wikipedia pages in Settings first.").send()
        return

    try:
        response = await cl.make_async(agent.chat)(message.content)
        await cl.Message(content=str(response)).send()
    except Exception as exc:
        await cl.Message(content=f"The agent could not answer: {exc}").send()
