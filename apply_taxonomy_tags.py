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
    cefr:a1             cefr:a2              cefr:b1
                        cefr:b2              cefr:c1
                        cefr:c2

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

NEW_PREFIXES = ("register:", "frequency:", "domain:", "cefr:")

# ── CEFR mapping (per English Grammar Profile / Cambridge English Profile) ─
# Highest-level form on the row wins (a card teaching past-perfect-continuous
# is C1-worthy even if it incidentally contains a present-simple clause).
CEFR_C2_TAGS = {
    "mandative", "mandative-subjunctive", "formulaic-subjunctive",
    "double-passive", "ergative", "middle-voice", "cleft-conditional",
    "comparative-correlative", "perfect-gerund", "perfect-participle",
    "negative-inversion", "as-if-counterfactual", "modal-perfect-continuous",
    "be-to-infinitive", "high-time", "on-condition-that",
}
CEFR_C1_TAGS = {
    "future-perfect-continuous", "future-will-perfect-continuous",
    "inverted-conditional", "inverted-vs-standard",
    "wish-past-perfect", "subjunctive", "causative",
    "narrative-layering", "hedging", "academic-hedging",
    "reduced-relative-past-participle", "perfect-infinitive",
    "passive-infinitive", "passive-gerund", "free-indirect-speech",
    "no-sooner-than", "hardly-when", "scarcely-when",
    "even-if-vs-even-though", "implicit-conditional",
    "semi-modal", "semi-modal-dare", "semi-modal-need",
    "would-rather", "would-sooner", "may-as-well",
}
CEFR_B2_TAGS = {
    "past-perfect-continuous", "future-perfect", "future-will-perfect",
    "conditional-third", "conditional-mixed", "mixed-conditional",
    "modal-perfect", "passive-perfect", "passive-modal",
    "passive-future", "passive-present-perfect", "passive-past-perfect",
    "passive-present-continuous", "passive-past-continuous",
    "reported-speech", "backshift", "reporting-verb",
    "wish", "if-only", "wish-past",
    "gerund-vs-infinitive", "pv-figurative", "pv-three-part",
    "pv-inseparable", "pv-separable",
    "cleft", "pseudo-cleft", "stative-vs-dynamic",
    "had-better", "ought-to", "must-have", "should-have",
    "could-have", "might-have",
}
CEFR_B1_TAGS = {
    "present-perfect-continuous", "past-perfect",
    "conditional-second", "used-to",
    "passive-present-simple", "passive-past-simple",
    "future-will-continuous", "future-continuous",
    "modal-ability", "modal-permission", "modal-obligation",
    "modal-deduction", "modal-possibility", "modal-advice",
    "phrasal-verb", "pv-transitive", "pv-intransitive", "pv-literal",
    "gerund", "to-infinitive", "bare-infinitive",
    "present-participle", "past-participle",
    "time-clause", "while", "since", "as-soon-as", "by-the-time",
    "tag-question", "indirect-question", "embedded-question",
    "question",
}
CEFR_A2_TAGS = {
    "present-perfect", "past-continuous",
    "future-will", "future-will-simple", "future-simple",
    "conditional-zero", "conditional-first",
    "going-to", "future-going-to",
}
CEFR_A1_TAGS = {
    "present-simple", "present-continuous", "past-simple",
    "imperative", "negative", "affirmative",
}


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


def infer_cefr(tag_set):
    """Highest-level grammatical form on the row wins.

    Using the English Grammar Profile / Cambridge English Profile baseline.
    """
    if tag_set & CEFR_C2_TAGS:
        return "cefr:c2"
    if tag_set & CEFR_C1_TAGS:
        return "cefr:c1"
    if tag_set & CEFR_B2_TAGS:
        return "cefr:b2"
    if tag_set & CEFR_B1_TAGS:
        return "cefr:b1"
    if tag_set & CEFR_A2_TAGS:
        return "cefr:a2"
    if tag_set & CEFR_A1_TAGS:
        return "cefr:a1"
    # Default for un-tagged rows: assume B1 (the deck targets B1+ learners).
    return "cefr:b1"


def infer_module(tag_set):
    """Infer module:* tag based on existing tags.
    
    Returns a list of module tags (may be multiple).
    """
    modules = []
    
    # L1 interference module
    l1_tags = {'l1-interference', 'l1-spanish', 'l1-french', 'l1-mandarin', 
               'l1-german', 'l1-russian', 'l1-japanese', 'l1-korean', 
               'l1-arabic', 'l1-portuguese'}
    if tag_set & l1_tags:
        modules.append('module:l1')
    
    # Phrasal verbs module
    pv_tags = {'phrasal-verb', 'pv-separable', 'pv-transitive', 'pv-intransitive',
               'pv-figurative', 'pv-literal'}
    if tag_set & pv_tags:
        modules.append('module:phrasal-verbs')
    
    # Discourse module
    discourse_tags = {'discourse', 'narrative', 'headline', 'recipe', 
                      'stage-direction', 'free-indirect'}
    if tag_set & discourse_tags:
        modules.append('module:discourse')
    
    # Passive/causative modules
    passive_tags = {'passive', 'get-passive', 'double-passive', 'dative-passive',
                    'ergative', 'middle-voice', 'causative'}
    if tag_set & passive_tags:
        if 'causative' in tag_set:
            modules.append('module:causative')
        else:
            modules.append('module:passive')
    
    # Stative/dynamic module
    stative_tags = {'stative', 'dynamic', 'raising-verb', 'control-verb'}
    if tag_set & stative_tags:
        modules.append('module:stative-dynamic')
    
    # Reported speech module
    reported_tags = {'reported-speech', 'backshift', 'reporting-verb',
                     'embedded-question'}
    if tag_set & reported_tags:
        modules.append('module:reported-speech')
    
    # Time clauses module
    if 'time-clause' in tag_set:
        modules.append('module:time-clauses')
    
    # Modals module
    modal_tags = {t for t in tag_set if t.startswith('modal-')}
    modal_specific = {'had-better', 'used-to', 'be-able-to', 'be-supposed-to',
                      'would-rather', 'would-sooner', 'dare', 'need-modal', 'shall'}
    if modal_tags or (tag_set & modal_specific):
        modules.append('module:modals')
    
    # Subjunctive module
    subj_tags = {'subjunctive', 'mandative-subjunctive', 'hypothetical-past',
                 'would-rather-different-subject', 'wish-past', 'wish-future',
                 'if-only', 'as-if-as-though'}
    if tag_set & subj_tags:
        modules.append('module:subjunctive')
    
    # Non-finite forms module
    nonfinite_tags = {'gerund', 'infinitive', 'participle', 'perfect-infinitive',
                      'perfect-gerund', 'bare-infinitive'}
    if tag_set & nonfinite_tags:
        modules.append('module:non-finite')
    
    # Conditionals module
    cond_tags = {'conditional', 'conditional-zero', 'conditional-first',
                 'conditional-second', 'conditional-third', 'conditional-mixed',
                 'on-condition-that', 'providing', 'suppose', 'supposing',
                 'in-case', 'even-if', 'even-though'}
    if tag_set & cond_tags:
        modules.append('module:conditionals')
    
    # Future module
    future_tags = {'future-will', 'future-going-to', 'future-continuous',
                   'future-perfect', 'future-perfect-continuous',
                   'present-continuous-trend', 'be-about-to', 'be-to', 'going-to'}
    if tag_set & future_tags:
        modules.append('module:future')
    
    # Inversion/cleft module
    inversion_tags = {'negative-inversion', 'inverted-conditional', 'fronting',
                      'locative-inversion', 'comparative-correlative', 'cleft',
                      'pseudo-cleft', 'it-cleft'}
    if tag_set & inversion_tags:
        modules.append('module:inversion-cleft')
    
    # Cohesion module
    cohesion_tags = {'tag-question', 'ellipsis', 'auxiliary-ellipsis'}
    if tag_set & cohesion_tags:
        modules.append('module:cohesion')
    
    # Default to core if no other module matched
    if not modules:
        modules.append('module:core')
    
    return modules


def augment_tags(tag_str, sentence_or_sample, card_type=None):
    """Augment tags with register, frequency, domain, cefr, module, and card-type.
    
    Args:
        tag_str: existing tags (space-separated)
        sentence_or_sample: text to infer domain from
        card_type: optional card type (recognition/contrast/production/cloze)
    
    Returns: augmented tag string
    """
    existing = tag_str.split()
    keep = [t for t in existing if not t.startswith(NEW_PREFIXES) 
            and not t.startswith('module:') and not t.startswith('card-type:')]
    tag_set = set(keep)
    new_tags = [
        infer_register(tag_set),
        infer_frequency(tag_set),
        infer_domain(sentence_or_sample),
        infer_cefr(tag_set),
    ]
    
    # Add module tags (may be multiple)
    new_tags.extend(infer_module(tag_set))
    
    # Add card-type if provided and not already present
    if card_type and not any(t.startswith('card-type:') for t in existing):
        new_tags.append(f'card-type:{card_type}')
    
    return " ".join(keep + new_tags)


# ── File I/O ─────────────────────────────────────────────────────────────
SCHEMAS = {
    # Schema: Sentence|Label|Aspect|Formula|MainUse|QuickCue|Contrast|WhenNotToUse|Tags
    "conjugations_recognition.txt": {"tag_idx": 8, "text_idx": 0, "fields": 9, "card_type": "recognition"},
    "conjugations_contrast.txt":     {"tag_idx": 6, "text_idx": 0, "fields": 7, "card_type": "contrast"},
    "conjugations_production.txt":   {"tag_idx": 5, "text_idx": 3, "fields": 6, "card_type": "production"},
    # Schema: Text|Hint|Tags  (3 fields)
    "conjugations_cloze.txt":        {"tag_idx": 2, "text_idx": 0, "fields": 3, "card_type": "cloze"},
}


def process_file(path: Path, spec):
    if not path.exists():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    out_lines = []
    rows_changed = 0
    card_type = spec.get("card_type")
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
        new_tags = augment_tags(row[spec["tag_idx"]], text, card_type=card_type)
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
