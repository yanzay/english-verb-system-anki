"""
Validate all three Anki source files against the new rich-field schemas.

Recognition: Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | Tags
Contrast:    Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
Production:  Prompt | Target | Aspect | Sample | Why | Tags
"""
import csv
import sys
from pathlib import Path

FILES = {
    'conjugations_recognition.txt': {
        'header': ['Sentence', 'Label', 'Aspect', 'Formula', 'MainUse', 'QuickCue', 'Contrast', 'Tags'],
        'required': ['Sentence', 'Label', 'Formula', 'MainUse', 'Tags'],
        'type': 'rec',
    },
    'conjugations_contrast.txt': {
        'header': ['Sentence', 'OptionA', 'OptionB', 'Answer', 'Why', 'Tip', 'Tags'],
        'required': ['Sentence', 'OptionA', 'OptionB', 'Answer', 'Why', 'Tags'],
        'type': 'con',
    },
    'conjugations_production.txt': {
        'header': ['Prompt', 'Target', 'Aspect', 'Sample', 'Why', 'Tags'],
        'required': ['Prompt', 'Target', 'Sample', 'Tags'],
        'type': 'pro',
    },
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
}

# Permit any label that begins with one of these canonical prefixes (extension-friendly)
ALLOWED_LABEL_PREFIXES = (
    'Phrasal Verb (',
    'Modal (',
    'Modal Perfect (',
    'L1 Error Correction (',
    'Academic Hedging',
    'Historical Present',
    'Hypothetical Past',
)

ALLOWED_ASPECTS = {
    'simple', 'progressive', 'perfective', 'perfect-progressive',
    'stative', 'modal', 'intentional',
    'zero', 'first', 'second', 'third', 'mixed',
    'backshift',
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

        # Label validation for recognition
        if type_ == 'rec':
            label = field_map.get('Label', '').strip()
            if label not in ALLOWED_LABELS and not label.startswith(ALLOWED_LABEL_PREFIXES):
                errors.append(f'{path}:{i}: unknown label "{label}"')
            aspect = field_map.get('Aspect', '').strip()
            if aspect and aspect not in ALLOWED_ASPECTS:
                errors.append(f'{path}:{i}: unknown aspect "{aspect}"')

        # Answer validation for contrast: must match OptionA or OptionB
        if type_ == 'con':
            answer = field_map.get('Answer', '').strip()
            opt_a = field_map.get('OptionA', '').strip()
            opt_b = field_map.get('OptionB', '').strip()
            if answer not in (opt_a, opt_b):
                errors.append(f'{path}:{i}: Answer "{answer}" not in options ("{opt_a}" / "{opt_b}")')

        # Tag presence
        tags = field_map.get('Tags', '').strip()
        if not tags:
            errors.append(f'{path}:{i}: empty Tags field')

    return len(rows)


def main():
    errors = []
    total = 0
    for path, spec in FILES.items():
        count = validate_file(path, spec, errors)
        total += count
        print(f'{path}: {count} rows')

    if errors:
        print(f'\nValidation FAILED ({len(errors)} errors):')
        for err in errors:
            print(f'  - {err}')
        sys.exit(1)

    print(f'\nValidation passed: {len(FILES)} files, {total} rows.')


if __name__ == '__main__':
    main()
