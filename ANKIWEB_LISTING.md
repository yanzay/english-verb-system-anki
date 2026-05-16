# AnkiWeb Shared-Deck Listing — English Verb System (v3.2.8)

Paste-ready copy for https://ankiweb.net/shared/upload. Each section maps to
one field in the upload form.

---

## Title (max 80 chars — pick one)

**Recommended (78):**
> English Verb System — Tense, Aspect, Conditionals & L1 Traps (Audio + IPA)

**Alternates:**
- `English Verb System — Curriculum-First (3,288 cards, GA audio, IPA, timelines)` (78)
- `English Verb System: Recognition · Contrast · Production · Cloze (with audio)` (79)

---

## Tags (space-separated; AnkiWeb truncates around 8 tags — leading ones matter most)

```
english grammar verbs tenses esl efl b1 b2 c1 conditionals modals phrasal-verbs ipa audio
```

Trim to the first 8 if AnkiWeb objects:

```
english grammar verbs tenses esl b1 b2 conditionals
```

---

## Category

**Languages → English** (top-level), sub-category **Grammar** if offered.

If asked for a target language: **English**. Source language: **English** (the
deck is monolingual; L1-interference modules are opt-in per learner's first
language but card text stays in English).

---

## Short summary (≈ 200 chars — shows in deck-search results)

> Curriculum-first English verb-system deck: 3,288 cards across 96 sub-decks
> covering tense, aspect, mood, voice, modals, phrasal verbs, conditionals
> and 10 L1-interference traps. Native-quality audio + IPA + timeline SVGs
> on every card. CEFR A2 → C2.

---

## Full description (Markdown supported on AnkiWeb)

```markdown
# English Verb System — v3.2.8

A **curriculum-first** Anki package for the entire English verb system —
tense, aspect, mood, voice, modals, non-finite forms, reported speech,
phrasal verbs, discourse constructions, listening/phonology, and L1
interference. Every card carries **audio (Google Neural2-F)**, a broad
**General-American IPA** transcription, and (for canonical tenses) an
SVG **timeline diagram**.

## At a glance

- **3,288 cards** across **96 sub-decks** (top deck: `English Verb System`)
- **2,409 unique sentences**, each with its own MP3 (~50 MB total, bundled in the .apkg)
- **2,638 hand-curated source rows** — every row schema-validated before each build
- Four card types woven together: **Recognition · Contrast · Production · Cloze**
- **CEFR coverage**: A2 → C2, with explicit `cefr:*` tags on every card
- **Tier-3 taxonomy**: `register:* / frequency:* / domain:*` tags on every card so you can build custom filtered decks (e.g. "spoken-only", "academic-only")

## Module map

```
01 - Foundations            06 - Mood
02 - Tense Core             07 - Non-Finite Forms
03 - Aspect Core            08 - Reported Speech
04 - Modality               09 - Phrasal Verbs
05 - Voice (Passive)        10 - Discourse Constructions
                            11 - Listening / Phonology
                            12 - Transformation & Register
                            13 - L1 Interference (opt in your L1 only)
```

Each module has four sub-decks — `1 - Recognition`, `2 - Contrast`,
`3 - Production`, `4 - Cloze` — so you can study by *skill* across topics
or by *topic* across skills.

## What makes this deck different

1. **Recognition + Contrast + Production + Cloze on every form.** Most
   English-grammar decks are recognition-only; this one drills the same
   tense from four cognitive angles, which is what the SLA literature
   actually says works.
2. **L1-interference module.** Sub-decks for Spanish, French, German,
   Russian, Mandarin, Japanese, Korean, Arabic, Portuguese, Dutch (and
   "Other") drill the *traps your first language sets for you*: age
   expressions, copula presence, V2 word order, recent past, since-vs-for,
   plural marking, etc. Enable only your L1; the rest stays buried.
3. **Listening / Phonology module.** Connected-speech reductions
   (`gonna`/`wanna`/`hafta`), modal weak forms, t-flapping, linking R,
   and contraction ambiguity (`I'd` = had or would?) — the things that
   make native speech hard to parse but that no other Anki deck covers.
4. **Native-quality TTS.** Every sentence is rendered with Google's
   `en-US-Neural2-F` voice (warm, natural, female GA). One MP3 per unique
   sentence — total media ≈ 50 MB.
5. **Built-in IPA + timeline diagrams.** Broad GA IPA on every back side
   (no extra add-on needed); SVG timelines auto-attached for every
   canonical tense label.
6. **Curriculum-first organisation.** Sub-decks follow a syllabus, not a
   tag dump. New cards are shuffled within each sub-deck so you don't get
   ten consecutive "present continuous" cards in a row.
7. **FSRS preset bundled.** A pre-tuned `English Verb System` FSRS preset
   auto-binds to all 96 sub-decks on import (Anki 24.10+). A second
   preset binds the L1 sub-decks at a slower pace.

## Recommended Anki settings

- **Anki 24.10 or newer** (FSRS scheduler v5; required for the bundled preset)
- **15–20 new cards/day** for the core modules
- **Burying** enabled (so Recognition + Production of the same sentence don't show same day)
- See `ANKI_SETTINGS.md` in the GitHub repo for the full recommended config

## Recommended add-ons (optional but nice)

- Review Heatmap
- Advanced Browser
- Image Occlusion Enhanced (for cards you add yourself)

## Source & contributions

Source TSVs, build scripts, validators, and the full CHANGELOG live at
**https://github.com/yanzay/english-verb-system-anki**

This is a free, MIT-licensed, community-built deck. Issues and PRs welcome.

## Changelog highlights (v3.2.8 — pre-release content audit, round 3)

- Repaired 9 schema-broken Production rows (L1-trap label retargeting + sample-morphology fixes)
- Cleared one tautological `WhenNotToUse`
- Re-rendered 61 missing MP3s; pruned 92 orphan ones — audio manifest is now in 1:1 sync with the corpus
- Synced README to authoritative numbers (2,638 source rows → 3,288 exported cards)
- Validator now exits 0 on the full pipeline (schema + audio hash check)

Full history: https://github.com/yanzay/english-verb-system-anki/blob/main/CHANGELOG.md
```

---

## Upload checklist

1. Open Anki desktop → ensure you're synced into AnkiWeb (Tools → Preferences → Network).
2. Right-click the **English Verb System** deck → **Share Deck…** → confirm "Include media" (it's already bundled in the .apkg, but the desktop dialog uses the live collection so this matters for the desktop path).
3. Browser opens to https://ankiweb.net/shared/upload — paste the metadata above.
4. Upload `english_verb_system_anki.apkg` (≈ 55 MB; well under the 100 MB AnkiWeb limit).
5. Choose **Languages → English** category.
6. Tick *"This deck is appropriate for all ages."*
7. Submit. AnkiWeb will assign a numeric shared-deck ID (e.g. `1234567890`).
8. **Save the ID** in the README under a new "Get this deck" section so future updates can be uploaded against the same listing (Updates use the same form with the existing deck ID pre-filled when you re-share from desktop).

## After publish

- Paste the AnkiWeb URL back into this file (replace `<TBD>`):
  - **AnkiWeb URL:** `<TBD>`
  - **Shared deck ID:** `<TBD>`
- Add a "Download from AnkiWeb" badge to the README pointing at the URL.
- Tag the release on GitHub: `git tag v3.2.8 && git push --tags` and attach
  `english_verb_system_anki.apkg` to a GitHub Release for users who don't
  use AnkiWeb.
