"""
Hiring agent scorer: rule gates + LLM judge.

The rule gates are absolute. The LLM judge can add nuance (good signal
on the nice-to-haves, narrative for the recruiter), but it cannot
override a must-have miss.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Candidate:
    name: str
    years_experience: int
    skills: list[str]
    portfolio_url: Optional[str] = None


@dataclass
class JobDescription:
    title: str
    must_haves: list[str]
    nice_to_haves: list[str] = field(default_factory=list)
    min_years: int = 0


@dataclass
class Score:
    candidate: str
    rule_passed: bool
    rule_misses: list[str]
    llm_score: float             # 0-1, from the LLM judge
    final_score: float           # rule_passed ? llm_score : capped at 0.4 (shortlist threshold is 0.7)
    shortlist: bool


def rule_check(c: Candidate, jd: JobDescription) -> tuple[bool, list[str]]:
    misses = []
    skill_set = {s.lower() for s in c.skills}
    for must in jd.must_haves:
        if must.lower() not in skill_set:
            misses.append(f"missing must-have: {must}")
    if c.years_experience < jd.min_years:
        misses.append(f"under min years: {c.years_experience} < {jd.min_years}")
    return (len(misses) == 0, misses)


def llm_judge_score(c: Candidate, jd: JobDescription) -> float:
    """Toy judge. Real impl: LLM with a calibrated prompt.

    Returns a 0-1 score based on how well the candidate's narrative
    matches the role. Rule-gated: only meaningful when rule_check passes.
    """
    skill_match = len(set(s.lower() for s in c.skills) & set(s.lower() for s in jd.must_haves + jd.nice_to_haves))
    total = max(1, len(jd.must_haves) + len(jd.nice_to_haves))
    return min(1.0, skill_match / total)


def score_candidate(c: Candidate, jd: JobDescription) -> Score:
    rule_passed, rule_misses = rule_check(c, jd)
    llm = llm_judge_score(c, jd)
    # Must-have miss caps the final score below the shortlist threshold.
    final = llm if rule_passed else min(0.4, llm)
    return Score(
        candidate=c.name,
        rule_passed=rule_passed,
        rule_misses=rule_misses,
        llm_score=llm,
        final_score=final,
        shortlist=final >= 0.7,
    )


if __name__ == "__main__":
    jd = JobDescription(
        title="Senior Data Engineer",
        must_haves=["Spark", "Kafka", "AWS"],
        nice_to_haves=["Iceberg", "dbt", "Flink"],
        min_years=5,
    )
    candidates = [
        Candidate("Alice", 7, ["Spark", "Kafka", "AWS", "Iceberg", "dbt"]),
        Candidate("Bob",   4, ["Spark", "Kafka", "AWS"]),                # under min years
        Candidate("Carol", 6, ["Spark", "AWS", "Flink"]),                # missing Kafka
        Candidate("Dave",  8, ["Spark", "Kafka", "AWS", "Flink", "dbt"]),
    ]
    for c in candidates:
        s = score_candidate(c, jd)
        print(f"{c.name}: rule_passed={s.rule_passed} final={s.final_score:.2f} shortlist={s.shortlist} misses={s.rule_misses}")
