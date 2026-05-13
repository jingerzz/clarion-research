# Clarion Research

Point-in-time, SEO-friendly snapshots of investment thesis briefs published by
**[Clarion Intelligence Systems](https://www.clarionintelligencesystems.com)**.

Each snapshot is a fully self-contained static HTML page (inline styles, no
external CSS/JS bundles) plus structured `JSON` and source `Markdown` companions.
This repository is the **source feed** for the official thesis pages on
`clarionintelligencesystems.com` — the website pulls from here, re-templates as
needed, and serves the canonical URLs.

> **Not investment advice.** All briefs are research outputs from Clarion's
> AI-native infrastructure. Point-in-time. For informational purposes only.

---

## What's in here

```
clarion-research/
├── theses/                    # one folder per ticker
│   ├── iren/
│   │   ├── index.html         # standalone HTML — inline styles, portable
│   │   ├── thesis.md          # source markdown thesis (CMS-friendly)
│   │   ├── thesis.json        # structured metadata (action, score, price, tags)
│   │   └── snapshot.json      # capture provenance (timestamp, source URL, sizes)
│   ├── onon/
│   ├── ttd/
│   ├── deck/
│   ├── meta/
│   ├── msft/
│   ├── googl/
│   ├── ffiv/
│   └── ibm/
├── tools/
│   └── sp500/                 # market regime dashboard (tooling example)
│       └── index.html
├── index/
│   └── theses.json            # rollup index — all tickers, actions, scores, paths
├── sitemap.xml                # canonical URL sitemap (points at .com)
├── robots.txt
├── scripts/
│   └── build.py               # regenerates everything from snapshots-raw/
└── .github/workflows/
    └── weekly-snapshot.yml    # optional: weekly automated re-snapshot
```

---

## Quick consume patterns

### 1. Embed in a Next.js / Astro / Webflow site

Read `index/theses.json` once at build time; render a `/research` landing page
plus one route per slug:

```js
// Next.js example
import theses from "./clarion-research/index/theses.json" assert { type: "json" };

export async function getStaticPaths() {
  return {
    paths: theses.theses.map(t => ({ params: { slug: t.slug } })),
    fallback: false,
  };
}
```

### 2. Drop the standalone HTML behind a reverse proxy

Each `theses/<slug>/index.html` is fully portable. You can serve them as-is
under `/research/<slug>` with any static host. The `<link rel="canonical">`
already points at `https://www.clarionintelligencesystems.com/research/<slug>`.

### 3. Re-template with your own design system

Use `thesis.md` for the prose and `thesis.json` for the structured fields
(action, score, price, tags, kill conditions). The HTML snapshot is the
reference rendering — your site can render it in any style while keeping the
data canonical.

---

## SEO contract

Every `index.html` ships with:

- `<title>` + `<meta name="description">` — ticker-specific
- `<link rel="canonical">` → the .com URL
- Open Graph + Twitter card tags, with absolute image URLs
- JSON-LD `Article` schema (author: Jing Xie, publisher: Clarion Intelligence Systems)
- `<meta name="robots" content="index, follow">`
- Snapshot provenance: `clarion:snapshot-date`, `clarion:source`

`sitemap.xml` and `robots.txt` at the repo root point at the canonical .com URLs
so your production site can host them directly.

---

## Regenerating snapshots

Snapshots are produced from the live React routes at
[https://cis.zo.space](https://cis.zo.space) (the Clarion sandbox).

```bash
# 1. Render each route → snapshots-raw/<slug>.html
#    (uses agent-browser / any headless Chromium)
./scripts/snapshot.sh

# 2. Process raw snapshots into per-thesis bundles + SEO heads
python3 scripts/build.py
```

The optional GitHub Actions workflow at
`.github/workflows/weekly-snapshot.yml` re-runs this every Sunday and opens a
PR with the diff, so every snapshot is a reviewable commit.

---

## License

Source code (build scripts, templates): MIT.
Research content (thesis text, charts, valuations): © Clarion Intelligence
Systems LLC. Reuse with attribution and a link back to the canonical URL.

---

## Author

**Jing Xie** — Founder & President, Clarion Intelligence Systems LLC
[clarionintelligencesystems.com](https://www.clarionintelligencesystems.com)
