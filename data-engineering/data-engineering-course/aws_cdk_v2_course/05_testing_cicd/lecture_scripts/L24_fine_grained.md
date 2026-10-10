---
lecture: L24
title: "Fine-grained assertions — hasResourceProperties, objectLike"
duration: "12:00"
section: 5
prereqs: ["L23"]
---

# L24 — Fine-Grained Assertions

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — Testing, Snapshots, Assertions, CI/CD
> **Duration:** 12:00

## Prereqs

L23 — Snapshot tests

## Key terms

- **`Match.objectLike(obj)`** — partial-match an object: the
  asserted keys must be present, the rest is wildcard.
- **`Match.arrayWith([…])`** — partial-match an array: the asserted
  elements must be present, the rest is wildcard.
- **`Match.stringLikeRegexp(re)`** — match a string against a
  regular expression.
- **`Match.serializedJson(inner)`** — match a stringified JSON
  against an inner matcher.
- **`Match.anyValue()`** — match anything (incl. `undefined`).

## Lecture

Subset matching (`hasResourceProperties({Foo: 1})` matches
`{Foo: 1, Bar: 2, Baz: 3}`) is great until your resource has a
nested object. Then you need **`Match.*` helpers** to say "I care
about *these* keys at *this* level":

```ts
import { Match } from 'aws-cdk-lib/assertions';

template.hasResourceProperties('AWS::IAM::Role', {
  AssumeRolePolicyDocument: Match.objectLike({
    Statement: Match.arrayWith([
      Match.objectLike({
        Effect: 'Allow',
        Principal: { Service: 'lambda.amazonaws.com' },
        Action: 'sts:AssumeRole',
      }),
    ]),
  }),
});
```

Common matchers:

| Matcher | Use |
|---|---|
| `objectLike(o)` | partial object match |
| `arrayWith([...])` | partial array match (subset) |
| `arrayEquals([...])` | exact array match |
| `stringLikeRegexp(re)` | string regex match |
| `anyValue()` | matches anything, incl. undefined |
| `serializedJson(inner)` | parses a JSON string, matches inner |
| `absent()` | asserts the field is *not* present |

A worked example — assert the Lambda's environment includes
`BUCKET_NAME` (and is otherwise allowed to be anything):

```ts
template.hasResourceProperties('AWS::Lambda::Function', {
  Environment: {
    Variables: Match.objectLike({
      BUCKET_NAME: Match.anyValue(),
    }),
  },
});
```

For Step Functions (L18), the state machine definition is a
stringified JSON:

```ts
template.hasResourceProperties('AWS::States::StateMachine', {
  DefinitionString: Match.serializedJson(Match.objectLike({
    StartAt: 'InvokeOrder',
    States: Match.objectLike({
      Done: Match.objectLike({ Type: 'Pass' }),
    }),
  })),
});
```

## Hands-on

Open `04_appsync_stepfunctions/code/app-sync-sfn/test/app-sync-sfn.test.ts`
and look at the 7 assertions. Notice the use of `Match.stringLikeRegexp`
for the schema and `Match.serializedJson` for the state-machine
definition.

## Quiz prep

- Which matcher asserts a partial array match? (`arrayWith`)
- Which matcher asserts a stringified JSON? (`serializedJson`)
- What's the difference between `objectLike` and `exactValue`?
  (objectLike is a subset match; exactValue requires every field)

## Further reading

- [Match helpers](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.assertions.Match.html)
- Next up: **L25 — CI/CD**
