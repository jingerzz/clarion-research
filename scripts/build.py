#!/usr/bin/env python3
"""
Build the clarion-research repo from raw rendered snapshots.

Inputs:
  - snapshots-raw/<route>.html  (full <html> captured via headless browser)
  - ~/clarion/theses/<TICKER>.md  (source markdown thesis, optional)

Outputs:
  - theses/<ticker>/index.html  (SEO-friendly, portable, inline styles preserved)
  - theses/<ticker>/thesis.md   (markdown copy)
  - theses/<ticker>/thesis.json (structured metadata)
  - theses/<ticker>/snapshot.json (timestamp + provenance)
  - index/theses.json           (rollup)
  - sitemap.xml
  - robots.txt
"""
from __future__ import annotations
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "snapshots-raw"
OUT = ROOT
THESES_DIR = OUT / "theses"
INDEX_DIR = OUT / "index"
CLARION_THESES = Path.home() / "clarion" / "theses"

CANONICAL_BASE = "https://www.clarionintelligencesystems.com"
SOURCE_BASE = "https://cis.zo.space"
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")
SNAPSHOT_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Catalog from homepage scrape — ticker → metadata
THESES = {
    "iren": {
        "ticker": "IREN",
        "company": "Iris Energy Limited",
        "action": "HOLD",
        "score": 65,
        "price_usd": 53.13,
        "tagline": "Vertically integrated AI infrastructure compounder. NVIDIA-validated with a $3.4B AI cloud contract. The market still prices it like a crypto miner.",
        "tags": ["AI Infrastructure", "Data Centers", "NVIDIA Contract"],
        "bucket": "Systematic",
        "md_file": "IREN.md",
        "title": "IREN Investment Thesis — Vertically Integrated AI Infrastructure Compounder",
    },
    "onon": {
        "ticker": "ONON",
        "company": "On Holding AG",
        "action": "ADD",
        "score": 80,
        "price_usd": 33.84,
        "tagline": "Swiss premium performance running brand growing at 3× the market rate. Record Q1 2026 margins at near 52-week low — mispricing worth owning.",
        "tags": ["Footwear", "Growth", "Margin Expansion"],
        "bucket": "Value",
        "md_file": None,  # no source md in clarion/theses
        "title": "ONON Investment Thesis — Premium Performance Brand at 52W Low",
    },
    "ttd": {
        "ticker": "TTD",
        "company": "The Trade Desk, Inc.",
        "action": "HOLD",
        "score": 70,
        "price_usd": 20.51,
        "tagline": "Largest independent DSP at 11× FCF. CEO Jeff Green bought $148M at $24.71 — stock now 17% below his cost. $1.3B net cash (13.6% of MC), zero debt. Amazon fear priced in.",
        "tags": ["AdTech", "CTV", "CEO $148M Insider Buy"],
        "bucket": "Value",
        "md_file": "TTD.md",
        "title": "TTD Investment Thesis — Largest Independent DSP at 11× FCF",
    },
    "deck": {
        "ticker": "DECK",
        "company": "Deckers Outdoor Corporation",
        "action": "WATCHLIST",
        "score": 68,
        "price_usd": 102.72,
        "tagline": "Two iconic brands (UGG + HOKA) running ahead of their multiple. 14.3× P/E on 40% ROE and 57.9% gross margins. HOKA is the underappreciated second engine.",
        "tags": ["Footwear", "Value", "HOKA Growth Engine"],
        "bucket": "Value",
        "md_file": "DECK.md",
        "title": "DECK Investment Thesis — UGG + HOKA at 14.3× P/E on 40% ROE",
    },
    "meta": {
        "ticker": "META",
        "company": "Meta Platforms, Inc.",
        "action": "DRAFT",
        "score": 54.6,
        "price_usd": 603.00,
        "tagline": "Cheapest large-cap AI at 22x trailing — ad moat + capex cycle peak = re-rate. Operating cash flow compounded at 28% CAGR: $71B→$116B over 3 years.",
        "tags": ["AI Advertising", "Llama Ecosystem", "Capex Peak Play"],
        "bucket": "Value",
        "md_file": "META.md",
        "title": "META Investment Thesis — Cheapest Large-Cap AI at 22× Trailing",
    },
    "msft": {
        "ticker": "MSFT",
        "company": "Microsoft Corporation",
        "action": "DRAFT",
        "score": 54.2,
        "price_usd": 407.77,
        "tagline": "AI monetization already happening at scale — Copilot × Azure = durable earnings compounder. 46.3% operating margin is best-in-class capital efficiency.",
        "tags": ["Copilot", "Azure AI", "Enterprise Moat"],
        "bucket": "Value",
        "md_file": "MSFT.md",
        "title": "MSFT Investment Thesis — Copilot × Azure Earnings Compounder",
    },
    "googl": {
        "ticker": "GOOGL",
        "company": "Alphabet Inc.",
        "action": "DRAFT",
        "score": 57,
        "price_usd": 387.35,
        "tagline": "Seven AI bets in one fortress balance sheet — antitrust overhang = entry discount, not thesis break. Near 52W high; patience entry required.",
        "tags": ["Seven AI Layers", "Google Cloud Gemini", "Near 52W High"],
        "bucket": "Value",
        "md_file": "GOOGL.md",
        "title": "GOOGL Investment Thesis — Seven AI Bets in One Fortress Balance Sheet",
    },
    "ffiv": {
        "ticker": "FFIV",
        "company": "F5, Inc.",
        "action": "DRAFT",
        "score": 43,
        "price_usd": 354.98,
        "tagline": "The invisible AI inference rails. $7.4B buyback (37% of market cap) is the floor — AI inference demand for on-prem load balancing is the ceiling.",
        "tags": ["AI Inference ADC Moat", "Buyback Yield", "Hidden Gem"],
        "bucket": "Value",
        "md_file": "FFIV.md",
        "title": "FFIV Investment Thesis — The Invisible AI Inference Rails",
    },
    "ibm": {
        "ticker": "IBM",
        "company": "International Business Machines Corporation",
        "action": "DRAFT",
        "score": 34.4,
        "price_usd": 219.22,
        "tagline": "Enterprise AI governance at the cheapest valuation. Regulated industries can't use OpenAI APIs — Watsonx.governance is purpose-built for that constraint. At 52W low.",
        "tags": ["Watsonx AI Governance", "At 52W Low", "Hybrid Cloud"],
        "bucket": "Value",
        "md_file": "IBM.md",
        "title": "IBM Investment Thesis — Enterprise AI Governance at 52W Low",
    },
}

# Tooling-example pages (not thesis briefs)
TOOLING = {
    "sp500": {
        "title": "S&P 500 Market Regime Dashboard — Clarion Intelligence Systems",
        "description": "Live market regime dashboard: SPY/TLT trend, equity hurdle vs. Shiller CAPE, breadth signals. Drives the Clarion Value Bucket allocation policy.",
        "kind": "dashboard",
    },
}

BUILT_ON_ZO_PATTERN = re.compile(
    r'<a[^>]*data-zo-built-on-badge[^>]*>.*?</a>',
    re.DOTALL | re.IGNORECASE,
)

ROOT_DIV_PATTERN = re.compile(
    r'<div id="root">(.*)</div>\s*$',
    re.DOTALL,
)


def extract_body(raw_html: str) -> str:
    """Pull the contents of <body> (or <div id=root>), strip Built-on-Zo badge."""
    # Try body first
    m = re.search(r"<body[^>]*>(.*)</body>", raw_html, flags=re.DOTALL | re.IGNORECASE)
    if m:
        body = m.group(1)
    else:
        body = raw_html
    body = BUILT_ON_ZO_PATTERN.sub("", body)
    return body.strip()


def build_seo_head(*, title: str, description: str, canonical: str, ticker: str | None,
                   og_image: str = "/assets/clarion-og-1200x628.png") -> str:
    og_image_abs = f"{CANONICAL_BASE}{og_image}" if og_image.startswith("/") else og_image
    safe_desc = description.replace('"', "&quot;")
    safe_title = title.replace('"', "&quot;")
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "author": {
            "@type": "Person",
            "name": "Jing Xie",
            "url": CANONICAL_BASE,
            "jobTitle": "Founder & President, Clarion Intelligence Systems",
        },
        "publisher": {
            "@type": "Organization",
            "name": "Clarion Intelligence Systems",
            "url": CANONICAL_BASE,
            "logo": {
                "@type": "ImageObject",
                "url": f"{CANONICAL_BASE}/assets/clarion-logo.png",
            },
        },
        "datePublished": NOW,
        "dateModified": NOW,
        "mainEntityOfPage": canonical,
        "image": og_image_abs,
    }
    if ticker:
        jsonld["about"] = {
            "@type": "Corporation",
            "tickerSymbol": ticker,
        }
    jsonld_block = json.dumps(jsonld, indent=2)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{safe_title}</title>
  <meta name="description" content="{safe_desc}" />
  <meta name="robots" content="index, follow" />
  <meta name="author" content="Jing Xie, Clarion Intelligence Systems" />
  <link rel="canonical" href="{canonical}" />

  <!-- Open Graph -->
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{safe_title}" />
  <meta property="og:description" content="{safe_desc}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{og_image_abs}" />
  <meta property="og:site_name" content="Clarion Intelligence Systems" />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{safe_title}" />
  <meta name="twitter:description" content="{safe_desc}" />
  <meta name="twitter:image" content="{og_image_abs}" />

  <!-- Snapshot provenance -->
  <meta name="clarion:snapshot-date" content="{SNAPSHOT_DATE}" />
  <meta name="clarion:source" content="{SOURCE_BASE}" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; }}
    button {{ font-family: inherit; }}
    a {{ color: inherit; text-decoration: none; }}
    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; transition: none !important; }}
    }}
  </style>

  <script type="application/ld+json">
{jsonld_block}
  </script>
</head>
<body>
"""


HTML_FOOTER = """
</body>
</html>
"""


def build_thesis_page(slug: str, meta: dict) -> None:
    raw = (RAW / f"{slug}.html").read_text(encoding="utf-8")
    body = extract_body(raw)
    canonical = f"{CANONICAL_BASE}/research/{slug}"
    head = build_seo_head(
        title=meta["title"],
        description=meta["tagline"],
        canonical=canonical,
        ticker=meta["ticker"],
    )
    out_dir = THESES_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(head + body + HTML_FOOTER, encoding="utf-8")

    # thesis.json
    thesis_json = {
        "slug": slug,
        "ticker": meta["ticker"],
        "company": meta["company"],
        "action": meta["action"],
        "score": meta["score"],
        "price_usd": meta["price_usd"],
        "tagline": meta["tagline"],
        "tags": meta["tags"],
        "bucket": meta["bucket"],
        "canonical_url": canonical,
        "source_url": f"{SOURCE_BASE}/{slug}",
        "snapshot_date": SNAPSHOT_DATE,
        "snapshot_iso": NOW,
        "title": meta["title"],
        "publisher": "Clarion Intelligence Systems",
        "author": "Jing Xie",
        "disclaimer": "Not investment advice. For informational purposes only.",
    }
    (out_dir / "thesis.json").write_text(json.dumps(thesis_json, indent=2), encoding="utf-8")

    # Copy markdown source if available
    if meta.get("md_file"):
        src_md = CLARION_THESES / meta["md_file"]
        if src_md.exists():
            md_text = src_md.read_text(encoding="utf-8")
            (out_dir / "thesis.md").write_text(md_text, encoding="utf-8")
        else:
            (out_dir / "thesis.md").write_text(
                f"# {meta['ticker']} — Source Markdown Not Available\n\n"
                f"This snapshot was rendered from {SOURCE_BASE}/{slug}.\n"
                f"The source markdown was not present at build time.\n",
                encoding="utf-8",
            )
    else:
        (out_dir / "thesis.md").write_text(
            f"# {meta['ticker']} — {meta['company']}\n\n"
            f"**Action:** {meta['action']}  |  **Score:** {meta['score']}  |  **Price:** ${meta['price_usd']:.2f}\n\n"
            f"{meta['tagline']}\n\n"
            f"Snapshot: {SNAPSHOT_DATE}. Source: {SOURCE_BASE}/{slug}\n",
            encoding="utf-8",
        )

    # snapshot.json (provenance)
    snap = {
        "slug": slug,
        "captured_at": NOW,
        "source_url": f"{SOURCE_BASE}/{slug}",
        "canonical_url": canonical,
        "raw_html_bytes": len(raw),
        "rendered_html_bytes": (out_dir / "index.html").stat().st_size,
    }
    (out_dir / "snapshot.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")
    print(f"  built theses/{slug}/")


def build_tooling_page(slug: str, meta: dict) -> None:
    raw = (RAW / f"{slug}.html").read_text(encoding="utf-8")
    body = extract_body(raw)
    canonical = f"{CANONICAL_BASE}/tools/{slug}"
    head = build_seo_head(
        title=meta["title"],
        description=meta["description"],
        canonical=canonical,
        ticker=None,
    )
    out_dir = OUT / "tools" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(head + body + HTML_FOOTER, encoding="utf-8")
    (out_dir / "snapshot.json").write_text(json.dumps({
        "slug": slug,
        "kind": meta["kind"],
        "captured_at": NOW,
        "source_url": f"{SOURCE_BASE}/{slug}",
        "canonical_url": canonical,
    }, indent=2), encoding="utf-8")
    print(f"  built tools/{slug}/")


def build_index_and_sitemap() -> None:
    rollup = {
        "publisher": "Clarion Intelligence Systems",
        "author": "Jing Xie",
        "generated_at": NOW,
        "snapshot_date": SNAPSHOT_DATE,
        "canonical_base": CANONICAL_BASE,
        "source_base": SOURCE_BASE,
        "theses": [],
        "tools": [],
    }
    for slug, meta in THESES.items():
        rollup["theses"].append({
            "slug": slug,
            "ticker": meta["ticker"],
            "company": meta["company"],
            "action": meta["action"],
            "score": meta["score"],
            "price_usd": meta["price_usd"],
            "tagline": meta["tagline"],
            "tags": meta["tags"],
            "bucket": meta["bucket"],
            "canonical_url": f"{CANONICAL_BASE}/research/{slug}",
            "html_path": f"theses/{slug}/index.html",
            "md_path": f"theses/{slug}/thesis.md",
            "json_path": f"theses/{slug}/thesis.json",
        })
    for slug, meta in TOOLING.items():
        rollup["tools"].append({
            "slug": slug,
            "kind": meta["kind"],
            "title": meta["title"],
            "description": meta["description"],
            "canonical_url": f"{CANONICAL_BASE}/tools/{slug}",
            "html_path": f"tools/{slug}/index.html",
        })

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    (INDEX_DIR / "theses.json").write_text(json.dumps(rollup, indent=2), encoding="utf-8")

    # sitemap.xml
    urls = []
    urls.append((CANONICAL_BASE + "/research/", NOW))
    for slug in THESES:
        urls.append((f"{CANONICAL_BASE}/research/{slug}", NOW))
    for slug in TOOLING:
        urls.append((f"{CANONICAL_BASE}/tools/{slug}", NOW))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>']
    sm.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url, lastmod in urls:
        sm.append(
            f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod><changefreq>weekly</changefreq></url>"
        )
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # robots.txt
    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: "
        f"{CANONICAL_BASE}/sitemap.xml\n",
        encoding="utf-8",
    )
    print("  built index/theses.json, sitemap.xml, robots.txt")


def main() -> None:
    print(f"Building clarion-research snapshot at {NOW}")
    THESES_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    for slug, meta in THESES.items():
        build_thesis_page(slug, meta)
    for slug, meta in TOOLING.items():
        build_tooling_page(slug, meta)
    build_index_and_sitemap()
    print("Done.")


if __name__ == "__main__":
    main()
