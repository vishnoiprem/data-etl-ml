import os
from typing import List

from pydantic import BaseModel, Field
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.program.openai import OpenAIPydanticProgram
from llama_index.readers.wikipedia import WikipediaReader

from utils import get_apikey


class WikiPageList(BaseModel):
    pages: List[str] = Field(
        description="Exact Wikipedia page titles requested by the user"
    )


def wikipage_list(request_query: str) -> List[str]:
    os.environ["OPENAI_API_KEY"] = get_apikey()
    prompt_template_str = """
Extract only the Wikipedia page titles from the user's request.
Return each requested title once, preserving the user's wording.
Do not add pages that were not requested.

User request: {request_query}
"""
    program = OpenAIPydanticProgram.from_defaults(
        output_cls=WikiPageList,
        prompt_template_str=prompt_template_str,
        llm=OpenAI(model="gpt-5-nano", temperature=0),
        verbose=False,
    )
    result = program(request_query=request_query)
    pages = [page.strip() for page in result.pages if page.strip()]
    if not pages:
        raise ValueError("No Wikipedia page titles were found in the request.")
    return pages


def create_wikidocs(page_titles: List[str]):
    reader = WikipediaReader()
    documents = reader.load_data(pages=page_titles, auto_suggest=False)
    if not documents:
        raise ValueError("Wikipedia returned no documents for the requested pages.")
    return documents


def create_index(request_query: str) -> VectorStoreIndex:
    os.environ["OPENAI_API_KEY"] = get_apikey()
    page_titles = wikipage_list(request_query)
    documents = create_wikidocs(page_titles)

    parser = SentenceSplitter(chunk_size=150, chunk_overlap=45)
    nodes = parser.get_nodes_from_documents(documents)

    # Local sentence embeddings, as requested by the project specification.
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return VectorStoreIndex(nodes)


if __name__ == "__main__":
    request = input("Wikipedia pages (example: Please index: London, Birmingham): ")
    index = create_index(request)
    print(f"Index created successfully with {len(index.docstore.docs)} nodes.")
