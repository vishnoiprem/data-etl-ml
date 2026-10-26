"""Trie walk visualization for the typeahead service.

Shows how the trie is structured and how a prefix walk + top-K slice
works on real data. Run after `python3 scripts/seed_data.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from code.service import TypeaheadService  # type: ignore  # noqa: E402


def ascii_trie(trie_node, depth: int = 0, max_depth: int = 3) -> str:
    if depth > max_depth:
        return ""
    out = []
    for ch, child in sorted(trie_node.children.items())[:6]:
        out.append("  " * depth + ch + "  (top:" +
                   ", ".join(w for w, _ in child.top_k[:3]) + ")")
        out.append(ascii_trie(child, depth + 1, max_depth))
    return "\n".join(s for s in out if s)


def main() -> None:
    svc = TypeaheadService(k=5)
    if not svc.load_default():
        print("Run scripts/seed_data.py first.")
        return

    print(f"Trie size: {svc.stats()['trie_nodes']} nodes\n")
    print("Sample sub-tree under 'p' (depth 3):")
    p_node = svc._trie.root.children.get("p")  # type: ignore[attr-defined]
    if p_node:
        print(ascii_trie(p_node))

    print("\nTop-5 suggestions for 'flas':")
    for w, f in svc.suggest("flas"):
        print(f"  {w:20s}  freq={f}")

    print("\nTop-5 suggestions for 'par':")
    for w, f in svc.suggest("par"):
        print(f"  {w:20s}  freq={f}")


if __name__ == "__main__":
    main()
