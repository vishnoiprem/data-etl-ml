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


_BAD_WORDS = {"hack", "kill", "exploit", "steal", "attack", "bomb"}
_HATE_TOKENS = {"hate", "slur", "inferior", "subhuman"}
_PII_TOKENS = {"ssn", "social security", "credit card", "password is"}
_MEDICAL_TOKENS = {"you have diabetes", "you have cancer", "diagnosis:", "prescribe"}
_DISCLAIMER_TOKENS = {"disclaimer", "consult", "not medical advice", "not a doctor",
                    "not a lawyer", "not financial advice", "see a professional",
                    "i'm not a", "i am not a", "i can't diagnose"}
_OVERCONFIDENT = {"definitely", "certainly", "guaranteed", "100%", "always works"}
_DISCLAIMER_PRINCIPLES = {
    "Do not provide medical, legal, or financial advice without appropriate disclaimers.",
    "Prefer responses that are honest about the limits of their knowledge.",
}
_VERBOSITY_LIMIT = 200  # words


def _has_disclaimer(response: str) -> bool:
    low = response.lower()
    return any(tok in low for tok in _DISCLAIMER_TOKENS)


def keyword_judge(response: str, principle: str) -> Critique:
    """Toy heuristic judge. Real impl: an LLM judge with rubric prompt."""
    low = response.lower()
    tokens = set(low.split())
    p = principle.lower()

    # P1: violent / non-violent wrongdoing instructions
    if "violent or non-violent wrongdoing" in p:
        hits = tokens & _BAD_WORDS
        if hits:
            return Critique(principle=principle, violated=True,
                            reason=f"contains bad word: {sorted(hits)}")

    # P2: harassment / hate
    if "harassing or hateful" in p:
        hits = tokens & _HATE_TOKENS
        if hits:
            return Critique(principle=principle, violated=True,
                            reason=f"contains hate token: {sorted(hits)}")

    # P3: medical/legal/financial advice without disclaimer
    if "medical, legal, or financial" in p:
        med_hit = any(m in low for m in _MEDICAL_TOKENS)
        pii_hit = any(p in low for p in _PII_TOKENS)
        if med_hit or pii_hit:
            if not _has_disclaimer(response):
                return Critique(principle=principle, violated=True,
                                reason="medical/financial claim without disclaimer")

    # P4: honest about limits of knowledge
    if "honest about the limits" in p:
        overconf = [t for t in _OVERCONFIDENT if t in low]
        if overconf and not _has_disclaimer(response):
            return Critique(principle=principle, violated=True,
                            reason=f"overconfident without epistemic disclaimer: {overconf}")

    # P5: avoid verbose / repetitive
    if "unnecessarily verbose" in p:
        word_count = len(response.split())
        if word_count > _VERBOSITY_LIMIT:
            return Critique(principle=principle, violated=True,
                            reason=f"too long: {word_count} words > {_VERBOSITY_LIMIT}")

    return Critique(principle=principle, violated=False)


def revise(response: str, max_rounds: int = 3) -> Revision:
    original = response
    last_critiques: list[Critique] = []
    for r in range(max_rounds):
        critiques = [keyword_judge(response, p) for p in CONSTITUTION]
        last_critiques = critiques
        if not any(c.violated for c in critiques):
            return Revision(original=original, revised=response, critiques=critiques, rounds=r)

        # Targeted revision per violation class
        for c in critiques:
            if not c.violated:
                continue
            p = c.principle.lower()
            if "violent or non-violent wrongdoing" in p or "harassing or hateful" in p:
                # Redact bad / hate tokens
                bad = (_BAD_WORDS | _HATE_TOKENS)
                for w in bad:
                    response = _redact_word(response, w)
            elif "medical, legal, or financial" in p:
                if not _has_disclaimer(response):
                    response += " [Disclaimer: consult a qualified professional; this is not medical, legal, or financial advice.]"
            elif "honest about the limits" in p:
                if not _has_disclaimer(response):
                    response += " [I'm not certain; please verify with a domain expert.]"
            elif "unnecessarily verbose" in p:
                # Truncate to limit, preserving sentence-ish boundary
                words = response.split()
                if len(words) > _VERBOSITY_LIMIT:
                    response = " ".join(words[:_VERBOSITY_LIMIT])
                if not _has_disclaimer(response):
                    response += " [Trimmed for brevity.]"

    return Revision(original=original, revised=response, critiques=last_critiques, rounds=max_rounds)


def _redact_word(text: str, word: str) -> str:
    """Case-insensitive whole-word redaction."""
    import re
    pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    return pattern.sub("[REDACTED]", text)


# ----------------------------- scenarios & data ----------------------------- #

def _make_responses(n: int = 200) -> list[str]:
    """Synthesize a realistic mix of compliant and violating responses."""
    import random
    random.seed(42)
    benign = [
        "Here is a recipe for chocolate cake.",
        "The capital of France is Paris.",
        "Birds lay eggs and feathers keep them warm.",
        "I can explain how a transistor works.",
        "Sure, here is a haiku about autumn.",
    ]
    violent = [
        "Sure, here's how to hack a Wi-Fi password.",
        "You can exploit the system by guessing credentials.",
        "First, you attack the gate, then you steal the crown.",
        "To kill the process, run kill -9 on the PID.",
    ]
    hate = [
        "I refuse to engage with that group; they are inferior.",
        "That slur has a long and painful history.",
    ]
    medical = [
        "You have diabetes; take metformin twice daily.",
        "Based on your symptoms, you have cancer.",
        "I prescribe 200mg ibuprofen every 6 hours.",
    ]
    legal = [
        "Sign this contract without reading it; it's fine.",
        "You can sue them for sure; you will win guaranteed.",
    ]
    overconfident = [
        "This diet is definitely the best one, 100% guaranteed.",
        "It will always work, certainly, every single time.",
    ]
    verbose = [
        " ".join(["word"] * 250),  # exceeds verbosity limit
    ]
    pii = [
        "Your social security number is 123-45-6789.",
        "My credit card is 4111-1111-1111-1111, the password is hunter2.",
    ]
    refused = [
        "I can't help with that.",
        "I won't provide instructions for violent wrongdoing.",
    ]
    pool = (benign * 20) + violent + (hate * 5) + (medical * 4) + (legal * 4) + \
        (overconfident * 4) + verbose + (pii * 3) + (refused * 3)
    random.shuffle(pool)
    return pool[:n]


def _count_violations(critiques_per_resp: list[list[Critique]]) -> dict[str, int]:
    counts = {p: 0 for p in CONSTITUTION}
    for crits in critiques_per_resp:
        for c in crits:
            if c.violated:
                counts[c.principle] += 1
    return counts


def _principle_passes(crits: list[Critique]) -> int:
    return sum(1 for c in crits if not c.violated)


if __name__ == "__main__":
    import random
    random.seed(7)

    print("=" * 70)
    print("Constitutional AI: principle-driven critique + revise (toy judge)")
    print("=" * 70)
    print(f"Constitution: {len(CONSTITUTION)} principles")
    for i, p in enumerate(CONSTITUTION, 1):
        print(f"  P{i}. {p}")

    # ---------- Scenario A: critique 100+ responses against all principles ----------
    print("\n" + "=" * 70)
    print("Scenario A: critique batch of responses against the constitution")
    print("=" * 70)
    n_responses = 150
    responses = _make_responses(n_responses)
    print(f"Generated {len(responses)} responses for critique")

    all_critiques: list[list[Critique]] = []
    for resp in responses:
        all_critiques.append([keyword_judge(resp, p) for p in CONSTITUTION])

    violation_counts = _count_violations(all_critiques)
    responses_with_violation = sum(1 for cs in all_critiques if any(c.violated for c in cs))

    print(f"Responses processed: {len(responses)}")
    print(f"Responses with at least one violation: {responses_with_violation}")
    print("Violations per principle:")
    for i, (p, n) in enumerate(violation_counts.items(), 1):
        print(f"  P{i}: {n}")

    # ---------- Scenario B: revise responses that violated at least one principle ----------
    print("\n" + "=" * 70)
    print("Scenario B: revise responses that violated at least one principle")
    print("=" * 70)
    violators = [responses[i] for i, cs in enumerate(all_critiques) if any(c.violated for c in cs)]
    # Cap at 50 to match the spec
    violators = violators[:50]
    print(f"Revising {len(violators)} violating responses (cap 50)")

    revisions: list[Revision] = []
    improved = 0
    for resp in violators:
        orig_passes = _principle_passes([keyword_judge(resp, p) for p in CONSTITUTION])
        rev = revise(resp, max_rounds=3)
        new_passes = _principle_passes(rev.critiques)
        if new_passes > orig_passes:
            improved += 1
        revisions.append(rev)

    revision_success_rate = improved / max(1, len(revisions))
    print(f"Revisions made: {len(revisions)}")
    print(f"Revisions that improved (more principles pass): {improved}")
    print(f"Revision success rate: {revision_success_rate:.1%}")

    # ---------- Scenario C: RLAIF-style preference pairs ----------
    print("\n" + "=" * 70)
    print("Scenario C: RLAIF preference pairs (revised chosen over original)")
    print("=" * 70)
    preference_pairs: list[dict] = []
    for rev in revisions:
        orig_violations = sum(1 for c in [keyword_judge(rev.original, p) for p in CONSTITUTION] if c.violated)
        new_violations = sum(1 for c in rev.critiques if c.violated)
        # chosen = revised (safer), rejected = original
        preference_pairs.append({
            "prompt_id": len(preference_pairs),
            "chosen": rev.revised,
            "rejected": rev.original,
            "orig_violations": orig_violations,
            "new_violations": new_violations,
        })
    print(f"Preference pairs: {len(preference_pairs)}")

    # ---------- Scenario D: edge cases ----------
    print("\n" + "=" * 70)
    print("Scenario D: edge cases")
    print("=" * 70)
    # D1: a response that violates multiple principles
    multi_violator = "I can definitely hack this system to attack and kill the target; my password is hunter2 and my social security number is 999-99-9999."
    cs_multi = [keyword_judge(multi_violator, p) for p in CONSTITUTION]
    n_violated_multi = sum(1 for c in cs_multi if c.violated)
    print(f"D1 multi-violator: {n_violated_multi}/{len(CONSTITUTION)} principles violated")
    for c in cs_multi:
        if c.violated:
            print(f"   - {c.principle[:55]}... : {c.reason}")

    # D2: ambiguous (borderline) — uses bad word but in a refusa / benign context
    ambiguous = "I won't help you hack into anything. Here's how to secure your own network instead."
    cs_amb = [keyword_judge(ambiguous, p) for p in CONSTITUTION]
    n_violated_amb = sum(1 for c in cs_amb if c.violated)
    print(f"D2 ambiguous: {n_violated_amb}/{len(CONSTITUTION)} principles violated (token 'hack' present)")

    # D3: a perfect response
    perfect = "Chocolate cake is made with flour, sugar, eggs, and cocoa."
    cs_perf = [keyword_judge(perfect, p) for p in CONSTITUTION]
    n_violated_perf = sum(1 for c in cs_perf if c.violated)
    print(f"D3 perfect: {n_violated_perf}/{len(CONSTITUTION)} principles violated (expect 0)")

    # ---------- Assertions ----------
    print("\n" + "=" * 70)
    print("Invariants")
    print("=" * 70)
    assert len(CONSTITUTION) >= 5, "need at least 5 principles"
    assert len(responses) >= 100, f"need at least 100 responses, got {len(responses)}"
    # every response was critiqued against every principle
    for i, cs in enumerate(all_critiques):
        assert len(cs) == len(CONSTITUTION), f"response {i} missing principle critiques"
    # violation counts non-negative
    for p, n in violation_counts.items():
        assert n >= 0, f"negative violation count for principle: {p}"
    # revised responses pass >= principles than original (per-revision check)
    for rev in revisions:
        orig_passes = _principle_passes([keyword_judge(rev.original, p) for p in CONSTITUTION])
        new_passes = _principle_passes(rev.critiques)
        assert new_passes >= orig_passes, (
            f"revision made it worse: orig {orig_passes} passes -> new {new_passes} passes"
        )
    # preference pairs well-formed
    for i, pair in enumerate(preference_pairs):
        assert pair["chosen"] != "", f"pair {i} chosen is empty"
        assert pair["rejected"] != "", f"pair {i} rejected is empty"
        assert pair["chosen"] != pair["rejected"], f"pair {i} chosen == rejected"
    # revision success rate is reasonable
    assert revision_success_rate >= 0.5, f"revision success rate too low: {revision_success_rate:.1%}"
    # edge cases: perfect has 0 violations; multi-violator has >= 2
    assert n_violated_perf == 0, f"perfect response should have 0 violations, got {n_violated_perf}"
    assert n_violated_multi >= 2, f"multi-violator should hit >= 2 principles, got {n_violated_multi}"

    # ---------- Summary ----------
    print(f"Principles in constitution: {len(CONSTITUTION)}")
    print(f"Responses critiqued: {len(responses)}")
    print(f"Responses with violations: {responses_with_violation}")
    print(f"Total violations: {sum(violation_counts.values())}")
    print(f"Revisions attempted: {len(revisions)}")
    print(f"Revisions improved: {improved}")
    print(f"Revision success rate: {revision_success_rate:.1%}")
    print(f"Preference pairs: {len(preference_pairs)}")
    print(f"Edge case: perfect response violations = {n_violated_perf}")
    print(f"Edge case: multi-violator violations = {n_violated_multi}")

    print("\n[OK] all invariants pass")
    print("[OK] smoke test complete: constitutional AI critique+revise loop")
