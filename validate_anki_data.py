"""
Validate all three Anki source files against the new rich-field schemas.

Recognition: Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | Tags
Contrast:    Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
Production:  Prompt | Target | Aspect | Sample | Why | Tags
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

FILES = {
    'conjugations_recognition.txt': {
        'header': ['Sentence', 'Label', 'Aspect', 'Formula', 'MainUse', 'QuickCue', 'Contrast', 'WhenNotToUse', 'Tags'],
        'required': ['Sentence', 'Label', 'Formula', 'MainUse', 'Tags'],
        'type': 'rec',
        'card_tag': 'recognition',
    },
    'conjugations_contrast.txt': {
        'header': ['Sentence', 'OptionA', 'OptionB', 'Answer', 'Why', 'Tip', 'Tags'],
        'required': ['Sentence', 'OptionA', 'OptionB', 'Answer', 'Why', 'Tags'],
        'type': 'con',
        'card_tag': 'contrast',
    },
    'conjugations_production.txt': {
        'header': ['Prompt', 'Target', 'Aspect', 'Sample', 'Why', 'Tags'],
        'required': ['Prompt', 'Target', 'Sample', 'Tags'],
        'type': 'pro',
        'card_tag': 'production',
    },
    'conjugations_cloze.txt': {
        'header': ['Text', 'Hint', 'Tags'],
        'required': ['Text', 'Tags'],
        'type': 'cloze',
        'card_tag': 'cloze',
    },
}

# Canonical Tier-3 taxonomy vocabularies (must agree with apply_taxonomy_tags.py).
# Image-Cue (was 'image') was retired in v2.7.0 — see CHANGELOG.
CARD_TYPE_TAGS = {'recognition', 'contrast', 'production', 'cloze'}
ALLOWED_REGISTERS = {'formal', 'neutral', 'informal', 'spoken', 'academic'}
ALLOWED_FREQUENCIES = {'high', 'mid', 'low'}
ALLOWED_DOMAINS = {
    'work', 'travel', 'news', 'dialogue', 'academic', 'narrative',
    'kitchen', 'sport', 'tech', 'family', 'general',
}

ALLOWED_LABELS = {
    # Core tense/aspect
    'Present Simple', 'Present Continuous', 'Present Perfect', 'Present Perfect Continuous',
    'Past Simple', 'Past Continuous', 'Past Perfect', 'Past Perfect Continuous',
    'Future Simple', 'Future Continuous', 'Future Perfect', 'Future Perfect Continuous',
    'Conditional Simple', 'Conditional Continuous', 'Conditional Perfect',
    'Conditional Perfect Continuous',
    # Present perfect uses
    'Present Perfect (Just)', 'Present Perfect (Already)', 'Present Perfect (Still)',
    # Past simple uses
    'Past Simple (Narrative Sequence)',
    # Past perfect continuous uses
    'Past Perfect Continuous (Narrative)',
    # Future forms
    'Be Going To', 'Present Continuous for Future Arrangement', 'Present Simple for Schedule',
    'Was/Were Going To', 'Be About To', 'Due To (Formal Future)',
    'Future Simple (will — offer)', 'Future Simple (will — promise)',
    'Present Continuous (Trend)', 'Present Continuous (Complaint)',
    'Future Continuous (Polite Enquiry)',
    # Conditionals
    'Zero Conditional', 'First Conditional', 'Second Conditional',
    'Third Conditional', 'Mixed Conditional',
    'Wish (Present Unreal)', 'Wish (Past Regret)',
    'If Only (Present Unreal)', 'If Only (Past Regret)',
    'Inverted Conditional (Third)', 'Inverted Conditional (Second)',
    'As Long As (Conditional)', 'As Long As (Permission)',
    'Provided That (Conditional)',
    # Passive
    'Present Simple Passive', 'Past Simple Passive', 'Present Perfect Passive',
    'Modal Passive', 'Present Continuous Passive',
    'Past Continuous Passive', 'Past Perfect Passive',
    'Get-Passive', 'Gerund Passive', 'Infinitive Passive', 'Dative Passive',
    'Active (Present Simple)', 'Active (Modal)', 'Past Simple Active',
    'Past Continuous Active',
    'Past Simple Passive (with agent)',
    # Stative / dynamic
    'Present Simple (Stative)', 'Present Continuous (Dynamic)',
    'Present Continuous (Dynamic Stative Shift)',
    # Reported speech
    'Reported Speech (Backshift)', 'Reported Speech (No Backshift)',
    'Reported Speech (Question)',
    # Time clauses
    'Time Clause (Future)', 'Time Clause (Past Perfect)',
    'Time Clause (Past Continuous)', 'Time Clause (Imperative + Before)',
    'Time Clause (Future Perfect)',
    # Composite / contrast labels
    'Future Simple (will)', 'Future Simple (will) vs Be Going To',
    'Future Simple (will) — request', 'Future Continuous — request',
    'Future Continuous — polite enquiry',
    'Present Simple (Stative) vs Present Continuous (Dynamic)',
    'Unless + First Conditional', 'As Long As + First Conditional',
    'Past Simple + Past Simple', 'Past Perfect + Past Simple',
    'Past Continuous + Past Simple',
    # ─── Modules 08–13: modals, reported speech, subjunctive, phrasal verbs,
    #     discourse, L1-interference (auto-generated)
    'Academic Hedging (It Could Be Argued)',
    'Academic Hedging Modal (Could)', 'Academic Hedging Modal (May)',
    'Academic Hedging Modal (Might)',
    'As If / As Though (Real)', 'As If / As Though (Unreal)',
    'Caption Present', 'Cleft Sentence (It-Cleft)',
    'Conditional (Polite Request)', 'Emphatic Do',
    'Future Perfect Simple', 'Future Simple (Formal Announcement)',
    'Going-To (Imminent)', 'Headline Present',
    'Historical Present (Narrative)', 'Historical Present (Sports Commentary)',
    'Hypothetical Past (Politeness)', 'Hypothetical Past Continuous (Politeness)',
    'If Only (Future)', "It's Time (Past Subjunctive)",
    'Mandative Subjunctive',
    # Modals
    'Modal (Be Able To)', 'Modal (Be Supposed To)',
    'Modal (Can — Ability)', "Modal (Can't — Negative Deduction)",
    'Modal (Could — Past Ability)', 'Modal (Had Better)',
    'Modal (Have To — External Obligation)',
    'Modal (May — Permission)', 'Modal (May — Possibility)',
    'Modal (Might — Possibility)', 'Modal (Must — Deduction)',
    'Modal (Must — Obligation)', 'Modal (Ought To)',
    'Modal (Should — Advice)', 'Modal (Used To)',
    'Modal (Would — Past Habit)',
    "Modal Perfect (Can't Have)", 'Modal Perfect (Could Have)',
    'Modal Perfect (Might Have)', 'Modal Perfect (Must Have)',
    "Modal Perfect (Needn't Have)", 'Modal Perfect (Should Have)',
    'Past Continuous (Tentative Request)', 'Past Perfect Simple',
    'Past Simple (Polite Distancing)', 'Performative Present',
    # Phrasal verbs (top 60)
    'Phrasal Verb (break down)', 'Phrasal Verb (break in)',
    'Phrasal Verb (break into)', 'Phrasal Verb (break out)',
    'Phrasal Verb (break up)', 'Phrasal Verb (bring about)',
    'Phrasal Verb (bring back)', 'Phrasal Verb (bring in)',
    'Phrasal Verb (bring up)', 'Phrasal Verb (calm down)',
    'Phrasal Verb (carry on)', 'Phrasal Verb (carry out)',
    'Phrasal Verb (carry over)', 'Phrasal Verb (come up with)',
    'Phrasal Verb (fall apart)', 'Phrasal Verb (fall behind)',
    'Phrasal Verb (fall through)', 'Phrasal Verb (find out)',
    'Phrasal Verb (get along with)', 'Phrasal Verb (get away with)',
    'Phrasal Verb (get over)', 'Phrasal Verb (get up)',
    'Phrasal Verb (give up)', 'Phrasal Verb (go ahead)',
    'Phrasal Verb (go off)', 'Phrasal Verb (go on)',
    'Phrasal Verb (go over)', 'Phrasal Verb (go through)',
    'Phrasal Verb (hand in)', 'Phrasal Verb (hand out)',
    'Phrasal Verb (hand over)', 'Phrasal Verb (hold back)',
    'Phrasal Verb (hold on)', 'Phrasal Verb (hold up)',
    'Phrasal Verb (look after)', 'Phrasal Verb (look down on)',
    'Phrasal Verb (look for)', 'Phrasal Verb (look forward to)',
    'Phrasal Verb (look into)', 'Phrasal Verb (look up to)',
    'Phrasal Verb (look up)', 'Phrasal Verb (make out)',
    'Phrasal Verb (make up for)', 'Phrasal Verb (make up)',
    'Phrasal Verb (pick up)', 'Phrasal Verb (put up with)',
    'Phrasal Verb (run out of)', 'Phrasal Verb (set aside)',
    'Phrasal Verb (set off)', 'Phrasal Verb (set out)',
    'Phrasal Verb (set up)', 'Phrasal Verb (take off)',
    'Phrasal Verb (take on)', 'Phrasal Verb (take out)',
    'Phrasal Verb (take over)', 'Phrasal Verb (turn around)',
    'Phrasal Verb (turn down)', 'Phrasal Verb (turn off)',
    'Phrasal Verb (turn on)', 'Phrasal Verb (turn up)',
    'Phrasal Verb (work out)',
    # L1 interference labels appearing as PRO Targets (canonical English forms)
    'Past Simple or Present Perfect', 'Present Perfect Simple',
    # Reported speech variants
    'Reported Speech (Wh-Question)', 'Reported Speech (Command)',
    'Reported Speech (Request)', 'Reported Speech (Suggest/Recommend)',
    # Subjunctive variants
    'Would Rather (Same Subject)', 'Would Rather (Different Subject)',
    'Wish (Future Annoyance)',
    # Discourse variants
    'Recipe Imperative', 'Stage Directions (Present)',
    'Will (Spontaneous Decision)', 'Pseudo-Cleft (What-Cleft)',
    # Passive paradigm completion
    'Future Simple Passive', 'Future Perfect Passive',
    'Conditional Passive (Second)', 'Conditional Perfect Passive (Third)',
    'Get-Passive (Past)', 'Get-Passive (Perfect)',
    'Causative Have', 'Causative Get',
    'Need + Gerund Passive',
    # Inverted/alternative conditionals
    'Suppose / Supposing (Conditional)',
    'Implicit Conditional (Imperative + And)',
    # Non-finite forms (module 10)
    'Gerund (Subject)', 'Gerund (After Verb)', 'Gerund (After Preposition)',
    'Infinitive (After Verb)', 'Infinitive (After Adjective)',
    'Infinitive (After Too/Enough)', 'Infinitive of Purpose',
    'Bare Infinitive (Modal)', 'Bare Infinitive (Let/Make)',
    'Bare Infinitive (Help)',
    'Perfect Infinitive', 'Perfect Gerund', 'Perfect Participle',
    'Present Participle (Adverbial)',
    # ─── Tier 1 expansions: missing topic clusters ───
    # Auxiliary ellipsis
    'Auxiliary Ellipsis (So + Aux + Subject)',
    'Auxiliary Ellipsis (Neither/Nor + Aux + Subject)',
    'Auxiliary Ellipsis (Short Reply)',
    # Tag questions
    'Tag Question (Positive Statement)', 'Tag Question (Negative Statement)',
    'Tag Question (Imperative)', 'Tag Question (Modal)',
    # Raising vs control
    'Raising Verb (Seem/Appear)', 'Control Verb (Want/Promise/Manage)',
    # Ditransitive passive
    'Ditransitive Passive (Recipient Subject)',
    'Ditransitive Passive (Theme Subject)',
    # Ergative / middle voice
    'Ergative (Inchoative)', 'Middle Voice (Generic)',
    # Reduced relative clauses
    'Reduced Relative (Present Participle)', 'Reduced Relative (Past Participle)',
    # Double passive
    'Double Passive (be + V-ed + to be + V-ed)',
    # Inversion after negative adverbials
    'Negative Inversion (Hardly/Scarcely)', 'Negative Inversion (Not Only)',
    'Negative Inversion (Never/Seldom/Rarely)', 'Negative Inversion (No Sooner)',
    'Negative Inversion (Only After/When)',
    # Inverted conditionals (third)
    'Inverted Conditional (Should — First)',
    # Light/delexical verbs
    'Light Verb (Have)', 'Light Verb (Take)', 'Light Verb (Make)',
    'Light Verb (Do)', 'Light Verb (Give)',
    # Formal BE + to-infinitive
    'Be + To-Infinitive (Formal Future)',
    # Shall
    'Shall (Suggestion)', 'Shall (Formal Future)',
    # Semi-modals
    'Semi-Modal (Dare)', 'Semi-Modal (Need)',
    'Modal (Would Rather)', 'Modal (Would Sooner)',
    # Suppose / supposing / provided / providing
    'Suppose (Conditional Suggestion)', 'Supposing (Hypothetical)',
    'Providing (Conditional)', 'On Condition That',
    'In Case (Precaution)',
    # Comparative inversion
    'Comparative Correlative (The …er, the …er)',
    # Even if / even though
    'Even If (Hypothetical Concession)', 'Even Though (Real Concession)',
    # Implicit conditional
    'Implicit Conditional (Coordination)',
    # Future-in-the-past
    'Future-in-the-Past (Was Going To)', 'Future-in-the-Past (Would)',
    'Future-in-the-Past (Was About To)',
    # Narrative tense layering
    'Narrative Layering (Past Simple + Past Continuous + Past Perfect)',
    # Modal + perfect continuous
    'Modal Perfect Continuous (Must Have Been V-ing)',
    'Modal Perfect Continuous (Should Have Been V-ing)',
    'Modal Perfect Continuous (Could Have Been V-ing)',
    # Embedded / indirect questions
    'Embedded Question (Yes/No)', 'Embedded Question (Wh-)',
    # Reporting verb patterns
    'Reporting Verb (Admit + V-ing)', 'Reporting Verb (Deny + V-ing)',
    'Reporting Verb (Suggest + V-ing)', 'Reporting Verb (Accuse Of + V-ing)',
    'Reporting Verb (Apologise For + V-ing)', 'Reporting Verb (Blame For + V-ing)',
    'Reporting Verb (Promise + To-Inf)', 'Reporting Verb (Refuse + To-Inf)',
    # Backshift exceptions
    'Reported Speech (Universal Truth — No Backshift)',
    'Reported Speech (Conditional 2/3 — No Backshift)',
    # Wish + would
    'Wish (Annoyance — Would)', 'Wish (Polite Request — Would)',
    # AmE vs BrE
    'Past Simple (American Variant)', 'Present Perfect (British Variant)',
    # Habitual would
    'Would (Habitual Past)', 'Used To (Habitual Past)',
    # As if / as though nuanced
    'As If / As Though (Past Perfect — Counterfactual)',
    # It's high time
    "It's High Time (Past Subjunctive)",
    # Cleft with verbs
    "Cleft Conditional (If It Weren't For)",
    # Causative production/contrast labels
    'Causative Have (Service)', 'Causative Get (Result)',
    'Causative Make (Compulsion)', 'Causative Let (Permission)',
    'Causative Help (Bare or To-Inf)',
    # ─── P1 wave additions: inversion + cleft ───
    'Reverse Pseudo-Cleft', 'Locative Inversion', 'Comparative/Degree Inversion',
    'Negative Inversion (Hardly)', 'Negative Inversion (No sooner)',
    'Negative Inversion (Never)', 'Negative Inversion (Rarely)',
    'Negative Inversion (Only after)', 'Negative Inversion (Only when)',
    'Negative Inversion (Not only… but also)', 'Negative Inversion (Seldom)',
    'Negative Inversion (Little did)', 'Negative Inversion (Scarcely)',
    'Negative Inversion (Under no circumstances)',
    'Negative Inversion (At no point)', 'Negative Inversion (On no account)',
    'Negative Inversion (Not until)', 'Negative Inversion (In no way)',
    # ─── P0 wave additions ───
    # A1/A2 ramp basics
    'Yes/No Question', 'Wh-Question', 'Short Answer',
    'Future Going To', 'Modal',
    'There Is / There Are', 'Have Got', 'Be (Identity)', 'Be (State)',
    'Imperative', 'Imperative (Negative)',
    'Can (Ability)', 'Can (Permission)', "Can't (Inability)",
    'Past Simple Irregular', 'Past Simple Regular', 'Past Simple Negative',
    'Past Simple Question',
    # Listening / phonology module
    'T-flapping', 'Linking R', 'Linking R or Linking Consonant',
    'T-flapping and Linking',
    'Reduction (gonna)', 'Reduction (wanna)', 'Reduction (gotta)',
    'Reduction (hafta)', 'Reduction (shoulda)', 'Reduction (woulda)',
    'Reduction (kinda)',
    'Contraction (have)', 'Contraction (is/has)', 'Contraction (had/would)',
    'Contraction Ambiguity (had/would)',
    'Modal Weak Form (can)', 'Modal Weak Form (must)',
    'Modal Weak Form (should)', 'Modal Weak Form (would)',
    'Stress Contrast (was/were)', 'Stress Contrast (modal)',
}

# Allow any label whose stem matches these phonological/connected-speech families
# (subagent-generated phrasing varies; we accept them as canonical).
PHON_LABEL_PREFIXES = (
    'Connected Speech',
    'Reduction (', 'Contraction (', 'Contraction Ambiguity',
    'Modal Weak Form', 'Stress Contrast', 'T-flap', 'Linking',
    'Weak Form',
)

# Permit any label that begins with one of these canonical prefixes (extension-friendly)
ALLOWED_LABEL_PREFIXES = (
    'Phrasal Verb (',
    'Modal (',
    'Modal Perfect (',
    'L1 Error Correction (',
    'Academic Hedging',
    'Historical Present',
    'Hypothetical Past',
) + PHON_LABEL_PREFIXES

# L1-interference recognition cards label the *trap*, not a tense — these are
# additional canonical labels for cross-linguistic transfer phenomena.
L1_TRAP_LABELS = {
    'Age Expression', 'Physical State', 'Third Person -s',
    'Article Use', 'Question Word Order', 'Present Perfect Duration',
    'Adjective Placement', 'Recent Past', 'Gerund After Verb',
    'Past Tense Morphology', 'Copula Presence', 'Existential There',
    'Adverbial Placement', 'V2 Word Order', 'Get vs Become',
    'Since vs For Duration', 'Until vs By', 'Perfect Tense Word Order',
    'Possession Existential', 'Negation Structure', 'Subject Presence',
    'Plural Marking', 'Preposition Use', 'Subject Case',
}
ALLOWED_LABELS |= L1_TRAP_LABELS

ALLOWED_ASPECTS = {
    'simple', 'progressive', 'perfective', 'perfect-progressive',
    'stative', 'modal', 'intentional',
    'zero', 'first', 'second', 'third', 'mixed',
    'backshift',
    # L1-interference rows describe a structural phenomenon rather than a verb
    # aspect; these are canonical "trap" categories.
    'agreement', 'articles', 'syntax', 'aspect', 'non-finite',
    'tense', 'be-verb', 'word-order', 'existential', 'preposition',
    'semantics', 'negation', 'pronoun', 'plural', 'possessive',
    # P0 additions
    'phonology', 'perfect', 'imperative', 'question',
}

# Canonical Label/Target → Aspect mapping. If a label appears here, the row's
# Aspect cell MUST match exactly. Labels not listed are unconstrained (their
# aspect is whatever the row supplies, validated only against ALLOWED_ASPECTS).
LABEL_TO_ASPECT = {
    'Present Simple': 'simple', 'Past Simple': 'simple', 'Future Simple': 'simple',
    'Conditional Simple': 'simple',
    'Present Continuous': 'progressive', 'Past Continuous': 'progressive',
    'Future Continuous': 'progressive', 'Conditional Continuous': 'progressive',
    'Present Perfect': 'perfective', 'Past Perfect': 'perfective',
    'Future Perfect': 'perfective', 'Conditional Perfect': 'perfective',
    'Present Perfect Continuous': 'perfect-progressive',
    'Past Perfect Continuous': 'perfect-progressive',
    'Future Perfect Continuous': 'perfect-progressive',
    'Conditional Perfect Continuous': 'perfect-progressive',
    'Be Going To': 'intentional',
    'Zero Conditional': 'zero', 'First Conditional': 'first',
    'Second Conditional': 'second', 'Third Conditional': 'third',
    'Mixed Conditional': 'mixed',
}

# Canonical Label/Target/Answer → required tense-family tag substring. The
# row's Tags must contain at least one tag token whose value is the canonical
# slug OR begins with `<slug>-` / contains `-<slug>-` / equals `<slug>-vs-…`
# (to accommodate composite contrast tags like `present-simple-vs-present-continuous`
# and module variants like `future-will-simple`).
LABEL_TO_TENSE_TAG = {
    'Present Simple': 'present-simple',
    'Present Continuous': 'present-continuous',
    'Present Perfect': 'present-perfect',
    'Present Perfect Continuous': 'present-perfect-continuous',
    'Past Simple': 'past-simple',
    'Past Continuous': 'past-continuous',
    'Past Perfect': 'past-perfect',
    'Past Perfect Continuous': 'past-perfect-continuous',
    'Future Simple': 'future-simple',
    'Future Continuous': 'future-continuous',
    'Future Perfect': 'future-perfect',
    'Future Perfect Continuous': 'future-perfect-continuous',
    'Conditional Simple': 'conditional-simple',
    'Conditional Continuous': 'conditional-continuous',
    'Conditional Perfect': 'conditional-perfect',
    'Conditional Perfect Continuous': 'conditional-perfect-continuous',
    'Be Going To': 'future-going-to',
    'Zero Conditional': 'conditional-zero',
    'First Conditional': 'conditional-first',
    'Second Conditional': 'conditional-second',
    'Third Conditional': 'conditional-third',
    'Mixed Conditional': 'conditional-mixed',
}


# Module-specific tense tag synonyms / abbreviations. Each canonical slug also
# matches any of these alternative tokens (or tokens containing them).
TENSE_TAG_SYNONYMS = {
    'future-simple':           {'future-will-simple', 'future-will-vs-going-to'},
    'future-going-to':         {'future-will-vs-going-to'},
    'future-continuous':       {'future-will-continuous'},
    'future-perfect':          {'future-will-perfect'},
    'future-perfect-continuous': {'future-will-perfect-continuous'},
    'past-perfect-continuous': {'ppc'},
    'present-perfect-continuous': {'ppc'},
    # Composite contrast tags such as `conditional-second-vs-third` count for
    # both endpoints.
    'conditional-zero':  {'conditional-zero-vs-first'},
    'conditional-first': {'conditional-zero-vs-first', 'conditional-first-vs-second'},
    'conditional-second': {'conditional-first-vs-second', 'conditional-second-vs-third'},
    'conditional-third': {'conditional-second-vs-third', 'conditional-third-vs-mixed'},
    'conditional-mixed': {'conditional-third-vs-mixed'},
}


def _tense_tag_present(tags, slug):
    """Return True if `tags` contains a tag token related to `slug`.

    Accepted forms (so module-specific variants like `future-will-simple`
    and contrast composites like `present-simple-vs-present-continuous`
    still match):
      - exact: slug
      - prefix: slug + '-' + …  (e.g. present-perfect-continuous matches present-perfect)
      - infix: …'-' + slug + '-' + … or ends with -slug
      - composite: '-vs-' + slug or slug + '-vs-' anywhere
      - synonym: any token in TENSE_TAG_SYNONYMS[slug] (or containing it)
    """
    candidates = {slug} | TENSE_TAG_SYNONYMS.get(slug, set())
    for t in tags:
        for cand in candidates:
            if t == cand or t.startswith(cand + '-') or t.endswith('-' + cand):
                return True
            if ('-' + cand + '-') in t:
                return True
    return False


# Canonical morphological signatures for production Sample sniff-checking.
# If Target is in this map, the Sample text must match the regex (case-insensitive).
import re as _re
TARGET_SAMPLE_PATTERNS = {
    'Present Perfect Continuous': _re.compile(r"\b(have|has|'ve|'s)\s+been\s+\w+ing\b", _re.I),
    'Past Perfect Continuous':    _re.compile(r"\b(had|'d)\s+been\s+\w+ing\b", _re.I),
    'Future Perfect Continuous':  _re.compile(r"\b(will|'ll)\s+have\s+been\s+\w+ing\b", _re.I),
    # Allow inverted/short forms: "Have you eaten?", "No, I haven't eaten yet."
    'Present Perfect':            _re.compile(r"\b(have|has|haven't|hasn't|'ve|'s)\s+(?:\w+\s+)?(\w+|not\s+\w+|already\s+\w+|just\s+\w+|never\s+\w+|ever\s+\w+)", _re.I),
    'Past Perfect':               _re.compile(r"\b(had|hadn't|'d)\s+(?:\w+\s+)?(\w+|not\s+\w+|already\s+\w+|just\s+\w+|never\s+\w+)", _re.I),
    'Future Perfect':             _re.compile(r"\b(will|'ll)\s+have\s+(?!been\b)\w+", _re.I),
    # Allow inverted question word order: "What are you doing?" / "Why is she crying?"
    'Present Continuous':         _re.compile(r"\b(am|is|are|'m|'s|'re)\s+(?:\w+\s+)?(?:not\s+)?\w+ing\b", _re.I),
    'Past Continuous':            _re.compile(r"\b(was|were)\s+(?:\w+\s+)?(?:not\s+)?\w+ing\b", _re.I),
    'Future Continuous':          _re.compile(r"\b(will|'ll)\s+(?:\w+\s+)?be\s+\w+ing\b", _re.I),
    # Be Going To: declarative `is going to`, negative `is not going to`,
    # and inverted question form `Are you going to …?`
    'Be Going To':                _re.compile(r"\b(am|is|are|'m|'s|'re)\s+\w*\s*(?:not\s+)?going\s+to\s+\w+|\b(am|is|are)\s+\w+\s+going\s+to\s+\w+", _re.I),
}


def load_rows(path, expected_header):
    """Parse a TSV with Anki-style #columns: header and #-comment metadata.

    The header is taken from the `#columns:Sentence\tLabel\t...` directive
    (Anki's own format). All non-comment lines are data rows.
    """
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    header = None
    data_lines = []
    for line in lines:
        if line.startswith('#columns:'):
            header = line[len('#columns:'):].split('\t')
        elif line and not line.startswith('#'):
            data_lines.append(line)
    if header is None:
        # Fallback: first non-comment line is the header (legacy)
        reader = csv.reader(data_lines, delimiter='\t', quotechar='"')
        header = next(reader)
        return header, list(reader)
    reader = csv.reader(data_lines, delimiter='\t', quotechar='"')
    return header, list(reader)


def validate_file(path, spec, errors):
    expected_header = spec['header']
    required = spec['required']
    n_fields = len(expected_header)
    type_ = spec['type']

    header, rows = load_rows(path, expected_header)

    if header != expected_header:
        errors.append(f'{path}: header mismatch\n  expected: {expected_header}\n  got:      {header}')
        return 0

    tag_idx = expected_header.index('Tags')

    for i, row in enumerate(rows, start=2):
        if len(row) != n_fields:
            errors.append(f'{path}:{i}: expected {n_fields} columns, got {len(row)}')
            continue

        field_map = dict(zip(expected_header, row))

        # Required field emptiness check
        for req in required:
            if not field_map.get(req, '').strip():
                errors.append(f'{path}:{i}: empty required field "{req}"')

        # Determine the row's "key label" (for recognition: Label;
        # production: Target; contrast: Answer) — used for cross-rule checks.
        key_label = ''
        if type_ == 'rec':
            key_label = field_map.get('Label', '').strip()
        elif type_ == 'pro':
            key_label = field_map.get('Target', '').strip()
        elif type_ == 'con':
            key_label = field_map.get('Answer', '').strip()

        # Label validation for recognition
        if type_ == 'rec':
            if key_label not in ALLOWED_LABELS and not key_label.startswith(ALLOWED_LABEL_PREFIXES):
                errors.append(f'{path}:{i}: unknown label "{key_label}"')

        # Aspect must be a known token AND match its label's canonical aspect
        if type_ in ('rec', 'pro'):
            aspect = field_map.get('Aspect', '').strip()
            if aspect and aspect not in ALLOWED_ASPECTS:
                errors.append(f'{path}:{i}: unknown aspect "{aspect}"')
            expected_aspect = LABEL_TO_ASPECT.get(key_label)
            if expected_aspect and aspect and aspect != expected_aspect:
                errors.append(
                    f'{path}:{i}: aspect "{aspect}" does not match '
                    f'label/target "{key_label}" (expected "{expected_aspect}")'
                )

        # Answer validation for contrast: must match OptionA or OptionB
        if type_ == 'con':
            opt_a = field_map.get('OptionA', '').strip()
            opt_b = field_map.get('OptionB', '').strip()
            if key_label not in (opt_a, opt_b):
                errors.append(f'{path}:{i}: Answer "{key_label}" not in options ("{opt_a}" / "{opt_b}")')

        # Cloze validation: must contain at least one {{c…::…}} marker AND the
        # answer between :: and }} must be non-empty (catches typos like "{{c1::}}").
        if type_ == 'cloze':
            text = field_map.get('Text', '')
            cloze_match = _re.search(r'\{\{c\d+::([^}|]*)(?:\|\|[^}]*)?\}\}', text)
            if not cloze_match:
                errors.append(f'{path}:{i}: cloze row missing or malformed {{c1::…}} marker')
            elif not cloze_match.group(1).strip():
                errors.append(f'{path}:{i}: cloze answer is empty')

        # Production sample must morphologically resemble its Target form
        if type_ == 'pro':
            sample = field_map.get('Sample', '').strip()
            pat = TARGET_SAMPLE_PATTERNS.get(key_label)
            if pat and sample and not pat.search(sample):
                # Allow alternative samples separated by " / " — pass if any half matches
                halves = [h.strip() for h in sample.split('/')]
                if not any(pat.search(h) for h in halves):
                    errors.append(
                        f'{path}:{i}: Sample does not match expected '
                        f'morphology of Target "{key_label}": {sample[:80]!r}'
                    )

        # Tag presence + Tier-3 taxonomy enforcement
        tags_str = field_map.get('Tags', '').strip()
        if not tags_str:
            errors.append(f'{path}:{i}: empty Tags field')
        else:
            toks = tags_str.split()

            # 1. exactly one card-type tag, matching the file
            cts = [t for t in toks if t in CARD_TYPE_TAGS]
            expected_ct = spec['card_tag']
            if not cts:
                errors.append(f'{path}:{i}: missing card-type tag (expected "{expected_ct}")')
            elif len(cts) > 1:
                errors.append(f'{path}:{i}: multiple card-type tags {cts} (expected exactly one "{expected_ct}")')
            elif cts[0] != expected_ct:
                errors.append(f'{path}:{i}: wrong card-type tag "{cts[0]}" (expected "{expected_ct}")')

            # 2. exactly one register / frequency / domain, from canonical vocab
            for family, allowed in (
                ('register', ALLOWED_REGISTERS),
                ('frequency', ALLOWED_FREQUENCIES),
                ('domain', ALLOWED_DOMAINS),
            ):
                vals = [t.split(':', 1)[1] for t in toks if t.startswith(family + ':')]
                if not vals:
                    errors.append(f'{path}:{i}: missing required tag family "{family}:"')
                elif len(vals) > 1:
                    errors.append(f'{path}:{i}: multiple "{family}:" tags ({vals})')
                else:
                    if vals[0] not in allowed:
                        errors.append(f'{path}:{i}: unknown {family} value "{vals[0]}"')

            # 3. legacy dash-style register- tokens are forbidden (use register: instead)
            legacy = [t for t in toks if t.startswith('register-')]
            if legacy:
                errors.append(f'{path}:{i}: legacy register-* tags {legacy} — use register:* form')

            # 4. duplicate tag tokens within a row
            if len(toks) != len(set(toks)):
                dupes = sorted({t for t in toks if toks.count(t) > 1})
                errors.append(f'{path}:{i}: duplicate tag tokens {dupes}')

            # 5. tense-family tag must agree with row's key label/target/answer
            #    (with variant-prefix matching so module-specific or composite
            #    tags like `future-will-simple` and `present-simple-vs-…` count).
            expected_slug = LABEL_TO_TENSE_TAG.get(key_label)
            if expected_slug and not _tense_tag_present(toks, expected_slug):
                errors.append(
                    f'{path}:{i}: tags missing tense-family tag for '
                    f'"{key_label}" (expected something like "{expected_slug}")'
                )

    return len(rows)


def cross_file_label_agreement(all_data):
    """Detect identical Sentences appearing across files with disagreeing labels.

    `all_data` maps path → (header, rows). Returns a list of error strings.
    """
    errs = []
    # sentence -> list of (path, line_no, label_kind, label_value)
    sightings = {}
    for path, (header, rows) in all_data.items():
        spec = FILES[path]
        type_ = spec['type']
        if type_ == 'cloze':
            continue  # cloze sentences contain {{c1::}} markup, not comparable
        if type_ == 'rec':
            sent_col, lbl_col = 'Sentence', 'Label'
        elif type_ == 'con':
            sent_col, lbl_col = 'Sentence', 'Answer'
        elif type_ == 'pro':
            # Production rows have a Prompt + Sample, no shared Sentence with
            # other files; skip.
            continue
        else:
            continue
        si = header.index(sent_col)
        li = header.index(lbl_col)
        for i, r in enumerate(rows, start=2):
            if len(r) <= max(si, li):
                continue
            key = r[si].strip().rstrip('.').lower()
            if not key:
                continue
            sightings.setdefault(key, []).append((path, i, lbl_col, r[li].strip()))
    for key, occs in sightings.items():
        labels = {o[3] for o in occs}
        if len(occs) >= 2 and len(labels) > 1:
            locations = ', '.join(f'{p}:{ln}({lk}={lv!r})' for p, ln, lk, lv in occs)
            errs.append(
                f'cross-file label disagreement for sentence {key[:60]!r}: {locations}'
            )
    return errs


# ── Audio manifest validation ────────────────────────────────────────────
AUDIO_DIR        = Path('media/audio')
AUDIO_MANIFEST   = Path('media/audio_manifest.json')
_AUDIO_CLOZE_RE  = _re.compile(r'\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}')
_AUDIO_BLANK_RE  = _re.compile(r'_{3,}|\[blank\]|\(blank\)', _re.IGNORECASE)
_AUDIO_CHOICE_ANNOTATION_RE = _re.compile(r'\s*\([^)]*\)\s*$')


def _audio_text_hash(text: str) -> str:
    return hashlib.sha1(text.strip().encode('utf-8')).hexdigest()[:12]


def _audio_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _audio_strip_choice_annotation(text: str) -> str:
    return _AUDIO_CHOICE_ANNOTATION_RE.sub('', (text or '').strip()).strip()


def _audio_spoken_sentence(sentence: str, *, option_a: str = '', option_b: str = '', answer: str = '') -> str:
    spoken = _AUDIO_CLOZE_RE.sub(r'\1', (sentence or '').strip())
    if _AUDIO_BLANK_RE.search(spoken):
        fill = (answer or '').strip()
        if fill == (option_a or '').strip():
            fill = option_a
        elif fill == (option_b or '').strip():
            fill = option_b
        fill = _audio_strip_choice_annotation(fill)
        if fill:
            spoken = _AUDIO_BLANK_RE.sub(fill, spoken)
    return spoken


def _audio_corpus_sentences(all_data):
    """Return the set of unique English sentences for which audio is expected.
    Mirrors collect_sentences() in build_audio.py."""
    sentences = set()
    for path, (header, rows) in all_data.items():
        if path.endswith('conjugations_recognition.txt'):
            for r in rows:
                if r and r[0].strip():
                    sentences.add(r[0].strip())
        elif path.endswith('conjugations_contrast.txt'):
            for r in rows:
                if r and r[0].strip():
                    option_a = r[1] if len(r) > 1 else ''
                    option_b = r[2] if len(r) > 2 else ''
                    answer = r[3] if len(r) > 3 else ''
                    sentences.add(
                        _audio_spoken_sentence(
                            r[0].strip(),
                            option_a=option_a,
                            option_b=option_b,
                            answer=answer,
                        )
                    )
        elif path.endswith('conjugations_production.txt'):
            for r in rows:
                if len(r) >= 4 and r[3].strip():
                    sentences.add(r[3].strip())
        elif path.endswith('conjugations_cloze.txt'):
            for r in rows:
                if r and r[0].strip():
                    sentences.add(_audio_spoken_sentence(r[0].strip()))
    return sentences


def validate_audio_manifest(all_data, errors, *, verify_sha=False, require=False):
    """Audio rule:
       1. media/audio_manifest.json exists and is valid JSON v1.
       2. Every corpus sentence has a manifest entry whose text matches and
          whose hash matches the expected sha1[:12].
       3. Each entry's MP3 exists on disk under media/audio/<hash>.mp3.
       4. Optional (verify_sha=True): on-disk sha256 matches manifest sha256.
       5. There are no orphan files on disk that are missing from the manifest
          and not in the corpus.
       6. require=False: if no manifest exists at all (e.g. fresh checkout
          without media), the rule is skipped with a warning rather than an
          error."""
    if not AUDIO_MANIFEST.exists():
        msg = f'audio: {AUDIO_MANIFEST} missing — run `python3 build_audio.py --rehash` after generating audio.'
        if require:
            errors.append(msg)
        else:
            print(f'  audio: skipping (no manifest at {AUDIO_MANIFEST}; pass --require-audio to enforce)')
        return 0

    try:
        manifest = json.loads(AUDIO_MANIFEST.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        errors.append(f'audio: {AUDIO_MANIFEST}: invalid JSON: {e}')
        return 0

    if manifest.get('version') != 1 or 'entries' not in manifest:
        errors.append(f'audio: {AUDIO_MANIFEST}: unsupported version or missing "entries"')
        return 0

    entries = manifest['entries']
    sentences = _audio_corpus_sentences(all_data)
    expected_hashes = {_audio_text_hash(s): s for s in sentences}

    checked = 0
    for h, text in sorted(expected_hashes.items()):
        entry = entries.get(h)
        if entry is None:
            errors.append(f'audio: missing manifest entry for sentence (hash {h}): {text[:60]!r}')
            continue
        if entry.get('text', '').strip() != text:
            errors.append(
                f'audio: manifest text mismatch for hash {h}: '
                f'manifest={entry.get("text", "")[:60]!r} vs corpus={text[:60]!r}'
            )
            continue
        # Recompute hash from manifest text — must agree with the key.
        if _audio_text_hash(entry['text']) != h:
            errors.append(f'audio: hash key {h} does not match sha1(text) for {text[:60]!r}')
        mp3 = AUDIO_DIR / f'{h}.mp3'
        if not mp3.exists():
            errors.append(f'audio: missing MP3 file media/audio/{h}.mp3 for {text[:60]!r}')
            continue
        if mp3.stat().st_size == 0:
            errors.append(f'audio: zero-byte MP3 media/audio/{h}.mp3 for {text[:60]!r}')
            continue
        if verify_sha:
            recorded = entry.get('sha256', '')
            if not recorded:
                errors.append(f'audio: manifest entry {h} missing sha256')
            else:
                actual = _audio_file_sha256(mp3)
                if actual != recorded:
                    errors.append(
                        f'audio: sha256 mismatch for media/audio/{h}.mp3 '
                        f'(manifest={recorded[:12]}…, on-disk={actual[:12]}…)'
                    )
        checked += 1

    # Orphan detection: on-disk MP3s with no corpus sentence.
    if AUDIO_DIR.exists():
        orphans = []
        for mp3 in AUDIO_DIR.glob('*.mp3'):
            if mp3.stem not in expected_hashes:
                orphans.append(mp3.name)
        if orphans:
            head = ', '.join(sorted(orphans)[:5])
            extra = '' if len(orphans) <= 5 else f' (+{len(orphans) - 5} more)'
            errors.append(f'audio: {len(orphans)} orphan MP3(s) on disk not in corpus: {head}{extra}')

    return checked


def main():
    ap_args = sys.argv[1:]
    require_audio = '--require-audio' in ap_args
    verify_audio_sha = '--verify-audio-sha' in ap_args
    skip_audio = '--no-audio-check' in ap_args

    errors = []
    total = 0
    all_data = {}
    for path, spec in FILES.items():
        count = validate_file(path, spec, errors)
        total += count
        print(f'{path}: {count} rows')
        # Re-parse to feed cross-file rules (cheap, files are small).
        all_data[path] = load_rows(path, spec['header'])

    # Cross-file consistency: same sentence shouldn't carry conflicting labels.
    cross_errs = cross_file_label_agreement(all_data)
    errors.extend(cross_errs)
    if cross_errs:
        print(f'\n  cross-file checks: {len(cross_errs)} disagreement(s)')

    if not skip_audio:
        audio_errs_before = len(errors)
        checked = validate_audio_manifest(
            all_data, errors,
            verify_sha=verify_audio_sha, require=require_audio,
        )
        new_audio_errs = len(errors) - audio_errs_before
        if checked or new_audio_errs:
            verb = 'verified' if verify_audio_sha else 'checked'
            print(f'  audio: {verb} {checked} sentence(s); {new_audio_errs} issue(s)')

    if errors:
        print(f'\nValidation FAILED ({len(errors)} errors):')
        for err in errors:
            print(f'  - {err}')
        sys.exit(1)

    print(f'\nValidation passed: {len(FILES)} files, {total} rows.')


if __name__ == '__main__':
    main()
