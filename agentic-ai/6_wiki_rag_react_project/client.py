"""Client A: in-process. No server involved — import the core and call it.

Run with:  python client.py "Please index: London, Birmingham"
"""

import sys

from rag_agent import build_agent

DEFAULT_PAGES = "Please index: 2023 United States banking crisis"


def main():
    pages = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PAGES

    print(f"Indexing: {pages}")
    agent = build_agent(pages)  # index + agent in one call
    print("Ready. Ask a question, or press Enter to quit.\n")

    while True:
        question = input("you > ").strip()
        if not question:
            break
        print(f"bot > {agent.chat(question)}\n")  # the only call per turn


if __name__ == "__main__":
    main()
