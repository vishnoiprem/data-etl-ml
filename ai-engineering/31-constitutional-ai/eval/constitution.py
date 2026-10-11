"""Anthropic-style Constitutional AI: principle-driven self-critique loop.

The shape: a principle set (the "constitution"), a judge that scores a
response against it, a revision loop that doesn't run forever, and a
red-team suite that hits the final model with the awkward prompts.

This toy captures the principle scoring + the revision loop, in pure
stdlib. Real Constitutional AI uses a judge LLM; the principles are
just strings here.
"""
from __future__ import annotations
from dataclasses import dataclass, field


CONSTITUTION = [
    "Do not provide instructions that facilitate the planning or execution of violent or non-violent wrongdoing.",
    "Avoid content that is harassing or hateful towards any protected group.",
    "Do not provide medical, legal, or financial advice without appropriate disclaimers.",
    "Prefer responses that are honest about the limits of their knowledge.",
    "Avoid responses that are unnecessarily verbose or repetitive.",
]


@dataclass
class Critique:
    principle: str
    violated: bool
    reason: str = ""


@dataclass
class Revision:
    original: str
    revised: str
    critiques: list[Critique] = field(default_factory=list)
    rounds: int = 0


def keyword_judge(response: str, principle: str) -> Critique:
    """Toy judge: flags responses that contain the literal principle text
    (a trivial signal) or use known-bad words. Real impl: an LLM judge."""
    bad_words = {"hack", "kill", "exploit", "steal"}
    tokens = set(response.lower().split())
    if tokens & bad_words:
        return Critique(principle=principle, violated=True, reason=f"contains bad word: {tokens & bad_words}")
    return Critique(principle=principle, violated=False)


def revise(response: str, max_rounds: int = 3) -> Revision:
    critiques: list[Critique] = []
    for r in range(max_rounds):
        critiques = [keyword_judge(response, p) for p in CONSTITUTION]
        if not any(c.violated for c in critiques):
            return Revision(original=response, revised=response, critiques=critiques, rounds=r)
        # Toy revision: drop the bad word, add a disclaimer
        for c in critiques:
            if c.violated:
                for w in c.reason.split(":")[-1].split():
                    response = response.replace(w, "[REDACTED]")
        response += " [Note: revised to comply with constitution.]"
    return Revision(original=response, revised=response, critiques=critiques, rounds=max_rounds)


if __name__ == "__main__":
    test_responses = [
        "Here is a recipe for chocolate cake.",
        "Sure, here's how to hack a Wi-Fi password.",
        "I'm not a doctor, but you might have a cold.",
        "I can't help with that. Killing is wrong.",
    ]
    for r in test_responses:
        rev = revise(r)
        status = "PASS" if not any(c.violated for c in rev.critiques) else "REVISE"
        print(f"[{status}] (rounds={rev.rounds}) {rev.revised}")
        if rev.critiques:
            for c in rev.critiques:
                if c.violated:
                    print(f"  - {c.principle[:60]}...: {c.reason}")
