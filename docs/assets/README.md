# Assets

Drop screenshots, demo GIFs, and diagrams here so they live next to the README
that references them.

## Conventions

- **Name them after the project folder**, not the date:
  - `scb-aml-architecture.png`
  - `realtime-stock-grafana.png`
  - `enterprise-rag-demo.gif`
- **Prefer `*-demo.gif`** for ≤15-sec animated clips (under 5 MB).
- **Prefer `*.png`** for static screenshots / architecture diagrams.
- **Co-locate with code** when an image is used in only one inner README.
  Keep this folder for assets linked from the **root README**.

## Where to capture / record

- Terminal screen-casts: **asciinema** (free, embeds in README) or **QuickTime** → GIF.
- Architecture diagrams: **Excalidraw / draw.io** → PNG.
- Streaming dashboards: **Grafana** → "Share → Direct link rendered image"
  (or a clean screenshot during a public-friendly data run).
- RAG web UI: short **Loom / OBS / screenpresso** capture.

## Sizes

| Use | Size |
|---|---|
| Inline README image | 1280 px wide, ≤ 200 KB |
| Hero / above-the-fold | 1920 × 1080 (GIF ≤ 8 MB) |
| Social preview | 1280 × 640 (see `.github/SOCIAL_PREVIEW.md`) |

Once an asset is added, reference it from the relevant README:

```markdown
![demo](docs/assets/realtime-stock-demo.gif)
```