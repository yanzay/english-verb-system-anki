# Recommended Anki Settings

After importing `english_verb_system_anki.apkg`, apply these deck option presets.
The deck is organized into five modules. Apply settings per module or create one
shared preset and adjust new-cards-per-day per module.

---

## How to apply deck options in Anki

1. Open Anki and click the gear icon next to a deck.
2. Choose **Options**.
3. Create a new preset (e.g. "English Verb System") and configure as below.
4. Apply the same preset to all five module decks, or create per-module presets
   for finer control.

---

## Recommended preset: "English Verb System"

### Daily limits
| Setting                   | Recommended value        |
|---------------------------|--------------------------|
| New cards per day         | 10 (core), 5 per other module |
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

### Display order
| Setting                   | Recommended value        |
|---------------------------|--------------------------|
| New/review order          | Show reviews before new  |
| Review sort order         | Due date, then random    |

---

## Suggested study path

### Stage 1 — Core Tense & Aspect
Start with `01 - Core Tense & Aspect::Recognition` only.
- New cards per day: 10
- Goal: reach 90%+ accuracy on recognition before moving on.

### Stage 2 — Add Contrast
Enable `01 - Core Tense & Aspect::Contrast`.
- New cards per day: 5
- Continue reviewing Recognition cards.

### Stage 3 — Add Production
Enable `01 - Core Tense & Aspect::Production`.
- New cards per day: 5
- Production is the most demanding; keep daily totals moderate.

### Stage 4 — Future Forms module
Enable all three `02 - Future Forms` decks.
- New cards per day: 5 per deck type.
- Focus especially on the contrast deck: will vs going to vs present continuous.

### Stage 5 — Conditionals module
Enable all three `03 - Conditionals` decks.
- New cards per day: 5 per deck type.
- Conditionals build on verb forms already mastered in Stage 1.

### Stage 6 — Passive Voice module
Enable all three `04 - Passive Voice` decks.
- New cards per day: 5 per deck type.

### Stage 7 — Stative vs Dynamic module
Enable all three `05 - Stative vs Dynamic` decks.
- New cards per day: 5 per deck type.
- These are the subtlest distinctions; save them until later stages.

---

## Tips for effective use

- **Never skip reviews** to add more new cards. Reviews always take priority.
- **Use filtered decks** to drill a specific form using the tag browser.
  - Example tag: `contrast conditional-first-vs-second`
- **Suspend** any card that feels too easy immediately; do not waste review time.
- **Use the Extra field** (shown after the answer) for deeper study only when needed.
  During fast review mode, focus only on the Back field.
- **Target 85–90% retention** during review sessions. If you are consistently
  above 95%, consider increasing the interval modifier slightly.
- **Review in the morning** if possible for better memory consolidation.
- **Leech management**: cards that trip you up 8 times will be auto-suspended.
  Review suspended cards weekly via Browse > is:suspended.

---

## Tag browser shortcuts

Use these searches in Anki's Browse window to study specific areas:

| Filter                              | Purpose                           |
|-------------------------------------|-----------------------------------|
| `tag:contrast`                      | All contrast cards                |
| `tag:production`                    | All production cards              |
| `tag:recognition`                   | All recognition cards             |
| `tag:conditional-first-vs-second`   | First vs second conditional       |
| `tag:passive-vs-active`             | Active vs passive contrast        |
| `tag:stative`                       | Stative verb recognition          |
| `tag:dynamic-stative`               | Dynamic use of stative verbs      |
| `tag:future-going-to-vs-will`       | Going to vs will contrast         |
| `tag:core`                          | Core-level cards only             |
| `tag:advanced`                      | Advanced-level cards only         |
