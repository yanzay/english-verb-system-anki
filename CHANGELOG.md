# Changelog

All notable changes to the English Verb System Anki deck are documented here.

## [2.0.0] - 2026-05-15

### 🎉 The "Preset That Actually Works" Release

This is a major architectural rewrite that fixes the long-standing issue where
the embedded FSRS preset was not auto-applied on import. Users no longer need
to manually import a preset JSON or apply settings through a multi-step UI dance.

### Fixed
- **Preset auto-binding on import (THE big one).** When you import the .apkg
  in Anki Desktop 23.10+, every sub-deck is automatically bound to the
  `English Verb System` preset (FSRS on, retention 0.9, sibling burying,
  150 reviews/day). No manual steps. No JSON to import. It just works.

### Changed
- **Migrated from `genanki` to the official `anki` PyPI package** for the
  final packaging step. The build pipeline now:
  1. Generates a v11-format .apkg with `genanki` (existing battle-tested
     model/template/note construction).
  2. Re-packages through the official `anki.Collection` API, binding every
     deck to our preset via `set_config_id_for_deck_dict()` and exporting
     with `with_deck_configs=true` and `legacy=false`.
  3. Validates the result through `validate_apkg.py`.
- The .apkg now uses the **modern v18 schema** with zstd-compressed payload
  (`collection.anki21b`) and protobuf media manifest. File size is similar.

### Removed
- The `english_verb_system_preset.json` standalone-import workaround is no
  longer needed (preset is now auto-applied). The file is retained for
  pre-23.10 Anki users.
- The `embed_fsrs_preset()` SQLite-hackery code path is now a fallback only.

### Technical
- New: `repackage_with_official_anki.py` (official-anki-backed repackager).
- New: `requirements.txt` lists `anki` and `zstandard` as build dependencies.
- Updated: `validate_apkg.py` now schema-aware (handles both legacy v11 JSON
  blobs in `col` and modern v18 `notetypes`/`fields`/`decks` tables, plus
  protobuf-encoded `Deck.kind` decoding for binding verification, plus
  zstd-decompression of modern `media` manifest).

### Acid-tested
Round-trip import into a fresh collection now produces:
- 69 decks, all bound to `English Verb System` preset
- preset has `fsrs=True, retention=0.9, perDay=10`
- 3,063 notes, 3,297 cards, 3,011 media files, all reachable

### Migration
If you imported a previous version: delete the old preset and re-import.
Anki should pick up the new preset automatically.
- **Image-Cue module** (47 CC-licensed Wikimedia photos for visual semantics of stative/dynamic, aspect, phrasal verbs)
- **Audio loudness normalization** (standardized across all TTS audio files)
- **IPA hover toggle** (interactive IPA phonetic transcription display)
- **Recommended add-ons documentation** (guide for optimal study setup)

### Changed
- Minor improvements to card styling for image display

## [1.5.0] — 2026-05-15

### Added

## [1.4.0] — 2025-11-15

### Added
- **P0 + P1 mega-expansion** (+1,129 cards across multiple domains):
  - Discourse markers and pragmatics
  - A1/A2 ramp (beginner-friendly examples)
  - Listening comprehension variants
  - Transformation exercises (active/passive, statement/question)
  - Reverse production (spot-the-error format)
  - Collocation patterns
  - Verb pattern frames
  - Register variation (formal/informal)
  - Modal auxiliaries axis
  - Inversion patterns
  - Causative constructions
  - Cleft structures
  - L1 interference (Korean, Arabic, Portuguese)
  - Domain-balanced examples
  - Spot-the-error cards
  - Module taxonomy expansion

## [1.3.0] — 2025-08-10

### Added
- **CEFR proficiency tags** (A1–C2 alignment for each card)
- **Sample field type** on production cards (explicit comparison in answer)
- **FSRS preset embedding** (automatic scheduler configuration on import)
- **L1 expansion** (additional language-specific interference notes)

## [1.2.0] — 2025-05-20

### Added
- **Tier-3 modules (06–13)** covering:
  - Module 06: Reported speech
  - Module 07: Time clauses
  - Module 08: Modals
  - Module 09: Subjunctive
  - Module 10: Non-finite forms
  - Module 11: Phrasal verbs
  - Module 12: Discourse & pragmatics
  - Module 13: L1 interference patterns

## [1.1.0] — 2025-02-14

### Added
- **Tier-2 media upgrade**:
  - Text-to-speech (TTS) audio recordings for all recognition and contrast sentences
  - IPA phonetic transcriptions (International Phonetic Alphabet) for key forms
  - Timeline diagrams (visual aspect representation)

## [1.0.0] — 2024-11-01

### Added
- **Initial English Verb System deck** with 5-module core:
  - Module 01: Core Tense & Aspect
  - Module 02: Future Forms
  - Module 03: Conditionals
  - Module 04: Passive Voice
  - Module 05: Stative vs Dynamic
- Recognition, Contrast, and Production card types
- HTML-based card styling and templates
- FSRS-compatible note schema
