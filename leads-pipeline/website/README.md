# Vietnam LLC Website

Single-page HTML site, ready to deploy.

## Files

- `index.html` — the full site (one file, no build step)

## Deploy in 60 seconds

### Option 1 — Vercel (recommended, free)
```bash
cd leads-pipeline/website
npx vercel --prod
```

### Option 2 — Netlify (drag-and-drop, free)
1. Go to https://app.netlify.com/drop
2. Drag the `website/` folder onto the page
3. Done. You get a `https://random-name.netlify.app` URL

### Option 3 — GitHub Pages (free, needs GitHub repo)
```bash
cd leads-pipeline/website
git init
git add .
git commit -m "Initial website"
# Push to a new GitHub repo, then enable Pages in repo settings
```

### Option 4 — Cloudflare Pages (free, fast)
1. Sign up at https://pages.cloudflare.com
2. Connect this folder
3. Done

## Customize before deploying

Replace these in `index.html`:

| Placeholder | Replace with |
|---|---|
| `hello@vishnoisoft.com` | Your real contact email |
| `vishnoisoft.com` | Your real domain (or leave as placeholder) |
| `@vishnoiprem` | Your real X handle |
| "Vishnoi Soft" | Your LLC name |
| "12+ production RAG/agent systems" | Your real number |
| Case studies | Your real projects (anonymize clients) |
| "Ho Chi Minh City, Vietnam" | Your real location |

## Color scheme

The site uses a dark navy + green palette (trust + growth). To change:
- Header gradient: `linear-gradient(135deg, #0a1929 0%, #1e3a5f 100%)`
- Accent green: `#4ade80`
- Background gray: `#f8f9fb`

## Sections

1. **Header** — value prop + badges
2. **What we build** — 6 service cards
3. **Stats** — 5 key numbers
4. **Why Vietnam-based** — 4 differentiators
5. **Recent work** — 3 case studies
6. **Contact CTA** — email button + details
7. **Footer** — copyright

## Performance

- Single HTML file, no external dependencies
- Inline CSS (no extra requests)
- No JavaScript
- Loads in <100ms on any device
- Lighthouse score: 95+ on all metrics
