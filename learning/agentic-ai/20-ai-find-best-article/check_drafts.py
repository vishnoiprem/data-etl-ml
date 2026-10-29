#!/usr/bin/env python3
"""Validate drafts against the project rules: word count, banned phrases, placeholders, structure."""
import re, sys, glob, os

BANNED = [
    "delve", "game-changer", "game changer", "unlock the power", "in conclusion",
    "it's important to note", "it is important to note", "in today's fast-paced world",
    "in today's fast paced world", "it is worth noting", "it's worth noting",
    "revolutionize", "revolutionise", "seamless", "leverage", "robust", "cutting-edge",
    "cutting edge", "ever-evolving landscape", "dive deep", "dives deep",
    "navigate the landscape", "tapestry", "testament to", "in the realm of",
    "realm of", "unlock", "supercharge", "skyrocket", "paradigm shift",
    "at the forefront of", "without further ado", "picture this", "imagine a world where",
    "the possibilities are endless", "sits at the intersection of", "paves the way for",
    "more than ever before", "in an era where", "synergy", "operationalize",
    "best-in-class", "next-level", "state-of-the-art", "actionability",
    "let's dive in", "let's unpack", "let's take a closer look",
    "this is where things get interesting", "the key takeaway is",
    "whether you're", "in today's world", "game-changing",
]

FP_BAD = [
    r"\bI (tested|ran|tried|used|built|shipped|deployed|measured|benchmarked|evaluated|worked)\b",
    r"\bwhen I\b", r"\bin my (team|experience|lab|previous)", r"\bI found that\b",
    r"\bI noticed\b", r"\bI learned\b", r"\bI have (used|tested|built|run)\b",
    r"\bwe (found|measured|tested|ran|noticed|learned) that\b",
    r"\bmy (team|experience|project|workflow)\b",
]


def body_of(text):
    i = text.find("\n---\n", 5)
    body = text[i + 5:] if i > 0 else text
    j = body.find("## Sources")
    return body[:j] if j > 0 else body


def full_body(text):
    i = text.find("\n---\n", 5)
    return text[i + 5:] if i > 0 else text


def check(path):
    t = open(path).read()
    problems = []
    body = body_of(t)
    full = full_body(t)
    words = len(body.split())
    if not (1000 <= words <= 1800):
        problems.append(f"body word count {words} outside 1000-1800")
    low = full.lower()
    for b in BANNED:
        if b in low:
            # find line
            for n, line in enumerate(full.split("\n"), 1):
                if b in line.lower():
                    problems.append(f"BANNED '{b}' line {n}: {line.strip()[:80]}")
                    break
    for pat in FP_BAD:
        for m in re.finditer(pat, full, re.I):
            s = max(0, m.start() - 40)
            problems.append(f"FP-LOOK '{m.group(0)}': ...{full[s:m.end()+40]}...")
    if "## Disclosure" not in t:
        problems.append("missing Disclosure section")
    if "## Sources" not in t:
        problems.append("missing Sources section")
    if "[AUTHOR EXPERIENCE" not in t:
        problems.append("no [AUTHOR EXPERIENCE] placeholder")
    if not re.search(r"^rubric_score:", t, re.M):
        problems.append("no rubric_score")
    if not re.search(r"^hard_fail:", t, re.M):
        problems.append("no hard_fail")
    if not re.search(r"^distinctness_angle:", t, re.M):
        problems.append("no distinctness_angle")
    for fld in ["title:", "subtitle:", "tags:", "platform:", "target_length:", "word_count:",
                "disclosure:", "sources_count:", "author_experience_placeholders:"]:
        if not re.search(r"^" + re.escape(fld), t, re.M):
            problems.append(f"missing front-matter {fld}")
    # source count check
    m = re.search(r"^sources_count: (\d+)", t, re.M)
    if m:
        listed = len(re.findall(r"^\s*-\s.*https?://", t, re.M))
        if listed < 6:
            problems.append(f"only {listed} source bullets with URLs (need >=6)")
    # closing question
    tail = full.strip().split("\n")
    q = [l for l in tail if l.strip().endswith("?")]
    if not q:
        problems.append("no closing question mark found")
    return words, problems


if __name__ == "__main__":
    pats = sys.argv[1:] or ["draft-*.md"]
    files = []
    for p in pats:
        files.extend(sorted(glob.glob(p)))
    bad = 0
    for f in files:
        w, probs = check(f)
        if probs:
            bad += 1
            print(f"\n=== {os.path.basename(f)} (body {w}w) ===")
            for p in probs:
                print("  -", p)
    print(f"\n{len(files)} files checked, {bad} with problems")
