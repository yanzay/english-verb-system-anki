# English Verb System Anki Package

A comprehensive English verb-system Anki study package covering tense, aspect, future forms,
conditionals, passive voice, and stative/dynamic verb distinctions.

## What is included

| File | Purpose |
|------|---------|
| `conjugations_recognition.txt` | Recognition notes — 8 fields per row (404 rows) |
| `conjugations_contrast.txt` | Contrast notes — 7 fields per row (208 rows) |
| `conjugations_production.txt` | Production notes — 6 fields per row (204 rows) |
| `anki_premium_schema_package.txt` | Schema and study strategy reference |
| `build_anki_package.py` | Builds the `.apkg` package from the source files |
| `validate_anki_data.py` | Validates field structure, labels, and answer integrity |
| `requirements.txt` | Pinned Python dependencies |
| `ANKI_SETTINGS.md` | Recommended Anki deck options and study path |

## Deck structure

The package produces 38 subdecks organized into 13 modules:

```
English Verb System
├── 01 - Core Tense & Aspect          (90 / 42 / 44)
├── 02 - Future Forms                 (20 / 14 / 10)
├── 03 - Conditionals                 (35 / 17 / 19)
├── 04 - Passive Voice                (40 / 19 / 20)
├── 05 - Stative vs Dynamic           (25 / 18 / 15)
├── 06 - Reported Speech              (22 / 20 / 19)
├── 07 - Time Clauses                 ( 9 /  6 /  4)
├── 08 - Modal Verbs                  (22 / 13 / 15)
├── 09 - Subjunctive & Wish           (15 / 12 /  7)
├── 10 - Non-Finite Forms             ( 8 /  6 /  6)
├── 11 - Phrasal Verbs (Top 60)       (63 / 28 / 30)
├── 12 - Discourse & Pragmatics       (22 / 13 /  5)
└── 13 - L1 Interference (6 langs)    (33 /  0 / 10)

Counts shown as Recognition / Contrast / Production.
Total: 816 cards across 38 subdecks.
```

## What each module covers

- **01–05** — the original core (tenses, future forms, conditionals, passive, stative/dynamic).
- **06 Reported Speech** — full backshift system + reported questions/commands/requests/modals.
- **07 Time Clauses** — when/before/after/by-the-time interactions with tense.
- **08 Modal Verbs** — must/should/may/might/can/could (deduction · obligation · advice · ability) plus modal perfects (should have / must have / could have / etc.) and used-to / would.
- **09 Subjunctive & Wish** — mandative subjunctive, wish (present/past/would), if only, would rather, it's time, as if/as though.
- **10 Non-Finite Forms** — gerund vs infinitive choice, bare infinitive after let/make/help, perfect infinitive/gerund/participle, infinitive of purpose.
- **11 Phrasal Verbs** — top 60 high-frequency phrasal verbs from BNC/COCA, with separability and confusable-pair drills.
- **12 Discourse & Pragmatics** — historical present, headline present, recipe imperative, hypothetical past for politeness, academic hedging modals, cleft sentences, emphatic do.
- **13 L1 Interference** — diagnostic + corrective cards for typical English errors made by Spanish, French, German, Russian, Mandarin, and Japanese speakers.

## Card styling

The shipped CSS includes a light/serif default plus a `@media (max-width: 600px)` block for mobile and full **dark-mode** support that activates automatically with Anki's night-mode toggle (`.nightMode` / `.night_mode` body class).

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

1. Open Anki.
2. Choose **File → Import**.
3. Select `english_verb_system_anki.apkg`.
4. Anki will create all 15 subdecks automatically.

### Step 5 — Apply recommended settings

See **`ANKI_SETTINGS.md`** for the full recommended Anki deck options preset
and suggested study path (staged from core recognition through to stative/dynamic cards).

## Recommended study path

| Stage | Module | Deck types to enable |
|-------|--------|----------------------|
| 1 | 01 - Core Tense & Aspect | Recognition only |
| 2 | 01 - Core Tense & Aspect | + Contrast |
| 3 | 01 - Core Tense & Aspect | + Production |
| 4 | 02 - Future Forms | All three |
| 5 | 03 - Conditionals | All three |
| 6 | 04 - Passive Voice | All three |
| 7 | 05 - Stative vs Dynamic | All three |

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
- All 219 rows pass validation before each build.
- Cards route to the correct module subdeck automatically based on their tags.
- See `ANKI_SETTINGS.md` for full recommended options including new cards/day,
  review limits, burying, leech thresholds, and tag-based filtering shortcuts.
