"""Show the LLM extracting a sample triple so you can see the graph being built."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_settings
from src.ingestion import load_corpus
from src.llm import get_llm


def main() -> None:
    s = get_settings()
    llm = get_llm()
    chunks = load_corpus(s.sample_data_dir / "corpus")
    print(f"Using LLM: {llm.name}\n")
    for c in chunks[:3]:
        prompt = (
            'Extract entity-relation-entity triples from the text below. '
            'Return JSON: {"triples": [{"head":..., "head_type":..., "rel":..., "tail":..., "tail_type":...}]}\n\n'
            f"Source: {c.doc_id}\nTitle: {c.title}\n\nText:\n{c.text[:600]}\n"
        )
        print(f"─── {c.chunk_id} ({c.title}) ───")
        try:
            out = llm.extract_json(prompt)
            triples = out.get("triples", [])
            if not triples:
                print("(no triples extracted)")
            for t in triples:
                print(f"  {t.get('head')} --[{t.get('rel')}]--> {t.get('tail')}")
        except Exception as e:
            print(f"  ERROR: {e}")
        print()


if __name__ == "__main__":
    main()
