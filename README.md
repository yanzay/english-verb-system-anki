# English Verb System Anki Package

A comprehensive English verb-system Anki study package covering tense, aspect, future forms,
conditionals, passive voice, and stative/dynamic verb distinctions.

## What is included

| File | Purpose |
|------|---------|
| `conjugations_recognition.txt` | Recognition notes — 9 fields per row (833 rows) |
| `conjugations_contrast.txt` | Contrast notes — 7 fields per row (654 rows) |
| `conjugations_production.txt` | Production notes — 6 fields per row (615 rows) |
| `conjugations_cloze.txt` | **Tier 3** — Cloze deletion notes (3 fields, 536 rows) |
| `apply_taxonomy_tags.py` | **Tier 3** — auto-injects `register:* / frequency:* / domain:*` tags |
| `anki_premium_schema_package.txt` | Schema and study strategy reference |
| `build_anki_package.py` | Builds the `.apkg` package from the source files (Tier 1 + Tier 2 media) |
| `build_audio.py` | **Tier 2** — generates one MP3 per unique sentence via Google Cloud TTS |
| `build_ipa.py` | **Tier 2** — generates broad GA IPA transcriptions per sentence (and per word) |
| `build_timelines.py` | **Tier 2** — generates SVG timeline diagrams per canonical tense label |
| `validate_anki_data.py` | Validates field structure, labels, and answer integrity |
| `requirements.txt` | Pinned Python dependencies |
| `ANKI_SETTINGS.md` | Recommended Anki deck options and study path |
| `media/audio/` | Generated MP3s (one per unique sentence, hashed filename) — gitignored |
| `media/timelines/` | Generated SVG timelines (one per tense label) — gitignored |
| `media/ipa_index.json` | Hash → IPA lookup used by the build script — gitignored |

## Deck structure (v3.2.0 — curriculum-first)

The package produces **85 sub-decks across 13 modules**, sequenced as a
proper curriculum (counts are deck placements; some cards live in
multiple sub-decks by design):

```
English Verb System
├── 00 - Foundation (12-Cell Grid)              ←   598 cards · ENABLED by default
├── 01 - Periphrastic Futures (be going to)     ←    37 cards · opt-in
├── 02 - Past Habits (used to)                  ←     7 cards · opt-in
├── 03 - Modal Verbs                            ←   125 cards · opt-in
├── 04 - Conditionals                           ←   192 cards · opt-in
├── 05 - Passive Voice                          ←   168 cards · opt-in
├── 06 - Mood (Subjunctive, Imperative)         ←    15 cards · opt-in
├── 07 - Non-Finite Forms                       ←    79 cards · opt-in
├── 08 - Reported Speech                        ←    70 cards · opt-in
├── 09 - Phrasal Verbs                          ←   101 cards · opt-in
├── 10 - Discourse Constructions                ←   757 cards · opt-in
├── 11 - Phonology & Connected Speech           ←    62 cards · opt-in
├── 12 - Transformation & Register              ←    73 cards · opt-in
└── 13 - L1 Interference (per-language)         ← 1,004 cards · opt-in (per L1)

Total: 2,794 unique cards across 85 sub-decks (3,288 deck placements).
```

Each module has 4 sub-decks: **Recognition · Contrast · Cloze · Production**.

### How the default works

On a fresh import of the `.apkg`:

* **Module 00 (Foundation)** is bound to the main `English Verb System`
  preset → 10 new cards/day, FSRS scheduling, sibling burying. You start
  studying immediately.
* **Modules 01–13** are bound to a separate `English Verb System (L1 — opt in)`
  preset that's set to **0 new cards/day**. The cards are present but
  silent.

This enforces the pedagogical principle "**master the canonical
12-cell tense+aspect grid first, then layer everything else on top**" —
a default the deck author can't accidentally let you skip.

### How to unlock a layer (or your L1)

When you're ready to add, say, **Module 03 - Modal Verbs**:

1. Click the gear icon ⚙ next to `English Verb System::03 - Modal Verbs`
2. **Deck Options** → at the top, switch the preset from
   `English Verb System (L1 — opt in)` to `English Verb System`
3. The 125 modal cards will start flowing in at 10/day alongside your
   Foundation reviews

Same flow for Module 13 sub-decks — switch only your L1 (e.g.
`13 - L1 Interference::🇷🇺 Russian speakers`) to the main preset.

### Recommended study path

| Phase | Weeks | Enable | Why |
|---|---|---|---|
| **1. Foundation** | 1–8 | 00 | Master the 12-cell grid (CEFR A1–B1) — every other layer presupposes this |
| **2. Modality** | 9–12 | 03 + 04 | Add modal verbs and conditional types — the next-most-frequent grammar |
| **3. Voice & Mood** | 13–16 | 05 + 06 | Passive voice and subjunctive — needed for B2 |
| **4. Non-finite + Reported** | 17–20 | 07 + 08 | Gerund/infinitive + reported speech — late-B2 sticking points |
| **5. Lexical** | any time | 09 | Top-frequency phrasal verbs — independent of the grammar curriculum |
| **6. Discourse + Phonology** | C1+ | 10 + 11 + 12 | Cleft, inversion, connected speech, register transformations |
| **L1 (anytime)** | any | 13 | Drill the contrasts that *your* L1 trips its speakers up on |

Module 02 (Past Habits) and 01 (Periphrastic Futures) are useful enrichment but optional — they cover a smaller surface area than the modal/conditional layers.

## What each module covers

- **00 Foundation (12-Cell Grid)** — the canonical 3 tenses × 4 aspects grid: Present/Past/Future × Simple/Continuous/Perfect/Perfect-Continuous. Plus the 12 cells in their passive variants and basic auxiliary patterns. **This is what every learner masters first.**
- **01 Periphrastic Futures** — `be going to`, `be about to`, `be to + inf` (formal future), `shall` (suggestion + formal). These are not part of the canonical grid; they're separate constructions that *express* future meaning.
- **02 Past Habits** — `used to` (states + actions, no longer true) vs `would` (dynamic actions only, narrative).
- **03 Modal Verbs** — must/should/may/might/can/could (deduction · obligation · advice · ability) plus modal perfects (should have / must have / could have / etc.) and semi-modals (`needn't`, `daren't`, `had better`).
- **04 Conditionals** — Type 0/1/2/3, mixed conditionals, inverted conditionals (*Had I known…, Were she…, Should you require…*), implicit conditionals, cleft conditionals (*if it weren't for…*).
- **05 Passive Voice** — all 12 cells in passive form, ditransitive passive (recipient vs theme subject), ergative/middle voice, reduced relative clauses, double passive, get-passive vs be-passive.
- **06 Mood** — mandative subjunctive (*I insist that he be…*), past subjunctive (*if I were…, it's high time you went…*), imperative variants (recipe imperative, polite imperative).
- **07 Non-Finite Forms** — gerund vs infinitive choice (verb-pattern), bare infinitive after let/make/help, perfect infinitive/gerund/participle, infinitive of purpose, raising vs control verbs.
- **08 Reported Speech** — full backshift system, reported questions/commands/requests/modals, reporting-verb patterns (`admit/deny + V-ing`, `accuse of`, `apologise for`), backshift exceptions (universal truths, conditional 2/3).
- **09 Phrasal Verbs** — top 60 high-frequency phrasal verbs from BNC/COCA, separability rules, confusable-pair drills.
- **10 Discourse Constructions** — cleft sentences (it-cleft, what-cleft, all-cleft, pseudo-cleft), existential there, negative inversion, fronting, emphatic do, tag questions, auxiliary ellipsis (*so do I, neither will…*), hedging modals, comparative correlatives (*the harder…*), narrative tense layering, indirect questions.
- **11 Phonology & Connected Speech** — weak forms (`have/has/was/were/to`), reductions (`gonna/gotta/wanna/shoulda`), contractions (`I'd/she'd/we've/it's`), t-flapping, linking-r, stress contrast, schwa elision.
- **12 Transformation & Register** — formal vs informal (modal paraphrase, register shift, AmE vs BrE), active↔passive transformations, tense-change drills.
- **13 L1 Interference** — split into per-language sub-decks for Spanish, French, German, Russian, Mandarin, Japanese, Korean, Arabic, Portuguese, Dutch + an "Other" catch-all. Each user enables only their own L1.

### Tier 1 expansions (history)

Earlier releases (v1.4 → v3.0) plugged twelve previously missing topic clusters
and backfilled all labels that had fewer than four examples per card type. The
listed clusters are part of the current 2,794-card corpus:

- **Auxiliary ellipsis** — *So do I / Neither will my colleagues / Nor do I*
- **Tag questions** — positive/negative/imperative/modal tag agreement
- **Negative inversion** — *Hardly had…, Not only did…, Never have I…, No sooner had…, Only after…*
- **Inverted conditionals** — *Had I known…, Were she…, Should you require…*
- **Raising vs control verbs** — *seem/appear* vs *manage/promise/want*
- **Ditransitive passive** — recipient-subject vs theme-subject variants
- **Ergative & middle voice** — *the bookshelf collapsed*, *vintage records sell quickly*
- **Reduced relative clauses** — *the man wearing…*, *the report submitted…*
- **Double passive** — *is expected to be signed*
- **Light / delexical verbs** — *have a shower, take a breath, make a decision*
- **Be + to-infinitive** (formal future) — *You are to report at 8 a.m.*
- **Shall** — suggestion + formal future
- **Semi-modals** — *daren't, needn't, would rather, would sooner*
- **Suppose / Supposing / Providing / On condition that / In case**
- **Comparative correlative** — *the harder you train, the faster you recover*
- **Even if vs even though** — hypothetical vs real concession
- **Implicit conditionals** — *one more interruption and I'll lose my temper*
- **Future-in-the-past** — *was going to / would / was about to*
- **Narrative tense layering** — past simple + past continuous + past perfect
- **Modal + perfect continuous** — *must have been working, should have been studying*
- **Embedded / indirect questions** — *Do you know whether…? Could you tell me where…?*
- **Reporting verb patterns** — *admit/deny/suggest + V-ing*, *accuse of, apologise for, blame for, promise/refuse + to-inf*
- **Backshift exceptions** — universal truths and conditional 2/3 don't backshift
- **Wish + would** — annoyance and polite-request senses
- **AmE vs BrE** — *I just got off the phone* vs *I've just spoken to him*
- **Habitual would vs used to** — dynamic habits only vs habits + states
- **As if + past perfect** — counterfactual past comparison
- **It's high time** — past subjunctive form
- **Cleft conditionals** — *if it weren't for her quick thinking…*
- **Causatives** — have/get/make/let/help with object + bare infinitive or past participle

## Card styling

The shipped CSS includes a light/serif default plus a `@media (max-width: 600px)` block for mobile and full **dark-mode** support that activates automatically with Anki's night-mode toggle (`.nightMode` / `.night_mode` body class). Tier 2 adds a warm IPA panel and centered timeline image.

## Tier 2 — multimodal upgrade (this release)

The deck now ships with three additional media layers that elevate it from
"good text deck" to "premium pronunciation + grammar deck":

### 🔊 Audio

- **One MP3 per unique sentence** (~2,348 unique sentences after dedup across the 2,794-card corpus).
- Synthesised with **Google Cloud Text-to-Speech**, voice `en-US-Neural2-F`
  (a warm, natural female voice). Fully configurable via `EVS_TTS_VOICE`
  env var or the `--voice` flag of `build_audio.py`.
- Filename = `<sha1[:12] of sentence>.mp3`, content-addressed and idempotent.
- Plays automatically on the front of every card via Anki's `[sound:…]` tag.
- **Idempotent + incremental:** `build_audio.py` records every render in
  `media/audio_manifest.json` (text, voice, rate, lang, sha256). Re-running it
  only synthesises sentences that are missing, whose params drifted, or whose
  on-disk file no longer matches its recorded sha. Orphan MP3s for sentences
  removed from the corpus are pruned automatically. `validate_anki_data.py`
  enforces the manifest and (with `--verify-audio-sha`) the file fingerprints.

### 🔤 IPA transcription

- Every sentence has a broad General-American IPA transcription on the back.
- Computed offline (no network) by the `eng-to-ipa` library
  (Carnegie-Mellon dict + heuristic fallback).
- Out-of-dictionary rate on this corpus is well under 1 % (heuristic fallback covers the long tail).
- Per-word audit dump in `media/ipa_words.json` lets you spot odd entries.

### ⏱️ Timeline diagrams

- 40 lightweight SVG diagrams (~1 KB each) — one per canonical
  tense / aspect label.
- Show the action's position relative to the **PAST / NOW / FUTURE** axis
  and whether it is punctual, durative, or perfective.
- Auto-invert in Anki dark mode via `@media (prefers-color-scheme: dark)`.
- 416 cards (those whose canonical Label/Answer/Target matches a known
  tense) get a timeline; the rest fall back to text only.

### How to (re)generate the media

The package as shipped already contains the media. To re-render from scratch:

```bash
# 1. Auth once with gcloud (uses Application Default Credentials)
gcloud auth application-default login

# 2. Install Python deps in a venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Generate the three media layers (timelines + IPA are free; audio uses paid TTS)
python3 build_timelines.py             # 40 SVGs, ~instant, free
python3 build_ipa.py                   # ~2,700 IPA strings, ~30 s, free
python3 build_audio.py                 # ~2,400 MP3s, ~12 min, ≈ US$3 (incremental on subsequent runs)

# 4. Rebuild the .apkg (now ~25 MB with audio bundled)
python3 build_anki_package.py
```

`build_audio.py --dry-run --limit 10` is the recommended cost-free smoke test
before committing a full re-render.

## Cloning the repository (Git LFS)

Audio (`media/audio/*.mp3`), IPA (`media/ipa/*.txt`), timeline diagrams
(`media/timelines/*.svg`), and the built `.apkg` are all stored in
**Git LFS** to keep the repository fast and under GitHub's hard size
limit.

You need [Git LFS](https://git-lfs.github.com/) installed once on your
machine before cloning:

```bash
# macOS
brew install git-lfs

# Ubuntu / Debian
sudo apt install git-lfs

# After install (one-time):
git lfs install
```

Then clone normally — LFS files download transparently:

```bash
git clone https://github.com/yanzay/english-verb-system-anki.git
cd english-verb-system-anki
```

If you cloned **before** installing LFS, fix the working tree with:

```bash
git lfs install
git lfs pull
```

You can verify the working tree is healthy with:

```bash
file media/audio/00516b6462bf.mp3      # → "Audio file with ID3..."
file media/timelines/abcdef123456.svg  # → "SVG Scalable Vector Graphics image..."
```

If those say `ASCII text`, you have LFS pointers instead of real files —
run `git lfs pull` to resolve.

**For users who only want the `.apkg`**: download the latest release from
the [GitHub Releases page](https://github.com/yanzay/english-verb-system-anki/releases)
or pull just that file: `git lfs pull --include="*.apkg"`.

---

## How to build and import

### Step 1 — Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### Step 2 — Validate source files

```bash
python3 validate_anki_data.py
```

### Step 3 — Build the package

```bash
python3 build_anki_package.py
```

This creates `english_verb_system_anki.apkg`.

### Step 4 — Import into Anki

1. Open Anki (23.10 or later strongly recommended).
2. Choose **File → Import**.
3. Select `english_verb_system_anki.apkg`.
4. In the import dialog, **leave "Update notetypes" and "Import deck
   presets" checked** (both are on by default in Anki 23.10+).
5. Anki creates all 85 sub-decks plus both presets
   (`English Verb System` + `English Verb System (L1 — opt in)`) and
   binds them automatically. **You're done — start studying Module 00.**

> 🛈 If you're on **Anki ≤ 23.09**, the importer ignores the embedded
> deck-options. In that case set up the preset by hand using
> [`ANKI_SETTINGS.md`](ANKI_SETTINGS.md) Path B.

(See **[Recommended study path](#recommended-study-path)** above for
when to enable each layer.)

## Field schemas

### Recognition (`conjugations_recognition.txt`)
| Field | Purpose |
|-------|---------|
| `Sentence` | The example sentence only — no instructions |
| `Label` | Canonical tense/aspect label e.g. *Present Perfect* |
| `Aspect` | Aspect tag e.g. *perfective*, *progressive*, *simple* |
| `Formula` | Structural formula e.g. *have/has + past participle* |
| `MainUse` | Primary communicative function |
| `QuickCue` | Signal words or features in the sentence |
| `Contrast` | What this is often confused with and why it isn't that |
| `Tags` | Space-separated tag string |

**Card front:** instruction line (from template) + `Sentence`  
**Card back:** `Label` (large) → `Aspect` badge → `Formula` / `MainUse` grid → `QuickCue` + `Contrast` info box

---

### Contrast (`conjugations_contrast.txt`)
| Field | Purpose |
|-------|---------|
| `Sentence` | The sentence to classify |
| `OptionA` | First label option |
| `OptionB` | Second label option |
| `Answer` | Correct label (must match OptionA or OptionB exactly) |
| `Why` | Explanation of why the answer is correct |
| `Tip` | Study tip or memory rule |
| `Tags` | Space-separated tag string |

**Card front:** instruction line + `Sentence` + styled A/B option boxes  
**Card back:** ✓ `Answer` badge → `Why` → `Tip` (italic)

---

### Production (`conjugations_production.txt`)
| Field | Purpose |
|-------|---------|
| `Prompt` | Constrained writing prompt |
| `Target` | Target form e.g. *Past Perfect* |
| `Aspect` | Aspect tag |
| `Sample` | A strong sample answer |
| `Why` | Why the sample answer demonstrates the target form |
| `Tags` | Space-separated tag string |

**Card front:** instruction line + `Prompt` + `Target` badge  
**Card back:** "Sample answer" label + `Sample` (styled) → "Why this works" + `Why`

## Labels used

The package uses a consistent canonical naming system:

**Core tense/aspect**
Present Simple · Present Continuous · Present Perfect · Present Perfect Continuous ·
Past Simple · Past Continuous · Past Perfect · Past Perfect Continuous ·
Future Simple · Future Continuous · Future Perfect · Future Perfect Continuous ·
Conditional Simple · Conditional Continuous · Conditional Perfect · Conditional Perfect Continuous

**Future forms**
Be Going To · Present Continuous for Future Arrangement · Present Simple for Schedule

**Conditionals**
Zero Conditional · First Conditional · Second Conditional · Third Conditional · Mixed Conditional

**Passive voice**
Present Simple Passive · Past Simple Passive · Present Perfect Passive · Modal Passive

**Stative / dynamic**
Present Simple (Stative) · Present Continuous (Dynamic Stative Shift)

## Notes

- The build script auto-installs `genanki` if it is missing.
- All 2,638 source rows pass schema validation (`python3 validate_anki_data.py --no-audio-check`) before each build.
- Cards route to the correct module subdeck automatically based on their tags.
- See `ANKI_SETTINGS.md` for full recommended options including new cards/day,
  review limits, burying, leech thresholds, and tag-based filtering shortcuts.

## P1 module additions

This release introduces the following modules, card types, and tagging:

**New modules**
- `module:l1` — L1 interference (Korean, Arabic, Portuguese added)
- `module:phrasal-verbs` — Phrasal verb patterns
- `module:discourse` — Discourse and narrative structures
- `module:passive` — Passive voice constructions
- `module:causative` — Causative structures
- `module:stative-dynamic` — Stative vs. dynamic verb distinctions
- `module:reported-speech` — Reported speech and backshift
- `module:time-clauses` — Time clause structures
- `module:modals` — Modal verbs and semi-modals
- `module:subjunctive` — Subjunctive mood
- `module:non-finite` — Non-finite forms (gerunds, infinitives, participles)
- `module:conditionals` — Conditional structures
- `module:future` — Future tense forms
- `module:inversion-cleft` — Inversion and cleft structures
- `module:cohesion` — Cohesive devices (tag questions, ellipsis)

**New card types**
- `card-type:recognition` — Recognize the tense/aspect
- `card-type:contrast` — Choose between two options
- `card-type:production` — Produce a sentence
- `card-type:cloze` — Fill in the missing form
- `Spot-the-Error` cards (model v1) — Error-correction variant for contrast rows
- `Reverse Production (Auto)` cards (model v1) — B2+ learners, standard tenses

**Tag taxonomy improvements**
- Every row now has a `module:*` tag (idempotent backfill)
- Every row now has a `card-type:*` tag where applicable
- Module assignment follows explicit rules (L1 > phrasal-verbs > discourse, etc.)
- Core module (`module:core`) as fallback for rows with no special tags

**Auto-generated cards**
- Spot-the-Error cards generated for rows tagged `error-correction`, 
  `l1-interference`, or `spot-the-error`
- Reverse Production cards auto-generated for recognition rows with 
  CEFR B2/C1/C2 and standard tenses (Present Simple, Past Simple, etc.)

## Versioning

This package follows semantic versioning. For a complete history of changes, see [CHANGELOG.md](CHANGELOG.md).

Current version: **3.2.11**
