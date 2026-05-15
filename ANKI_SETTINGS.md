# Recommended Anki Settings

The `.apkg` ships with **two presets** embedded:

- **`English Verb System`** — the main FSRS preset (retention 0.90,
  sibling burying on, 1m/10m learning steps, leech suspend at 8 lapses).
- **`English Verb System (L1 — opt in)`** — same scheduler with
  **0 new cards/day**. Bound to every non-Foundation sub-deck so the
  curriculum stays sequenced ("master the 12-cell grid first, then
  unlock layers").

> ⚠️ **Anki bug:** deck-options bundled inside an `.apkg` are **not
> reliably honoured on import** — your decks may show the **Default**
> preset on a fresh import (long-standing Anki behaviour, still present
> in Anki 23.10+). Re-apply the preset once after import using one of
> the paths below.

---

## Path A — One-click import (Anki 23.10 and later) ⭐ recommended

1. Download `english_verb_system_preset.json` from this repo (it ships
   alongside the `.apkg`).
2. In Anki, click the gear icon next to **any** sub-deck of
   `English Verb System` → **Deck options**.
3. In the deck-options page, click the **⋮ (three-dot menu)** in the
   top-right → **Import preset…**
4. Select the downloaded `english_verb_system_preset.json`. The preset
   `English Verb System` appears in the preset dropdown.
5. With the preset selected, click **Save** (bottom-right).

Bind every sub-deck to the preset in one shot:

6. **Right-click** the parent **`English Verb System`** deck → **Deck
   options**.
7. From the preset dropdown choose **English Verb System**.
8. Click **Save** → when asked **"Apply to all sub-decks?"** click
   **Yes**.

That binds all 85 sub-decks at once. Done.

---

## Path B — Manual setup (any Anki version)

If you're on an older Anki, or step 6–8 above didn't propagate, set it
up by hand:

1. Open Anki and click the gear icon next to any
   `English Verb System::*` deck → **Deck options**.
2. Add a new preset (the **+** button) called `English Verb System` and
   configure it per the table below.
3. Repeat steps 6–8 above to bind it to every sub-deck.

---

## Recommended preset: "English Verb System"

### Daily limits
| Setting                   | Recommended value        |
|---------------------------|--------------------------|
| New cards per day         | 10                       |
| Maximum reviews per day   | 150                      |

### New cards
| Setting                   | Recommended value        |
|---------------------------|--------------------------|
| Learning steps            | 1m 10m                   |
| Graduating interval       | 1 day                    |
| Easy interval             | 4 days                   |
| Starting ease             | 250%                     |
| New card order            | In order added           |

### Reviews
| Setting                   | Recommended value        |
|---------------------------|--------------------------|
| Maximum interval          | 365 days                 |
| Interval modifier         | 100%                     |
| Hard interval             | 120%                     |
| Easy bonus                | 130%                     |

### Lapses
| Setting                   | Recommended value        |
|---------------------------|--------------------------|
| Relearning steps          | 10m                      |
| Minimum interval          | 1 day                    |
| Leech threshold           | 8 lapses                 |
| Leech action              | Suspend card             |

### Burying
| Setting                   | Recommended value        |
|---------------------------|--------------------------|
| Bury new siblings         | On                       |
| Bury review siblings      | On                       |

### FSRS
| Setting                   | Recommended value        |
|---------------------------|--------------------------|
| Use FSRS                  | On                       |
| Desired retention         | 0.90                     |
| FSRS parameters           | (Anki defaults — let it self-tune after ~50 reviews) |

---

## Curriculum-first defaults (v3.2.0)

The deck enforces "Foundation first" via a **two-preset** strategy:

| Preset | Bound to | New cards/day |
|--------|----------|----------------|
| `English Verb System` | `00 - Foundation` | 10 |
| `English Verb System (L1 — opt in)` | `01`–`13` (all other modules) | **0** |

To unlock a layer (e.g. `03 - Modal Verbs`), open Deck Options on that
sub-deck and switch its preset from `English Verb System (L1 — opt in)`
to `English Verb System`. The 125 modal cards start flowing at 10/day
alongside Foundation reviews.

For Module 13 (L1 Interference), enable only the sub-deck for **your**
L1 — e.g. `13 - L1 Interference::🇷🇺 Russian speakers`. Drilling
contrasts that don't trip up your L1 wastes review time.

---

## Suggested study path

| Phase | Weeks | Enable | Why |
|-------|-------|--------|-----|
| **1. Foundation** | 1–8 | `00` | Master the 12-cell grid (CEFR A1–B1); every other layer presupposes this |
| **2. Modality** | 9–12 | `03 + 04` | Modals + conditionals — the next-most-frequent grammar |
| **3. Voice & Mood** | 13–16 | `05 + 06` | Passive + subjunctive — needed for B2 |
| **4. Non-finite + Reported** | 17–20 | `07 + 08` | Gerund/infinitive + reported speech — late-B2 sticking points |
| **5. Lexical** | any time | `09` | Top-frequency phrasal verbs — independent of grammar curriculum |
| **6. Discourse + Phonology** | C1+ | `10 + 11 + 12` | Cleft, inversion, connected speech, register transformations |
| **L1** | any | `13` (your L1 only) | Drill the contrasts that *your* L1 trips its speakers up on |

Modules `01` (Periphrastic Futures) and `02` (Past Habits) are useful
enrichment but optional — they cover a smaller surface area than the
modal/conditional layers.

---

## Tips for effective use

- **Never skip reviews** to add more new cards. Reviews always take
  priority — letting them stack up wrecks FSRS scheduling.
- **Use filtered decks** to drill a specific form via the tag browser.
  Example: `tag:contrast tag:conditional-second` for second-conditional
  contrast cards only.
- **Suspend cards that feel trivial** rather than rating them Easy
  repeatedly — easier on the scheduler.
- **Trust 0.90 retention.** If you're consistently above 95%, FSRS
  will lengthen intervals on its own; don't manually crank the modifier.
- **Leech management:** cards that lapse 8 times auto-suspend. Review
  them weekly via `Browse → is:suspended` and either rephrase or remove.

---

## Tag browser shortcuts

Useful searches in Anki's Browse window for slicing the deck:

| Filter                              | Purpose                                     |
|-------------------------------------|---------------------------------------------|
| `tag:card-type:recognition`         | All recognition cards                       |
| `tag:card-type:contrast`            | All contrast cards                          |
| `tag:card-type:production`          | All production cards                        |
| `tag:card-type:cloze`               | All cloze cards                             |
| `tag:cefr:a1` / `a2` / `b1` / `b2` / `c1` / `c2` | CEFR-level filter             |
| `tag:module:core`                   | Core 12-cell grid only                      |
| `tag:module:conditionals`           | All conditional types                       |
| `tag:module:modals`                 | All modal verbs                             |
| `tag:module:passive`                | All passive-voice cards                     |
| `tag:module:phrasal`                | All phrasal-verb cards                      |
| `tag:module:reported-speech`        | All reported-speech cards                   |
| `tag:module:phonology`              | All phonology / connected-speech cards      |
| `tag:l1-russian` (etc.)             | L1-specific interference cards              |
| `tag:register:formal`               | Formal-register cards (essays, exams)       |
| `tag:register:spoken`               | Spoken-register cards (everyday English)    |
