# Changelog

All notable changes to the English Verb System Anki deck are documented here.

## [3.2.11] - 2026-05-16

### Fixed (Universal spoken-text normalization)
- **Applied blank/cloze sentence normalization as a shared mechanism across all
  media paths**, not only contrast/spot call sites. `media_for_sentence()` now
  resolves spoken text centrally before audio/IPA hash lookup.
- **Extended collectors/validators to normalize every sentence source**
  (recognition, production samples, cloze text, contrast rows with answer
  substitution) so future rows/card variants cannot regress to placeholder-based
  hashes.
- **Audited placeholder-bearing rows** (`___`, `[blank]`, `(blank)`, cloze
  markers) across corpora and verified package build + validation still resolve
  100% of expected audio entries.

## [3.2.10] - 2026-05-16

### Fixed (Blank-card audio now uses full sentence)
- **Resolved incomplete back-side audio on blank-style cards** (including
  Spot-the-Error rows generated from contrast data). Audio/IPA lookup no
  longer hashes placeholder text like `___`; it now resolves blanks to the
  authored answer phrase and synthesizes the full natural sentence.
- **Audited and aligned all sentence collectors** used by media generation and
  validation (`build_audio.py`, `build_ipa.py`, `build_anki_package.py`,
  `validate_anki_data.py`) so they compute the same spoken sentence for
  contrast/spot/cloze rows.
- **Regenerated Tier-2 media + package** after the pipeline fix:
  audio manifest rebuilt, orphan hashes pruned, new hashes rendered, IPA index
  synced, and `.apkg` rebuilt with v3.2.10 stamp.

## [3.2.9] - 2026-05-16

### Fixed (Recognition focus-highlight overhaul)
- **Fixed broken `Future Perfect Continuous` highlight** that was
  selecting `"will not"` for `"They will not have been waiting long."`
  The previous regex put `\s+not` as an alternation branch terminating
  on the auxiliary, so any negative cluster collapsed to `"will not"`.
  Replaced with a proper `\bwill(?:\s+not|n't)?{SUBJ}\s+have\s+been\s+\w+ing\b`.
- **Comprehensive Recognition highlight audit & rewrite.** Rebuilt all
  verb-cluster patterns in `_extract_focus()` so they correctly cover
  the four clause shapes — declarative positive, declarative negative,
  yes/no question, wh-question — with one shared `SUBJ`/`NEG` slot
  vocabulary. Coverage went from **494 / 833 highlighted rows (59 %)
  with 51 demonstrably wrong** to **813 / 833 highlighted (97.6 %)
  with the residual 20 being intentional L1-trap and phonology rows
  where the whole sentence is the focus** (Article Use, V2 Word Order,
  Get vs Become, T-flapping, Linking R, Subject Case, etc.).
- **Added curated irregular past-participle list (`IRREG_PP`)** so
  perfect tenses now match `lost / left / found / bought / gone /
  seen / done / made / known / taken / written / spoken / chosen / …`
  instead of failing on every irregular and capturing only the
  auxiliary.
- **Added contraction support** (`'ve`, `'s`, `'d`, `'ll`, `'re`,
  `'m`) to every perfect/continuous tense pattern so cards like
  `"I've already written the letter."`, `"He'd sooner resign…"`,
  `"At this hour next week, I'd be lying on a beach…"`,
  `"She's just finished the report."` now extract the full cluster.
- **Added phrasal-verb extractor** that pulls the canonical phrasal
  out of the parenthetical in the Label (`Phrasal Verb (look up to)`),
  inflects the head (look/looks/looked/looking with full irregular
  forms for go/come/get/give/take/make/break/fall/etc.), and matches
  the full multi-word verb across the sentence — so all 60+ phrasal
  Recognition rows now have correct highlights.
- **Added high-precision sub-form fallbacks** for `Wish (Present
  Unreal / Past Regret)`, `If Only`, `Be About To`, `Was/Were Going
  To`, `Get-Passive`, `Be Able To`, `Be Supposed To`, `Had Better`,
  `Due To (Formal Future)`, `Time Clause (Future / Future Perfect /
  Past Continuous / Past Perfect)`, `Conditional (Zero/First/Second/
  Third/Mixed/Unless/As Long As/Provided That)`, `Reported Speech
  (Suggest/Recommend)`, `Stative Present Simple`, `Present Perfect
  with Just/Still/Already/Yet`, `Present Continuous (Complaint —
  always/forever/constantly Ving)`, `Light Verb (Take/Make/Have/Give/
  Do)`, `Modal (Would Sooner/Would Rather)`, `Mandative Subjunctive`,
  `Bare Infinitive (Let/Make)`, `Perfect Infinitive/Gerund/Participle`,
  and `Implicit Conditional (Coordination)`.
- **Added passive-label short-circuit** so `"Coffee is grown in
  Colombia."` (label `Present Simple Passive`) now highlights
  `"is grown"` instead of being claimed by the present-simple
  `\b\w+s\b` 3sg fallback and stopping at `"is"`.
- **Improved Past Simple matcher** to recognise irregular forms by
  literal token (`came / went / got / gave / took / made / said /
  saw / found / told / brought / broke / fell / held / ran / kept /
  left / paid / sold / sat / stood / ate / drank / thought / spoke /
  wrote / read / met / cut / put / set / let / bet / hurt / cost /
  hit / shut / sang / swam / knew / grew / threw / drew / flew /
  showed / blew / drove / rode / chose / froze / stole / woke / bit /
  hid / fell / lost / bought / caught / fought / taught / sought /
  sent / spent / built / burnt / dealt / dreamt / learnt / swept /
  crept / bent / lent / won / held / fled / led / fed / bred / laid /
  wept / withdrew / undertook / overcame`) so cards like `"She ate
  breakfast at the hotel yesterday morning."`, `"He said hello."`,
  and `"She got the job."` highlight the actual past form.
- **Improved Present Simple matcher** to highlight the bare-verb
  cluster after a pronoun (`"I drink coffee every morning…"`,
  `"I eat rice every day…"`, `"I use a pen."`).
- **Added last-resort generic verb-cluster fallback** so any row with
  an auxiliary or post-pronoun verb gets *some* highlight even when
  the row's specific Label doesn't match a registered key.

### Build verified
3,288 cards · 96 sub-decks · 0 schema errors · 0 audio errors · v3.2.9
stamp on the apkg. Recognition highlight coverage 97.6 % across all
833 rows.

## [3.2.8] - 2026-05-16

### Fixed (pre-release content audit, round 3)
- **Repaired 9 schema-broken Production rows.** Six L1-interference rows had
  generic verbal Targets (e.g. `Past Simple`, `Present Perfect`,
  `Present Continuous`) but L1-trap aspects (`semantics`, `tense`, `plural`,
  …); they now use the canonical L1 trap labels (`Physical State`,
  `Recent Past`, `Get vs Become`, `Perfect Tense Word Order`,
  `Plural Marking`, `Since vs For Duration`). Three "ask/answer" Production
  prompts had short colloquial samples that didn't pattern-match the
  declared verbal Target morphology — samples were rewritten to make the
  target form unambiguous (`What are you doing right now?`,
  `What were you doing at 3 PM yesterday?`, `No, I haven't eaten yet.`).
- **Cleared one tautological `WhenNotToUse`** in Recognition row 749
  (`When chess match is finished` for the present-perfect-continuous chess
  example) — the column now carries an explanatory contrast instead of
  restating the form's own scope.
- **Fixed the validator's hidden curly-quote bug.** `validate_anki_data.py`
  carried `Cleft Conditional (If It Weren\u2019t For)` (curly apostrophe)
  in its `ALLOWED_LABELS` set — TSV rows use a straight ASCII apostrophe
  for that label, so the validator was emitting a spurious "unknown label"
  on every Cleft Conditional row. Replaced with the matching straight
  form. Also widened the production morphology regexes for Present /
  Past / Future Continuous and Present / Past Perfect to accept inverted
  question forms (`What are you doing?`) and short answers
  (`No, I haven't eaten yet.`).
- **Pruned 92 orphan MP3s** (and their `audio_manifest.json` entries) for
  sentences that had been removed from the corpus in earlier audits but
  whose audio assets still lingered on disk. The manifest is back in sync
  with the source TSVs (2,348 entries → matches `_audio_corpus_sentences`
  output exactly).
- **Synced README to authoritative numbers and v3.2.8.** "Current version"
  pill jumped from a stale `2.0.0` to `3.2.8`. The "Tier 1 expansions"
  blurb (`816 → 1,113 cards`), the audio sentence count (`1,113 cards,
  ~1,041 unique sentences`), the IPA count (`14 / 1,566 unique words`),
  the MP3-count `~1,218`, and the validation tally `All 1,373 rows pass`
  were all replaced with the v3.2.8 figures (`2,794` cards, `~2,348`
  unique sentences, `~2,400` MP3s, `2,638` source rows).

### Build verified
2,794 cards · 85 sub-decks · 0 schema errors
(`python3 validate_anki_data.py --no-audio-check` exits 0) · two presets
auto-bound (`English Verb System` + `English Verb System (L1 — opt in)`).

## [3.2.8 — round 2] - 2026-05-16

### Fixed (pre-release content audit, round 2)
- **Repaired 95 schema-broken Production rows** where the `Target` field
  contained a full sentence (e.g. `"My team has won the championship."`)
  instead of a form name. The Anki template renders Target as a small
  pill above the typed answer; with a sentence in there the card showed
  the answer to itself before the learner typed anything. Fix: derive a
  proper form name from each row's tags + aspect (`Present Perfect`,
  `Be Going To (Future)`, `Have Got (Possession)`, etc.) and promote
  the original sentence into `Sample` (the canonical answer used by
  `{{type:Sample}}`). Throwaway extra sentences in the old `Sample`
  field — e.g. `"She has scored three goals. They have beaten their
  rivals."` for a single-answer card — were dropped.
- **Re-tagged a misclassified L1-interference row.** Row 618 was tagged
  `gerund-after-verb` but contained `I need to go to the store.`
  (infinitive, not gerund). Re-tagged to `need-to` and renamed Target.
- **Normalised 5 stray curly-quote characters** in
  `conjugations_recognition.txt` and `conjugations_contrast.txt`
  (`o'clock`, `Weren't`) to straight ASCII apostrophes for consistency
  with the other 1,623+ apostrophes already in straight form.
- **Rewrote `anki_premium_schema_package.txt`** end-to-end. The previous
  version documented a hypothetical Front/Back/Extra schema that has
  never matched any shipped note type and gave instructions to import
  TSVs by hand into Anki — instructions that haven't applied since v2.0
  when we moved to the `.apkg` build pipeline. The new version is a
  faithful reference for the four real note types, the 13-module
  curriculum-first deck structure, the two presets, and the tag
  taxonomy actually shipped.

## [3.2.7] - 2026-05-16

### Fixed (pre-release content audit)
- **Removed 26 placeholder `vs related forms` Contrast values** in the
  Recognition deck. Affected reported-speech, mandative-subjunctive,
  wish/if-only, would-rather, as-if/as-though, and it's-time rows.
  Each row now ships a category-specific contrast that names the
  exact form being disambiguated against (e.g. `vs direct "I will
  help" → "would help" (will → would)` instead of the meaningless
  generic).
- **Cleared 10 tautological `When [noun] is finished` WhenNotToUse**
  values that just restated the form's own scope. The field is now
  empty on those rows; the QuickCue + MainUse already convey the
  correct usage window.
- **De-duplicated 3 sentence/label pairs** that appeared twice in the
  Recognition source. Kept the richer L1-interference variants for
  age-expression rows ("I am 25 years old.", "She is 30 years old.")
  and the perfect-aspect variant for the inverted-conditional row
  ("Had I known the truth, I would have acted differently."). The
  weaker earlier copies were dropped.
- **Synced README deck-structure table to authoritative build numbers.**
  Old totals (3,524 / 96 sub-decks / 14 modules) reflected a pre-3.2.0
  layout that double-counted L1-interference rows and still listed the
  retired Image-Cue module. Real numbers as of 3.2.7 build:
  **2,794 unique cards across 85 sub-decks in 13 modules** (3,288
  deck placements, since L1-interference rows route to one shared L1
  deck plus their per-language deck by design).
- **Rewrote `ANKI_SETTINGS.md` for the v3.2 deck structure.** The
  previous version still documented the legacy thematic deck names
  (`01 - Core Tense & Aspect`, `02 - Future Forms`, …) which haven't
  existed since v3.2.0's curriculum-first restructure, and claimed
  the package binds 52 sub-decks (now 85). New version documents the
  two-preset opt-in strategy and provides curriculum-aligned tag
  shortcuts.

### Documentation correction
- **Removed obsolete "preset JSON sidecar" instructions** from README
  Step 5 and `ANKI_SETTINGS.md` Path A. The two presets ARE embedded
  in the `.apkg` and DO auto-bind on import in Anki 23.10+ (verified by
  importing into a fresh test collection: `English Verb System` binds
  to 59 decks, `English Verb System (L1 — opt in)` binds to 51 decks,
  Default keeps 1). Older docs assumed the long-standing Anki bug
  applies; under modern Anki with `with_deck_configs=True` (the
  default in the import dialog) it doesn't. The standalone
  `english_verb_system_preset.json` is no longer shipped as a release
  asset.

### Build verified
2,794 cards · 85 sub-decks · 0 errors · two presets auto-bound
(`English Verb System` + `English Verb System (L1 — opt in)`).

## [3.2.0] – [3.2.6] - 2026-05-15

### Changed
- **Curriculum-first deck restructure (v3.2.0).** Replaced the legacy
  12 thematic modules with a 13-module sequenced curriculum derived
  directly from the grammatical category taxonomy:
  `00 Foundation → 01 Periphrastic Futures → 02 Past Habits →
  03 Modal Verbs → 04 Conditionals → 05 Passive Voice → 06 Mood →
  07 Non-Finite Forms → 08 Reported Speech → 09 Phrasal Verbs →
  10 Discourse Constructions → 11 Phonology & Connected Speech →
  12 Transformation & Register → 13 L1 Interference (per-language)`.
- **Two-preset opt-in strategy.** Foundation (`00`) is bound to the
  main `English Verb System` preset (10 new/day, FSRS, sibling burying).
  Modules `01–13` are bound to a separate `English Verb System (L1 — opt
  in)` preset with **0 new cards/day** so users explicitly enable each
  layer when they're ready. Mirrors how Cambridge / Oxford / Pearson
  sequence EFL syllabi (CEFR A1→C2).
- **Per-L1 sub-decks under Module 13.** Spanish, French, German,
  Russian, Mandarin, Japanese, Korean, Arabic, Portuguese, Dutch each
  get their own deck so a learner only sees the contrasts that
  actually trip up speakers of *their* L1.

### v3.2.1 – v3.2.6 (point releases)
- v3.2.1: aux-form rows route to Foundation (was misrouted to register).
- v3.2.2: re-binding the L1 opt-in preset survives Anki re-imports.
- v3.2.3: per-language Cloze sub-decks added (were missing).
- v3.2.4: standalone `english_verb_system_preset.json` emitted next to
  the `.apkg` for one-click Deck-Options Import (Anki 23.10+).
- v3.2.5: deck description includes a Changelog link in the deck list.
- v3.2.6: misc. category-routing fixes for edge-case construction tags.

## [3.1.0] - [3.1.1] - 2026-05-15

### Changed
- **Grammatical category taxonomy (v3.1.0).** Introduced 15-category
  classification (`tense-aspect`, `aux-form`, `periphrastic-future`,
  `periphrastic-past-habit`, `modal`, `conditional`, `voice`, `mood`,
  `non-finite`, `reported-speech`, `phrasal-verb`, `construction`,
  `phonology`, `transformation`, `register`) computed by `_category_for()`
  from each row's Label/Answer/Target/tags. Used to drive both deck
  routing and per-card prompts.
- **Always-honest, category-aware prompts (v3.1.1).** Every Recognition,
  Contrast, Cloze, and Production card now displays a prompt that names
  the *expected answer category* — e.g. "Identify the highlighted
  modal" / "Which conditional type fits?" / "Fill in the missing
  passive form" / "Write a sentence using the target subjunctive" —
  instead of the muddled generic ("Which form fits this sentence?").
  Eliminates the prior failure mode where a Recognition card asked
  "What tense?" but the answer was "Negative Inversion".

## [3.0.0] - 2026-05-15

### Added
- **Design-system v3.0 CSS rewrite.** All ~50 hardcoded colors
  consolidated into two CSS-variable token blocks (light + dark) at
  the top of the stylesheet. Every class below uses `var(--*)` so
  light↔dark theming is automatic and impossible to miss.
- **Focus highlight on Recognition cards.** The targeted span is
  wrapped in `<mark class="focus">` so prompts like "Identify the
  highlighted weak form" become unambiguous — the highlighted span
  tells the learner what to analyse.
- **Foundation deck (Module 00, 12-cell grid).** The canonical 3
  tenses × 4 aspects grid is now its own ENABLED-by-default deck
  before any layer.

## [2.7.0] - 2026-05-15

### Removed
- **Image-Cue module (Module 14) deleted entirely.** The premise — fetch
  Wikimedia Commons photos via keyword search to illustrate verbal aspect,
  stative/dynamic contrasts, and phrasal verbs — produced semantically
  random matches in practice (e.g. "woman thinking in profile" returned
  a Picasso sculpture in Chicago). Even with perfect matching, most
  aspect contrasts (`thinks` vs `is thinking`, `has finished` vs `was
  finishing`) are inherently abstract and cannot be disambiguated by a
  still photograph. Better no images than misleading images.

### Cleaned up
- 267 image-cue rows in `conjugations_image.txt` (deleted)
- 266 jpg/png assets in `media/images/` (deleted, ~58 MB freed in LFS)
- `build_images.py` Wikimedia fetcher (deleted)
- `media/images_index.json` manifest (deleted)
- All Module 14 references in `build_anki_package.py`: MODULE_TAGS,
  MODULE_NAMES, row_module() priority list, DECK_IDS, TYPE_SUFFIX,
  Image-Cue note model, ingestion loop
- Deck tree now ends cleanly at Module 13 (L1 Interference). No
  "Coming soon" placeholder, no empty Module 14 deck.

### Build verified
3,320 cards · 109 decks · 0 errors · preset auto-binds. The 50-deck
"unbound from main preset" warning corresponds to the per-language L1
sub-decks intentionally bound to a zero-cards/day preset (v2.5.1).

## [2.3.0] - 2026-05-15

### Changed
- **Complete CSS rewrite as a design-system with semantic tokens.**
  All ~50 hardcoded colors that had been scattered across the
  stylesheet are now consolidated into two CSS-variable blocks at
  the top of the file: one light-theme token set, one dark-theme
  token set. Every class below the tokens uses `var(--*)` so
  switching themes is automatic and impossible to miss.

### Fixed
- **Many field values that were invisible on Anki dark theme are
  now properly themed.** Previously the dark-mode override block
  covered only `.option`, `.answer-correct`, `.info-box` and a
  few others; classes like `.meta-key`, `.meta-val`, `.info-key`,
  `.info-val`, `.why-block`, `.tip-block`, `.target-badge`,
  `.sample-label`, `.sample-answer`, `.attribution`, `.cloze`
  inherited the original light-theme colors and showed as nearly-
  black-on-near-black. With the design-system rewrite they now
  pick up the dark token automatically.
- Timeline SVGs (drawn with dark strokes on transparent background)
  are now `filter: invert(0.92) hue-rotate(180deg)` in dark mode,
  so they remain legible against the dark card background without
  needing two separate asset sets.
- Anki's `{{type:Sample}}` rendered comparison table (typeans /
  typeGood / typeBad / typeMissed classes) now picks up themed
  colors so the input box and result diff are readable on dark.
- Added `color-scheme: light dark` on `.card` so native form
  controls (especially the type-in-the-answer input on iOS/iPadOS
  WebKit) render with theme-matching default chrome.
- New `.attribution` class (since-removed image-cue back side) styled
  and themed for proper visibility in both modes.

### Token taxonomy
```
--bg-card  --bg-surface  --bg-surface-2
--fg-strong --fg-default --fg-muted --fg-faint --fg-fainter
--border-default --border-muted --border-strong
--success-* --info-* --warn-* --danger-* --hint-*
--ipa-* --sample-fg --target-* --cloze-fg
--shadow-image
```
Every semantic accent ships as a triplet (-bg / -fg / -border) so
new callout components can reuse the system without inventing
new colors.

### Build verified
3,063 notes · 3,297 cards · 0 errors · 0 warnings · preset still
auto-binds on import.

## [2.2.0] - 2026-05-15

### Changed
- **Card front content is now centered** for distraction-free recall.
  Added a `.front` CSS rule (`text-align: center`) and wrapped the
  question portion of all 7 templates in `<div class="front">…</div>`.
  The instruction line, sentence/prompt, A/B options, image, and
  back-side echo of the question all sit center-stage; answer details
  below the `<hr id="answer">` rule remain left-aligned for readability.
- **Audio now autoplays only when the answer is revealed.** The
  `{{Audio}}` field was removed from every `qfmt` (front side) and
  retained on every `afmt` (back side). Anki's autoplay behavior plays
  any `[sound:…]` tag rendered on the currently displayed side, so this
  one change ensures pronunciation is heard at the moment of feedback,
  not before the learner has tried to recall.

### Why this matters (pedagogy)
- *Effortful recall*: hearing the audio before attempting recall would
  short-circuit the retrieval struggle that drives memory consolidation.
  Listening on reveal turns the audio into a confirmation/correction
  signal — exactly when a learner can map sound onto their guess.
- *Visual focus*: a centered prompt eliminates left-edge eye-anchoring
  and removes a small but constant cognitive scan; especially helpful on
  AnkiMobile and tablets where wide left-aligned text drifts off the
  thumb-zone.

## [2.1.0] - 2026-05-15

### Removed
- ** PyPI dependency.** Eliminated the last vestige of the legacy
  packager. The  file in this repo is now a drop-in *shim*
  built directly on top of the official  API. The shim
  exposes the tiny subset of genanki we use (, , ,
  ) so 1,287 lines of model/template/note construction code in
   continue to work unchanged.
-  (no longer needed — the shim writes
  the modern .apkg directly).
-  standalone import workaround.

### Changed
-  no longer pins .
-  is now a no-op stub (preset is created via the
  proper Anki backend API inside the shim's ).

### Why this matters
The shim creates the FSRS preset and binds every deck to it via
 *during* the export step, then exports
with . Result: a modern v18 .apkg
whose preset auto-applies to all 68 sub-decks the moment the user
imports it in Anki Desktop 23.10+. Acid-tested with round-trip import
into a fresh Collection: every sub-deck binds to English Verb System
preset (FSRS on, retention 0.9, 10 new/day, 150 reviews/day).

### Verified
- 3,063 notes, 3,297 cards, 7 models, 3,011 media files (109 MB .apkg)
- 0 validator errors, 0 warnings
- 100% of non-default decks bound to FSRS preset on import

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
