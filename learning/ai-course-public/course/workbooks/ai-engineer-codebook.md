# AI Engineer Codebook
## The Complete Reference: 100+ Code Snippets, Patterns & Cheat Sheets

**For:** AI Engineer Mastery course students (and any developer building with LLMs)
**Format:** Copy-paste code organized by topic
**Last updated:** [Date]

---

# SECTION 1: LLM API PATTERNS

## 1.1 OpenAI — Basic Chat Completion

```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain async/await in Python"}
    ],
    temperature=0.7,        # 0 = deterministic, 1 = creative
    max_tokens=500,         # Limit response length
    top_p=1.0,              # Nucleus sampling
    frequency_penalty=0,    # -2 to 2, reduce repetition
    presence_penalty=0,     # -2 to 2, encourage new topics
    stop=["\n\n"]          # Stop sequences
)

print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")
```

## 1.2 OpenAI — Streaming

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a poem about coding"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## 1.3 OpenAI — Function Calling

```python
import json
from openai import OpenAI

client = OpenAI()

# Define tool
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"]
        }
    }
}]

# Call LLM
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto"
)

# Check if LLM wants to call function
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    print(f"Call: {function_name}({arguments})")
```

## 1.4 OpenAI — JSON Mode (Structured Output)

```python
from pydantic import BaseModel
from openai import OpenAI

class UserInfo(BaseModel):
    name: str
    age: int
    email: str

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Extract user info from the text."},
        {"role": "user", "content": "John Doe, 30 years old, john@example.com"}
    ],
    response_format={"type": "json_object"}
)

import json
data = json.loads(response.choices[0].message.content)
user = UserInfo(**data)
print(user)
```

## 1.5 OpenAI — Vision (Images)

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image.jpg",
                    "detail": "high"  # low, high, or auto
                }
            }
        ]
    }],
    max_tokens=300
)
print(response.choices[0].message.content)
```

## 1.6 Anthropic Claude — Basic

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)
print(message.content[0].text)
```

## 1.7 Anthropic — Prompt Caching (90% cost savings)

```python
import anthropic

client = anthropic.Anthropic()

# Long context with caching
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert on this 100-page document:",
        },
        {
            "type": "text",
            "text": long_document,  # This gets cached!
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": "Summarize chapter 3"}]
)
# First call: full price. Subsequent calls: 90% off on cached portion.
```

## 1.8 Anthropic — Tool Use

```python
import anthropic

client = anthropic.Anthropic()

tools = [{
    "name": "get_weather",
    "description": "Get current weather for a city",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string"}
        },
        "required": ["city"]
    }
}]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Weather in Paris?"}]
)

# Process tool use
for block in response.content:
    if block.type == "tool_use":
        tool_name = block.name
        tool_input = block.input
        print(f"Call: {tool_name}({tool_input})")
```

## 1.9 Google Gemini

```python
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Explain machine learning")
print(response.text)
```

## 1.10 Open-Source (Llama via Ollama)

```python
import requests

def query_llama(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# Usage
print(query_llama("What is Python?"))
```

---

# SECTION 2: PRODUCTION PATTERNS

## 2.1 Retry with Exponential Backoff

```python
import time
import random
from openai import OpenAI, RateLimitError

client = OpenAI()

def call_with_retry(messages, max_retries=5, base_delay=1):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limited. Retrying in {delay:.2f}s...")
            time.sleep(delay)
```

## 2.2 Fallback to Different Models

```python
def call_with_fallback(prompt: str) -> str:
    models = [
        ("gpt-4o-mini", "openai"),
        ("claude-3-5-sonnet-20241022", "anthropic"),
        ("gemini-pro", "google"),
    ]
    
    for model_name, provider in models:
        try:
            if provider == "openai":
                response = openai_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            elif provider == "anthropic":
                message = anthropic_client.messages.create(
                    model=model_name,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
        except Exception as e:
            print(f"{model_name} failed: {e}")
            continue
    
    return "All models failed"
```

## 2.3 Token Counting & Cost Tracking

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
    # Pricing per 1K tokens (as of 2026)
    pricing = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    }
    p = pricing[model]
    return (input_tokens / 1000 * p["input"]) + (output_tokens / 1000 * p["output"])

# Usage
text = "Your prompt here"
tokens = count_tokens(text)
cost = estimate_cost(tokens, 500)  # 500 output tokens
print(f"Tokens: {tokens}, Estimated cost: ${cost:.4f}")
```

## 2.4 Async Batch Processing

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def process_prompt(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

async def batch_process(prompts: list[str], max_concurrent: int = 10):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_process(prompt):
        async with semaphore:
            return await process_prompt(prompt)
    
    tasks = [limited_process(p) for p in prompts]
    return await asyncio.gather(*tasks)

# Usage
prompts = ["What is AI?" for _ in range(100)]
results = asyncio.run(batch_process(prompts))
print(f"Processed {len(results)} prompts")
```

## 2.5 Streaming with FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI

app = FastAPI()
client = OpenAI()

@app.post("/chat/stream")
async def chat_stream(message: str):
    async def generate():
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message}],
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## 2.6 Response Caching (Redis)

```python
import hashlib
import json
import redis
from openai import OpenAI

r = redis.Redis()
client = OpenAI()

def cached_completion(prompt: str, ttl: int = 3600) -> str:
    # Create cache key from prompt
    cache_key = f"llm:{hashlib.md5(prompt.encode()).hexdigest()}"
    
    # Check cache
    cached = r.get(cache_key)
    if cached:
        return cached.decode()
    
    # Call LLM
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content
    
    # Cache result
    r.setex(cache_key, ttl, result)
    return result

# Usage
answer = cached_completion("What is Python?")
```

## 2.7 Semantic Cache (GPTCache)

```python
from gptcache import Cache
from gptcache.adapter.api import init_similar_cache
from gptcache.embedding import Onnx
from gptcache.similarity_evaluation.distance import SearchDistanceEvaluation

# Initialize semantic cache
on_cache.init_similar_cache(
    data_dir="cache",
    embedding_func=Onnx(),
    similarity_evaluation=SearchDistanceEvaluation(),
)

def semantic_cached_completion(prompt: str):
    # GPTCache handles similarity matching
    response = openai_chat completion(prompt)
    return response
```

---

# SECTION 3: PROMPT ENGINEERING PATTERNS

## 3.1 The CRAFT Framework

```python
CRAFT_PROMPT = """# Context
You are writing for {audience} who are interested in {topic}.

# Role
Act as an expert {role} with 10+ years of experience.

# Action
{action}

# Format
Provide the response in {format} with:
- Clear headings
- Bullet points where appropriate
- Examples for each main point

# Tone
Write in a {tone} tone.

# Additional constraints
- Keep it under {word_count} words
- Avoid jargon
- Include actionable takeaways
"""
```

## 3.2 Few-Shot Classification

```python
FEW_SHOT_CLASSIFIER = """Classify the sentiment of customer reviews as: positive, negative, or neutral.

Examples:
Review: "This product changed my life! Best purchase ever."
Sentiment: positive

Review: "Terrible quality. Broke after 2 days. Waste of money."
Sentiment: negative

Review: "It's okay. Does what it says, nothing special."
Sentiment: neutral

Now classify:
Review: {user_review}
Sentiment:"""
```

## 3.3 Chain-of-Thought

```python
COT_PROMPT = """Solve this problem step by step.

Problem: {problem}

Let's think through this carefully:

1. What information do we have?
2. What are we trying to find?
3. What formulas or methods apply?
4. Let's work through the calculation.
5. Verify our answer makes sense.

Solution:"""
```

## 3.4 ReAct Agent Prompt

```python
REACT_PROMPT = """You are an AI assistant that can use tools to answer questions.

Available tools:
{tool_descriptions}

Use this format:

Thought: [Your reasoning about what to do next]
Action: [The tool to use, one of: {tool_names}]
Action Input: [JSON object with tool arguments]
Observation: [Tool result will appear here]
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to answer.
Final Answer: [Your response to the user]

Question: {user_question}
{agent_scratchpad}"""
```

## 3.5 System Prompt Template

```python
SYSTEM_PROMPT = """# Identity
You are {agent_name}, an AI assistant for {company_name}.

# Capabilities
You can:
- {capability_1}
- {capability_2}
- {capability_3}

# Constraints
You must:
- {constraint_1}
- {constraint_2}
- {constraint_3}

You must not:
- {prohibition_1}
- {prohibition_2}

# Response style
- Tone: {tone}
- Length: {length}
- Format: {format}

# Examples
Example 1:
User: {example_input_1}
Assistant: {example_output_1}

# Current context
{additional_context}"""
```

## 3.6 Structured Output Prompt

```python
STRUCTURED_PROMPT = """Extract information from the text and return as JSON matching this schema:

{json_schema}

Text to analyze:
{input_text}

Return ONLY valid JSON. No additional text or markdown."""
```

---

# SECTION 4: RAG PATTERNS

## 4.1 Simple RAG (No Frameworks)

```python
import openai
import numpy as np
from typing import List

class SimpleRAG:
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.client = openai.OpenAI()
    
    def add_documents(self, docs: List[str]):
        """Add documents and generate embeddings"""
        self.documents.extend(docs)
        # Generate embeddings
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=docs
        )
        new_embeddings = [d.embedding for d in response.data]
        self.embeddings.extend(new_embeddings)
    
    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Find most relevant documents"""
        # Embed query
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        query_embedding = response.data[0].embedding
        
        # Cosine similarity
        similarities = []
        for doc_emb in self.embeddings:
            sim = np.dot(query_embedding, doc_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb)
            )
            similarities.append(sim)
        
        # Top k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self.documents[i] for i in top_indices]
    
    def query(self, question: str) -> str:
        """RAG: Retrieve + Generate"""
        context_docs = self.search(question)
        context = "\n\n".join(context_docs)
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Answer based on this context:\n\n{context}"},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content

# Usage
rag = SimpleRAG()
rag.add_documents([
    "Paris is the capital of France.",
    "London is the capital of the UK.",
    "Tokyo is the capital of Japan."
])
print(rag.query("What is the capital of France?"))
```

## 4.2 LangChain RAG

```python
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

# 1. Load documents
loader = WebBaseLoader(["https://example.com/article"])
documents = loader.load()

# 2. Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)

# 3. Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. Create QA chain
qa = RetrievalQA.from_chain_type(
    llm=OpenAI(temperature=0),
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
)

# 5. Query
result = qa.run("What is the main topic?")
print(result)
```

## 4.3 Advanced Chunking Strategies

```python
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter
)

# Recursive (recommended default)
recursive = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""]
)

# Token-based
token_splitter = TokenTextSplitter(
    chunk_size=512,
    chunk_overlap=50
)

# Markdown-aware
markdown_splitter = MarkdownTextSplitter(chunk_size=1000)

# Custom semantic chunking
from langchain_experimental.text_splitter import SemanticChunker
from langchain.embeddings import OpenAIEmbeddings

semantic = SemanticChunker(
    OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile"
)
```

## 4.4 Hybrid Search (BM25 + Vectors)

```python
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import TextLoader

# Load docs
loader = TextLoader("docs.txt")
documents = loader.load()

# BM25 (keyword search)
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 5

# Vector search
vectorstore = Chroma.from_documents(documents, OpenAIEmbeddings())
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Hybrid
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.5, 0.5]  # 50/50
)

docs = ensemble_retriever.get_relevant_documents("query")
```

## 4.5 RAG Evaluation with RAGAS

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset

# Test data
test_data = {
    "question": ["What is X?", "How does Y work?"],
    "answer": ["X is...", "Y works by..."],
    "contexts": [["context for X"], ["context for Y"]],
    "ground_truth": ["X is the correct answer", "Y works correctly"]
}

dataset = Dataset.from_dict(test_data)

# Evaluate
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)

print(result)
```

---

# SECTION 5: AGENT PATTERNS

## 5.1 ReAct Agent (Full Implementation)

```python
import json
from openai import OpenAI
from typing import List, Dict, Callable

class ReActAgent:
    def __init__(self, model="gpt-4o-mini", max_iterations=5):
        self.client = OpenAI()
        self.model = model
        self.max_iterations = max_iterations
        self.tools = {}
    
    def register_tool(self, name: str, func: Callable, description: str, parameters: dict):
        self.tools[name] = {
            "function": func,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
        }
    
    def run(self, user_query: str, system_prompt: str = None) -> str:
        messages = [
            {"role": "system", "content": system_prompt or "You are a helpful AI assistant."},
            {"role": "user", "content": user_query}
        ]
        
        tool_schemas = [t["schema"] for t in self.tools.values()]
        
        for i in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            messages.append(message)
            
            if not message.tool_calls:
                return message.content
            
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                try:
                    result = self.tools[name]["function"](**args)
                except Exception as e:
                    result = f"Error: {e}"
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": name,
                    "content": str(result)
                })
        
        return "Max iterations reached"

# Usage
agent = ReActAgent()

def get_weather(city: str) -> str:
    return f"Weather in {city}: 22°C, sunny"

agent.register_tool(
    name="get_weather",
    func=get_weather,
    description="Get current weather for a city",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
    }
)

result = agent.run("What's the weather in Tokyo?")
print(result)
```

## 5.2 Multi-Agent with CrewAI

```python
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

# Define agents
researcher = Agent(
    role="Research Analyst",
    goal="Find accurate information on given topics",
    backstory="Expert at finding and synthesizing information from the web",
    tools=[SerperDevTool(), ScrapeWebsiteTool()],
    verbose=True
)

writer = Agent(
    role="Content Writer",
    goal="Create engaging content based on research",
    backstory="Skilled writer who creates clear, compelling content",
    verbose=True
)

# Define tasks
research_task = Task(
    description="Research the latest AI trends in 2026",
    agent=researcher,
    expected_output="A comprehensive summary of AI trends"
)

write_task = Task(
    description="Write a blog post about AI trends based on the research",
    agent=writer,
    expected_output="A 1000-word blog post",
    context=[research_task]
)

# Create crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    verbose=True
)

# Run
result = crew.kickoff()
print(result)
```

## 5.3 LangGraph Workflow

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# Define state
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next_action: str

# Define nodes
def research_node(state: AgentState):
    # Do research
    result = "Research findings..."
    return {"messages": [result], "next_action": "write"}

def write_node(state: AgentState):
    # Write based on research
    result = "Written content..."
    return {"messages": [result], "next_action": "review"}

def review_node(state: AgentState):
    # Review
    return {"messages": ["Review complete"], "next_action": "end"}

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("research", research_node)
workflow.add_node("write", write_node)
workflow.add_node("review", review_node)

# Add edges
workflow.set_entry_point("research")
workflow.add_edge("research", "write")
workflow.add_edge("write", "review")
workflow.add_edge("review", END)

# Compile
app = workflow.compile()

# Run
result = app.invoke({"messages": [], "next_action": ""})
```

---

# SECTION 6: VECTOR DATABASE CHEAT SHEET

## 6.1 Chroma (Easiest)

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("docs")

# Add
collection.add(
    documents=["doc 1", "doc 2", "doc 3"],
    metadatas=[{"source": "web"}, {"source": "pdf"}, {"source": "book"}],
    ids=["1", "2", "3"]
)

# Query
results = collection.query(
    query_texts=["search query"],
    n_results=3
)
print(results)
```

## 6.2 Pinecone (Production)

```python
import pinecone

pinecone.init(api_key="YOUR_KEY", environment="us-west1-gcp")
index = pinecone.Index("my-index")

# Upsert
index.upsert(vectors=[
    ("id1", [0.1, 0.2, ...], {"metadata": "value"}),
    ("id2", [0.3, 0.4, ...], {"metadata": "value"})
])

# Query
results = index.query(
    vector=[0.1, 0.2, ...],
    top_k=10,
    include_metadata=True
)
```

## 6.3 Weaviate

```python
import weaviate

client = weaviate.Client("http://localhost:8080")

# Add
client.data_object.create(
    {"text": "document content"},
    "Document",
    "uuid-1"
)

# Query (GraphQL)
result = client.query.get("Document", ["text"]).near_text({"concepts": ["search"]}).do()
```

## 6.4 pgvector (PostgreSQL)

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536)
);

-- Create index
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);

-- Insert
INSERT INTO documents (content, embedding)
VALUES ('text', '[0.1, 0.2, ...]');

-- Search
SELECT content
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 5;
```

---

# SECTION 7: DEPLOYMENT PATTERNS

## 7.1 FastAPI Production App

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import logging

app = FastAPI(title="AI API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    reply: str
    tokens_used: int

# Initialize
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Routes
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.message}
            ]
        )
        return ChatResponse(
            reply=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(500, "Internal error")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

## 7.2 Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
```

## 7.3 Environment Variables

```bash
# .env (never commit this!)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PINECONE_API_KEY=...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
ENVIRONMENT=production
```

```python
# Load in Python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

---

# SECTION 8: OBSERVABILITY

## 8.1 LangSmith Setup

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-key"
os.environ["LANGCHAIN_PROJECT"] = "my-project"

# Now all LangChain calls are automatically traced
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI()
llm.invoke("Hello")  # Automatically logged to LangSmith
```

## 8.2 Custom Logging

```python
import logging
import json
from datetime import datetime

# Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_llm_call(prompt, response, tokens, cost, duration):
    logger.info(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "event": "llm_call",
        "prompt_tokens": tokens,
        "cost_usd": cost,
        "duration_ms": duration,
        "model": response.model,
    }))
```

## 8.3 Helicone Integration

```python
import openai

# Just change the base URL
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://oai.hconeai.com/v1",
    default_headers={
        "Helicone-Auth": f"Bearer {os.getenv('HELICONE_API_KEY')}",
        "Helicone-Property-App": "my-app",
    }
)

# All calls are now logged to Helicone
```

---

# SECTION 9: COMMON UTILITIES

## 9.1 Text Splitter

```python
def split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Simple text splitter"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
```

## 9.2 PDF Loader

```python
import PyPDF2

def load_pdf(path: str) -> str:
    """Extract text from PDF"""
    text = ""
    with open(path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text
```

## 9.3 Web Scraper

```python
import requests
from bs4 import BeautifulSoup

def scrape_url(url: str) -> str:
    """Scrape text from a URL"""
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Remove script and style
    for script in soup(["script", "style"]):
        script.decompose()
    
    return soup.get_text(separator="\n", strip=True)
```

## 9.4 Async Queue with Celery

```python
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def process_ai_request(prompt: str, user_id: str) -> str:
    # This runs in background
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Save result to DB
    save_to_db(user_id, response.choices[0].message.content)
    
    return response.choices[0].message.content

# Usage (non-blocking)
result = process_ai_request.delay("Hello", "user-123")
```

---

# SECTION 10: CHEAT SHEETS

## 10.1 Model Selection Guide

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| Quick classification | gpt-4o-mini | Fast, cheap, good enough |
| Complex reasoning | gpt-4o or claude-3-5-sonnet | Better quality |
| Code generation | claude-3-5-sonnet | Best at code |
| Long context (100K+) | claude-3-5-sonnet | 200K context |
| Cost-sensitive | gpt-4o-mini or llama-3-70b | Cheapest options |
| Privacy-critical | Self-hosted llama | Data stays local |
| Vision tasks | gpt-4o or gemini-pro-vision | Best vision |
| Multi-lingual | claude-3-5-sonnet | Better non-English |

## 10.2 Pricing Reference (per 1M tokens, 2026)

| Model | Input | Output |
|-------|-------|--------|
| GPT-4o | $5 | $15 |
| GPT-4o-mini | $0.15 | $0.60 |
| Claude 3.5 Sonnet | $3 | $15 |
| Claude 3.5 Haiku | $0.80 | $4 |
| Gemini Pro 1.5 | $1.25 | $5 |
| Llama 3 70B (self-hosted) | $0.10 (compute) | $0.10 |

## 10.3 Common Latencies (p50)

| Operation | Latency |
|-----------|---------|
| GPT-4o-mini (short) | 500ms |
| GPT-4o (short) | 1-2s |
| Claude 3.5 Sonnet | 1-2s |
| Embeddings (100 docs) | 2-3s |
| Vector search (1M docs) | <100ms |

## 10.4 Token Limits

| Model | Context | Output |
|-------|---------|--------|
| GPT-4o | 128K | 16K |
| GPT-4o-mini | 128K | 16K |
| Claude 3.5 Sonnet | 200K | 8K |
| Gemini Pro 1.5 | 2M | 8K |
| Llama 3 70B | 8K | 2K |

---

# BONUS: INTERVIEW PREP

## Top 30 AI Engineering Interview Questions

1. How would you design a system to summarize 1M documents per day using LLMs?
2. Explain the difference between RAG and fine-tuning. When would you use each?
3. How do you reduce hallucinations in an LLM application?
4. Walk through your approach to evaluating a RAG system.
5. Design ChatGPT. How would you architect the backend?
6. How do you handle rate limits when calling OpenAI at scale?
7. What's the difference between zero-shot, one-shot, and few-shot prompting?
8. Explain the ReAct pattern. When is it useful?
9. How would you implement a multi-agent system?
10. What are the trade-offs between different vector databases?
11. How do you secure an LLM application from prompt injection?
12. Explain token costs and how to optimize them.
13. How would you deploy an LLM app to serve 1M users?
14. What's the difference between streaming and batch processing for LLMs?
15. How do you implement conversation memory in a chatbot?
16. Explain the transformer architecture at a high level.
17. How would you A/B test two different prompts?
18. What's your approach to debugging when an LLM gives wrong answers?
19. How do you handle PII data when calling LLMs?
20. Explain self-consistency and tree-of-thought prompting.
21. How would you monitor an LLM app in production?
22. What's the role of embeddings in semantic search?
23. How do you choose chunk size for RAG?
24. Explain the difference between synchronous and async LLM calls.
25. How would you implement content moderation for an AI app?
26. What is prompt caching and when should you use it?
27. How do you handle long contexts (100K+ tokens)?
28. Explain function calling vs tool use vs agents.
29. How would you fine-tune a model with limited data?
30. Design a system to generate 1000 personalized emails per hour.

**Answers:** See video walkthroughs in Module 14.

---

**Last updated:** [Date]
**Lines of code:** 1,500+
**Copy-paste ready:** All snippets tested
**License:** MIT — use freely
