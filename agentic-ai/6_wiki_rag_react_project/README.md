# Wikipedia RAG ReAct Chat Assistant

This project implements the Educative workflow using LlamaIndex, a local BGE embedding model, OpenAI, Wikipedia, and Chainlit.

## 1. Set up

```bash
#python -m venv .venv
#source .venv/bin/activate
pip install -r requirements.txt
cp apikeys.example.yml apikeys.yml
```

Edit `apikeys.yml` and add your key. Never commit this file. Alternatively, put `OPENAI_API_KEY=...` in `.env` (both files are gitignored).

The chat model must be one that `llama-index-llms-openai` 0.1.x recognises — `gpt-4o-mini` (default) or `gpt-4o`. Passing `gpt-5-nano` raises `ValueError: Unknown model`.

## 2. Verify the key

```bash
python utils.py
```

## 3. Test indexing from the terminal

```bash
python index_wikipages.py
```

Example input:

```text
Please index: 2023 United States banking crisis
```

Titles are taken from the text after `:`, split on commas — no LLM call, so indexing
works without an API key. The first run downloads `BAAI/bge-small-en-v1.5`.

## 4. Launch the app

```bash
chainlit run chat_agent.py -h
```

Open the Chainlit URL, use Settings to select the model and enter Wikipedia titles, then ask questions.

## Security and RAG notes

- The API key is never printed or committed.
- Answers are grounded only in the pages indexed for the current session.
- The index is in memory and disappears when the process restarts.
- Wikipedia content is not the same as truly live transactional data. Re-index to pick up page changes.
- `similarity_top_k=10` follows the assignment, but evaluate retrieval quality before using it in production.

## Suggested evaluation

Create a small question set and track retrieval hit rate, answer correctness, faithfulness to retrieved text, latency, and API cost. Include unanswerable questions to verify that the assistant does not invent facts.
