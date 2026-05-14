#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOW=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
SNAPSHOT_DATE=$(date -u +%Y-%m-%d)

SOURCE_MD="/home/workspace/clarion/letters/2026-letter.md"
RAW_HTML="$ROOT/snapshots-raw/letter.html"
OUT="$ROOT/letter"

mkdir -p "$OUT"

CANONICAL="https://www.clarionintelligencesystems.com/letter"
SOURCE="https://cis.zo.space/letter"

python3 << PYEOF
import re
from datetime import datetime, timezone
from pathlib import Path

root = Path("$ROOT")
raw = Path("$RAW_HTML")
out = Path("$OUT")
source_md = Path("$SOURCE_MD")
canonical = "$CANONICAL"
source_url = "$SOURCE"
snapshot_date = "$SNAPSHOT_DATE"
now_iso = "$NOW"

raw_text = raw.read_text()

body_match = re.search(r'<body>(.*?)</body>', raw_text, re.DOTALL)
body_inner = body_match.group(1) if body_match else ''

body_inner = re.sub(r'<script[\s\S]*?</script>', '', body_inner)

body_inner = re.sub(r'<(link|meta)\s[^>]*/?>', '', body_inner)

head_match = re.search(r'<head>(.*?)</head>', raw_text, re.DOTALL)
head_inner = head_match.group(1) if head_match else ''
global_styles = ''
for m in re.finditer(r'<style[^>]*>([\s\S]*?)</style>', head_inner):
    global_styles += m.group(1) + '\n'
for m in re.finditer(r'<style[^>]*>([\s\S]*?)</style>', body_inner):
    global_styles += m.group(1) + '\n'

for m in re.finditer(r'<link[^>]*rel=["\']stylesheet["\'][^>]*/?>', head_inner):
    global_styles += f'/* original: {m.group(0)} */\n'

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 Investor Letter — Clarion Intelligence Systems</title>
<meta name="description" content="The Clarion Intelligence System 2026 investor letter. Q2 regime snapshot, portfolio positions, thesis health, and what we learned. Point-in-time: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}. Not investment advice.">
<meta name="author" content="Jing Xie">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Clarion Intelligence Systems">
<meta property="og:title" content="2026 Investor Letter — Clarion Intelligence Systems">
<meta property="og:description" content="Q2 2026 investor letter: ORANGE regime, portfolio construction, thesis health, and five lessons from managing an AI-native multi-strategy book.">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{canonical}/assets/clarion-og-1200x628.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="628">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="2026 Investor Letter — Clarion Intelligence Systems">
<meta name="twitter:description" content="Q2 2026 investor letter: ORANGE regime, portfolio construction, thesis health, and five lessons.">
<meta name="twitter:image" content="{canonical}/assets/clarion-og-1200x628.png">

<meta name="article:published_time" content="2026-05-13">
<meta name="article:author" content="Jing Xie">
<meta name="article:section" content="Investing">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Clarion Intelligence System — 2026 Investor Letter",
  "author": {{
    "@type": "Person",
    "name": "Jing Xie"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "Clarion Intelligence Systems LLC"
  }},
  "datePublished": "2026-05-13",
  "dateModified": "2026-05-13",
  "description": "Q2 2026 investor letter: ORANGE regime, portfolio construction, thesis health, and five lessons from managing an AI-native multi-strategy book.",
  "url": "{canonical}"
}}
</script>

<style>
{global_styles}
</style>
</head>
<body>
{body_inner}
</body>
</html>'''

(out / "index.html").write_text(html)

src = source_md.read_text() if source_md.exists() else ""
(out / "letter.md").write_text(src)

import json
snapshot = {
    "type": "letter",
    "title": "2026 Investor Letter",
    "slug": "letter",
    "canonical_url": canonical,
    "source_url": source_url,
    "snapshot_date": snapshot_date,
    "snapshot_at": now_iso
}
(out / "snapshot.json").write_text(json.dumps(snapshot, indent=2))

PYEOF

echo "built $OUT/index.html"
echo "built $OUT/letter.md"
echo "built $OUT/snapshot.json"
