# Chapter Authoring Spec — Google Dataflow with Apache Beam

You are writing chapters for a production-quality technical course on
**Google Dataflow with Apache Beam**. The course lives at
`data-engineering/data-Course/google/Dataflow/` in the repo.

## Hard requirements — a linter checks ALL of these

1. **Filename**: `NN-kebab-case.md`, zero-padded 2 digits, lowercase,
   hyphens only. E.g. `02-architecture-and-portability.md`.
2. **First line**: `# N.M — Chapter Title` where `N.M` is the module and
   chapter number, and the dash is an em dash `—` (U+2014) with spaces.
3. **Second line**: a metadata line starting with `> **`, in the form:
   `> **Section N · Module Name · Lecture N.M · 6:30**`
4. **Exactly these 8 H2 sections, in this order, all present**:
   ```
   ## 🎯 What you will learn
   ## 🧠 Concept
   ## 🛠️ Hands-On
   ## 🛠️ Common Errors and Fixes
   ## 💡 Production Notes
   ## 🔑 Key Takeaways
   ## 📚 Practice Exercises
   ## 📖 Further Reading
   ```
   You may add extra `## 🧠 <Subtopic>` H2 sections between `## 🧠 Concept`
   and `## 🛠️ Hands-On` ONLY. No other H2 sections.
5. **The `## 🧠 Concept` section must come before `## 🛠️ Hands-On`**, and
   every other section in the order listed above.
6. **At least one fenced code block** in the chapter.
7. **The `## 📚 Practice Exercises` section must contain at least one
   numbered exercise** matching `^\d+\.\s+\S` (so `1. **Title.** ...`).
8. **Every `python` fenced block must be syntactically valid Python on
   its own** — the linter runs `ast.parse` on each one. A bare pipeline
   fragment like `| "Label" >> beam.Map(x)` is NOT valid Python; mark
   such fragments with a ` ```text ` fence instead. Fence fragments with
   `bash`, `text`, `sql`, or `yaml` freely.
9. **Every `beam.<attr>` access in a `python` fence must exist in the
   installed apache-beam SDK** — the linter checks with `hasattr`. Use
   real API names only. (`beam.combiners.Count.PerKey()` is real;
   `beam.combiners.Sum` is NOT — use `beam.CombinePerKey(sum)`.)
10. **Transform labels must be unique within one Python fence / function
    scope.** `p | "Same" >> ...` twice in the same function is an error.
    Different functions may reuse the same label.
11. **No leftover markers**: no `TODO`, `FIXME`, `XXX`, `HACK`, `CHANGEME`,
    `PLACEHOLDER_VALUE`, `your-project-id` anywhere in the file.
12. **Placeholders** like `YOUR_PROJECT_ID`, `YOUR_BUCKET` are ALLOWED
    (they are in the safe list) but should be inside `bash` blocks.
13. **Every relative markdown link must resolve** — if you link to
    `../resources/SETUP.md`, that file must exist. Prefer plain URLs for
    external links, and be careful with relative links.

## Content requirements

- **Depth over breadth.** Each chapter should be substantial — aim for
  roughly 400–700 lines of markdown. A chapter that skims is a failed
  chapter.
- **The `## 🧠 Concept` section** explains the *why* and the mechanism,
  not just the API. Include tables where they clarify a comparison.
- **The `## 🛠️ Hands-On` section** must be runnable. It should work
  against the course project. The working directory when a reader runs
  these is the course root
  `data-engineering/data-Course/google/Dataflow/`.
- **Real code.** Use the actual project modules where relevant:
  - `project/transforms.py` — pure logic: `parse_order_line`,
    `parse_event_payload`, `normalise_currency`, `is_valid_order`,
    `build_revenue_summary`, `dedup_key`, `window_key`; Beam half:
    `ParseOrderFn`, `RevenueByRegionFn`, `to_summary_row`,
    `format_summary_csv`, `write_summary_to_csv`.
  - `project/beam_options.py` — `build_options`, `resolve_runner`,
    `is_local`, `apply_dataflow_defaults`, `pipeline_options_summary`,
    `describe_environment`, `load_dotenv`.
  - `project/batch_pipeline.py` — `build_pipeline(pipeline, *, input_path,
    output_path, bigquery_table, statuses, reference_path)`.
  - `project/streaming_pipeline.py` — `build_streaming_pipeline(...)`.
  - `project/requirements.txt`, `project/tests/test_transforms.py`,
    `project/tests/test_pipelines.py`.
  - `resources/sample_data.py` — generates `./sample_data/` with
    `orders.csv`, `orders.ndjson`, `events.ndjson`, `events.csv`,
    `malformed_orders.csv`, `product_reference.ndjson`, `summary.json`.
    Flags: `--output-dir`, `--hot-key-rate`, `--late-events`.
  - `resources/audit_course.py` (the linter), `resources/test_course.py`
    (structural tests), `resources/beam_client.py`,
    `resources/SETUP.md`, `resources/CHEATSHEET.md`,
    `resources/GLOSSARY.md`, `resources/FAQ.md`.
- **The `## 🛠️ Common Errors and Fixes` section** must show the actual
  error message and the actual fix. Real messages from Beam, verbatim.
- **The `## 💡 Production Notes` section** gives operational wisdom:
  failure modes, costs, scale numbers, what to do at 3am.
- **The `## 📚 Practice Exercises` section** has 4–6 exercises. Each
  should be a real task with enough detail to be attempted, and where
  useful give the expected answer inline.
- **The `## 📖 Further Reading` section** lists 3–6 real URLs with titles.
  Use genuine Apache Beam / Google Cloud documentation URLs.
- **No emoji beyond the mandated section headers.** No chatty filler.
- Write in a confident, precise, engineering-register voice. Explain
  trade-offs honestly, including where the "obvious" advice is wrong.
- **Numbers should be plausible and specific** (costs, latencies, worker
  counts) rather than vague.
- Do NOT invent APIs. If unsure whether an API exists, prefer one you are
  certain about (`beam.Map`, `beam.FlatMap`, `beam.Filter`,
  `beam.Flatten`, `beam.ParDo`, `beam.CombinePerKey`,
  `beam.GroupByKey`, `beam.CoGroupByKey`, `beam.Reshuffle`,
  `beam.WindowInto`, `beam.Create`, `beam.combiners.Count.PerKey`,
  `beam.io.ReadFromText`, `beam.io.WriteToText`,
  `beam.io.ReadFromPubSub`, `beam.io.WriteToBigQuery`,
  `beam.transforms.window.FixedWindows`,
  `beam.transforms.trigger.AfterCount`,
  `beam.transforms.trigger.AfterWatermark`,
  `beam.transforms.trigger.AccumulationMode`,
  `beam.pvalue.AsDict`, `beam.pvalue.AsIter`,
  `beam.window.TimestampedValue`, `beam.DoFn`).
- The `## 🔑 Key Takeaways` section uses `- ` bullets, 5–8 of them.
