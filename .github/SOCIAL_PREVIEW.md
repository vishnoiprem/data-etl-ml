# Social preview / Open Graph image

GitHub renders this on the repo card, in search, in stars feeds, and in any
embed that uses OpenGraph.

## Spec

- **Filename:** `.github/social-preview.png`
- **Recommended size:** **1280 × 640 px** (also accepts 1200×630)
- **Max file size:** **1 MB**
- **Format:** PNG (preferred), JPG
- **Background:** contrasty, no fine detail — viewers see this at ~250 px wide

## Layout suggestion

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Prem Vishnoi                                            │
│  Data · ETL · ML · AI Engineering                        │
│                                                          │
│  Spark · Kafka · Flink · Airflow · AWS Bedrock           │
│  LangChain · LangGraph · RAG · Multi-Agent               │
│                                                          │
│  15+ production-style projects · 1 repo                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## How to generate

Easiest — open `docs/assets/social-preview.html` (Figma / Keynote / Canva /
Pixelmator works too), export PNG at 1280×640, save as
`.github/social-preview.png`.

Colors to match this README's badge palette:

- Background: `#0d1117` (GitHub dark)
- Accent:     `#FF9900` (AWS)
- Secondary:  `#E25A1C` (Spark)
- Text:       `#f0f6fc`

After dropping the PNG, GitHub picks it up automatically — no commit message
needed. To force a refresh in the GitHub UI: Settings → General → "Social
preview" → Upload → Save.