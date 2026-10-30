# Frameworks — Which One to Use When

Three frameworks appear across the rounds. They overlap, so pick by question type.

| Framework | Use when | Steps |
|-----------|----------|-------|
| **ADR** (Architecture Decision Record) | Any "why did you choose X" technical question (Round 2) | Context → Options → Decision → Trade-offs → Consequences |
| **Migration Framework** | The scenario is a migration, at the technical-plan level (Rounds 2–3) | Assess → Plan → Migrate → Validate → Optimize |
| **Client Engagement Model** | Case study or any client-delivery question; the outer wrapper (Round 3) | Discover → Design → Deliver → Operate |

## How they nest

```
Client Engagement Model (outer)
  Discover : Assess
  Design   : Plan  (+ ADRs for each key decision)
  Deliver  : Migrate → Validate
  Operate  : Optimize
```

Rule of thumb: lead with the Engagement Model for case studies, drop into the Migration Framework for the technical plan, and use an ADR for each decision you defend.

## ADR template

```
Title:        <decision>
Context:      <business and technical constraints>
Options:      A / B / C with one-line pros and cons
Decision:     <chosen option and why>
Trade-offs:   <what you give up>
Consequences: <risks, follow-ups, how you'd revisit>
```

## Migration strategies (6 R's)
Rehost, Replatform, Refactor, Repurchase, Retire, Retain. For each, know when to use it, the main risk and a rough timeline.
