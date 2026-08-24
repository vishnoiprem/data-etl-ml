import os

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

import boto3
# NOTE: this venv runs LangChain v1, where the legacy RetrievalQA chain and the
# conversation-memory classes moved out of the `langchain` package into
# `langchain_classic`. Prompts now live in `langchain_core`.
from langchain_classic.chains import RetrievalQA
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_aws import AmazonKnowledgeBasesRetriever, ChatBedrock

import config

# Define constants -- sourced from aws.env, never hardcoded here
KNOWLEDGE_BASE_ID = config.KNOWLEDGE_BASE_ID

# ------------------------------------------------------
# Helper functions


def get_bedrock_client():
    """Initialize the Bedrock client."""
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        **config.BOTO_KWARGS,
    )
    return bedrock_runtime


def create_retrieval_qa():
    """Create the RetrievalQA system."""
    model_id = config.MODEL_ID
    # Claude Haiku 4.5 rejects `temperature` and `top_p` together, so only
    # temperature is set here -- 0.0 keeps answers deterministic and grounded.
    model_kwargs = {
        "temperature": 0.0,
        "top_k": 250,
        "stop_sequences": ["\n\nHuman"],
    }

    # Prompt template -- keeps the model anchored to retrieved context instead of
    # answering from its own parametric knowledge.
    template = '''Answer the question based only on the following context:
    {context}

    Question: {question}

    Answer:'''

    prompt = PromptTemplate(template=template, input_variables=['context', 'question'])

    # Amazon Bedrock - KnowledgeBase Retriever.
    # Pass an explicit client: the retriever's own key arguments expect SecretStr, and
    # a client keeps credential handling identical to the generator below.
    retriever = AmazonKnowledgeBasesRetriever(
        knowledge_base_id=KNOWLEDGE_BASE_ID,
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
        client=boto3.client("bedrock-agent-runtime", **config.BOTO_KWARGS),
    )

    # Bedrock LLM integration
    bedrock_runtime = get_bedrock_client()
    llm = ChatBedrock(
        model_id=model_id,
        client=bedrock_runtime,
        max_tokens=512,
        model_kwargs=model_kwargs,
    )

    # ConversationBufferMemory to store chat history
    memory = ConversationBufferMemory(memory_key="chat_history")

    # Initialize RetrievalQA, wiring in the prompt above
    qa = RetrievalQA.from_llm(
        llm=llm,
        retriever=retriever,
        prompt=prompt,
        return_source_documents=True,  # Keep source documents in result
        memory=None,  # Memory management is handled separately
        output_key="result"
    )

    return qa, memory


def get_answer(query, qa, memory):
    """Get the answer for a query using the QA system."""
    result = qa.invoke({"query": query})
    # Save context manually
    memory.save_context({"query": query}, {"result": result["result"]})
    return result["result"]


if __name__ == "__main__":
    qa, memory = create_retrieval_qa()
    question = "What is SageMaker?"
    print("Q:", question)
    print("A:", get_answer(question, qa, memory))
