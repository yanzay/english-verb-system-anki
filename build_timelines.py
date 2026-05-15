#!/usr/bin/env python3
"""
Tier-2 timeline-SVG generator for the English Verb System Anki package.

Produces one minimalist SVG diagram per canonical tense / aspect label,
showing where the action sits relative to the PAST / NOW / FUTURE axis
and whether it's punctual, durative, or perfective.

Output:
  media/timelines/<slug>.svg
  media/timelines_index.json   — { canonical_label: filename.svg }

Each SVG is ~400×120 px, light-themed, with @media-prefers-color-scheme
inversion so it looks good on Anki dark mode too. Embedded via Anki's
standard <img src="filename.svg"> reference.

Add new labels by editing the SPECS table.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT_DIR = Path("media/timelines")
INDEX_JSON = Path("media/timelines_index.json")


def slug(label: str) -> str:
    s = label.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s or "untitled"


# ── SVG primitives ──────────────────────────────────────────────────────
HEADER = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120" \
font-family="-apple-system, Segoe UI, Arial, sans-serif" font-size="11">
<style>
  .axis  {{ stroke:#374151; stroke-width:1.5; }}
  .tick  {{ stroke:#374151; stroke-width:1; }}
  .label {{ fill:#6b7280; font-size:10px; }}
  .now   {{ fill:#dc2626; font-weight:700; }}
  .event {{ fill:#1d4ed8; }}
  .arrow {{ fill:#1d4ed8; }}
  .dur   {{ stroke:#1d4ed8; stroke-width:6; stroke-linecap:round; opacity:0.85; }}
  .dot   {{ fill:#1d4ed8; }}
  .title {{ font-size:12px; fill:#111827; font-weight:600; }}
  @media (prefers-color-scheme: dark) {{
    .axis, .tick {{ stroke:#9ca3af; }}
    .label {{ fill:#9ca3af; }}
    .title {{ fill:#f9fafb; }}
    .now   {{ fill:#fca5a5; }}
    .event, .dur, .arrow, .dot {{ stroke:#93c5fd; fill:#93c5fd; }}
  }}
</style>
<text x="10" y="18" class="title">{title}</text>
<line x1="20"  y1="80" x2="380" y2="80" class="axis" marker-end="url(#arrow)"/>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="6" refY="3"
       orient="auto"><path d="M0,0 L6,3 L0,6 Z" class="arrow"/></marker></defs>
<line x1="60"  y1="76" x2="60"  y2="84" class="tick"/>
<line x1="200" y1="74" x2="200" y2="86" class="tick"/>
<line x1="340" y1="76" x2="340" y2="84" class="tick"/>
<text x="60"  y="100" text-anchor="middle" class="label">PAST</text>
<text x="200" y="100" text-anchor="middle" class="now">NOW</text>
<text x="340" y="100" text-anchor="middle" class="label">FUTURE</text>
'''
FOOTER = "\n</svg>\n"


def dot(x: int, y: int = 80, label: str | None = None) -> str:
    s = f'<circle cx="{x}" cy="{y}" r="5" class="dot"/>'
    if label:
        s += f'<text x="{x}" y="{y - 10}" text-anchor="middle" class="event">{label}</text>'
    return s


def dur(x1: int, x2: int, y: int = 80, label: str | None = None) -> str:
    s = f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="dur"/>'
    if label:
        cx = (x1 + x2) // 2
        s += f'<text x="{cx}" y="{y - 10}" text-anchor="middle" class="event">{label}</text>'
    return s


def arrow_dur_to(x: int, y: int = 80, label: str | None = None) -> str:
    """Duration extending up to a point (used for perfect aspects)."""
    return dur(x - 80, x, y, label) + dot(x)


def write_svg(label: str, body: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{slug(label)}.svg"
    OUT_DIR.joinpath(fname).write_text(
        HEADER.format(title=label) + body + FOOTER, encoding="utf-8")
    return fname


# ── Per-label specs ─────────────────────────────────────────────────────
# Coordinate convention: PAST≈60, NOW=200, FUTURE≈340. Y axis = 80.
SPECS = {
    # ── Present family ─────────────────────────────────────────────────
    "Present Simple":
        # generic: small dots scattered across (habit / general truth)
        dot(110) + dot(160) + dot(200, label="•") + dot(240) + dot(290),
    "Present Continuous":
        dur(180, 220, label="now"),
    "Present Perfect":
        # dot somewhere in the past with arrow → now
        dot(120) + f'<line x1="120" y1="80" x2="195" y2="80" class="dur"/>' + dot(200, label="now"),
    "Present Perfect Continuous":
        dur(120, 200, label="up to now") + dot(200),

    # ── Past family ────────────────────────────────────────────────────
    "Past Simple": dot(80, label="x"),
    "Past Continuous": dur(60, 110, label="ongoing past"),
    "Past Perfect":
        dot(50, label="earlier") + dot(110, label="past ref"),
    "Past Perfect Continuous":
        dur(40, 110, label="duration → past ref") + dot(110),

    # ── Future family ──────────────────────────────────────────────────
    "Future Simple": dot(320, label="will V"),
    "Future Continuous": dur(290, 350, label="ongoing"),
    "Future Perfect":
        dot(300, label="x") + f'<line x1="200" y1="80" x2="300" y2="80" class="dur"/>'
        + dot(330, label="ref"),
    "Future Perfect Continuous":
        dur(220, 320, label="duration → future ref") + dot(330),

    # ── Conditional family (counterfactual present/past) ───────────────
    "Conditional Simple":
        # ghost-dot in counterfactual present
        dot(200, label="(would V)"),
    "Conditional Continuous":
        dur(180, 220, label="(would be V-ing)"),
    "Conditional Perfect":
        dot(80, label="(would have V-ed)"),
    "Conditional Perfect Continuous":
        dur(50, 110, label="(would have been V-ing)"),

    # ── Future forms ───────────────────────────────────────────────────
    "Be Going To":
        dot(200, label="decision") + f'<line x1="200" y1="80" x2="320" y2="80" class="dur"/>'
        + dot(320, label="planned action"),
    "Present Continuous for Future Arrangement":
        dot(200) + dot(310, label="arrangement"),
    "Present Simple for Schedule":
        dot(310, label="scheduled") ,

    # ── Conditionals (zero/first/second/third) ─────────────────────────
    "Zero Conditional":
        dot(110) + dot(200) + dot(290),  # always true across all time
    "First Conditional": dot(310, label="real future"),
    "Second Conditional": dot(200, label="(unreal present)"),
    "Third Conditional": dot(80, label="(unreal past)"),
    "Mixed Conditional":
        dot(80, label="unreal past") + dot(200, label="unreal present"),

    # ── Passive (mirror their active counterparts visually) ────────────
    "Present Simple Passive": dot(200, label="x"),
    "Past Simple Passive": dot(80, label="x"),
    "Present Perfect Passive": dot(120) + dot(200, label="now"),
    "Past Continuous Passive": dur(60, 110, label="ongoing past"),
    "Past Perfect Passive": dot(50) + dot(110, label="past ref"),
    "Present Continuous Passive": dur(180, 220, label="now"),
    "Modal Passive": dot(200, label="(modal V-ed)"),
    "Get-Passive": dot(80, label="change-of-state"),

    # ── Stative / dynamic ──────────────────────────────────────────────
    "Present Simple (Stative)":
        dur(60, 340, label="permanent state"),
    "Present Continuous (Dynamic)":
        dur(180, 220, label="dynamic now"),
    "Present Continuous (Dynamic Stative Shift)":
        dur(180, 220, label="temporary state"),

    # ── Reported speech / future-in-the-past ───────────────────────────
    "Reported Speech (Backshift)": dot(80, label="reported event"),
    "Future-in-the-Past (Was Going To)":
        dot(80, label="past view") + f'<line x1="80" y1="80" x2="160" y2="80" class="dur"/>'
        + dot(160, label="planned"),
    "Future-in-the-Past (Would)":
        dot(80, label="said") + dot(180, label="(would V)"),

    # ── Modal perfect continuous ───────────────────────────────────────
    "Modal Perfect Continuous (Must Have Been V-ing)":
        dur(60, 110, label="must have been V-ing"),

    # ── Narrative layering ─────────────────────────────────────────────
    "Narrative Layering (Past Simple + Past Continuous + Past Perfect)":
        dot(50, label="had V-ed") + dur(80, 130, label="was V-ing") + dot(110, label="V-ed"),
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = {}
    for label, body in SPECS.items():
        fname = write_svg(label, body)
        index[label] = fname
    INDEX_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(f"✓ Wrote {len(SPECS)} timeline SVGs to {OUT_DIR}/")
    print(f"  Index: {INDEX_JSON}")


if __name__ == "__main__":
    main()
