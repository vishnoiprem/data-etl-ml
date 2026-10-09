# Lesson 3.2: Build RAG from Scratch
## Full Lesson Script (28-minute video)

---

## COLD OPEN (0:00 - 0:45)

[VISUAL: Split screen — left: ChatGPT giving a wrong answer. Right: same question with RAG giving a correct answer from a real document]

**NARRATOR:**
"ChatGPT is brilliant — until you ask it about your company's data, your private documents, or anything that happened after its training cutoff. Then it either makes stuff up or says 'I don't know.'

But what if I told you there's a 50-line pattern that fixes this completely? A pattern that lets ChatGPT answer questions about *your* data, with *citations*, and without *hallucinating*?

It's called RAG — Retrieval-Augmented Generation. And in the next 28 minutes, you're going to build one from scratch. No frameworks. No magic. Just Python and an API call.

By the end, you'll have a working system that can answer questions about any document you give it. Let's go."

---

## HOOK (0:45 - 1:30)

**NARRATOR:**
"Every AI product you've used — Notion AI, GitHub Copilot Chat, the new ChatGPT with file uploads — they all use some version of RAG. It's the most important pattern in applied AI today.

But here's the thing: most people learn RAG wrong. They start with a framework like LangChain, copy-paste code, and never understand what's actually happening. Then when it breaks in production — and it will — they're stuck.

Today, we're going to fix that. We're going to build RAG from first principles. Then we'll look at how LangChain does it. By the end, you'll understand *both* the why and the how.

This is one of the highest-leverage lessons in the entire course. Pay attention."

---

## WHAT IS RAG? (1:30 - 4:00)

[VISUAL: Animated diagram showing the 4 steps of RAG]

**NARRATOR:**
"RAG stands for Retrieval-Augmented Generation. Let me break that down:

**Retrieval** — Find the relevant information from your knowledge base.
**Augmented** — Add that information to the LLM's context.
**Generation** — Let the LLM generate an answer based on that context.

That's it. The LLM is still the brain. We're just giving it the right information at the right time.

Here's the 4-step flow:

**Step 1: User asks a question.** 'What was our Q3 revenue?'

**Step 2: We search our knowledge base** for documents relevant to that question. We don't send the whole document. We send only the most relevant chunks.

**Step 3: We build a prompt** that includes both the user's question AND the retrieved chunks. Something like: 'Based on the following context, answer the user's question. Context: [retrieved chunks]. Question: [user question].'

**Step 4: The LLM generates an answer** based on the context, not its training data. And because the context is right there in the prompt, the LLM can also cite its sources.

This pattern solves 3 huge problems:

1. **Hallucination** — The LLM has facts to work with, not just its memory.
2. **Stale knowledge** — You can update your knowledge base anytime without retraining.
3. **Private data** — The LLM never sees your data during training. You just send it at query time.

Now let's build it."

---

## SETUP (4:00 - 5:30)

[VISUAL: Terminal, setting up environment]

**NARRATOR:**
"Here's what you'll need:

- Python 3.10+
- An OpenAI API key (for both the LLM and embeddings)
- A sample document (I'll provide one)

Let me set up the project:

```bash
mkdir rag-from-scratch
cd rag-from-scratch
python -m venv venv
source venv/bin/activate
pip install openai numpy python-dotenv
```

Now, the key insight: RAG has two phases — **indexing** (done once) and **querying** (done at request time). Let's build them separately."

---

## PHASE 1: INDEXING (5:30 - 12:00)

[VISUAL: Code editor, building the indexer]

**NARRATOR:**
"The indexing phase has 3 steps:

1. **Chunk** your documents into small pieces
2. **Embed** each chunk (convert text → vector)
3. **Store** the vectors in a way you can search later

Let me show you each step.

**Step 1: Chunking**

The whole document won't fit in the LLM's context. So we split it into smaller pieces — usually 200-500 tokens each. Why this size? Smaller chunks are more precise but lose context. Larger chunks have more context but are less precise. 500 tokens is a good default.

```python
import os
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np

load_dotenv()
client = OpenAI()

def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    '''Split a document into overlapping chunks'''
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks

# Load a document
with open('company-handbook.txt', 'r') as f:
    document = f.read()

chunks = chunk_document(document)
print(f"Created {len(chunks)} chunks")
```

Notice the **overlap**. That's important. If a sentence spans two chunks, we want some overlap so we don't lose context. 50 tokens of overlap is usually enough.

**Step 2: Embedding**

Now we convert each chunk into a vector — a list of 1,536 numbers (for OpenAI's `text-embedding-3-small` model). These numbers represent the *meaning* of the text. Similar meanings → similar vectors.

```python
def get_embedding(text: str) -> list[float]:
    '''Get embedding for a text chunk'''
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# Embed all chunks
embeddings = [get_embedding(chunk) for chunk in chunks]
print(f"Created {len(embeddings)} embeddings of dimension {len(embeddings[0])}")
```

This is a one-time cost. For 1,000 chunks, this costs about $0.02. Take a screenshot of this.

**Step 3: Store in numpy array (for now)**

For production, you'd use a vector database. For learning, numpy is fine.

```python
# Save chunks and embeddings
np.save('embeddings.npy', np.array(embeddings))

with open('chunks.txt', 'w') as f:
    for i, chunk in enumerate(chunks):
        f.write(f'CHUNK_{i}:{chunk}\n---\n')
```

In the next lesson, we'll swap this for Pinecone. For now, this works.

That's the indexing phase. It takes maybe 30 seconds for 1,000 chunks. Now the fun part: querying."

---

## PHASE 2: QUERYING (12:00 - 19:00)

[VISUAL: Code editor, building the query function]

**NARRATOR:**
"The query phase also has 3 steps:

1. **Embed** the user's question
2. **Search** for the most similar chunks
3. **Generate** an answer using those chunks

**Step 1: Embed the question**

Same model. Same dimensions. The question and the chunks live in the same vector space.

```python
def search(query: str, top_k: int = 3):
    '''Search for the most relevant chunks'''
    # Embed the query
    query_embedding = get_embedding(query)
    
    # Load stored embeddings
    stored_embeddings = np.load('embeddings.npy')
    
    # Calculate cosine similarity
    similarities = np.dot(stored_embeddings, query_embedding) / (
        np.linalg.norm(stored_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top-k most similar chunks
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    # Load the actual chunk text
    with open('chunks.txt', 'r') as f:
        content = f.read()
    all_chunks = content.split('\n---\n')
    
    return [all_chunks[i] for i in top_indices]
```

**Step 2: Cosine similarity**

I'm using **cosine similarity** to measure how similar two vectors are. It returns a value between -1 and 1. 1 means identical. 0 means unrelated. -1 means opposite.

In practice, for embeddings, scores above 0.7 usually mean 'very relevant'. 0.5-0.7 is 'somewhat relevant'. Below 0.5 is probably noise.

**Step 3: Generate the answer**

Now we send the user's question PLUS the retrieved chunks to the LLM:

```python
def answer_question(question: str) -> str:
    '''Answer a question using RAG'''
    # 1. Retrieve relevant chunks
    relevant_chunks = search(question, top_k=3)
    context = '\n\n'.join(relevant_chunks)
    
    # 2. Build the prompt
    prompt = f'''Answer the following question based on the context provided. 
If the answer is not in the context, say "I don't have that information."

Context:
{context}

Question: {question}

Answer:'''
    
    # 3. Generate the answer
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant. Always cite your sources by referencing the chunk numbers.'},
            {'role': 'user', 'content': prompt}
        ],
        temperature=0  # Lower temperature = more deterministic
    )
    
    return response.choices[0].message.content

# Try it
print(answer_question('What is the company's vacation policy?'))
```

Three things to notice:

1. **The system prompt tells the LLM to cite sources.** This is important. Without it, the LLM will just give you an answer. With it, you get `[Source: CHUNK_42]`-style citations.

2. **`temperature=0` makes outputs deterministic.** For factual Q&A, you want consistent answers. For creative writing, use higher temperatures.

3. **We tell the LLM to say 'I don't have that information.'** This is the single most important line. It prevents hallucination. Without it, the LLM will make stuff up when the answer isn't in the context.

That's the entire RAG system. Let me show you it working."

---

## DEMO (19:00 - 22:00)

[VISUAL: Terminal, running the RAG system with 4 test questions]

**NARRATOR:**
"Let's test this with a real document — a 50-page company handbook.

**Test 1: Factual question**

```python
print(answer_question('How many vacation days do employees get?'))
```

[Output:]
```
According to the employee handbook, full-time employees receive 20 vacation days 
per year, accrued at 1.67 days per month. [Source: CHUNK_12]
```

The LLM gave a precise answer with a citation. The citation lets you verify it.

**Test 2: Question that requires combining multiple chunks**

```python
print(answer_question('What happens if I get sick during vacation?'))
```

[Output:]
```
If you get sick during vacation, you can convert your vacation days to sick days 
by notifying HR within 48 hours and providing a doctor's note. Sick days do not 
count against your vacation balance. [Source: CHUNK_12, CHUNK_18]
```

Notice it cited TWO chunks. The LLM combined information from both to give a complete answer.

**Test 3: Question that isn't in the document**

```python
print(answer_question('What is the CEO's salary?'))
```

[Output:]
```
I don't have that information in the provided context.
```

The LLM didn't make up an answer. It admitted it doesn't know. This is exactly what we want.

**Test 4: A tricky question**

```python
print(answer_question('Can I work from home on Fridays?'))
```

[Output:]
```
According to the handbook, the company has a flexible work-from-home policy. 
Employees can work from home up to 2 days per week with manager approval. 
[Source: CHUNK_25]
```

The LLM correctly understood that 'Fridays' wasn't specific in the handbook, but the general policy applies.

Pretty cool, right? This is a working RAG system in ~100 lines of code."

---

## PRODUCTION IMPROVEMENTS (22:00 - 25:00)

[VISUAL: Code editor, showing improvements]

**NARRATOR:**
"Now let's make this production-ready. Four improvements:

**1. Use a real vector database**

Numpy is fine for 1,000 documents. For 1 million, you need a real vector DB. We'll cover Pinecone, Chroma, and pgvector in the next lesson. The API is almost identical.

**2. Better chunking**

500-token chunks with 50-token overlap is a good start. But for technical docs, you might want to chunk by section. For code, you might chunk by function. Smart chunking can boost accuracy by 20-30%.

**3. Hybrid search**

Embeddings are great for semantic meaning. But what if someone searches for an exact term like 'CHUNK_42' or a product SKU? For that, you need keyword search (BM25). Combine both = hybrid search. We'll cover this in Level 4.

**4. Re-ranking**

Sometimes the top-3 chunks aren't quite right. A re-ranker model (like Cohere's `rerank-3`) re-scores them. This adds latency but boosts accuracy significantly.

These are the patterns you'll use in every production RAG system. Take notes."

---

## COMMON PITFALLS (25:00 - 27:00)

[VISUAL: Bullet points on screen]

**NARRATOR:**
"Top 5 RAG mistakes I see all the time:

**1. Chunks too big or too small**
❌ 50 tokens (loses context)
❌ 2000 tokens (too much noise, dilutes the signal)
✅ 300-500 tokens with 50-token overlap

**2. Not handling 'no answer' cases**
If your context doesn't have the answer, the LLM will hallucinate. ALWAYS include: 'If the answer is not in the context, say you don't know.'

**3. No metadata filtering**
If you have 10,000 documents, searching all of them is slow. Add metadata (date, author, category) and filter before searching. 10x speedup.

**4. Ignoring chunk boundaries**
Don't split mid-sentence. Use sentence boundaries. For markdown, respect headers. For code, respect function boundaries.

**5. No evaluation**
How do you know your RAG is working? You need a test set. Generate 50 question-answer pairs. Run them through your RAG. Measure accuracy. We'll cover RAGAS evaluation in Level 5.

Avoid these and you're 90% ahead of most RAG implementations."

---

## HOMEWORK (27:00 - 28:00)

[VISUAL: Code editor showing starter code]

**NARRATOR:**
"Your homework: Build RAG over your own data.

**Pick one:**
- 📄 Your resume (so you can ask questions about yourself)
- 📚 A book you love (so you can ask questions about it)
- 💼 Your company's documentation
- 📰 A collection of articles on a topic you care about

**Requirements:**
- Chunk the document properly
- Store embeddings (numpy is fine for now)
- Build a query function
- Test with 5 different question types
- Add citations to your answers

**Bonus:**
- Add metadata filtering (by section, date, etc.)
- Try a different chunk size and measure the impact
- Add a simple web UI with Streamlit

Post your solutions in Discord #showcase. Best ones get featured in the next cohort.

**Starter code:** https://github.com/aiforbiz/ai-engineer-course/tree/main/lesson-3-2

That's Lesson 3.2. You now understand:
- What RAG is and why it matters
- How to build it from scratch
- How to chunk, embed, and search
- How to generate answers with citations
- Common pitfalls and how to avoid them

Next lesson: **3.3 — Production RAG with LangChain**. We'll take this 100-line system and turn it into a production-grade app with monitoring, caching, and a real vector database.

If this was useful, hit like and subscribe. See you in the next one. 🚀"

---

## CHAPTERS (for YouTube)

```
0:00 - Cold open: ChatGPT fails, RAG wins
0:45 - What is RAG and why it matters
1:30 - The 4-step RAG flow explained
4:00 - Setting up the project
5:30 - Phase 1: Chunking documents
8:00 - Phase 1: Embedding chunks
10:30 - Phase 1: Storing embeddings
12:00 - Phase 2: Embedding the query
14:00 - Phase 2: Cosine similarity search
16:30 - Phase 2: Generating the answer
19:00 - Demo: 4 real test questions
22:00 - Production improvements
25:00 - Top 5 RAG mistakes
27:00 - Homework & next lesson
```

---

**Duration:** 28 minutes
**Difficulty:** Intermediate
**Prerequisites:** Python, OpenAI API basics, basic linear algebra
**Code:** https://github.com/aiforbiz/ai-engineer-course/tree/main/lesson-3-2
**Next lesson:** 3.3 - Production RAG with LangChain
