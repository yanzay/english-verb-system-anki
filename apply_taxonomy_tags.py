#!/usr/bin/env python3
"""
Tier-3 taxonomy tagger.

Augments the Tags field of every row in:
    conjugations_recognition.txt
    conjugations_contrast.txt
    conjugations_production.txt
    conjugations_cloze.txt        (if present)

with three new prefix-tag families:

    register:formal     register:neutral     register:informal
                        register:spoken      register:academic
    frequency:high      frequency:mid        frequency:low
    domain:work         domain:travel        domain:news
                        domain:dialogue      domain:academic
                        domain:narrative     domain:kitchen
                        domain:sport         domain:tech
                        domain:family        domain:general

Inference is heuristic, deterministic, and idempotent — re-running the script
won't add duplicate tags.  Tags can be hand-corrected afterwards: this is
just the "first pass" so the corpus has a consistent baseline.

Heuristics
----------
* Register
    - 'register-formal' tag, modal-perfect, inverted-conditional, formal
      reporting verbs, 'It is …', subjunctive  →  register:formal
    - imperative + softening tag, 'wish + would', AmE-ish phrasings,
      contractions, 2nd-person 'you'  →  register:informal
    - mandative subjunctive, 'be + to-infinitive', shall, semi-modals
      'daren't / needn't', double-passive, negative inversion
      → register:formal
    - tag-question, auxiliary ellipsis, embedded question, light verb
      → register:spoken
    - hedging modals, 'it could be argued', headline present, recipe
      imperative → register:academic / register:formal
    - everything else → register:neutral

* Frequency
    - core tense/aspect labels (present-simple, present-continuous,
      past-simple, present-perfect, past-continuous, will, going-to,
      modal can/will/should/must) → frequency:high
    - inverted/conditional perfect continuous, future perfect continuous,
      mandative subjunctive, double-passive, ergative/middle-voice
      → frequency:low
    - everything else → frequency:mid

* Domain
    - keyword scan against a small lexicon (case-insensitive substring
      match on the Sentence field — for production rows, on the Sample
      field).
"""
from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

# ── Heuristic lexicons ──────────────────────────────────────────────────
DOMAIN_KEYWORDS = {
    "work": [
        "office", "meeting", "report", "deadline", "client", "colleague",
        "project", "boss", "manager", "team", "presentation", "contract",
        "quarter", "budget", "interview", "intern", "company", "firm",
        "executive", "negotiat", "merger", "audit", "consultancy",
        "auditor", "committee", "board", "headquarter", "corporate",
        "staff",
    ],
    "travel": [
        "flight", "airport", "ticket", "hotel", "passport", "tourist",
        "vacation", "holiday", "trip", "journey", "abroad", "luggage",
        "boarding", "Berlin", "Paris", "Lisbon", "Tokyo", "Iceland",
        "Madrid", "Beijing", "Lyon", "Saint Petersburg", "Vancouver",
        "Greece", "Moscow", "London",
    ],
    "news": [
        "President", "minister", "government", "election", "treaty",
        "press release", "headline", "spokesperson", "official", "summit",
        "regulator", "approve", "announc", "nation", "council",
    ],
    "dialogue": [
        " — ", "?", "wedding", "birthday", "interrupt", "thanks",
        "please", "sorry", "would you", "could you", "shall we",
        "wouldn't you",
    ],
    "academic": [
        "thesis", "dissertation", "research", "scholar", "scientif",
        "experiment", "professor", "university", "campus", "study",
        "students", "exam", "essay", "biology", "physics", "history",
        "lecture", "questionnaire", "marathon",
    ],
    "narrative": [
        "yesterday", "last night", "once upon", "while ", "when ",
        "before ", "after ", "by the time", "the moment",
        "no sooner", "hardly had", "story", "novel",
    ],
    "kitchen": [
        "lasagna", "dinner", "breakfast", "lunch", "coffee", "shower",
        "kitchen", "restaurant", "cook", "bake", "eat ",
    ],
    "sport": [
        "marathon", "match", "team", "training", "gym", "race",
        "coach", "stadium", "swim", "run ", "ran ", "running",
    ],
    "tech": [
        "software", "server", "code", "data", "app", "website",
        "system", "rack", "database", "browser", "AI", "model",
    ],
    "family": [
        "parents", "brother", "sister", "grandmother", "grandfather",
        "children", "child", "son", "daughter", "wife", "husband",
        "uncle", "aunt", "cousin", "family", "mother", "father",
        "kids",
    ],
}

# Order matters: first match wins. 'general' is the fallback.
DOMAIN_PRIORITY = ["news", "academic", "work", "tech", "travel", "kitchen",
                   "sport", "family", "narrative", "dialogue"]

REGISTER_FORMAL_TAGS = {
    "register-formal", "inverted-conditional", "modal-perfect",
    "mandative", "be-to-infinitive", "shall", "semi-modal",
    "semi-modal-dare", "semi-modal-need", "double-passive",
    "negative-inversion", "high-time", "subjunctive",
    "reduced-relative-past-participle", "cleft-conditional",
    "on-condition-that",
}
REGISTER_INFORMAL_TAGS = {
    "register-informal", "wish-annoyance", "implicit-conditional",
    "ame-vs-bre",
}
REGISTER_SPOKEN_TAGS = {
    "tag-question", "auxiliary-ellipsis", "embedded-question",
    "indirect-question", "light-verb", "discourse",
}
REGISTER_ACADEMIC_TAGS = {
    "hedging", "academic-hedging", "headline", "recipe", "performative",
}

FREQUENCY_HIGH_TAGS = {
    "present-simple", "present-continuous", "past-simple", "past-continuous",
    "present-perfect", "future-going-to", "future-will", "modal", "core",
    "phrasal-verb", "passive-present-simple", "passive-past-simple",
    "conditional-first", "conditional-zero",
}
FREQUENCY_LOW_TAGS = {
    "conditional-perfect-continuous", "future-perfect-continuous",
    "mandative", "double-passive", "ergative", "middle-voice",
    "negative-inversion", "passive-past-perfect", "passive-past-continuous",
    "perfect-gerund", "perfect-participle", "be-to-infinitive",
    "cleft-conditional", "comparative-correlative", "as-if-counterfactual",
    "modal-perfect-continuous",
}

NEW_PREFIXES = ("register:", "frequency:", "domain:")


# ── Inference ────────────────────────────────────────────────────────────
def infer_register(tag_set):
    if tag_set & REGISTER_FORMAL_TAGS:
        return "register:formal"
    if tag_set & REGISTER_ACADEMIC_TAGS:
        return "register:academic"
    if tag_set & REGISTER_SPOKEN_TAGS:
        return "register:spoken"
    if tag_set & REGISTER_INFORMAL_TAGS:
        return "register:informal"
    return "register:neutral"


def infer_frequency(tag_set):
    if tag_set & FREQUENCY_LOW_TAGS:
        return "frequency:low"
    if tag_set & FREQUENCY_HIGH_TAGS:
        return "frequency:high"
    return "frequency:mid"


def infer_domain(text):
    low = (text or "").lower()
    for dom in DOMAIN_PRIORITY:
        for kw in DOMAIN_KEYWORDS[dom]:
            if kw.lower() in low:
                return f"domain:{dom}"
    return "domain:general"


def augment_tags(tag_str, sentence_or_sample):
    existing = tag_str.split()
    keep = [t for t in existing if not t.startswith(NEW_PREFIXES)]
    tag_set = set(keep)
    new_tags = [
        infer_register(tag_set),
        infer_frequency(tag_set),
        infer_domain(sentence_or_sample),
    ]
    return " ".join(keep + new_tags)


# ── File I/O ─────────────────────────────────────────────────────────────
SCHEMAS = {
    "conjugations_recognition.txt": {"tag_idx": 7, "text_idx": 0, "fields": 8},
    "conjugations_contrast.txt":     {"tag_idx": 6, "text_idx": 0, "fields": 7},
    "conjugations_production.txt":   {"tag_idx": 5, "text_idx": 3, "fields": 6},
    "conjugations_cloze.txt":        {"tag_idx": 3, "text_idx": 0, "fields": 4},
}


def process_file(path: Path, spec):
    if not path.exists():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    out_lines = []
    rows_changed = 0
    for line in lines:
        if not line or line.startswith("#"):
            out_lines.append(line)
            continue
        # parse one row at a time so quoted fields with embedded tabs survive
        reader = csv.reader([line], delimiter="\t", quotechar='"')
        row = next(reader)
        if len(row) < spec["fields"]:
            out_lines.append(line)
            continue
        text = row[spec["text_idx"]]
        new_tags = augment_tags(row[spec["tag_idx"]], text)
        if new_tags != row[spec["tag_idx"]]:
            row[spec["tag_idx"]] = new_tags
            rows_changed += 1
        # write back as TSV; only quote if needed
        buf = io.StringIO()
        csv.writer(buf, delimiter="\t", quotechar='"',
                   quoting=csv.QUOTE_MINIMAL).writerow(row)
        out_lines.append(buf.getvalue().rstrip("\r\n"))
    path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return rows_changed


def main():
    total = 0
    for fname, spec in SCHEMAS.items():
        n = process_file(Path(fname), spec)
        if n:
            print(f"  {fname}: {n} rows updated")
        total += n
    print(f"\n✓ Tier-3 taxonomy tags applied to {total} rows.")


if __name__ == "__main__":
    main()
