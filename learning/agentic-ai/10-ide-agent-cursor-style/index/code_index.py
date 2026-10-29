"""
Code index: Tree-sitter symbol extraction + symbol-level retrieval.

The unit is the symbol, not the file. A symbol is a function, class,
method, or top-level constant. We embed (name + docstring + first N
lines of body) per symbol and retrieve against the symbol, not the file.

Real impl: tree-sitter-language-pack + a real embedder + a vector store.
"""
from __future__ import annotations
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Symbol:
    name: str
    kind: str          # "function" | "class" | "method" | "constant"
    file: str
    line: int
    body: str          # full body
    snippet: str       # name + docstring + first 5 lines, used for embedding


def python_symbols(path: str, source: str) -> list[Symbol]:
    """Toy Python symbol extractor. Real impl: tree-sitter.

    Catches top-level def/class and indented def inside a class. Misses
    nested closures, decorators, and async — that's a real-impl problem.
    """
    syms: list[Symbol] = []
    lines = source.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(?:def|class|async\s+def)\s+(\w+)", line)
        if m and (i == 0 or not lines[i - 1].rstrip().endswith("\\")):
            name = m.group(1)
            kind = "class" if line.lstrip().startswith("class") else "function"
            # capture indented block
            indent = len(line) - len(line.lstrip())
            j = i + 1
            while j < len(lines) and (lines[j].strip() == "" or len(lines[j]) - len(lines[j].lstrip()) > indent):
                j += 1
            body = "\n".join(lines[i:j])
            snippet = "\n".join(lines[i : min(i + 6, j)])
            syms.append(Symbol(name=name, kind=kind, file=path, line=i, body=body, snippet=snippet))
            i = j
        else:
            i += 1
    return syms


@dataclass
class CodeIndex:
    symbols: list[Symbol] = field(default_factory=list)
    by_name: dict[str, list[Symbol]] = field(default_factory=lambda: defaultdict(list))
    by_id: dict[str, Symbol] = field(default_factory=dict)

    def add(self, syms: Iterable[Symbol]):
        for s in syms:
            sid = hashlib.sha1(f"{s.file}:{s.line}:{s.name}".encode()).hexdigest()[:12]
            self.by_id[sid] = s
            self.by_name[s.name].append(s)
            self.symbols.append(s)

    def search_by_name(self, query: str, top_k: int = 5) -> list[Symbol]:
        """Substring search. Real impl: vector retrieval."""
        q = query.lower().strip()
        # exact > prefix > substring
        scored: list[tuple[int, Symbol]] = []
        for s in self.symbols:
            n = s.name.lower()
            if n == q:
                scored.append((0, s))
            elif n.startswith(q):
                scored.append((1, s))
            elif q in n:
                scored.append((2, s))
        scored.sort()
        return [s for _, s in scored[:top_k]]

    def stats(self) -> dict:
        return {
            "total_symbols": len(self.symbols),
            "unique_names": len(self.by_name),
            "kinds": {k: sum(1 for s in self.symbols if s.kind == k) for k in {"function", "class", "method", "constant"}},
        }


def build_index(repo: Path) -> CodeIndex:
    """Walk a repo, index all .py files."""
    idx = CodeIndex()
    for py in repo.rglob("*.py"):
        try:
            source = py.read_text()
        except UnicodeDecodeError:
            continue
        idx.add(python_symbols(str(py), source))
    return idx


if __name__ == "__main__":
    # Toy example
    src = '''
def hello(name):
    """Say hello."""
    return f"hello {name}"


class UserResolver:
    """Resolves a user by id."""
    def resolve(self, user_id):
        ...
'''
    syms = python_symbols("toy.py", src)
    idx = CodeIndex()
    idx.add(syms)
    print(f"indexed {idx.stats()}")
    print(f"search 'user': {[(s.name, s.kind, s.file, s.line) for s in idx.search_by_name('user')]}")
