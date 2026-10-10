---
lecture: L07
title: "cdk init — the TypeScript project template"
duration: "10:00"
section: 2
prereqs: ["L06"]
---

# L07 — `cdk init` — The TypeScript Project Template

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 2 — App, Stack, Construct
> **Duration:** 10:00

## Prereqs

L06 — L1/L2/L3 constructs

## Key terms

- **`cdk init`** — the CLI command that scaffolds a new CDK project
  from a template (`--language typescript`).
- **`app.ts`** — the bin entry file. Created by `cdk init` from the
  template.
- **`hello-cdk-stack.ts`** — the default stack file. Lives under
  `lib/`.

## Lecture

`cdk init` writes a working CDK project so you don't have to. The
templates are battle-tested — use them.

```bash
mkdir hello-cdk && cd hello-cdk
cdk init app --language typescript    # ← scaffolds the project

# what you get:
# ├── bin/
# │   └── hello-cdk.ts              # the CDK App entry
# ├── lib/
# │   └── hello-cdk-stack.ts        # the Stack (the only stack)
# ├── test/
# │   └── hello-cdk.test.ts         # a passing snapshot test
# ├── README.md
# ├── cdk.json                     # CLI config ("app" points to bin/hello-cdk.ts)
# ├── jest.config.js               # Jest config wired for TypeScript
# ├── package.json                 # deps: aws-cdk-lib, constructs, jest, ts-jest
# ├── tsconfig.json
# └── .gitignore
```

After `cdk init` finishes:

```bash
npm install                # pulls aws-cdk-lib, constructs, jest, ...
npx cdk synth              # synthesize — should write cdk.out/
npm test                   # run the snapshot test
```

The default template is intentionally minimal — **delete what's
inside the Stack** and replace with what you actually want.
Production-quality projects typically:

- Replace the inline app-id in `bin/*.ts` with something meaningful
- Add a `cdk.context.json` for environment values (L28)
- Add `.npmrc` + `.nvmrc`
- Rename the stack file to match its purpose (`orders-api-stack.ts`,
  not the `hello-cdk-stack.ts` the template ships)

## Hands-on

```bash
mkdir /tmp/cdk-scratch && cd /tmp/cdk-scratch
cdk init app --language typescript
npx cdk synth --quiet | jq 'keys'
# [ "CDKMetadata", "Resources", "Conditions", … ]
```

You don't need to keep this directory — `code/hello-cdk/` in this
course is the canonical starting point.

## Quiz prep

- What command scaffolds a new CDK TypeScript project? (`cdk init app --language typescript`)
- Where does the bin entry live? (`bin/<project>.ts`)
- Where does the default stack live? (`lib/<project>-stack.ts`)

## Further reading

- [`cdk init` reference](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)
- Next up: **L08 — `cdk synth`**
