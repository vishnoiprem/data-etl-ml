from typing import List

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.wikipedia import WikipediaReader

# Local embeddings only: indexing makes no OpenAI call at all.
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def wikipage_list(request_query: str) -> List[str]:
    """Pull page titles out of a request like 'Please index: London, Paris'."""
    text = request_query.split(":", 1)[-1] if ":" in request_query else request_query
    pages = [title.strip() for title in text.split(",") if title.strip()]
    if not pages:
        raise ValueError("No Wikipedia page titles were found in the request.")
    return pages


def create_wikidocs(page_titles: List[str]):
    documents = WikipediaReader().load_data(pages=page_titles, auto_suggest=False)
    if not documents:
        raise ValueError("Wikipedia returned no documents for the requested pages.")
    return documents


def create_index(request_query: str) -> VectorStoreIndex:
    page_titles = wikipage_list(request_query)
    documents = create_wikidocs(page_titles)

    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    nodes = SentenceSplitter(chunk_size=150, chunk_overlap=45).get_nodes_from_documents(
        documents
    )
    return VectorStoreIndex(nodes)


if __name__ == "__main__":
    request = input("Wikipedia pages (example: Please index: London, Birmingham): ")
    index = create_index(request)
    print(f"Index created successfully with {len(index.docstore.docs)} nodes.")
