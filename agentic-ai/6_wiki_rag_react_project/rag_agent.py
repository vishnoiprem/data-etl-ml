"""The RAG core, with no UI attached.

Every entry point (Chainlit app, FastAPI host, plain script) imports from here,
so the retrieval and agent behaviour is defined in exactly one place.
"""

import os

from llama_index.core import VectorStoreIndex
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.llms.openai import OpenAI

from index_wikipages import create_index
from utils import get_apikey

# Models known to llama-index-llms-openai 0.1.x; "gpt-5-*" is rejected by it.
MODELS = ["gpt-4o-mini", "gpt-4o"]

# The OpenAI client reads the key from the environment at call time.
os.environ["OPENAI_API_KEY"] = get_apikey()


def wikisearch_engine(index: VectorStoreIndex):
    """Retriever + synthesiser: the thing that actually searches the index."""
    return index.as_query_engine(
        response_mode="compact",
        verbose=True,
        similarity_top_k=10,
    )


def create_react_agent(index: VectorStoreIndex, model_name: str = MODELS[0]) -> ReActAgent:
    """Wrap the query engine as a tool and give it to a ReAct agent."""
    wikipedia_tool = QueryEngineTool(
        query_engine=wikisearch_engine(index),
        metadata=ToolMetadata(
            name="Wikipedia",
            description="Useful for performing searches on the indexed Wikipedia knowledge base.",
        ),
    )
    return ReActAgent.from_tools(
        tools=[wikipedia_tool],
        llm=OpenAI(model=model_name, temperature=0),
        verbose=True,
        max_iterations=10,
    )


def build_agent(request_query: str, model_name: str = MODELS[0]) -> ReActAgent:
    """Index the requested pages and return a ready-to-chat agent.

    This is the one call a host needs: everything before it is retrieval setup,
    everything after it is `agent.chat(question)`.
    """
    index = create_index(request_query)
    return create_react_agent(index, model_name)
