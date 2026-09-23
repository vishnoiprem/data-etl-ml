"""Client B: over HTTP. Talks to server.py, so the model runs in that process.

Start the host first:  uvicorn server:app --port 8000
Then:                  python client_http.py "Which banks failed in 2023?"
"""

import sys

import requests

HOST = "http://localhost:8000"
PAGES = "Please index: 2023 United States banking crisis"


def index(pages: str = PAGES) -> dict:
    response = requests.post(f"{HOST}/index", json={"pages": pages}, timeout=600)
    response.raise_for_status()
    return response.json()


def ask(question: str) -> str:
    response = requests.post(f"{HOST}/ask", json={"question": question}, timeout=300)
    response.raise_for_status()
    return response.json()["answer"]


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "What triggered the crisis?"

    # Index once per server process; skip this if /health already reports ready.
    if not requests.get(f"{HOST}/health", timeout=30).json()["ready"]:
        print("indexing:", index())

    print("answer:", ask(question))


if __name__ == "__main__":
    main()
