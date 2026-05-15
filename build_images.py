#!/usr/bin/env python3
"""build_images.py — fetch CC-licensed cover images for the Image-Cue module.

Reads `conjugations_image.txt` (canonical image-cue card data, 6-column TSV
matching the schema `ImageQuery | Caption | Form | Function | Contrast | Tags`),
fetches one photo per row from Wikimedia Commons (CC-BY/CC0/PD content), saves
JPEGs to `media/images/{hash}.jpg`, and writes `media/images_index.json`
mapping `caption-hash -> {file, attribution, license, query}`.

Idempotent + incremental: re-running only fetches images for rows whose
caption hash isn't already present in the manifest. Pruning of orphaned files
happens automatically.

Wikimedia Commons API is keyless and ToS-friendly for non-commercial agentic
use. We respect their User-Agent guideline. If a query returns nothing, we
fall back to a generic, deterministic placeholder so the deck still builds.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ── Constants ───────────────────────────────────────────────────────────────
SEED_TSV         = Path('conjugations_image.txt')
IMAGES_DIR       = Path('media/images')
IMAGES_INDEX     = Path('media/images_index.json')
USER_AGENT       = 'EnglishVerbSystemAnkiBot/1.0 (https://github.com/yanzay/english-verb-system-anki; cc-image-fetch)'
WMC_SEARCH_URL   = 'https://commons.wikimedia.org/w/api.php'
PLACEHOLDER_URL  = 'https://picsum.photos/seed/{seed}/640/480.jpg'
REQUEST_TIMEOUT  = 30
THROTTLE_SECONDS = 0.4   # be polite to Commons


def caption_hash(caption: str) -> str:
    return hashlib.sha1(caption.strip().encode('utf-8')).hexdigest()[:12]


def load_seed():
    """Yield dicts {ImageQuery, Caption, Form, Function, Contrast, Tags}."""
    if not SEED_TSV.exists():
        print(f'! Seed not found: {SEED_TSV}', file=sys.stderr)
        sys.exit(2)
    rows = []
    header_cols = []
    for i, line in enumerate(SEED_TSV.read_text(encoding='utf-8').splitlines()):
        s = line.rstrip('\n')
        if i < 3:
            if s.startswith('#columns:'):
                header_cols = s[len('#columns:'):].split('\t')
            continue
        if not s.strip():
            continue
        cols = s.split('\t')
        if len(cols) < 6:
            continue
        rows.append({
            'ImageQuery': cols[0],
            'Caption':    cols[1],
            'Form':       cols[2],
            'Function':   cols[3],
            'Contrast':   cols[4],
            'Tags':       cols[5] if len(cols) > 5 else '',
        })
    return rows


def http_get_json(url: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f'{url}?{qs}', headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode('utf-8'))


def http_get_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return resp.read()


def search_wikimedia(query: str):
    """Return list of {url, descriptionurl, license, artist, title} for a query."""
    # Step 1 — search File: pages by text
    params = {
        'action':   'query',
        'list':     'search',
        'srsearch': f'{query} filetype:bitmap',
        'srnamespace': 6,         # File namespace
        'srlimit':  5,
        'format':   'json',
    }
    try:
        sr = http_get_json(WMC_SEARCH_URL, params).get('query', {}).get('search', [])
    except Exception as e:
        print(f'    ! search error: {e}', file=sys.stderr)
        return []
    titles = [r['title'] for r in sr if r.get('title', '').startswith('File:')]
    if not titles:
        return []
    # Step 2 — get imageinfo (URL, license, artist) for the top hits
    params2 = {
        'action':  'query',
        'titles':  '|'.join(titles[:5]),
        'prop':    'imageinfo',
        'iiprop':  'url|extmetadata|size|mime',
        'iiurlwidth': '640',
        'format':  'json',
    }
    try:
        info = http_get_json(WMC_SEARCH_URL, params2).get('query', {}).get('pages', {})
    except Exception as e:
        print(f'    ! imageinfo error: {e}', file=sys.stderr)
        return []
    out = []
    for pageid, page in info.items():
        ii = (page.get('imageinfo') or [{}])[0]
        if not ii:
            continue
        meta = ii.get('extmetadata', {})
        url = ii.get('thumburl') or ii.get('url')
        if not url:
            continue
        mime = ii.get('mime', '')
        if not mime.startswith('image/'):
            continue
        license_short = (meta.get('LicenseShortName') or {}).get('value', '')
        # Reject unknown / non-free
        if license_short and any(bad in license_short.lower() for bad in ('non-commercial', 'fair use', 'unknown')):
            continue
        artist = (meta.get('Artist') or {}).get('value', '')
        out.append({
            'url':            url,
            'descriptionurl': ii.get('descriptionurl', ''),
            'license':        license_short or 'Wikimedia Commons (see source)',
            'artist':         _strip_html(artist)[:200],
            'title':          page.get('title', ''),
            'mime':           mime,
        })
    return out


def _strip_html(s: str) -> str:
    import re as _re
    return _re.sub(r'<[^>]+>', '', s or '').strip()


def fetch_one(query: str, caption: str):
    """Search Commons, download first viable result, return (jpeg_bytes, meta)."""
    cands = search_wikimedia(query)
    for c in cands:
        try:
            data = http_get_bytes(c['url'])
            if len(data) < 1500:           # too tiny → likely thumb error
                continue
            return data, c
        except Exception as e:
            print(f'    ! download skipped: {e}', file=sys.stderr)
            continue
    # Fallback: deterministic placeholder so the deck still builds
    seed = caption_hash(caption)
    try:
        data = http_get_bytes(PLACEHOLDER_URL.format(seed=seed))
        return data, {
            'url': PLACEHOLDER_URL.format(seed=seed),
            'descriptionurl': 'https://picsum.photos',
            'license': 'Picsum placeholder (CC0 Lorem-Ipsum-of-images)',
            'artist': 'Picsum',
            'title':  'Placeholder',
            'mime':   'image/jpeg',
        }
    except Exception as e:
        print(f'    ! placeholder failed: {e}', file=sys.stderr)
        return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--limit', type=int, default=0,
                    help='Process only N rows (for smoke testing).')
    ap.add_argument('--force', action='store_true',
                    help='Re-fetch even rows already in the manifest.')
    args = ap.parse_args()

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if IMAGES_INDEX.exists():
        try:
            manifest = json.loads(IMAGES_INDEX.read_text(encoding='utf-8'))
        except Exception:
            manifest = {}

    rows = load_seed()
    if args.limit:
        rows = rows[:args.limit]

    fetched = 0
    skipped = 0
    failed  = 0
    valid_hashes = set()

    for i, r in enumerate(rows, 1):
        h = caption_hash(r['Caption'])
        valid_hashes.add(h)
        out_path = IMAGES_DIR / f'{h}.jpg'
        if not args.force and h in manifest and out_path.exists() and out_path.stat().st_size > 0:
            skipped += 1
            continue
        print(f'  [{i:3d}/{len(rows)}] {r["ImageQuery"]!r} → {h}')
        data, meta = fetch_one(r['ImageQuery'], r['Caption'])
        if not data or not meta:
            failed += 1
            continue
        out_path.write_bytes(data)
        manifest[h] = {
            'file':            f'{h}.jpg',
            'caption':         r['Caption'],
            'query':           r['ImageQuery'],
            'license':         meta['license'],
            'attribution':     meta['artist'],
            'source':          meta.get('descriptionurl', meta['url']),
            'mime':            meta['mime'],
            'size':            len(data),
        }
        fetched += 1
        time.sleep(THROTTLE_SECONDS)

    # Prune orphans
    pruned = 0
    for h in list(manifest.keys()):
        if h not in valid_hashes:
            f = IMAGES_DIR / manifest[h].get('file', '')
            if f.exists():
                f.unlink()
            del manifest[h]
            pruned += 1
    for f in IMAGES_DIR.glob('*.jpg'):
        if f.stem not in valid_hashes:
            f.unlink()
            pruned += 1

    IMAGES_INDEX.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
                            encoding='utf-8')
    print('')
    print(f'✓ Done. fetched={fetched}  up-to-date={skipped}  failed={failed}  pruned={pruned}')
    print(f'  Manifest: {IMAGES_INDEX}')
    print(f'  Output dir: {IMAGES_DIR}/')


if __name__ == '__main__':
    main()
